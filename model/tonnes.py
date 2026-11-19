"""Tonne model: monthly bridge from kilns online to net tCO2e, plus the
closed-form "what has to be true" solver.

Independent analysis using public information and synthetic data.
Not affiliated with or endorsed by Varaha.

Bridge (per month m):
    kilns_online_m = kilns_total * ramp_share_m
    kiln_days_m    = kilns_online_m * (op_days_m * s - relocation_loss_m)
    batches_m      = kiln_days_m * batches_per_kiln_day
    biochar_t_m    = batches_m * dry_biomass_per_batch_t * biochar_yield_dry_frac
    gross_m        = biochar_t_m * Corg * 44/12 * persistence        (all batches)
    rejected_m     = gross_m * (1 - pass_rate)
    project_em_m   = accepted biochar * (CH4_EF * GWP + other)       (claimed batches only)
    buffer_m       = (gross - rejected - project_em) * buffer_frac
    net_m          = gross - rejected - project_em - buffer

Every term is affine in each solver lever, so the solver is exact and closed-form:
    net(x) = a + b·x  ⇒  x* = x0 + (T − net(x0)) / b
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from model.assumptions import (MONTHS, defaults, load_params, meta, monthly_op_days, scenario_mc_ranges,
                               scenario_params, scenarios)

CAL_DAYS_2027 = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
EV_ELEMENTS = ("ev_photo", "ev_temp_log", "ev_feed_weight", "ev_char_weight", "ev_geotag", "ev_timestamp")


# --------------------------------------------------------------------------- unit factors
# All functions below accept scalars or numpy arrays (Monte Carlo) for every parameter.
def _a(p: dict, k: str) -> np.ndarray:
    return np.asarray(p[k], dtype=float)


def evidence_completeness(p: dict):
    """P(all six evidence elements valid) assuming independence."""
    out = 1.0
    for e in EV_ELEMENTS:
        out = out * _a(p, e)
    return out


def dmrv_pass_rate(p: dict):
    """Share of produced batches that end up credited.

    pass = [c + (1 − c)·r] · (1 − quality_rej) · (1 − audit_rej)
    c = evidence completeness, r = remediation share of incomplete batches.
    """
    c = evidence_completeness(p)
    effective = c + (1 - c) * _a(p, "evidence_remediation_frac")
    return effective * (1 - _a(p, "quality_rejection_frac")) * (1 - _a(p, "audit_rejection_frac"))


def gross_t_per_t_biochar(p: dict):
    return _a(p, "biochar_corg_frac") * _a(p, "co2_per_c") * _a(p, "persistence_factor")


def project_em_t_per_t_biochar(p: dict):
    return _a(p, "ch4_ef_g_per_kg_biochar") / 1000.0 * _a(p, "ch4_gwp100") + _a(p, "other_project_emissions_t_per_t_biochar")


def _col(p: dict, k: str) -> np.ndarray:
    """Parameter as a column vector (…, 1) so it broadcasts against the 12-month axis."""
    return _a(p, k)[..., None]


def _days(p: dict) -> np.ndarray:
    return np.stack([_a(p, f"op_days_{m}") for m in MONTHS], axis=-1)


def ramp_shares(p: dict) -> np.ndarray:
    """Share of kilns online per month: linear from ramp_start_share (Jan) to 1.0 at ramp_full_month."""
    start, full = _col(p, "ramp_start_share"), _col(p, "ramp_full_month")
    months = np.arange(1, 13)
    share = start + (1 - start) * (months - 1) / np.maximum(full - 1, 1e-9)
    share = np.where(full <= 1, 1.0, share)
    return np.clip(share, 0, 1)


def relocation_loss_days(p: dict) -> np.ndarray:
    """Operating days lost per kiln per month to site moves, spread pro rata over operating days."""
    lost = 365.0 / _col(p, "relocation_interval_days") * _col(p, "relocation_downtime_days")
    days = _days(p)
    return lost * days / days.sum(axis=-1, keepdims=True)


def cycle_ceiling_batches_per_day(p: dict, shifts: float | None = None) -> float:
    """Max batches per kiln-day given cycle time and crew shifts."""
    cycle = p["burn_time_h"] + p["quench_time_h"] + p["handling_time_h"]
    s = p["shifts_per_kiln_day"] if shifts is None else shifts
    return s * p["working_hours_per_shift"] / cycle


def kiln_fill_ratio(p: dict, dry_biomass_per_batch_t: float | None = None) -> float:
    """Implied biochar volume per batch ÷ kiln volume. >1 means the batch size is physically
    inconsistent with the assumed kiln (needs a bigger kiln or denser char)."""
    dry = p["dry_biomass_per_batch_t"] if dry_biomass_per_batch_t is None else dry_biomass_per_batch_t
    char_m3 = dry * p["biochar_yield_dry_frac"] / p["biochar_bulk_density_t_m3"]
    return char_m3 / p["kiln_volume_m3"]


# --------------------------------------------------------------------------- core (vectorised)
def bridge_arrays(p: dict, *, pass_rate=None, op_days_scale: float = 1.0,
                  kiln_add: tuple[float, int] | None = None) -> dict[str, np.ndarray]:
    """Monthly bridge as arrays of shape (..., 12). Works for scalar or array-valued parameters."""
    pr = dmrv_pass_rate(p) if pass_rate is None else np.asarray(pass_rate, dtype=float)
    pr = np.asarray(pr)[..., None]
    days = _days(p) * op_days_scale
    kilns = _col(p, "kilns_total") * ramp_shares(p)
    if kiln_add is not None:
        extra, from_month = kiln_add
        kilns = kilns + extra * (np.arange(1, 13) >= from_month)
    kiln_days = kilns * np.maximum(days - relocation_loss_days(p), 0) * _col(p, "biomass_availability_factor")
    batches = kiln_days * _col(p, "batches_per_kiln_day")
    dry = batches * _col(p, "dry_biomass_per_batch_t")
    char = dry * _col(p, "biochar_yield_dry_frac")
    gross = char * gross_t_per_t_biochar(p)[..., None]
    rejected = gross * (1 - pr)
    proj = char * pr * project_em_t_per_t_biochar(p)[..., None]
    pre_buffer = gross - rejected - proj
    buffer = pre_buffer * _col(p, "buffer_deduction_frac")
    net = pre_buffer - buffer
    return {"kilns_online": np.broadcast_to(kilns, net.shape), "op_days": np.broadcast_to(days, net.shape),
            "kiln_days": kiln_days, "batches": batches, "dry_feed_t": dry, "biochar_t": char,
            "gross_tco2e": gross, "rejected_tco2e": rejected, "project_emissions_tco2e": proj,
            "buffer_tco2e": buffer, "net_tco2e": net, "pass_rate": np.broadcast_to(pr, net.shape)}


@lru_cache(maxsize=1)
def plan_phasing() -> np.ndarray:
    """Monthly plan (sums to the target): the plan-implied scenario's monthly shape scaled to target."""
    net = bridge_arrays(scenario_params("plan_implied"))["net_tco2e"]
    return meta()["target_net_tco2e"] * net / net.sum()


# --------------------------------------------------------------------------- bridge
def monthly_bridge(p: dict | None = None, *, pass_rate: float | None = None,
                   op_days_scale: float = 1.0, kiln_add: tuple[float, int] | None = None) -> pd.DataFrame:
    """Deterministic monthly tonne bridge. Returns one row per month plus cumulative columns."""
    p = p or defaults()
    arr = bridge_arrays(p, pass_rate=pass_rate, op_days_scale=op_days_scale, kiln_add=kiln_add)
    df = pd.DataFrame({"month": [m.capitalize() for m in MONTHS],
                       **{k: np.asarray(v, dtype=float) for k, v in arr.items() if k != "pass_rate"}})
    df["cum_net_tco2e"] = df["net_tco2e"].cumsum()
    df["plan_tco2e"] = plan_phasing()
    df["plan_cum_tco2e"] = df["plan_tco2e"].cumsum()
    return df


def annual_net(p: dict | None = None, **kw) -> float:
    p = p or defaults()
    return float(bridge_arrays(p, **kw)["net_tco2e"].sum())


# --------------------------------------------------------------------------- solver
@dataclass
class Lever:
    key: str            # parameter name, or special: "pass_rate", "op_days_scale"
    label: str
    unit: str
    kind: str           # "operational" | "accounting"


LEVERS = [
    Lever("batches_per_kiln_day", "Batches per kiln-day", "batches/kiln-day", "operational"),
    Lever("op_days_scale", "Operating days per year", "days/yr", "operational"),
    Lever("dry_biomass_per_batch_t", "Dry biomass per batch", "t dry/batch", "operational"),
    Lever("pass_rate", "dMRV pass rate", "share of batches", "operational"),
    Lever("kilns_total", "Kilns at full operation", "kilns", "operational"),
    Lever("ch4_ef_g_per_kg_biochar", "CH4 emission factor (moisture control)", "g CH4/kg char", "operational"),
    Lever("persistence_factor", "Persistence factor", "fraction", "accounting"),
    Lever("biochar_corg_frac", "Biochar organic C", "fraction", "accounting"),
]


def _eval(p: dict, key: str, x: float) -> float:
    if key == "pass_rate":
        return annual_net(p, pass_rate=x)
    if key == "op_days_scale":
        return annual_net(p, op_days_scale=x)
    q = dict(p)
    q[key] = x
    return annual_net(q)


def _baseline_value(p: dict, key: str) -> float:
    if key == "pass_rate":
        return dmrv_pass_rate(p)
    if key == "op_days_scale":
        return 1.0
    return p[key]


def solve_lever(p: dict, key: str, target: float) -> float:
    """Exact closed-form solve: net is affine in each lever."""
    x0 = _baseline_value(p, key)
    dx = max(abs(x0) * 0.1, 1e-3)
    n0, n1 = _eval(p, key, x0), _eval(p, key, x0 + dx)
    slope = (n1 - n0) / dx
    if slope == 0:
        return float("nan")
    return x0 + (target - n0) / slope


def _display(p: dict, key: str, x: float) -> float:
    """Convert solver units to display units (op_days_scale → days/yr)."""
    if key == "op_days_scale":
        return x * sum(monthly_op_days(p))
    return x


def _range(p: dict, key: str) -> tuple[float, float]:
    """Plausible range of each lever in display units, from assumptions.yaml bounds."""
    params = load_params()
    if key == "pass_rate":
        return dmrv_pass_rate(_dmrv_at(p, "bad")), dmrv_pass_rate(_dmrv_at(p, "good"))
    if key == "op_days_scale":
        return (sum(params[f"op_days_{m}"].low for m in MONTHS), sum(params[f"op_days_{m}"].high for m in MONTHS))
    return params[key].low, params[key].high


def _dmrv_at(p: dict, which: str) -> dict:
    """Parameter set with every dMRV input at its good or bad bound."""
    params = load_params()
    q = dict(p)
    for e in EV_ELEMENTS + ("evidence_remediation_frac",):
        q[e] = params[e].high if which == "good" else params[e].low
    for e in ("quality_rejection_frac", "audit_rejection_frac"):
        q[e] = params[e].low if which == "good" else params[e].high
    return q


def _feasibility(p: dict, key: str, x_display: float) -> str:
    lo, hi = _range(p, key)
    if key == "pass_rate" and x_display > 1:
        return "Infeasible alone (>100%)"
    if key == "op_days_scale" and x_display > sum(CAL_DAYS_2027) - 52:  # beyond 6-day weeks year-round
        return "Infeasible alone (exceeds calendar)"
    if key in ("persistence_factor", "biochar_corg_frac") and x_display > 1:
        return "Infeasible alone (>1)"
    if key == "ch4_ef_g_per_kg_biochar" and x_display < 0:
        return "Infeasible alone (<0)"
    if key == "batches_per_kiln_day":
        two_shift = cycle_ceiling_batches_per_day(p, shifts=2)
        if x_display > two_shift:
            return "Infeasible alone (exceeds 2-shift cycle ceiling)"
    if lo <= x_display <= hi:
        return "Within plausible range"
    return "Beyond plausible range"


def solver_table(p: dict | None = None, target: float | None = None) -> pd.DataFrame:
    """For each lever: value required to hit the target, holding all others at default."""
    p = p or defaults()
    target = target or meta()["target_net_tco2e"]
    base_net = annual_net(p)
    rows = []
    for lv in LEVERS:
        x0 = _baseline_value(p, lv.key)
        xs = solve_lever(p, lv.key, target)
        d0, ds = _display(p, lv.key, x0), _display(p, lv.key, xs)
        lo, hi = _range(p, lv.key)
        rows.append({
            "lever": lv.label, "key": lv.key, "kind": lv.kind, "unit": lv.unit,
            "default": d0, "required": ds, "change_pct": (ds / d0 - 1) * 100 if d0 else np.nan,
            "plausible_low": lo, "plausible_high": hi,
            "feasibility": _feasibility(p, lv.key, ds),
            "check_net_at_required": _eval(p, lv.key, xs),
        })
    df = pd.DataFrame(rows)
    df.attrs["base_net"] = base_net
    df.attrs["target"] = target
    return df


# --------------------------------------------------------------------------- lever stacks
def _good_bound_params(p: dict) -> dict[str, dict]:
    """Operational levers and the parameter values at their 'good' bound."""
    params = load_params()
    return {
        "Dry biomass per batch": {"dry_biomass_per_batch_t": params["dry_biomass_per_batch_t"].high},
        "Batches per kiln-day": {"batches_per_kiln_day": params["batches_per_kiln_day"].high},
        "CH4 EF (dry feedstock ≤15%)": {"ch4_ef_g_per_kg_biochar": params["ch4_ef_g_per_kg_biochar"].low},
        "dMRV pass rate": {k: v for k, v in _dmrv_at(p, "good").items()
                           if k in EV_ELEMENTS + ("evidence_remediation_frac", "quality_rejection_frac", "audit_rejection_frac")},
        "Operating days": {f"op_days_{m}": params[f"op_days_{m}"].high for m in MONTHS},
        "Kilns at full operation": {"kilns_total": params["kilns_total"].high},
        "Faster ramp": {"ramp_start_share": params["ramp_start_share"].high,
                        "ramp_full_month": params["ramp_full_month"].low},
    }


def _blend(p: dict, moves: dict, t: float) -> dict:
    q = dict(p)
    for k, v in moves.items():
        q[k] = p[k] + t * (v - p[k])
    return q


def uniform_stretch(p: dict | None = None, target: float | None = None) -> float:
    """Fraction t of the way from default to good bound that ALL operational levers must move
    together to hit target. Returns >1 if even all-good-bounds falls short."""
    p = p or defaults()
    target = target or meta()["target_net_tco2e"]
    all_moves: dict = {}
    for mv in _good_bound_params(p).values():
        all_moves.update(mv)
    f = lambda t: annual_net(_blend(p, all_moves, t)) - target
    if f(1.0) < 0:
        return float("inf")
    return float(brentq(f, 0.0, 1.0, xtol=1e-6))


def greedy_stack(p: dict | None = None, target: float | None = None) -> pd.DataFrame:
    """Fewest-levers path: repeatedly move the lever with the largest gain to its good bound;
    the last lever is moved only as far as needed (solved exactly)."""
    p = dict(p or defaults())
    target = target or meta()["target_net_tco2e"]
    remaining = _good_bound_params(p)
    rows = [{"step": "Literature-anchored defaults", "net_tco2e": annual_net(p), "fraction_of_range_used": np.nan}]
    cur = p
    while remaining and annual_net(cur) < target:
        gains = {name: annual_net(_blend(cur, mv, 1.0)) for name, mv in remaining.items()}
        best = max(gains, key=gains.get)
        mv = remaining.pop(best)
        if gains[best] >= target:
            t = brentq(lambda t: annual_net(_blend(cur, mv, t)) - target, 0.0, 1.0, xtol=1e-8)
        else:
            t = 1.0
        cur = _blend(cur, mv, t)
        rows.append({"step": best, "net_tco2e": annual_net(cur), "fraction_of_range_used": t})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- sensitivity
TONNE_GROUPS = ("network", "kiln_physics", "calendar", "carbon_accounting", "dmrv")


def _bounds_for(name: str, ranges: dict | None) -> tuple[float, float]:
    prm = load_params()[name]
    if ranges and name in ranges:
        return ranges[name][0], ranges[name][-1]
    return prm.low, prm.high


def oat_sensitivity(p: dict | None = None, ranges: dict | None = None) -> pd.DataFrame:
    """One-at-a-time (tornado) swing in annual net tonnes as each parameter moves low → high,
    others held at `p`. `ranges` (scenario mc_ranges) override yaml bounds. Monthly operating days and
    all dMRV inputs are also swung together as grouped rows. Parameters with no effect drop out."""
    p = p or defaults()
    params = load_params()
    base = annual_net(p)
    rows = []
    for name, prm in params.items():
        if prm.group not in TONNE_GROUPS or name.startswith("op_days_"):
            continue
        lo, hi = _bounds_for(name, ranges)
        if lo == hi:
            continue
        lo_net, hi_net = annual_net({**p, name: lo}), annual_net({**p, name: hi})
        if abs(hi_net - lo_net) < 1e-6:
            continue
        rows.append({"parameter": name, "status": prm.status, "low": lo, "high": hi,
                     "net_at_low": lo_net, "net_at_high": hi_net, "swing": abs(hi_net - lo_net)})
    cal_lo = {**p, **{f"op_days_{m}": params[f"op_days_{m}"].low for m in MONTHS}}
    cal_hi = {**p, **{f"op_days_{m}": params[f"op_days_{m}"].high for m in MONTHS}}
    lo_net, hi_net = annual_net(cal_lo), annual_net(cal_hi)
    rows.append({"parameter": "operating_calendar (all months)", "status": "ASSUMPTION – VERIFY",
                 "low": sum(params[f"op_days_{m}"].low for m in MONTHS),
                 "high": sum(params[f"op_days_{m}"].high for m in MONTHS),
                 "net_at_low": lo_net, "net_at_high": hi_net, "swing": abs(hi_net - lo_net)})
    lo_net, hi_net = annual_net(_dmrv_at(p, "bad")), annual_net(_dmrv_at(p, "good"))
    rows.append({"parameter": "dmrv_pass_rate (all dMRV inputs)", "status": "ASSUMPTION – VERIFY",
                 "low": float(dmrv_pass_rate(_dmrv_at(p, "bad"))), "high": float(dmrv_pass_rate(_dmrv_at(p, "good"))),
                 "net_at_low": lo_net, "net_at_high": hi_net, "swing": abs(hi_net - lo_net)})
    df = pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)
    df.attrs["base_net"] = base
    return df


def tornado(scenario: str = "plan_implied") -> pd.DataFrame:
    """Scenario-centred tornado using the scenario's Monte Carlo ranges where defined."""
    return oat_sensitivity(scenario_params(scenario), scenario_mc_ranges(scenario))


# --------------------------------------------------------------------------- scenarios & Monte Carlo
def scenario_summary() -> pd.DataFrame:
    """Deterministic annual net and key drivers for every scenario in assumptions.yaml."""
    rows = []
    for key, spec in scenarios().items():
        p = scenario_params(key)
        rows.append({"scenario": key, "label": spec["label"], "description": spec["description"],
                     "net_tco2e": annual_net(p), "pass_rate": float(dmrv_pass_rate(p)),
                     "overrides": ", ".join(f"{k}={v:g}" for k, v in (spec.get("overrides") or {}).items())})
    return pd.DataFrame(rows)


def sample_params(scenario: str, n: int, seed: int) -> dict[str, np.ndarray | float]:
    """Triangular draws for every tonne-relevant parameter: (low, mode, high) from assumptions.yaml with
    the mode at the scenario value, or from the scenario's mc_ranges where given. Independent draws."""
    rng = np.random.default_rng(seed)
    base = scenario_params(scenario)
    ranges = scenario_mc_ranges(scenario)
    out: dict = dict(base)
    for name, prm in load_params().items():
        if prm.group not in TONNE_GROUPS:
            continue
        if name in ranges:
            lo, mode, hi = ranges[name]
        else:
            lo, hi = prm.low, prm.high
            mode = min(max(base[name], lo), hi)
        if hi <= lo:
            continue
        out[name] = rng.triangular(lo, mode, hi, size=n)
    return out


def monte_carlo(scenario: str = "plan_implied", n: int | None = None, seed: int | None = None) -> dict:
    """Annual and cumulative-monthly net tonne distribution for a scenario."""
    n = n or int(meta()["mc_runs"])
    seed = meta()["random_seed"] if seed is None else seed
    draws = sample_params(scenario, n, seed)
    arr = bridge_arrays(draws)
    monthly = arr["net_tco2e"]
    annual = monthly.sum(axis=-1)
    cum = np.cumsum(monthly, axis=-1)
    target = meta()["target_net_tco2e"]
    return {
        "scenario": scenario, "n": n, "annual": annual,
        "p10": float(np.percentile(annual, 10)), "p50": float(np.percentile(annual, 50)),
        "p90": float(np.percentile(annual, 90)), "mean": float(annual.mean()),
        "prob_hit": float((annual >= target).mean()),
        "cum_p10": np.percentile(cum, 10, axis=0), "cum_p50": np.percentile(cum, 50, axis=0),
        "cum_p90": np.percentile(cum, 90, axis=0),
    }


def p50_drift_decomposition(scenario: str = "plan_implied") -> pd.DataFrame:
    """Why the Monte Carlo P50 sits below the deterministic design point: for each sampled parameter,
    the % change in annual net when it moves from its mode (scenario value) to the mean of its
    triangular distribution. Negative = the nominal value is optimistic relative to its range."""
    p = scenario_params(scenario)
    ranges = scenario_mc_ranges(scenario)
    base = annual_net(p)
    rows = []
    for name, prm in load_params().items():
        if prm.group not in TONNE_GROUPS:
            continue
        lo, mode, hi = ranges.get(name, (prm.low, min(max(p[name], prm.low), prm.high), prm.high))
        if hi <= lo:
            continue
        mean = (lo + mode + hi) / 3
        rows.append({"parameter": name, "status": prm.status, "mode": mode, "mean": mean,
                     "pct_change": (annual_net({**p, name: mean}) / base - 1) * 100})
    df = pd.DataFrame(rows).sort_values("pct_change").reset_index(drop=True)
    df.attrs["base_net"] = base
    return df


# --------------------------------------------------------------------------- lever simulator
def _lever_specs(p: dict) -> list[dict]:
    """Each lever: label, how it changes the run, and its fixed ₹ cost on top of the cost-model delta."""
    sites = p["kilns_total"] / p["kilns_per_site"]
    pr0 = float(dmrv_pass_rate(p))
    non_monsoon = [m for m in MONTHS if m not in ("jun", "jul", "aug", "sep")]
    cal_cap = dict(zip(MONTHS, CAL_DAYS_2027))
    ramp_new = max(1.0, p["ramp_full_month"] - p["lever_ramp_months_saved"])
    bpd_new = p["batches_per_kiln_day"] * (1 + p["lever_second_shift_share"] * p["lever_second_shift_uplift"])
    ch4_new = min(p["ch4_ef_g_per_kg_biochar"], p["ch4_ef_dry_g_per_kg"])
    return [
        {"lever": f"dMRV QA desk (+{p['lever_dmrv_step_pp']:.0f} pp pass rate)",
         "kw": {"pass_rate": min(pr0 + p["lever_dmrv_step_pp"] / 100, 0.99)}, "params": {},
         "fixed_inr": p["lever_dmrv_cost_inr"], "owner": "MRV lead"},
        {"lever": f"Add {p['lever_kilns_added']:.0f} kilns from month {p['lever_kilns_from_month']:.0f}",
         "kw": {"kiln_add": (p["lever_kilns_added"], int(p["lever_kilns_from_month"]))}, "params": {},
         "fixed_inr": 0.0, "owner": "Head of field ops"},
        {"lever": f"+{p['lever_extra_op_days_per_month']:.0f} operating days/month outside monsoon",
         "kw": {}, "params": {f"op_days_{m}": min(p[f"op_days_{m}"] + p["lever_extra_op_days_per_month"], cal_cap[m] - 4)
                              for m in non_monsoon},
         "fixed_inr": p["lever_op_days_cost_inr_per_site"] * sites, "owner": "Site supervisors"},
        {"lever": "Dry feedstock to ≤15% moisture",
         "kw": {}, "params": {"ch4_ef_g_per_kg_biochar": ch4_new,
                              "biomass_moisture_frac": min(p["biomass_moisture_frac"], p["moisture_dry_threshold"] - 0.02)},
         "fixed_inr": p["lever_drying_cost_inr_per_site"] * sites, "per_t_dry_inr": p["lever_drying_cost_inr_per_t_dry"],
         "owner": "Site supervisors / QA"},
        {"lever": f"Second shift on {p['lever_second_shift_share']:.0%} of kilns",
         "kw": {}, "params": {"batches_per_kiln_day": bpd_new},
         "fixed_inr": p["lever_second_shift_fixed_inr_per_kiln"] * p["lever_second_shift_share"] * p["kilns_total"],
         "owner": "Head of field ops"},
        {"lever": f"Operator academy: full fleet {p['lever_ramp_months_saved']:.0f} months earlier",
         "kw": {}, "params": {"ramp_full_month": ramp_new},
         "fixed_inr": p["lever_ramp_cost_inr"], "owner": "People / training lead"},
    ]


def lever_simulator(p: dict | None = None, target: float | None = None,
                    reference_net: float | None = None) -> pd.DataFrame:
    """Incremental net tonnes and incremental ₹ cost of each lever vs `p`; ranked by ₹ per incremental tonne.
    ₹ delta = change in the full cost model (variable costs of extra batches, capex, community payments,
    registry fees) + the lever's own fixed cost. `reference_net` (e.g. the Monte Carlo P50) defines the gap
    to target used for '% of gap closed'; defaults to the deterministic net."""
    from model.economics import total_cost_inr  # local import to avoid a cycle

    p = p or scenario_params("plan_implied")
    target = target or meta()["target_net_tco2e"]
    base_net = annual_net(p)
    base_cost = total_cost_inr(p)
    gap = max(target - (base_net if reference_net is None else reference_net), 0.0)
    rows = []
    for spec in _lever_specs(p):
        q = {**p, **spec["params"]}
        net = annual_net(q, **spec["kw"])
        cost = total_cost_inr(q, **spec["kw"]) + spec["fixed_inr"]
        if "per_t_dry_inr" in spec:
            cost += spec["per_t_dry_inr"] * float(bridge_arrays(q, **spec["kw"])["dry_feed_t"].sum())
        d_net, d_cost = net - base_net, cost - base_cost
        rows.append({"lever": spec["lever"], "owner": spec["owner"], "delta_net_t": d_net, "delta_cost_inr": d_cost,
                     "inr_per_incremental_t": d_cost / d_net if d_net > 1 else np.nan,
                     "gap_closed_pct": (d_net / gap * 100) if gap > 0 else np.nan})
    df = pd.DataFrame(rows)
    df["no_effect"] = df["delta_net_t"] <= 1
    df = df.sort_values(["no_effect", "inr_per_incremental_t"]).reset_index(drop=True)
    df.attrs.update(base_net=base_net, gap=gap, target=target)
    return df


# --------------------------------------------------------------------------- implications
def implied_requirements(p: dict | None = None, target: float | None = None) -> dict[str, float]:
    """Operating footprint implied by delivering `target` at the given unit factors."""
    p = p or defaults()
    target = target or meta()["target_net_tco2e"]
    bridge = monthly_bridge(p)
    net = bridge["net_tco2e"].sum()
    dry = bridge["dry_feed_t"].sum()
    net_per_dry = net / dry
    dry_needed = target / net_per_dry
    as_received = dry_needed / (1 - p["biomass_moisture_frac"])
    per_village = p["village_dry_biomass_t_per_season"] * p["farmer_supply_share"] * p["harvest_seasons_per_year"]
    villages = dry_needed / per_village
    kiln_years = (ramp_shares(p) * np.array(monthly_op_days(p))).sum() / sum(monthly_op_days(p))
    return {
        "net_per_t_dry": net_per_dry,
        "net_per_t_biochar": net / bridge["biochar_t"].sum(),
        "dry_feed_needed_t": dry_needed,
        "as_received_feed_needed_t": as_received,
        "biomass_spend_inr": as_received * 1000 * p["biomass_price_inr_per_kg"],
        "villages_needed": villages,
        "farmers_engaged": villages * p["farmers_per_village"],
        "effective_fleet_share": kiln_years,
        "net_per_kiln_year_needed_full_fleet": target / p["kilns_total"],
        "net_per_kiln_year_needed_with_ramp": target / (p["kilns_total"] * kiln_years),
        "default_net_per_kiln_year_full": net / (p["kilns_total"] * kiln_years),
        "operators": p["kilns_total"] * p["operators_per_kiln"] * p["shifts_per_kiln_day"],
        "operator_replacements_per_year": p["kilns_total"] * p["operators_per_kiln"]
                                         * p["shifts_per_kiln_day"] * p["operator_attrition_monthly"] * 12,
    }

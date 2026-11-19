"""KPI definitions: the single source of truth for every metric shown in the app.

Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.

Each function documents its formula and the decision it supports. Functions take the generator's
tables (pandas DataFrames) and return a scalar, or a Series/DataFrame when `by` is given.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from model.assumptions import MONTHS, scenario_params
from model.tonnes import CAL_DAYS_2027, plan_phasing

EV_COLS = ["ev_photo", "ev_temp_log", "ev_feed_weight", "ev_char_weight", "ev_geotag", "ev_timestamp"]


def _grp(df: pd.DataFrame, by):
    return df.groupby(by, observed=True) if by is not None else None


# --------------------------------------------------------------------------- RAG helper
def rag(value: float, green: float, amber: float, higher_is_better: bool = True) -> str:
    """'Green' / 'Amber' / 'Red' against thresholds from assumptions.yaml (kpi_thresholds group)."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "Grey"
    if higher_is_better:
        return "Green" if value >= green else ("Amber" if value >= amber else "Red")
    return "Green" if value <= green else ("Amber" if value <= amber else "Red")


# --------------------------------------------------------------------------- planned capacity
def planned_kiln_days(kilns: pd.DataFrame, start: str | pd.Timestamp = "2027-01-01",
                      end: str | pd.Timestamp = "2027-12-31", p: dict | None = None, by: str | None = None):
    """Σ over commissioned kilns and days in [start, end] of (planned op days in month ÷ calendar days).
    The denominator for utilisation: the operating kiln-days the plan expects."""
    p = p or scenario_params("plan_implied")
    days = pd.date_range(start, end, freq="D")
    frac = np.array([p[f"op_days_{MONTHS[d.month - 1]}"] / CAL_DAYS_2027[d.month - 1] for d in days])
    comm = kilns.commission_date.values[:, None] <= days.values[None, :]
    per_kiln = (comm * frac[None, :]).sum(axis=1)
    s = pd.Series(per_kiln, index=kilns.index)
    if by:
        return s.groupby(kilns[by].values).sum()
    return float(s.sum())


# --------------------------------------------------------------------------- production KPIs
def kiln_utilisation(batches: pd.DataFrame, kilns: pd.DataFrame, start="2027-01-01", end="2027-12-31",
                     p: dict | None = None, by: str | None = None):
    """Formula: kiln-days with ≥1 batch ÷ planned operating kiln-days (commissioned kilns × planned op-day share).
    Decision: low utilisation with normal batches/kiln-day points to idle days (no feedstock, no crew,
    relocation) rather than slow burns → fix supply or staffing, not technique."""
    b = batches[(batches.date >= start) & (batches.date <= end)]
    used = b.drop_duplicates(["kiln_id", "date"])
    if by:
        num = used.groupby(by).size()
        den = planned_kiln_days(kilns, start, end, p, by=by)
        return (num / den).fillna(0)
    return len(used) / planned_kiln_days(kilns, start, end, p)


def batches_per_kiln_day(batches: pd.DataFrame, by=None):
    """Formula: batches ÷ kiln-days on which the kiln ran (≥1 batch).
    Decision: compares running productivity to the plan's 1.8; a gap here is cycle time or crew skill."""
    if by:
        g = batches.groupby(by, observed=True)
        return g.size() / g.apply(lambda x: x[["kiln_id", "date"]].drop_duplicates().shape[0])
    return len(batches) / batches[["kiln_id", "date"]].drop_duplicates().shape[0]


def yield_pct(batches: pd.DataFrame, by=None):
    """Formula: Σ biochar t ÷ Σ dry feedstock t.
    Decision: falling yield signals over-burning (late quench) or wet feedstock → retrain on quench timing."""
    if by:
        g = batches.groupby(by, observed=True)
        return g.biochar_t.sum() / g.dry_feedstock_t.sum()
    return float(batches.biochar_t.sum() / batches.dry_feedstock_t.sum())


def evidence_completeness_pct(batches: pd.DataFrame, by=None):
    """Formula: share of batches with all six evidence elements valid at first submission
    (photos, temperature log, feedstock weight, biochar weight, geotag, timestamp).
    Decision: the leading indicator of credit loss; act on the weakest element per site."""
    ok = batches[EV_COLS].all(axis=1)
    if by:
        return ok.groupby(batches[by] if isinstance(by, str) else [batches[c] for c in by]).mean()
    return float(ok.mean())


def batch_acceptance_pct(batches: pd.DataFrame, by=None):
    """Formula: accepted batches ÷ all batches (after remediation, quality and audit checks).
    Decision: the dMRV pass rate the tonne model uses; each pp ≈ 1% of net tonnes."""
    if by:
        return batches.groupby(by, observed=True).accepted.mean()
    return float(batches.accepted.mean())


def net_t_per_kiln_week(batches: pd.DataFrame, kilns: pd.DataFrame, start="2027-01-01", end="2027-12-31", by=None):
    """Formula: Σ net tCO2e ÷ commissioned kiln-weeks in the window.
    Decision: the single productivity number to compare sites; plan-implied ≈ 4.5 t/kiln-week in season."""
    b = batches[(batches.date >= start) & (batches.date <= end)]
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    live_days = (e - kilns.commission_date.clip(lower=s)).dt.days.clip(lower=0) + 1
    weeks = pd.Series(live_days.values / 7, index=kilns.kiln_id.values)
    if by == "site_id":
        return b.groupby("site_id").net_tco2e.sum() / weeks.groupby(kilns.site_id.values).sum()
    if by == "kiln_id":
        return (b.groupby("kiln_id").net_tco2e.sum() / weeks).fillna(0)
    return float(b.net_tco2e.sum() / weeks.sum())


def biomass_days_of_cover(deliveries: pd.DataFrame, batches: pd.DataFrame, as_of="2027-12-31", window_days: int = 14):
    """Formula (per site): feedstock on hand (Σ delivered dry t − Σ consumed dry t, to as_of) ÷
    average daily consumption over the trailing `window_days` operating days.
    Decision: < kpi_cover_amber days → stockout next week; pull deliveries forward or move kilns."""
    as_of = pd.Timestamp(as_of)
    d = deliveries[deliveries.date <= as_of].groupby("site_id").dry_t.sum()
    c_all = batches[batches.date <= as_of]
    c = c_all.groupby("site_id").dry_feedstock_t.sum()
    stock = (d - c.reindex(d.index).fillna(0)).clip(lower=0)
    recent = c_all[c_all.date > as_of - pd.Timedelta(days=window_days)]
    run_days = recent.groupby("site_id").date.nunique().clip(lower=1)
    daily = recent.groupby("site_id").dry_feedstock_t.sum() / run_days
    cover = (stock / daily.reindex(stock.index)).replace([np.inf, -np.inf], np.nan)
    return pd.DataFrame({"stock_dry_t": stock, "daily_use_t": daily.reindex(stock.index), "days_of_cover": cover})


# --------------------------------------------------------------------------- people KPIs
def operator_productivity_vs_cohort(batches: pd.DataFrame, operators: pd.DataFrame) -> pd.DataFrame:
    """Formula: for each lead operator, batches per running day and acceptance, compared with the network
    curve at the same tenure (weeks since training). Ratio > 1 = ahead of the learning curve.
    Decision: coach operators below 0.85× curve; pair new operators with those above 1.1×."""
    b = batches.assign(tenure_wk=(batches.lead_tenure_days // 7).clip(upper=26))
    per_day = b.groupby(["operator_id", "date", "tenure_wk"]).agg(n=("batch_id", "size"), acc=("accepted", "mean")).reset_index()
    curve = per_day.groupby("tenure_wk").agg(curve_bpd=("n", "mean"), curve_acc=("acc", "mean"))
    per_day = per_day.join(curve, on="tenure_wk")
    out = per_day.groupby("operator_id").agg(days=("date", "size"), bpd=("n", "mean"), acceptance=("acc", "mean"),
                                             curve_bpd=("curve_bpd", "mean"), curve_acc=("curve_acc", "mean"),
                                             tenure_wk=("tenure_wk", "max"))
    out["productivity_vs_curve"] = out.bpd / out.curve_bpd
    out["acceptance_vs_curve"] = out.acceptance / out.curve_acc
    out = out.join(operators.set_index("operator_id")[["site_id", "kiln_id", "cohort", "role"]])
    out.attrs["curve"] = curve
    return out.reset_index()


def operator_attrition(operators: pd.DataFrame, month: int | None = None, by=None):
    """Formula: leavers in month ÷ operators employed at the start of that month (all months if month=None →
    average monthly rate). Decision: above kpi_attrition_amber, hold a training cohort in reserve for that site."""
    rates = []
    for m in ([month] if month else range(1, 13)):
        s, e = pd.Timestamp(2027, m, 1), pd.Timestamp(2027, m, 1) + pd.offsets.MonthEnd(0)
        emp = operators[(operators.training_date < s) & (operators.attrition_date.isna() | (operators.attrition_date >= s))]
        left = emp[(emp.attrition_date >= s) & (emp.attrition_date <= e)]
        if by:
            rates.append((left.groupby(by).size() / emp.groupby(by).size()).fillna(0))
        else:
            rates.append(len(left) / max(len(emp), 1))
    if by:
        return pd.concat(rates, axis=1).mean(axis=1)
    return float(np.mean(rates))


# --------------------------------------------------------------------------- community KPIs
def village_payment_sla(deliveries: pd.DataFrame, sla_days: float, by=None):
    """Formula: share of village deliveries paid within `sla_days` of delivery (payment_lag_days ≤ SLA).
    Decision: the integrity KPI. Breaches precede supply declines by 4–6 weeks; escalate any site below amber."""
    ok = deliveries.payment_lag_days <= sla_days
    if by:
        return ok.groupby(deliveries[by]).mean()
    return float(ok.mean())


def median_payment_lag(deliveries: pd.DataFrame, by=None):
    """Formula: median of (payment date − delivery date) in days.
    Decision: trend matters more than level; a rising median at one site is the earliest warning of a backlog."""
    if by:
        return deliveries.groupby(by).payment_lag_days.median()
    return float(deliveries.payment_lag_days.median())


def biochar_return_completion(returns: pd.DataFrame, batches: pd.DataFrame, by=None):
    """Formula: Σ biochar returned to villages (kg) ÷ Σ biochar produced (kg) in the same period.
    Decision: returning biochar is part of the community promise and of soil application evidence;
    below amber, schedule a return run before the next procurement cycle."""
    if by == "site_id":
        produced = batches.groupby("site_id").biochar_t.sum() * 1000
        return (returns.groupby("site_id").kg.sum() / produced).fillna(0)
    if by == "village_id":
        return returns.groupby("village_id").kg.sum() / returns.groupby("village_id").produced_kg_period.sum()
    return float(returns.kg.sum() / (batches.biochar_t.sum() * 1000))


# --------------------------------------------------------------------------- financial & delivery KPIs
def inr_per_net_t(batches: pd.DataFrame, deliveries: pd.DataFrame, sites: pd.DataFrame, p: dict | None = None, by=None):
    """Formula: (actual biomass spend + operator pay + logistics + MRV + allocated fixed costs) ÷ net tCO2e,
    using economics.archetype_economics for allocation. Decision: compare with breakeven credit price."""
    from model.economics import archetype_economics

    ae = archetype_economics(batches, deliveries, sites, p)
    if by == "archetype":
        g = ae.groupby("archetype")
        return g.inr.sum() / g.net_t.first()
    return float(ae.inr.sum() / ae.groupby("archetype").net_t.first().sum())


def cumulative_delivery_vs_plan(batches: pd.DataFrame) -> pd.DataFrame:
    """Formula: cumulative net tCO2e by month ÷ cumulative plan (plan-implied monthly shape scaled to 100k).
    Decision: the headline control-tower number; below kpi_vs_plan_amber triggers the lever review."""
    actual = batches.groupby(batches.date.dt.month).net_tco2e.sum().reindex(range(1, 13), fill_value=0)
    plan = pd.Series(plan_phasing(), index=range(1, 13))
    df = pd.DataFrame({"month": [m.capitalize() for m in MONTHS], "actual": actual.values, "plan": plan.values})
    df["cum_actual"] = df.actual.cumsum()
    df["cum_plan"] = df.plan.cumsum()
    df["ratio"] = df.cum_actual / df.cum_plan
    return df


# --------------------------------------------------------------------------- scorecards
def site_scorecard(t: dict[str, pd.DataFrame], p: dict | None = None, start="2027-01-01", end="2027-12-31") -> pd.DataFrame:
    """One row per site with core KPIs and RAG status."""
    p = p or scenario_params("plan_implied")
    b = t["batches"][(t["batches"].date >= start) & (t["batches"].date <= end)]
    d = t["biomass_deliveries"][(t["biomass_deliveries"].date >= start) & (t["biomass_deliveries"].date <= end)]
    k = t["kilns"]
    s = t["sites"].set_index("site_id")
    df = pd.DataFrame(index=s.index)
    df["district"], df["archetype"] = s.district, s.archetype
    df["net_t"] = b.groupby("site_id").net_tco2e.sum()
    df["utilisation"] = kiln_utilisation(b, k, start, end, p, by="site_id")
    df["batches_per_kiln_day"] = batches_per_kiln_day(b, by="site_id")
    df["evidence_completeness"] = evidence_completeness_pct(b, by="site_id")
    df["acceptance"] = batch_acceptance_pct(b, by="site_id")
    df["net_t_per_kiln_week"] = net_t_per_kiln_week(b, k, start, end, by="site_id")
    cover = biomass_days_of_cover(t["biomass_deliveries"], t["batches"], as_of=end)
    df["days_of_cover"] = cover.days_of_cover
    df["payment_sla"] = village_payment_sla(d, p["payment_sla_days"], by="site_id")
    df["median_payment_lag"] = median_payment_lag(d, by="site_id")
    df["return_completion"] = biochar_return_completion(
        t["biochar_returns"][(t["biochar_returns"].date >= start) & (t["biochar_returns"].date <= end)], b, by="site_id")
    df = df.fillna({"net_t": 0})
    df["rag_utilisation"] = df.utilisation.apply(lambda v: rag(v, p["kpi_utilisation_green"], p["kpi_utilisation_amber"]))
    df["rag_acceptance"] = df.acceptance.apply(lambda v: rag(v, p["kpi_acceptance_green"], p["kpi_acceptance_amber"]))
    df["rag_evidence"] = df.evidence_completeness.apply(lambda v: rag(v, p["kpi_evidence_green"], p["kpi_evidence_amber"]))
    df["rag_cover"] = df.days_of_cover.apply(lambda v: rag(v, p["kpi_cover_green"], p["kpi_cover_amber"]))
    df["rag_payment"] = df.payment_sla.apply(lambda v: rag(v, p["kpi_payment_sla_green"], p["kpi_payment_sla_amber"]))
    df["rag_return"] = df.return_completion.apply(lambda v: rag(v, p["kpi_return_green"], p["kpi_return_amber"]))
    rag_cols = [c for c in df.columns if c.startswith("rag_")]
    df["overall"] = df[rag_cols].apply(
        lambda r: "Red" if (r == "Red").any() else ("Amber" if (r == "Amber").sum() >= 2 else "Green"), axis=1)
    return df.reset_index()


# --------------------------------------------------------------------------- risk register
def risk_register(t: dict[str, pd.DataFrame], p: dict | None = None) -> pd.DataFrame:
    """Top delivery risks quantified in tonnes from the synthetic actuals (and the tonne model for methodology),
    with likelihood/impact and RAG. Ranked by tonnes at risk."""
    from model.tonnes import tornado

    p = p or scenario_params("plan_implied")
    b, d, s = t["batches"], t["biomass_deliveries"], t["sites"]
    buffer = 1 - p["buffer_deduction_frac"]
    pe = b.biochar_t * (b.ch4_g_per_kg / 1000 * p["ch4_gwp100"] + p["other_project_emissions_t_per_t_biochar"])
    potential = ((b.gross_tco2e - pe) * buffer)
    rej_lost = float(potential[~b.accepted].sum())
    acc = batch_acceptance_pct(b)

    # throughput: actual batches vs planned batches on commissioned kiln-days
    planned_batches = planned_kiln_days(t["kilns"], p=p) * p["batches_per_kiln_day"]
    net_per_batch = float(b.net_tco2e.sum() / len(b))
    thr_lost = max(planned_batches - len(b), 0) * net_per_batch
    bpd = batches_per_kiln_day(b)
    util = kiln_utilisation(b, t["kilns"], p=p)

    # biomass & payments: biomass-constrained + late-payer sites vs average-site net per kiln
    arch = s.set_index("site_id").archetype
    per_site = b.groupby("site_id").net_tco2e.sum()
    avg_per_site = per_site[arch[arch == "Average"].index.difference(s[s.late_payer].site_id)].mean()
    constrained = list(arch[arch == "Biomass-constrained"].index) + list(s[s.late_payer].site_id)
    sup_lost = float((avg_per_site - per_site.reindex(constrained).fillna(0)).clip(lower=0).sum())
    sla = village_payment_sla(d, p["payment_sla_days"])
    worst_sla = village_payment_sla(d, p["payment_sla_days"], by="site_id").min()

    # people
    attr = operator_attrition(t["operators"])
    new_acc = b[b.lead_tenure_days <= 14].accepted.mean()
    mature_acc = b[b.lead_tenure_days > 60].accepted.mean()
    new_lost = float(potential[(b.lead_tenure_days <= 14)].sum() * (mature_acc - new_acc))

    # methodology (model)
    tor = tornado("plan_implied").set_index("parameter")
    base = tor.attrs["base_net"]
    meth = sum(max(base - min(tor.loc[x, "net_at_low"], tor.loc[x, "net_at_high"]), 0)
               for x in ("persistence_factor", "ch4_ef_g_per_kg_biochar") if x in tor.index)

    rows = [
        {"risk": "dMRV rejections", "driver": "Missing temperature logs and photos; MRV-weak sites; new operators",
         "signal": f"Acceptance {acc:.0%} vs {p['kpi_acceptance_green']:.0%} target", "tonnes_at_risk": rej_lost,
         "likelihood": "High", "impact": "High", "rag": rag(acc, p["kpi_acceptance_green"], p["kpi_acceptance_amber"]),
         "owner": "MRV lead", "source": "synthetic actuals"},
        {"risk": "Kiln throughput below design", "driver": "Idle kiln-days (stockouts, vacancies, relocations) and cycle time",
         "signal": f"{bpd:.2f} batches per running kiln-day vs {p['batches_per_kiln_day']:.1f} plan; utilisation {util:.0%}", "tonnes_at_risk": thr_lost,
         "likelihood": "High", "impact": "High", "rag": rag(bpd / p["batches_per_kiln_day"], p["kpi_vs_plan_green"], p["kpi_vs_plan_amber"]),
         "owner": "Head of field ops", "source": "synthetic actuals"},
        {"risk": "Biomass supply and payment integrity", "driver": "Constrained catchments; late village payments erode supply 4–6 weeks later",
         "signal": f"Paid within SLA: {sla:.0%} network, {worst_sla:.0%} worst site", "tonnes_at_risk": sup_lost,
         "likelihood": "Medium", "impact": "High", "rag": rag(worst_sla, p["kpi_payment_sla_green"], p["kpi_payment_sla_amber"]),
         "owner": "Community & finance leads", "source": "synthetic actuals"},
        {"risk": "Operator churn and learning curve", "driver": "New operators fail evidence more often in their first two weeks",
         "signal": f"Attrition {attr:.1%}/month; new-operator acceptance {new_acc:.0%} vs {mature_acc:.0%}",
         "tonnes_at_risk": new_lost, "likelihood": "Medium", "impact": "Medium",
         "rag": rag(attr, p["kpi_attrition_green"], p["kpi_attrition_amber"], higher_is_better=False),
         "owner": "People / training lead", "source": "synthetic actuals"},
        {"risk": "Methodology parameters", "driver": "Persistence factor and CH4 treatment not yet confirmed",
         "signal": "Open question with standard / verifier", "tonnes_at_risk": meth,
         "likelihood": "Medium", "impact": "High", "rag": "Amber", "owner": "Carbon / MRV lead", "source": "tonne model"},
    ]
    df = pd.DataFrame(rows)
    df["category"] = np.where(df.source == "tonne model", "Calibration", "Delivery")
    return df.sort_values(["category", "tonnes_at_risk"], ascending=[False, False]).reset_index(drop=True)

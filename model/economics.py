"""Unit economics, cash timeline and pathway benchmark.

Independent analysis using public information and synthetic data.
Not affiliated with or endorsed by Varaha.

All ₹ figures are 2027 annual unless stated. Capital items are annualised over their life for ₹/t;
the cash timeline uses them as up-front spend.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from model.assumptions import MONTHS, load_params, scenario_params
from model.tonnes import bridge_arrays

CATEGORY = {
    "Biomass purchase": "Feedstock",
    "Biomass transport": "Logistics",
    "Biochar return logistics": "Logistics",
    "Operator pay": "Field operations",
    "Water": "Field operations",
    "Field supervision": "Field operations",
    "Lab testing": "MRV & certification",
    "dMRV devices (annualised)": "MRV & certification",
    "dMRV platform": "MRV & certification",
    "Verification & rating": "MRV & certification",
    "Registry fees": "MRV & certification",
    "Kilns (annualised capex)": "Assets & sites",
    "Sites: setup & relocation": "Assets & sites",
    "Community benefit share": "Community",
    "Programme overhead": "Overhead",
}
VARIABLE = {"Biomass purchase", "Biomass transport", "Biochar return logistics", "Operator pay", "Water",
            "Lab testing", "Registry fees", "Community benefit share"}


def _totals(p: dict, pass_rate=None, kiln_add=None) -> dict:
    arr = bridge_arrays(p, pass_rate=pass_rate, kiln_add=kiln_add)
    extra = kiln_add[0] if kiln_add else 0.0
    kilns_cap = p["kilns_total"] + extra
    avg_sites_active = float(np.mean(arr["kilns_online"])) / p["kilns_per_site"]
    return {
        "arr": arr,
        "batches": float(arr["batches"].sum()), "dry": float(arr["dry_feed_t"].sum()),
        "char": float(arr["biochar_t"].sum()), "net": float(arr["net_tco2e"].sum()),
        "kilns_cap": kilns_cap, "sites_cap": kilns_cap / p["kilns_per_site"], "avg_sites": avg_sites_active,
    }


def cost_buckets(p: dict | None = None, *, pass_rate=None, kiln_add=None) -> pd.DataFrame:
    """Annual ₹ by cost bucket, with ₹ per net tCO2e and variable/fixed tag."""
    p = p or scenario_params("plan_implied")
    t = _totals(p, pass_rate, kiln_add)
    as_received = t["dry"] / (1 - p["biomass_moisture_frac"])
    fx = p["inr_per_usd"]
    b = {
        "Biomass purchase": as_received * 1000 * p["biomass_price_inr_per_kg"],
        "Biomass transport": as_received * p["avg_haul_km"] * p["transport_inr_per_t_km"],
        "Biochar return logistics": t["char"] * p["biochar_return_inr_per_t"],
        "Operator pay": t["batches"] * p["operator_pay_inr_per_batch"],
        "Water": t["batches"] * p["water_l_per_batch"] * p["water_cost_inr_per_l"],
        "Field supervision": t["avg_sites"] * p["supervisors_per_site"] * p["supervisor_inr_per_month"] * 12,
        "Lab testing": t["batches"] * p["lab_sample_frac"] * p["lab_test_inr_per_sample"],
        "dMRV devices (annualised)": t["kilns_cap"] * p["dmrv_device_inr_per_kiln"] / p["dmrv_device_life_years"],
        "dMRV platform": p["dmrv_platform_inr_per_year"],
        "Verification & rating": p["verification_inr_per_year"] + p["rating_fee_inr_per_year"],
        "Registry fees": t["net"] * p["registry_fee_usd_per_t"] * fx,
        "Kilns (annualised capex)": t["kilns_cap"] * p["kiln_capex_inr"] / p["kiln_life_years"],
        "Sites: setup & relocation": t["sites_cap"] * (p["site_setup_inr"] / p["site_asset_life_years"]
                                                       + 365 / p["relocation_interval_days"] * p["relocation_cost_inr"]),
        "Community benefit share": t["net"] * p["community_benefit_inr_per_net_t"],
        "Programme overhead": p["program_overhead_inr_per_year"],
    }
    df = pd.DataFrame({"bucket": list(b), "inr": list(b.values())})
    df["category"] = df.bucket.map(CATEGORY)
    df["type"] = np.where(df.bucket.isin(VARIABLE), "variable", "fixed")
    df["inr_per_net_t"] = df.inr / t["net"]
    df.attrs["net_t"] = t["net"]
    return df


def total_cost_inr(p: dict, **kw) -> float:
    return float(cost_buckets(p, **kw).inr.sum())


def cost_per_net_t(p: dict | None = None) -> float:
    df = cost_buckets(p)
    return float(df.inr.sum() / df.attrs["net_t"])


def breakeven_price_usd(p: dict | None = None) -> float:
    p = p or scenario_params("plan_implied")
    return cost_per_net_t(p) / p["inr_per_usd"]


def margin_table(p: dict | None = None) -> pd.DataFrame:
    """Contribution margin (after variable costs) and full margin per net t at low/default/high price."""
    p = p or scenario_params("plan_implied")
    prm = load_params()["credit_price_usd"]
    df = cost_buckets(p)
    net = df.attrs["net_t"]
    var_t = df.loc[df.type == "variable", "inr"].sum() / net
    full_t = df.inr.sum() / net
    rows = []
    for label, price in (("Low", prm.low), ("Default", p["credit_price_usd"]), ("High", prm.high)):
        rev_t = price * p["inr_per_usd"]
        rows.append({"case": label, "price_usd": price, "revenue_inr_per_t": rev_t,
                     "variable_cost_inr_per_t": var_t, "full_cost_inr_per_t": full_t,
                     "contribution_margin_inr_per_t": rev_t - var_t, "full_margin_inr_per_t": rev_t - full_t,
                     "full_margin_pct": (rev_t - full_t) / rev_t, "annual_full_margin_inr": (rev_t - full_t) * net})
    return pd.DataFrame(rows)


def cash_timeline(p: dict | None = None) -> pd.DataFrame:
    """Monthly cash: spend as incurred, revenue after production→issuance→cash lags. Extends into 2028 until
    the December 2027 vintage is paid. Capital items are spent when kilns/sites come online."""
    p = p or scenario_params("plan_implied")
    df = cost_buckets(p)
    arr = bridge_arrays(p)
    batches = np.asarray(arr["batches"], float)
    net_m = np.asarray(arr["net_tco2e"], float)
    kilns_m = np.asarray(arr["kilns_online"], float)
    lag = int(round(p["production_to_issuance_months"])), int(round(p["issuance_to_cash_months"]))
    horizon = 12 + lag[0] + lag[1] + 1
    spend = np.zeros(horizon)
    revenue = np.zeros(horizon)
    by = dict(zip(df.bucket, df.inr))
    per_batch_var = sum(by[k] for k in ("Biomass purchase", "Biomass transport", "Biochar return logistics",
                                         "Operator pay", "Water", "Lab testing"))
    spend[:12] += per_batch_var * batches / batches.sum()
    new_kilns = np.diff(np.concatenate([[0.0], kilns_m]))
    capex_per_kiln = p["kiln_capex_inr"] + p["dmrv_device_inr_per_kiln"] + p["site_setup_inr"] / p["kilns_per_site"]
    spend[:12] += np.maximum(new_kilns, 0) * capex_per_kiln
    monthly_fixed = (p["dmrv_platform_inr_per_year"] + p["verification_inr_per_year"] + p["rating_fee_inr_per_year"]
                     + p["program_overhead_inr_per_year"]) / 12
    spend[:12] += monthly_fixed
    spend[:12] += kilns_m / p["kilns_per_site"] * (p["supervisors_per_site"] * p["supervisor_inr_per_month"]
                                                   + p["relocation_cost_inr"] * 365 / p["relocation_interval_days"] / 12)
    price_inr = p["credit_price_usd"] * p["inr_per_usd"]
    for m in range(12):
        issue = m + lag[0]
        cash = issue + lag[1]
        spend[issue] += net_m[m] * p["registry_fee_usd_per_t"] * p["inr_per_usd"]
        revenue[cash] += net_m[m] * price_inr
        spend[cash] += net_m[m] * p["community_benefit_inr_per_net_t"]
    months = pd.period_range("2027-01", periods=horizon, freq="M").strftime("%b %Y")
    out = pd.DataFrame({"month": months, "spend_inr": spend, "revenue_inr": revenue})
    out["net_cash_inr"] = out.revenue_inr - out.spend_inr
    out["cum_cash_inr"] = out.net_cash_inr.cumsum()
    out.attrs["working_capital_need_inr"] = float(-out.cum_cash_inr.min())
    out.attrs["trough_month"] = out.month.iloc[int(out.cum_cash_inr.idxmin())]
    return out


def direct_cost_per_kg_biochar(p: dict | None = None) -> float:
    """Field-level cost per kg biochar (operator pay + supervision), to compare with the public
    ~₹10/kg partner-fee anchor (which presumably bundles more)."""
    p = p or scenario_params("plan_implied")
    df = cost_buckets(p)
    t = _totals(p)
    by = dict(zip(df.bucket, df.inr))
    return (by["Operator pay"] + by["Field supervision"]) / (t["char"] * 1000)


def archetype_economics(batches: pd.DataFrame, deliveries: pd.DataFrame, sites: pd.DataFrame,
                        p: dict | None = None) -> pd.DataFrame:
    """₹ per net t by site archetype from synthetic actuals. Variable costs from the data; fixed costs per kiln
    and per site from assumptions.yaml; network overheads allocated by net tonnes."""
    p = p or scenario_params("plan_implied")
    site_arch = sites.set_index("site_id")["archetype"]
    kilns_per_arch = sites.groupby("archetype")["kilns"].sum()
    sites_per_arch = sites.groupby("archetype").size()
    b = batches.assign(archetype=batches.site_id.map(site_arch))
    d = deliveries.assign(archetype=deliveries.site_id.map(site_arch))
    g = b.groupby("archetype").agg(net=("net_tco2e", "sum"), char=("biochar_t", "sum"), n=("batch_id", "size"))
    dg = d.groupby("archetype").agg(biomass_inr=("amount_inr", "sum"), kg=("kg", "sum"))
    total_net = g.net.sum()
    shared = (p["dmrv_platform_inr_per_year"] + p["verification_inr_per_year"] + p["rating_fee_inr_per_year"]
              + p["program_overhead_inr_per_year"])
    rows = []
    for arch in g.index:
        n, net, char = g.loc[arch, "n"], g.loc[arch, "net"], g.loc[arch, "char"]
        k, s = kilns_per_arch[arch], sites_per_arch[arch]
        buckets = {
            "Feedstock": dg.loc[arch, "biomass_inr"],
            "Logistics": dg.loc[arch, "kg"] / 1000 * p["avg_haul_km"] * p["transport_inr_per_t_km"]
                         + char * p["biochar_return_inr_per_t"],
            "Field operations": n * (p["operator_pay_inr_per_batch"] + p["water_l_per_batch"] * p["water_cost_inr_per_l"])
                                + s * p["supervisors_per_site"] * p["supervisor_inr_per_month"] * 12,
            "MRV & certification": n * p["lab_sample_frac"] * p["lab_test_inr_per_sample"]
                                   + k * p["dmrv_device_inr_per_kiln"] / p["dmrv_device_life_years"]
                                   + net * p["registry_fee_usd_per_t"] * p["inr_per_usd"],
            "Assets & sites": k * p["kiln_capex_inr"] / p["kiln_life_years"]
                              + s * (p["site_setup_inr"] / p["site_asset_life_years"]
                                     + 365 / p["relocation_interval_days"] * p["relocation_cost_inr"]),
            "Community": net * p["community_benefit_inr_per_net_t"],
            "Overhead (allocated)": shared * net / total_net,
        }
        for cat, inr in buckets.items():
            rows.append({"archetype": arch, "category": cat, "inr": inr, "inr_per_net_t": inr / net, "net_t": net})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- pathway benchmark
PATHWAYS = {"distributed": "Distributed biochar", "industrial": "Industrial biochar",
            "regenag": "Regenerative agriculture", "erw": "Enhanced rock weathering"}
CRITERIA = {"cost": "Cost per t", "permanence": "Permanence", "time_to_cash": "Time to cash",
            "delivery_risk": "Delivery risk (5 = low)", "mrv_simplicity": "MRV simplicity",
            "cobenefits": "Co-benefits", "scalability": "Scalability"}
DELIVERY_DRIVERS = {
    "distributed": "Biomass supply, operator turnover, evidence capture across hundreds of kilns",
    "industrial": "Plant commissioning and uptime, feedstock contracts, capex",
    "regenag": "Practice adoption and reversal, multi-year measurement",
    "erw": "Measurement uncertainty, rock sourcing and spreading logistics",
}
SCALE_CONSTRAINT = {
    "distributed": "Trained labour and supervision span; residue logistics",
    "industrial": "Capex and permitting per reactor",
    "regenag": "Farmer enrolment and retention",
    "erw": "Rock supply near farms; verification capacity",
}


def pathway_matrix(weights: dict[str, float] | None = None, model_usd_per_t: float | None = None) -> pd.DataFrame:
    """Scored matrix (1–5, higher = better for the developer) with adjustable weights.
    Cost score is derived from the midpoint of each pathway's USD/t range."""
    prm = {k: v.default for k, v in load_params().items() if v.group == "pathway"}
    w = {c: prm[f"pw_weight_{c}"] for c in CRITERIA}
    if weights:
        w.update(weights)
    mids = {k: (prm[f"pw_cost_usd_low_{k}"] + prm[f"pw_cost_usd_high_{k}"]) / 2 for k in PATHWAYS}
    lo, hi = min(mids.values()), max(mids.values())
    rows = []
    for k, label in PATHWAYS.items():
        scores = {"cost": 1 + 4 * (hi - mids[k]) / (hi - lo)}
        for c in CRITERIA:
            if c != "cost":
                scores[c] = prm[f"pw_{c}_{k}"]
        total_w = sum(w.values()) or 1.0
        weighted = sum(w[c] * scores[c] for c in CRITERIA) / total_w
        rows.append({"pathway": label, "cost_range_usd": f"${prm[f'pw_cost_usd_low_{k}']:.0f}–{prm[f'pw_cost_usd_high_{k}']:.0f}",
                     **{CRITERIA[c]: round(scores[c], 1) for c in CRITERIA}, "weighted_score": weighted,
                     "delivery_risk_drivers": DELIVERY_DRIVERS[k], "scalability_constraint": SCALE_CONSTRAINT[k]})
    df = pd.DataFrame(rows).sort_values("weighted_score", ascending=False).reset_index(drop=True)
    if model_usd_per_t is not None:
        df.attrs["model_distributed_usd_per_t"] = model_usd_per_t
    df.attrs["weights"] = w
    return df


def monthly_cost_index() -> list[str]:
    return [m.capitalize() for m in MONTHS]

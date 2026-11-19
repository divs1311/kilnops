"""Regenerate every document from model outputs so no quoted number can drift from the model.

Run: python -m tools.build_docs [--no-pdf]
  1. computes key numbers → docs/key_numbers.json
  2. fills <<placeholders>> in docs/templates/* → README.md, docs/memo.tex, docs/talk_track.md, docs/sop_site_launch.md
  3. compiles docs/memo.pdf (pdflatex) and docs/sop_site_launch.pdf (pandoc)

Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys

import pandas as pd

from model import economics, kpis, tonnes
from model.assumptions import ROOT, load_params, meta, scenario_params

TEMPLATES = ROOT / "docs" / "templates"
OUTPUTS = {"README.md.tmpl": ROOT / "README.md", "memo.tex.tmpl": ROOT / "docs" / "memo.tex",
           "talk_track.md.tmpl": ROOT / "docs" / "talk_track.md", "sop_site_launch.md.tmpl": ROOT / "docs" / "sop_site_launch.md"}
TABLES = ("sites", "kilns", "kiln_status", "operators", "villages", "batches", "biomass_deliveries", "biochar_returns", "payouts")


def kt(x: float) -> str:
    return f"{x / 1000:,.1f}k"


def kt0(x: float) -> str:
    return f"{x / 1000:,.0f}k"


def inr(x: float) -> str:
    if abs(x) >= 1e7:
        return f"₹{x / 1e7:,.1f} crore"
    if abs(x) >= 1e5:
        return f"₹{x / 1e5:,.1f} lakh"
    return f"₹{x:,.0f}"


def rs(x: float) -> str:
    return f"{'−' if x < 0 else ''}₹{abs(x):,.0f}"


def pct(x: float, d: int = 0) -> str:
    return f"{x * 100:.{d}f}%"


def compute() -> dict[str, str]:
    m = meta()
    target = m["target_net_tco2e"]
    P = load_params()
    lit, plan = scenario_params("literature"), scenario_params("plan_implied")
    T = {n: pd.read_parquet(ROOT / "data" / f"{n}.parquet") for n in TABLES}
    b, d, s = T["batches"], T["biomass_deliveries"], T["sites"]

    mc_plan, mc_lit = tonnes.monte_carlo("plan_implied"), tonnes.monte_carlo("literature")
    mcs = {k: tonnes.monte_carlo(k) for k in ("biomass_shock", "mrv_slippage", "slow_ramp", "upside")}
    det = tonnes.scenario_summary().set_index("scenario").net_tco2e
    br_plan = tonnes.monthly_bridge(plan)
    st_lit = tonnes.solver_table(lit).set_index("key")
    lit_net = tonnes.annual_net(lit)
    lv = tonnes.lever_simulator(plan, reference_net=mc_plan["p50"])
    eff = lv[~lv.no_effect].reset_index(drop=True)
    cb = economics.cost_buckets(plan).set_index("bucket")
    net_plan = cb.attrs["net_t"]
    cost_t = economics.cost_per_net_t(plan)
    be = economics.breakeven_price_usd(plan)
    mt = economics.margin_table(plan).set_index("case")
    cash = economics.cash_timeline(plan)
    rr = kpis.risk_register(T, plan)
    dlv = rr[rr.category == "Delivery"].reset_index(drop=True)
    cal = rr[rr.category == "Calibration"].iloc[0]
    dvp = kpis.cumulative_delivery_vs_plan(b)
    sla = plan["payment_sla_days"]
    sla_site = kpis.village_payment_sla(d, sla, by="site_id")
    worst_site = sla_site.idxmin()
    ons = kpis.payment_supply_onset(d, worst_site, sla)
    rej = b[~b.accepted].rejection_reason.astype(str).value_counts()
    rej = rej[rej.index != ""]
    ae = economics.archetype_economics(b, d, s, plan).groupby("archetype").inr_per_net_t.sum()
    imp_plan = tonnes.implied_requirements(plan)
    imp_lit = tonnes.implied_requirements(lit)
    tor = tonnes.tornado("plan_implied")
    drift = tonnes.p50_drift_decomposition("plan_implied")
    new_acc = b[b.lead_tenure_days <= 14].accepted.mean()
    mat_acc = b[b.lead_tenure_days > 60].accepted.mean()
    acc = kpis.batch_acceptance_pct(b)
    bpd_act = kpis.batches_per_kiln_day(b)
    counts = pd.Series([p.status for p in P.values()]).value_counts()
    ch4_share = lambda ef: ef / 1000 * plan["ch4_gwp100"] / float(tonnes.gross_t_per_t_biochar(plan))

    K = {
        "disclaimer": m["disclaimer"],
        "target": kt0(target), "target_full": f"{target:,}",
        "n_params": f"{len(P)}", "n_public": f"{counts.get('PUBLIC', 0)}", "n_lit": f"{counts.get('LITERATURE', 0)}",
        "n_assump": f"{counts.get('ASSUMPTION – VERIFY', 0)}", "mc_runs": f"{int(m['mc_runs']):,}",
        # literature view
        "lit_net": kt(lit_net), "lit_share": pct(lit_net / target), "lit_p50": kt(mc_lit["p50"]),
        "lit_throughput": f"{lit['dry_biomass_per_batch_t'] * lit['batches_per_kiln_day']:.2f}",
        "lit_throughput_req": f"{lit['dry_biomass_per_batch_t'] * lit['batches_per_kiln_day'] * target / lit_net:.1f}",
        "lit_bpd_req": f"{st_lit.loc['batches_per_kiln_day', 'required']:.1f}",
        "lit_footprint_dry": kt0(imp_lit["dry_feed_needed_t"]), "lit_villages": f"{imp_lit['villages_needed']:,.0f}",
        # plan design point
        "plan_dry": f"{plan['dry_biomass_per_batch_t']:.1f}", "plan_bpd": f"{plan['batches_per_kiln_day']:.1f}",
        "plan_ch4": f"{plan['ch4_ef_g_per_kg_biochar']:.0f}", "plan_kiln_m3": f"{plan['kiln_volume_m3']:.0f}",
        "plan_moisture": pct(plan["moisture_dry_threshold"]), "plan_throughput": f"{plan['dry_biomass_per_batch_t'] * plan['batches_per_kiln_day']:.1f}",
        "plan_det": kt(det["plan_implied"]), "plan_p10": kt(mc_plan["p10"]), "plan_p50": kt(mc_plan["p50"]),
        "plan_p90": kt(mc_plan["p90"]), "plan_prob": pct(mc_plan["prob_hit"], 1), "contingency": kt0(target - mc_plan["p50"]),
        "plan_pass": pct(float(tonnes.dmrv_pass_rate(plan))),
        "plan_loss_share": pct((br_plan.rejected_tco2e.sum() + br_plan.project_emissions_tco2e.sum() + br_plan.buffer_tco2e.sum())
                               / br_plan.gross_tco2e.sum()),
        "plan_h1_share": pct(br_plan.net_tco2e.iloc[:6].sum() / br_plan.net_tco2e.sum()),
        "plan_monsoon_share": pct(br_plan.net_tco2e.iloc[5:9].sum() / br_plan.net_tco2e.sum()),
        "plan_dry_feed": kt0(imp_plan["dry_feed_needed_t"]), "plan_ar_feed": kt0(imp_plan["as_received_feed_needed_t"]),
        "plan_villages": f"{imp_plan['villages_needed']:,.0f}", "plan_farmers": kt0(imp_plan["farmers_engaged"]),
        "plan_operators": f"{imp_plan['operators']:,.0f}", "plan_replacements": f"{imp_plan['operator_replacements_per_year']:,.0f}",
        "drift_total": pct(1 - mc_plan["p50"] / det["plan_implied"]),
        "drift_top": drift.parameter.iloc[0], "drift_top_pct": f"{drift['pct_change'].iloc[0]:.0f}%",
        "tor_top1": tor.parameter.iloc[0], "tor_top2": tor.parameter.iloc[1],
        "ch4_share_5": pct(ch4_share(5)), "ch4_share_30": pct(ch4_share(30)), "ch4_share_15": pct(ch4_share(15)),
        "pers_uplift": pct(tonnes.annual_net({**plan, "persistence_factor": P["persistence_factor"].high}) / det["plan_implied"] - 1),
        "anchor_kiln": f"{target / plan['kilns_total']:.0f}", "anchor_ramp": f"{imp_plan['net_per_kiln_year_needed_with_ramp']:.0f}",
        "dmrv_step": f"{plan['lever_dmrv_step_pp']:.0f}",
        # scenarios
        "shock_p50": kt(mcs["biomass_shock"]["p50"]), "mrv_p50": kt(mcs["mrv_slippage"]["p50"]),
        "ramp_p50": kt(mcs["slow_ramp"]["p50"]), "upside_p50": kt(mcs["upside"]["p50"]), "upside_det": kt(det["upside"]),
        # actuals
        "act_net": kt(dvp.cum_actual.iloc[-1]), "act_ratio": pct(dvp.ratio.iloc[-1]), "act_acc": pct(acc),
        "act_bpd": f"{bpd_act:.2f}", "new_acc": pct(new_acc), "mat_acc": pct(mat_acc),
        "rej1": rej.index[0].lower(), "rej2": rej.index[1].lower(), "rej12_share": pct(rej.iloc[:2].sum() / rej.sum()),
        "mrvweak_acc": pct(b.merge(s[["site_id", "archetype"]], on="site_id").groupby("archetype").accepted.mean()["MRV-weak"]),
        "net_sla": pct(kpis.village_payment_sla(d, sla), 0), "worst_site": worst_site, "worst_sla": pct(sla_site.min()),
        "median_sla": pct(sla_site.median()), "sla_days": f"{sla:.0f}",
        "onset_gap": f"{ons['gap_weeks']:.0f}", "onset_before": f"{ons['ratio_before']:.2f}", "onset_after": f"{ons['ratio_after']:.2f}",
        "onset_date": f"{ons['onset_pay']:%d %b}",
        "arch_gap": f"₹{ae.max() - ae.min():,.0f}", "arch_worst": ae.idxmax(), "arch_best": ae.idxmin(),
        # risks
        **{f"risk{i + 1}": dlv.risk[i] for i in range(3)},
        **{f"risk{i + 1}_t": kt(dlv.tonnes_at_risk[i]) for i in range(3)},
        **{f"risk{i + 1}_sig": dlv.signal[i] for i in range(3)},
        **{f"risk{i + 1}_rag": dlv.rag[i] for i in range(3)},
        **{f"risk{i + 1}_lik": dlv.likelihood[i] for i in range(3)},
        **{f"risk{i + 1}_imp": dlv.impact[i] for i in range(3)},
        "cal_risk_t": kt(cal.tonnes_at_risk),
        # levers
        **{f"lev{i + 1}": eff.lever[i] for i in range(3)},
        **{f"lev{i + 1}_cost": f"₹{eff.inr_per_incremental_t[i]:,.0f}" for i in range(3)},
        **{f"lev{i + 1}_t": kt(eff.delta_net_t[i]) for i in range(3)},
        **{f"lev{i + 1}_gap": f"{eff.gap_closed_pct[i]:.0f}%" for i in range(3)},
        **{f"lev{i + 1}_inr": inr(eff.delta_cost_inr[i]) for i in range(3)},
        "lev_ratio": f"{eff.inr_per_incremental_t[1] / eff.inr_per_incremental_t[0]:.0f}",
        "lev_top3_gap": f"{eff.gap_closed_pct[:3].sum():.0f}%",
        "lev_shift_t": kt(lv.set_index("lever").delta_net_t.filter(like="Second shift").iloc[0]),
        "lev_shift_cost": f"₹{lv.set_index('lever').inr_per_incremental_t.filter(like='Second shift').iloc[0]:,.0f}",
        "lev_kilns_t": kt(lv.set_index("lever").delta_net_t.filter(like="kilns").iloc[0]),
        # economics
        "cost_t": f"₹{cost_t:,.0f}", "cost_usd": f"${cost_t / plan['inr_per_usd']:,.0f}", "breakeven": f"${be:,.0f}",
        "price": f"${plan['credit_price_usd']:.0f}", "price_low": f"${P['credit_price_usd'].low:.0f}",
        "price_high": f"${P['credit_price_usd'].high:.0f}", "margin_pct": pct(mt.loc["Default", "full_margin_pct"]),
        "margin_low_t": rs(mt.loc["Low", "full_margin_inr_per_t"]), "margin_high_t": rs(mt.loc["High", "full_margin_inr_per_t"]),
        "feed_share": pct(cb.loc["Biomass purchase", "inr"] / cb.inr.sum()),
        "per_10paise": f"₹{cb.loc['Biomass purchase', 'inr_per_net_t'] * 0.1 / plan['biomass_price_inr_per_kg']:,.0f}",
        "wc": inr(cash.attrs["working_capital_need_inr"]), "wc_month": cash.attrs["trough_month"],
        "annual_spend": inr(cb.inr.sum()), "lit_cost_t": f"₹{economics.cost_per_net_t(lit):,.0f}",
        "direct_kg": f"₹{economics.direct_cost_per_kg_biochar(plan):,.1f}", "partner_fee": f"₹{plan['partner_fee_inr_per_kg_biochar']:.0f}",
        "biomass_per_kg_char": f"₹{plan['biomass_price_inr_per_kg'] / (1 - plan['biomass_moisture_frac']) / plan['biochar_yield_dry_frac']:,.1f}",
        # SOP constants (all from yaml)
        "sop_cover": f"{plan['biomass_cover_days_target']:.0f}", "sop_cover_red": f"{plan['kpi_cover_amber']:.0f}",
        "sop_moisture": pct(plan["moisture_dry_threshold"]), "sop_hcorg": f"{plan['h_corg_max_eligible']:.1f}",
        "sop_lab": pct(plan["lab_sample_frac"]), "sop_water": f"{plan['water_l_per_batch']:.0f}",
        "sop_burn": f"{plan['burn_time_h']:.0f}", "sop_temp": f"{P['peak_temp_mean_c'].low:.0f}",
        "sop_radius": f"{plan['collection_radius_km']:.0f}", "sop_train": f"{plan['training_weeks_to_full']:.0f}",
        "sop_ops": f"{plan['operators_per_kiln']:.0f}", "sop_kps": f"{plan['kilns_per_site']:.0f}",
        "sop_return": f"{plan['biochar_return_interval_days']:.0f}", "sop_reloc": f"{plan['relocation_interval_days']:.0f}",
        "sop_reloc_down": f"{plan['relocation_downtime_days']:.0f}", "sop_acc_green": pct(plan["kpi_acceptance_green"]),
        "sop_sla_green": pct(plan["kpi_payment_sla_green"]), "sop_return_green": pct(plan["kpi_return_green"]),
        "sop_ev_green": pct(plan["kpi_evidence_green"]), "sop_price": f"₹{plan['biomass_price_inr_per_kg']:.1f}",
        "sop_attr": pct(plan["kpi_attrition_amber"]), "sla_amber": pct(plan["kpi_payment_sla_amber"]),
    }
    return K


def render(K: dict[str, str]) -> dict:
    out = {}
    for tmpl, dest in OUTPUTS.items():
        text = (TEMPLATES / tmpl).read_text(encoding="utf-8")
        missing = sorted(set(re.findall(r"<<(\w+)>>", text)) - set(K))
        if missing:
            raise KeyError(f"{tmpl}: unknown placeholders {missing}")
        val = (lambda k: _tex(K[k])) if tmpl.endswith(".tex.tmpl") else (lambda k: K[k])
        out[dest] = re.sub(r"<<(\w+)>>", lambda mm: val(mm.group(1)), text)
    return out


def _tex(s: str) -> str:
    return (s.replace("\\", r"\textbackslash{}").replace("%", r"\%").replace("$", r"\$").replace("&", r"\&")
            .replace("_", r"\_").replace("#", r"\#").replace("₹", r"\rupee{}")
            .replace("–", "--").replace("−", "$-$").replace("CO₂", r"CO\textsubscript{2}").replace("₄", r"\textsubscript{4}"))


def build_pdfs() -> None:
    docs = ROOT / "docs"
    if shutil.which("xelatex"):
        for _ in range(2):
            subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "memo.tex"], cwd=docs,
                           check=True, capture_output=True)
        for ext in (".aux", ".log", ".out"):
            (docs / f"memo{ext}").unlink(missing_ok=True)
    if shutil.which("pandoc"):
        subprocess.run(["pandoc", "sop_site_launch.md", "-o", "sop_site_launch.pdf", "--pdf-engine=xelatex",
                        "-V", "geometry:margin=1.8cm", "-V", "fontsize=10pt", "-V", "mainfont=Inter",
                        "-V", "colorlinks=true", "-V", "linkcolor=teal"],
                       cwd=docs, check=True, capture_output=True)


def main(pdf: bool = True) -> dict[str, str]:
    K = compute()
    (ROOT / "docs" / "key_numbers.json").write_text(json.dumps(K, indent=2, ensure_ascii=False), encoding="utf-8")
    for dest, text in render(K).items():
        dest.write_text(text, encoding="utf-8")
    if pdf:
        build_pdfs()
    return K


if __name__ == "__main__":
    K = main(pdf="--no-pdf" not in sys.argv)
    print(json.dumps(K, indent=1, ensure_ascii=False))

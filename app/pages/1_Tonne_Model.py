"""Tonne model and "what has to be true".

Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import (ACCENT, ACCENT_LIGHT, GREY, GREY_LIGHT, TARGET, drift, fmt_inr, fmt_pct, fmt_t, footer, levers, mc,
                    page_setup, params_for, scenario_list, scenario_table, so_what, tornado)
from model import tonnes
from model.assumptions import load_params

page_setup("Tonne Model")
st.title("Tonne model and “what has to be true”")

SLIDERS = [
    ("dry_biomass_per_batch_t", "Dry biomass per batch (t)", 0.05),
    ("batches_per_kiln_day", "Batches per kiln-day", 0.05),
    ("kilns_total", "Kilns at full operation", 5.0),
    ("ramp_full_month", "Month fleet is fully online", 1.0),
    ("biomass_availability_factor", "Kiln-days with feedstock (share)", 0.01),
    ("ch4_ef_g_per_kg_biochar", "CH₄ emission factor (g/kg char)", 0.5),
    ("persistence_factor", "Persistence factor", 0.01),
    ("biochar_corg_frac", "Biochar organic C", 0.01),
    ("evidence_remediation_frac", "Evidence remediation share", 0.05),
    ("buffer_deduction_frac", "Buffer deduction", 0.01),
]
P = load_params()
scn = scenario_list()
labels = {k: v["label"] for k, v in scn.items()}

top = st.columns([1.2, 2])
with top[0]:
    scenario = st.radio("Scenario", list(labels), index=list(labels).index("plan_implied"),
                        format_func=lambda k: labels[k], key="scenario")
    st.caption(scn[scenario]["description"])
base = params_for(scenario)


def _reset():
    for key, _, _ in SLIDERS:
        st.session_state[f"sl_{key}"] = float(base[key])


if st.session_state.get("_scn_loaded") != scenario:
    _reset()
    st.session_state["_scn_loaded"] = scenario

with top[1]:
    st.markdown("**Levers** (bounded by `assumptions.yaml` ranges)")
    cols = st.columns(2)
    for i, (key, label, step) in enumerate(SLIDERS):
        prm = P[key]
        lo, hi = min(prm.low, base[key]), max(prm.high, base[key])
        cols[i % 2].slider(label, float(lo), float(hi), step=step, key=f"sl_{key}",
                           help=f"{prm.status} · {prm.source}")
    st.button("Reset to scenario defaults", on_click=_reset)

p = {**base, **{k: st.session_state[f"sl_{k}"] for k, _, _ in SLIDERS}}
bridge = tonnes.monthly_bridge(p)
net = bridge.net_tco2e.sum()
m = mc(scenario)
changed = any(abs(p[k] - base[k]) > 1e-9 for k, _, _ in SLIDERS)

c = st.columns(4)
c[0].metric("Deterministic net (current levers)", fmt_t(net), f"{net / TARGET - 1:+.0%} vs target")
c[1].metric("dMRV pass rate", fmt_pct(float(tonnes.dmrv_pass_rate(p)), 1))
c[2].metric(f"Monte Carlo P50 · {labels[scenario]}", fmt_t(m["p50"]), f"P10 {fmt_t(m['p10'])} · P90 {fmt_t(m['p90'])}", delta_color="off")
c[3].metric("Probability ≥100k t", fmt_pct(m["prob_hit"], 1))
if changed:
    st.caption("Sliders move the deterministic bridge and solver. Monte Carlo figures are for the selected scenario as defined in assumptions.yaml.")

# ------------------------------------------------------------------ bridge
st.subheader("Tonne bridge, 2027")
l, r = st.columns([1, 1.2])
with l:
    steps = [("Gross removals", bridge.gross_tco2e.sum(), "absolute"), ("dMRV rejections", -bridge.rejected_tco2e.sum(), "relative"),
             ("Project emissions", -bridge.project_emissions_tco2e.sum(), "relative"), ("Buffer", -bridge.buffer_tco2e.sum(), "relative"),
             ("Net", net, "total")]
    fig = go.Figure(go.Waterfall(x=[s[0] for s in steps], y=[s[1] for s in steps], measure=[s[2] for s in steps],
                                 text=[fmt_t(abs(s[1])) for s in steps], textposition="outside",
                                 increasing=dict(marker_color=ACCENT), decreasing=dict(marker_color=GREY_LIGHT),
                                 totals=dict(marker_color=ACCENT), connector=dict(line=dict(color=GREY_LIGHT))))
    fig.add_hline(y=TARGET, line_dash="dash", line_color="#B91C1C", annotation_text="100k target", annotation_position="top left")
    fig.update_layout(height=340, yaxis_tickformat="~s", yaxis_title="tCO₂e", showlegend=False)
    st.plotly_chart(fig, width="stretch")
    share = (bridge.rejected_tco2e.sum() + bridge.project_emissions_tco2e.sum() + bridge.buffer_tco2e.sum()) / bridge.gross_tco2e.sum()
    so_what(f"{share:.0%} of gross removals are lost before credit. Rejections are the largest deduction and the most controllable.")
with r:
    fig = go.Figure()
    fig.add_bar(x=bridge.month, y=bridge.net_tco2e, name="Net (current levers)", marker_color=ACCENT)
    fig.add_scatter(x=bridge.month, y=bridge.plan_tco2e, name="Plan phasing", mode="lines+markers", line=dict(color=GREY, dash="dash"))
    fig.update_layout(height=340, yaxis_tickformat="~s", yaxis_title="Net tCO₂e per month")
    st.plotly_chart(fig, width="stretch")
    h1 = bridge.net_tco2e.iloc[:6].sum() / net
    so_what(f"Jan–Jun carries {h1:.0%} of the year. Jul–Aug is close to zero, so Q1 throughput decides the year.")

# ------------------------------------------------------------------ solver
st.subheader("What has to be true: the value each lever needs, on its own, to deliver 100k t")
st_tbl = tonnes.solver_table(p)
show = st_tbl[["lever", "kind", "default", "required", "change_pct", "plausible_low", "plausible_high", "feasibility"]].copy()
show.columns = ["Lever", "Type", "Current", "Required for 100k", "Change", "Plausible low", "Plausible high", "Verdict"]
show["Change"] = show["Change"].map(lambda v: f"{v:+.0f}%")
st.dataframe(show, hide_index=True, width="stretch",
             column_config={c_: st.column_config.NumberColumn(format="%.2f") for c_ in
                            ["Current", "Required for 100k", "Plausible low", "Plausible high"]})
feasible = (st_tbl.feasibility == "Within plausible range").sum()
so_what(f"{feasible} of {len(st_tbl)} levers can close the gap alone within their plausible range. "
        + ("Below 100k, the plan needs a stack of levers, not one heroic assumption." if net < TARGET
           else "At these settings the target is met. The table shows how much headroom each lever has before it falls short."))

# ------------------------------------------------------------------ tornado + MC
l, r = st.columns(2)
with l:
    st.subheader(f"Tornado · {labels[scenario]}")
    tor = tornado(scenario).head(12).iloc[::-1]
    fig = go.Figure()
    base_net = tonnes.annual_net(base)
    for row in tor.itertuples():
        lo_, hi_ = sorted([row.net_at_low, row.net_at_high])
        fig.add_bar(y=[row.parameter], x=[hi_ - lo_], base=[lo_], orientation="h",
                    marker_color=ACCENT if row.status != "ASSUMPTION – VERIFY" else "#F59E0B", showlegend=False,
                    hovertemplate=f"{row.parameter}<br>low {row.low:.3g} → {row.net_at_low:,.0f} t<br>high {row.high:.3g} → {row.net_at_high:,.0f} t<extra></extra>")
    fig.add_vline(x=base_net, line_color=GREY)
    fig.add_vline(x=TARGET, line_color="#B91C1C", line_dash="dash")
    fig.update_layout(height=420, xaxis_tickformat="~s", xaxis_title="Annual net tCO₂e (input low → high)")
    st.plotly_chart(fig, width="stretch")
    so_what("Amber bars are unverified analyst assumptions. Validate the longest amber bars first, and measure them in week 1.")
with r:
    st.subheader(f"Monte Carlo · {m['n']:,} runs")
    fig = go.Figure(go.Histogram(x=m["annual"], nbinsx=60, marker_color=ACCENT_LIGHT))
    for q, lab in ((m["p10"], "P10"), (m["p50"], "P50"), (m["p90"], "P90")):
        fig.add_vline(x=q, line_color=ACCENT, line_dash="dot", annotation_text=lab)
    fig.add_vline(x=TARGET, line_color="#B91C1C", annotation_text="100k")
    fig.update_layout(height=250, xaxis_tickformat="~s", xaxis_title="Annual net tCO₂e", yaxis_title="Runs", bargap=0.02)
    st.plotly_chart(fig, width="stretch")
    dr = drift(scenario).head(8).iloc[::-1]
    fig = go.Figure(go.Bar(y=dr["parameter"], x=dr["pct_change"], orientation="h", marker_color=GREY))
    fig.update_layout(height=230, xaxis_title="% change in net when input moves from nominal to its expected value",
                      margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")
    so_what(f"Why P50 ({fmt_t(m['p50'])}) sits below the design point: most nominal values are at the favourable end of their "
            "range. Each bar is a buffer the plan does not yet hold.")

# ------------------------------------------------------------------ scenarios & levers
st.subheader("Scenarios")
stbl = scenario_table()[["label", "net_tco2e", "p10", "p50", "p90", "prob_hit", "pass_rate", "overrides"]].copy()
stbl.columns = ["Scenario", "Deterministic", "P10", "P50", "P90", "P(≥100k)", "Pass rate", "What changes"]
st.dataframe(stbl, hide_index=True, width="stretch",
             column_config={**{c_: st.column_config.NumberColumn(format="%,.0f") for c_ in ["Deterministic", "P10", "P50", "P90"]},
                            "P(≥100k)": st.column_config.NumberColumn(format="percent"),
                            "Pass rate": st.column_config.NumberColumn(format="percent")})
so_what("Slow ramp and MRV slippage each cost about as much as a weak biomass season. All three are execution risks that Q1 actions can reduce.")

st.subheader("Lever simulator · ₹ per incremental tonne (vs plan-implied)")
lv = levers("plan_implied")
lvs = lv.copy()
lvs["inr_per_incremental_t"] = lvs.inr_per_incremental_t.fillna(np.nan)
fig = go.Figure(go.Bar(y=lvs.lever[::-1], x=lvs.inr_per_incremental_t[::-1], orientation="h", marker_color=ACCENT,
                       text=[("already in plan" if n else f"+{fmt_t(d)} · {g:.0f}% of gap") for n, d, g in
                             zip(lvs.no_effect[::-1], lvs.delta_net_t[::-1], lvs.gap_closed_pct[::-1])],
                       textposition="outside"))
fig.update_layout(height=300, xaxis_title="₹ per incremental net tCO₂e", xaxis_range=[0, lvs.inr_per_incremental_t.max() * 1.45])
st.plotly_chart(fig, width="stretch")
eff = lvs[~lvs.no_effect]
so_what(f"{eff.iloc[0].lever} is about {eff.iloc[1].inr_per_incremental_t / eff.iloc[0].inr_per_incremental_t:.0f}× cheaper per tonne "
        f"than the next lever. Together the top three close about {eff.head(3).gap_closed_pct.sum():.0f}% of the gap between the P50 and the target.")
footer()

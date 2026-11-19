"""KilnOps · Executive Summary (home page).

Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.
"""
import plotly.graph_objects as go
import streamlit as st

from common import (ACCENT, ACCENT_LIGHT, GREY, RAG_COLOR, TARGET, chip, delivery_vs_plan, fmt_inr, fmt_pct, fmt_t,
                    footer, levers, mc, page_setup, risks, scenario_table, so_what)

page_setup("Executive Summary")

st.title("Can a 450-kiln distributed network deliver 100k tCO₂e in 2027?")
st.caption("Executive summary · what has to be true, the top risks, and the levers ranked by ₹ per incremental tonne")

sc = scenario_table().set_index("scenario")
plan, lit = mc("plan_implied"), mc("literature")
dvp = delivery_vs_plan()
actual, ratio = dvp.cum_actual.iloc[-1], dvp.ratio.iloc[-1]

c = st.columns(5)
c[0].metric("P50 net t, plan-implied", fmt_t(plan["p50"]), f"{(plan['p50'] / TARGET - 1):+.0%} vs 100k target", delta_color="normal")
c[1].metric("Probability of ≥100k t", fmt_pct(plan["prob_hit"], 1), help="Share of 5,000 Monte Carlo runs at or above 100k t net.")
c[2].metric("Design point (nominal)", fmt_t(sc.loc["plan_implied", "net_tco2e"]),
            help="Deterministic plan-implied scenario: 2.5 t dry batches, 1.8 batches/kiln-day, dried feedstock.")
c[3].metric("Synthetic actuals, full year", fmt_t(actual), f"{ratio:.0%} of plan", delta_color="off")
c[4].metric("P50 on literature defaults", fmt_t(lit["p50"]), "calibration risk", delta_color="off",
            help="If kiln throughput and methane match published values rather than the plan's design.")
so_what(f"At the design point the network clears 100k t only if every input lands at nominal. Execution variance pulls "
        f"the P50 to {fmt_t(plan['p50'])} (P10–P90 {fmt_t(plan['p10'])}–{fmt_t(plan['p90'])}), so the plan needs about "
        f"{fmt_t(TARGET - plan['p50'], 0)} of contingency, bought through the levers below.")

left, right = st.columns([1.25, 1])
with left:
    st.subheader("Cumulative delivery vs plan")
    fig = go.Figure()
    months = dvp.month.tolist()
    fig.add_trace(go.Scatter(x=months, y=plan["cum_p90"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=months, y=plan["cum_p10"], fill="tonexty", fillcolor="rgba(153,213,204,0.35)",
                             line=dict(width=0), name="Model P10–P90"))
    fig.add_trace(go.Scatter(x=months, y=dvp.cum_plan, name="Plan (100k t)", line=dict(color=GREY, dash="dash")))
    fig.add_trace(go.Scatter(x=months, y=dvp.cum_actual, name="Synthetic actuals", line=dict(color=ACCENT, width=3)))
    fig.update_layout(height=330, yaxis_title="Cumulative net tCO₂e", yaxis_tickformat="~s")
    st.plotly_chart(fig, width="stretch")
    so_what(f"Actuals track about {1 - ratio:.0%} below plan from January. The monsoon (Jun–Sep) adds almost nothing, so the "
            f"shortfall must be recovered in Jan–May and Oct–Dec. H1 slippage is effectively permanent.")

with right:
    st.subheader("Top 3 delivery risks")
    rr = risks()
    top = rr[rr.category == "Delivery"].head(3)
    html = "<table style='width:100%;font-size:.85rem;border-collapse:collapse'>"
    html += "<tr style='color:#6B7280;text-align:left'><th>Risk</th><th>Signal</th><th style='text-align:right'>t at risk</th><th>RAG</th></tr>"
    for r in top.itertuples():
        html += (f"<tr style='border-top:1px solid #E5E7EB'><td><b>{r.risk}</b><br><span style='color:#6B7280'>{r.driver}</span></td>"
                 f"<td>{r.signal}</td><td style='text-align:right'>{fmt_t(r.tonnes_at_risk)}</td><td>{chip(r.rag)}</td></tr>")
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)
    cal = rr[rr.category == "Calibration"].iloc[0]
    st.markdown(f"<div style='font-size:.82rem;margin-top:.6rem'>Calibration risk, not an ops risk: <b>{cal.risk}</b> "
                f"(up to {fmt_t(cal.tonnes_at_risk)} downside). {cal.signal}.</div>", unsafe_allow_html=True)
    so_what("Rejections and idle kiln-days are the largest controllable losses. Late village payments are smaller in tonnes, "
            "but they are the risk that reaches buyers and ratings.")

st.subheader("Top 3 levers, ranked by ₹ per incremental tonne")
lv = levers("plan_implied")
lv = lv[~lv.no_effect].head(3)
cols = st.columns(3)
for col, r in zip(cols, lv.itertuples()):
    col.markdown(f"<div style='border:1px solid #E5E7EB;border-radius:8px;padding:.7rem .9rem'>"
                 f"<div style='font-size:.8rem;color:#6B7280'>Owner: {r.owner}</div>"
                 f"<div style='font-weight:600;margin:.2rem 0'>{r.lever}</div>"
                 f"<div style='font-size:1.4rem;color:{ACCENT};font-weight:700'>₹{r.inr_per_incremental_t:,.0f}/t</div>"
                 f"<div style='font-size:.82rem'>+{fmt_t(r.delta_net_t)} · {fmt_inr(r.delta_cost_inr)} · "
                 f"{r.gap_closed_pct:.0f}% of P50 gap</div></div>", unsafe_allow_html=True)
so_what(f"Recovering tonnes already produced (dMRV) costs about ₹{lv.iloc[0].inr_per_incremental_t:,.0f}/t. Producing new tonnes "
        f"costs about ₹{lv.iloc[1].inr_per_incremental_t:,.0f}/t, close to full unit cost. Fix evidence capture before adding capacity.")

footer()

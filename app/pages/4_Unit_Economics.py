"""Unit economics and pathway benchmark.

Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import (ACCENT, ACCENT_LIGHT, GREY, GREY_LIGHT, cash, cost_stack, fmt_inr, fmt_t, footer, load_tables,
                    page_setup, params_for, scenario_list, so_what)
from model import economics
from model.assumptions import load_params

page_setup("Unit Economics")
st.title("Unit economics and pathway benchmark")

scn = scenario_list()
scenario = st.radio("Scenario", ["plan_implied", "literature"], horizontal=True, format_func=lambda k: scn[k]["label"])
p = params_for(scenario)
cs = cost_stack(scenario)
net = float(economics.cost_buckets(p).attrs["net_t"])
cost_t = cs.inr.sum() / net
be = cost_t / p["inr_per_usd"]
margins = economics.margin_table(p)
cash_df, wc, trough = cash(scenario)
P = load_params()

c = st.columns(5)
c[0].metric("Full cost per net t", f"₹{cost_t:,.0f}", f"${be:,.0f}/t", delta_color="off")
c[1].metric("Breakeven credit price", f"${be:,.0f}", f"vs ${p['credit_price_usd']:.0f} anchor", delta_color="off")
c[2].metric("Full margin at anchor price", f"{margins.loc[1, 'full_margin_pct']:.0%}", fmt_inr(margins.loc[1, "annual_full_margin_inr"]), delta_color="off")
c[3].metric("Peak working capital", fmt_inr(wc), f"trough {trough}", delta_color="off")
c[4].metric("Annual spend", fmt_inr(cs.inr.sum()), f"{fmt_t(net)} net", delta_color="off")

# ------------------------------------------------------------------ cost stack
l, r = st.columns([1.3, 1])
with l:
    st.subheader("Cost stack, ₹ per net tCO₂e")
    cat = cs.groupby("category").inr_per_net_t.sum().sort_values(ascending=False)
    fig = go.Figure(go.Waterfall(x=list(cat.index) + ["Total"], y=list(cat.values) + [cat.sum()],
                                 measure=["relative"] * len(cat) + ["total"],
                                 text=[f"₹{x:,.0f}" for x in list(cat.values) + [cat.sum()]], textposition="outside",
                                 increasing=dict(marker_color=ACCENT_LIGHT), totals=dict(marker_color=ACCENT),
                                 connector=dict(line=dict(color=GREY_LIGHT))))
    fig.add_hline(y=p["credit_price_usd"] * p["inr_per_usd"], line_dash="dash", line_color=GREY,
                  annotation_text=f"Revenue at ${p['credit_price_usd']:.0f}", annotation_position="top left")
    fig.update_layout(height=360, yaxis_title="₹ per net t", showlegend=False)
    st.plotly_chart(fig, width="stretch")
    bio = cs.set_index("bucket").loc["Biomass purchase", "inr_per_net_t"]
    so_what(f"Feedstock is {bio / cost_t:.0%} of cost. Every ₹0.10/kg on biomass price moves cost by about "
            f"₹{bio * 0.1 / p['biomass_price_inr_per_kg']:,.0f}/t. Tonnes per kg of residue (yield, CH₄, pass rate) are the real cost lever.")
with r:
    st.subheader("By bucket")
    tbl = cs[["bucket", "category", "type", "inr", "inr_per_net_t"]].sort_values("inr", ascending=False)
    st.dataframe(tbl, hide_index=True, width="stretch", height=360,
                 column_config={"inr": st.column_config.NumberColumn("₹ / year", format="₹%,.0f"),
                                "inr_per_net_t": st.column_config.NumberColumn("₹ / net t", format="₹%,.0f")})
    so_what("Variable costs scale with batches. Fixed costs (kilns, dMRV, staff) fall per tonne as throughput rises.")

# ------------------------------------------------------------------ margin
l, r = st.columns(2)
with l:
    st.subheader("Margin vs credit price")
    prices = np.linspace(P["credit_price_usd"].low * 0.8, P["credit_price_usd"].high * 1.1, 60)
    var_t = cs.loc[cs.type == "variable", "inr_per_net_t"].sum()
    fig = go.Figure()
    fig.add_scatter(x=prices, y=prices * p["inr_per_usd"] - var_t, name="Contribution margin / t", line=dict(color=ACCENT_LIGHT, width=2))
    fig.add_scatter(x=prices, y=prices * p["inr_per_usd"] - cost_t, name="Full margin / t", line=dict(color=ACCENT, width=3))
    fig.add_hline(y=0, line_color=GREY)
    fig.add_vline(x=be, line_dash="dot", line_color=GREY, annotation_text=f"breakeven ${be:.0f}")
    for _, row in margins.iterrows():
        fig.add_vline(x=row.price_usd, line_color="#E5E7EB")
    fig.update_layout(height=320, xaxis_title="Credit price (USD/t)", yaxis_title="₹ per net t")
    st.plotly_chart(fig, width="stretch")
    so_what(f"At ${P['credit_price_usd'].low:.0f} the network loses money on every tonne, and at ${P['credit_price_usd'].high:.0f} it earns "
            f"₹{margins.loc[2, 'full_margin_inr_per_t']:,.0f}/t. Price risk is as large as delivery risk.")
with r:
    st.subheader("Cash timeline")
    fig = go.Figure()
    fig.add_bar(x=cash_df.month, y=-cash_df.spend_inr / 1e7, name="Spend (₹ cr)", marker_color=GREY_LIGHT)
    fig.add_bar(x=cash_df.month, y=cash_df.revenue_inr / 1e7, name="Credit revenue (₹ cr)", marker_color=ACCENT_LIGHT)
    fig.add_scatter(x=cash_df.month, y=cash_df.cum_cash_inr / 1e7, name="Cumulative cash (₹ cr)", line=dict(color=ACCENT, width=3))
    fig.update_layout(height=320, barmode="relative", yaxis_title="₹ crore")
    st.plotly_chart(fig, width="stretch")
    so_what(f"Cash troughs at {fmt_inr(wc)} in {trough}. Issuance lag ({p['production_to_issuance_months']:.0f} months) plus collection "
            f"({p['issuance_to_cash_months']:.0f} month) means feedstock is paid for about a quarter before credits are.")

# ------------------------------------------------------------------ archetypes & calibration
l, r = st.columns([1.3, 1])
with l:
    st.subheader("₹ per net t by site archetype (synthetic actuals)")
    T = load_tables()
    ae = economics.archetype_economics(T["batches"], T["biomass_deliveries"], T["sites"], params_for("plan_implied"))
    fig = px.bar(ae, x="archetype", y="inr_per_net_t", color="category",
                 color_discrete_sequence=[ACCENT, "#5EAAA0", ACCENT_LIGHT, "#374151", GREY, GREY_LIGHT, "#E5E7EB"])
    fig.update_layout(height=340, yaxis_title="₹ per net t", xaxis_title="", legend_title_text="")
    st.plotly_chart(fig, width="stretch")
    tot = ae.groupby("archetype").inr_per_net_t.sum().sort_values()
    so_what(f"{tot.index[-1]} sites cost ₹{tot.iloc[-1] - tot.iloc[0]:,.0f}/t more than {tot.index[0].lower()} sites. "
            "The residue is paid for but the credit is lost at rejection, so cost per tonne follows acceptance.")
with r:
    st.subheader("Calibration check")
    direct = economics.direct_cost_per_kg_biochar(p)
    st.markdown(f"""
| | ₹ per kg biochar |
|---|---:|
| Field labour + supervision (this model) | **₹{direct:,.1f}** |
| Partner fee, public Banni anchor | ₹{p['partner_fee_inr_per_kg_biochar']:.0f} |
| Biomass at ₹{p['biomass_price_inr_per_kg']:.1f}/kg raw | ₹{p['biomass_price_inr_per_kg'] / (1 - p['biomass_moisture_frac']) / p['biochar_yield_dry_frac']:,.1f} |
""")
    so_what("The public ~₹10/kg partner fee is several times the model's direct field cost, so it presumably bundles supervision, logistics, "
            "application and margin. Ask for the breakdown before benchmarking contracts.")

# ------------------------------------------------------------------ pathway benchmark
st.subheader("Pathway benchmark (adjustable weights)")
st.caption("Scores 1–5, higher is better for a developer. Qualitative and ASSUMPTION – VERIFY except where marked. Context: public offtakes "
           "include Google (100k t industrial biochar by 2030), Microsoft (>100k t over 3 years from 18 industrial reactors) and "
           "GSK (>500k regen-ag credits, ~100k t/yr 2028–2033).")
crit = economics.CRITERIA
wcols = st.columns(len(crit))
weights = {}
for col, (key, label) in zip(wcols, crit.items()):
    weights[key] = col.slider(label, 0.0, 1.0, float(P[f"pw_weight_{key}"].default), 0.05, key=f"w_{key}")
pm = economics.pathway_matrix(weights)
l, r = st.columns([1.6, 1])
with l:
    show = pm.drop(columns=["delivery_risk_drivers", "scalability_constraint"])
    st.dataframe(show, hide_index=True, width="stretch",
                 column_config={"weighted_score": st.column_config.ProgressColumn("Weighted score", min_value=1, max_value=5, format="%.2f")})
    st.dataframe(pm[["pathway", "delivery_risk_drivers", "scalability_constraint"]], hide_index=True, width="stretch")
with r:
    fig = go.Figure(go.Bar(y=pm.pathway[::-1], x=pm.weighted_score[::-1], orientation="h",
                           marker_color=[ACCENT if x == "Distributed biochar" else GREY_LIGHT for x in pm.pathway[::-1]]))
    fig.update_layout(height=260, xaxis_range=[1, 5], xaxis_title="Weighted score")
    st.plotly_chart(fig, width="stretch")
    model_usd = cost_t / p["inr_per_usd"]
    so_what(f"Distributed biochar wins on time to cash and co-benefits and loses on MRV complexity. This model's ${model_usd:,.0f}/t "
            f"sits at the top of the assumed $50–120 range, so its cost advantage depends on hitting throughput.")
footer()

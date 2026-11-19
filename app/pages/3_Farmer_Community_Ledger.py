"""Farmer & Community Ledger: the integrity layer.

Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import (ACCENT, ACCENT_LIGHT, GREY, RAG_COLOR, fmt_inr, fmt_pct, fmt_t, footer, load_tables, page_setup,
                    params_for, so_what)
from model import kpis

page_setup("Farmer & Community Ledger")
st.title("Farmer and community ledger")
st.markdown("Buyers, ratings agencies and methodology eligibility all depend on residue suppliers being paid on time and "
            "biochar coming back to their fields. This page treats that as a **delivery system and a commercial moat**, "
            "not a compliance afterthought.")

T = load_tables()
p = params_for("plan_implied")
sla = p["payment_sla_days"]
d, v, rt, b, s = T["biomass_deliveries"], T["villages"], T["biochar_returns"], T["batches"], T["sites"]

supplying = v[v.village_id.isin(d.village_id.unique())]
c = st.columns(6)
c[0].metric("Villages supplying", f"{len(supplying):,}")
c[1].metric("Farmers in supplying villages", f"{supplying.farmer_count.sum():,}")
c[2].metric("Paid to village committees", fmt_inr(d.amount_inr.sum()))
c[3].metric(f"Paid within {sla:.0f}-day SLA", fmt_pct(kpis.village_payment_sla(d, sla), 1))
c[4].metric("Median payment lag", f"{kpis.median_payment_lag(d):.0f} days")
c[5].metric("Biochar returned", fmt_t(rt.kg.sum() / 1000), f"{kpis.biochar_return_completion(rt, b):.0%} of produced", delta_color="off")
so_what("Network averages look healthy. The site view below shows where they hide a problem.")

# ------------------------------------------------------------------ SLA by site (discovery)
st.subheader("Payment SLA by site")
by_site = pd.DataFrame({"sla": kpis.village_payment_sla(d, sla, by="site_id"), "lag": kpis.median_payment_lag(d, by="site_id")}).reset_index()
by_site["status"] = by_site.sla.apply(lambda x: kpis.rag(x, p["kpi_payment_sla_green"], p["kpi_payment_sla_amber"]))
by_site = by_site.sort_values("sla")
fig = go.Figure(go.Bar(x=by_site.site_id, y=by_site.sla, marker_color=[RAG_COLOR[x] for x in by_site.status],
                       hovertemplate="%{x}: %{y:.0%} paid within SLA<extra></extra>"))
fig.add_hline(y=p["kpi_payment_sla_green"], line_dash="dot", line_color=GREY, annotation_text="target")
fig.update_layout(height=260, yaxis_tickformat=".0%", yaxis_range=[0, 1.02], yaxis_title=f"Deliveries paid ≤ {sla:.0f} days")
st.plotly_chart(fig, width="stretch")
worst = by_site.iloc[0]
so_what(f"{worst.site_id} is the outlier: {worst.sla:.0%} of deliveries paid within SLA against about "
        f"{by_site.sla.median():.0%} elsewhere. Select it below to see what happened to its supply.")

# ------------------------------------------------------------------ causal view
site = st.selectbox("Site drill-down", by_site.site_id.tolist(), index=0,
                    format_func=lambda x: f"{x} · {s.set_index('site_id').district[x]} · {s.set_index('site_id').archetype[x]}")
wk = lambda df: df.date.dt.to_period("W").dt.start_time
dd = d.assign(week=wk(d))
site_w = dd[dd.site_id == site].groupby("week").agg(dry_t=("dry_t", "sum"), lag=("payment_lag_days", "mean"))
peers = dd[dd.site_id != site].groupby(["week", "site_id"]).dry_t.sum().groupby("week").mean()
ser = site_w.join(peers.rename("peer_dry_t"), how="right").fillna({"dry_t": 0})
ser["supply_ratio"] = ser.dry_t / ser.peer_dry_t
ser = ser[(ser.index >= "2027-01-04") & (ser.peer_dry_t > ser.peer_dry_t.quantile(0.2))]

# Onset analysis: first week payments breach 2× SLA, then first week supply falls below 75% of its pre-breach level.
lag_on = ser.index[(ser.lag > 2 * sla).fillna(False)]
onset_pay = lag_on[0] if len(lag_on) else None
onset_sup, gap_wk = None, None
if onset_pay is not None:
    baseline = ser.loc[ser.index < onset_pay, "supply_ratio"].mean()
    roll = ser.supply_ratio.rolling(3, min_periods=2).mean()
    drop = roll[(roll.index > onset_pay) & (roll < 0.75 * baseline)]
    if len(drop):
        onset_sup = drop.index[0] - pd.Timedelta(weeks=1)  # rolling window centre ≈ one week earlier
        gap_wk = (onset_sup - onset_pay).days / 7

l, r = st.columns([1.6, 1])
with l:
    st.subheader("Late payments → supply decline, with a lag")
    fig = go.Figure()
    fig.add_bar(x=ser.index, y=ser.supply_ratio, name="Supply vs average peer site (×)", marker_color=ACCENT_LIGHT)
    fig.add_scatter(x=ser.index, y=ser.lag, name="Mean payment lag (days)", yaxis="y2", line=dict(color="#B91C1C", width=2.5),
                    connectgaps=False)
    fig.add_hline(y=sla, line_dash="dot", line_color="#B91C1C", yref="y2", annotation_text="SLA", annotation_position="right")
    if onset_pay is not None:
        fig.add_vline(x=onset_pay, line_color="#B91C1C", line_dash="dash")
        fig.add_annotation(x=onset_pay, y=1.02, yref="paper", text="payments break SLA", showarrow=False, font=dict(color="#B91C1C", size=11))
    if onset_sup is not None:
        fig.add_vline(x=onset_sup, line_color=ACCENT, line_dash="dash")
        fig.add_annotation(x=onset_sup, y=0.94, yref="paper", text="supply drops", showarrow=False, font=dict(color=ACCENT, size=11))
    fig.update_layout(height=340, yaxis=dict(title="Supply ratio", rangemode="tozero"),
                      yaxis2=dict(title="Payment lag (days)", overlaying="y", side="right", showgrid=False, rangemode="tozero"))
    st.plotly_chart(fig, width="stretch")
with r:
    st.subheader("Onset gap")
    if gap_wk is not None:
        st.metric("Weeks from payment breach to supply drop", f"{gap_wk:.0f}")
        st.metric("Supply before vs after breach",
                  f"{ser.loc[ser.index < onset_pay, 'supply_ratio'].mean():.2f}× → "
                  f"{ser.loc[(ser.index >= onset_sup) & (ser.index < onset_sup + pd.Timedelta(weeks=8)), 'supply_ratio'].mean():.2f}×")
        st.caption("Supply is measured relative to the average peer site in the same week, which removes seasonality. "
                   "A drop means at least 25% below the pre-breach level on a 3-week rolling basis.")
    else:
        st.metric("Weeks from payment breach to supply drop", "–")
        st.caption("No sustained payment breach (lag above 2× SLA) at this site.")
if gap_wk is not None:
    so_what(f"At {site}, payments broke the SLA in the week of {onset_pay:%d %b} and supply fell about {gap_wk:.0f} weeks later. "
            "Villages respond to how they were paid a month earlier, so a payment backlog is a stockout warning 4–6 weeks out.")
else:
    so_what("Sites paying on time show no breach and no matching supply drop. Compare with the worst-SLA site to see the pattern.")

# ------------------------------------------------------------------ village ledger
st.subheader(f"Village ledger · {site}")
ds = d[d.site_id == site]
rs = rt[rt.site_id == site]
led = ds.groupby("village_id").agg(deliveries=("delivery_id", "size"), biomass_t=("kg", lambda x: x.sum() / 1000),
                                   paid_inr=("amount_inr", "sum"), median_lag=("payment_lag_days", "median"),
                                   within_sla=("payment_lag_days", lambda x: (x <= sla).mean()))
led = led.join(rs.groupby("village_id").agg(biochar_returned_kg=("kg", "sum"), produced_kg=("produced_kg_period", "sum")))
led["return_completion"] = led.biochar_returned_kg / led.produced_kg
led = led.join(v.set_index("village_id")[["farmer_count", "residue_type"]]).reset_index()
st.dataframe(led.sort_values("within_sla"), hide_index=True, width="stretch", height=300,
             column_config={"biomass_t": st.column_config.NumberColumn("Biomass (t, as received)", format="%,.0f"),
                            "paid_inr": st.column_config.NumberColumn("₹ paid", format="₹%,.0f"),
                            "median_lag": st.column_config.NumberColumn("Median lag (d)", format="%.0f"),
                            "within_sla": st.column_config.NumberColumn("Paid ≤ SLA", format="percent"),
                            "biochar_returned_kg": st.column_config.NumberColumn("Biochar returned (kg)", format="%,.0f"),
                            "return_completion": st.column_config.NumberColumn("Return completion", format="percent"),
                            "produced_kg": None})
so_what("This is the ledger a village committee or an auditor would ask for: what each village supplied, what it was paid and when, "
        "and what came back. Publishing it per site is the benefit-sharing disclosure.")

l, r = st.columns(2)
with l:
    st.subheader("Payment lag distribution")
    fig = go.Figure()
    fig.add_histogram(x=d[d.site_id != site].payment_lag_days, name="Other sites", histnorm="percent", marker_color="#D1D5DB", xbins=dict(size=2))
    fig.add_histogram(x=ds.payment_lag_days, name=site, histnorm="percent", marker_color=ACCENT, opacity=0.8, xbins=dict(size=2))
    fig.add_vline(x=sla, line_dash="dot", line_color="#B91C1C", annotation_text="SLA")
    fig.update_layout(barmode="overlay", height=300, xaxis_title="Days from delivery to payment", yaxis_title="% of deliveries")
    st.plotly_chart(fig, width="stretch")
    so_what("The long right tail is the backlog. Track the 90th percentile weekly, not the average.")
with r:
    st.subheader("SLA breach list")
    br = ds[ds.payment_lag_days > sla].assign(days_late=lambda x: x.payment_lag_days - sla)
    br = br.sort_values("days_late", ascending=False).head(50)
    st.dataframe(br[["village_id", "date", "kg", "amount_inr", "payment_due_date", "payment_date", "days_late"]],
                 hide_index=True, width="stretch", height=300,
                 column_config={"kg": st.column_config.NumberColumn("kg", format="%,.0f"),
                                "amount_inr": st.column_config.NumberColumn("₹", format="₹%,.0f"),
                                "date": st.column_config.DateColumn("Delivered"),
                                "payment_due_date": st.column_config.DateColumn("Due"),
                                "payment_date": st.column_config.DateColumn("Paid")})
    so_what(f"{len(ds[ds.payment_lag_days > sla]):,} breaches at {site}. Every breach over 14 days late should reach the finance lead in the "
            "weekly review, with a date the village will be paid.")
footer()

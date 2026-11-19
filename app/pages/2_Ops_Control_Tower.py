"""Ops Control Tower: site, kiln and operator KPIs with RAG.

Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import (ACCENT, ACCENT_LIGHT, GREY, RAG_COLOR, RAG_ICON, fmt_pct, fmt_t, footer, load_tables, page_setup,
                    params_for, so_what)
from model import kpis

page_setup("Ops Control Tower")
st.title("Ops control tower")
st.caption("Synthetic 2027 operating year. Filter by archetype, site and week. RAG thresholds are in assumptions.yaml (kpi_thresholds).")

T = load_tables()
p = params_for("plan_implied")
sites = T["sites"]

f = st.columns([1.2, 2, 1.6])
arch = f[0].multiselect("Archetype", sorted(sites.archetype.unique()), default=sorted(sites.archetype.unique()))
site_opts = sites[sites.archetype.isin(arch)].site_id.tolist()
sel = f[1].multiselect("Sites", site_opts, default=site_opts, format_func=lambda s: f"{s} · {sites.set_index('site_id').district[s]}")
wk = f[2].slider("Weeks of 2027", 1, 52, (1, 52))
start = pd.Timestamp("2027-01-01") + pd.Timedelta(days=7 * (wk[0] - 1))
end = min(pd.Timestamp("2027-01-01") + pd.Timedelta(days=7 * wk[1] - 1), pd.Timestamp("2027-12-31"))
if not sel:
    st.warning("Select at least one site.")
    st.stop()

b = T["batches"][(T["batches"].site_id.isin(sel)) & (T["batches"].date.between(start, end))]
k = T["kilns"][T["kilns"].site_id.isin(sel)]
sub = {**T, "batches": T["batches"][T["batches"].site_id.isin(sel)], "kilns": k,
       "sites": sites[sites.site_id.isin(sel)],
       "biomass_deliveries": T["biomass_deliveries"][T["biomass_deliveries"].site_id.isin(sel)],
       "biochar_returns": T["biochar_returns"][T["biochar_returns"].site_id.isin(sel)]}
if b.empty:
    st.info("No batches in this window (monsoon weeks or sites not yet launched).")
    st.stop()

sc = kpis.site_scorecard(sub, p, start=str(start.date()), end=str(end.date()))
cover_alerts = (sc.days_of_cover < p["kpi_cover_amber"]).sum()
c = st.columns(6)
c[0].metric("Net tCO₂e", fmt_t(b.net_tco2e.sum()))
c[1].metric("Batch acceptance", fmt_pct(kpis.batch_acceptance_pct(b), 1))
c[2].metric("Evidence complete (1st pass)", fmt_pct(kpis.evidence_completeness_pct(b), 1))
c[3].metric("Batches / running kiln-day", f"{kpis.batches_per_kiln_day(b):.2f}", f"plan {p['batches_per_kiln_day']:.1f}", delta_color="off")
c[4].metric("Kiln utilisation", fmt_pct(kpis.kiln_utilisation(b, k, start, end, p), 0))
c[5].metric("Sites below cover threshold", f"{cover_alerts}", f"< {p['kpi_cover_amber']:.0f} days", delta_color="off")

# ------------------------------------------------------------------ site RAG table + map
st.subheader("Site scorecard")
l, r = st.columns([1.7, 1])
with l:
    tbl = sc.copy()
    for col, rcol in (("utilisation", "rag_utilisation"), ("acceptance", "rag_acceptance"), ("evidence_completeness", "rag_evidence"),
                      ("days_of_cover", "rag_cover"), ("payment_sla", "rag_payment"), ("return_completion", "rag_return")):
        fmt = (lambda v: f"{v:.1f}") if col == "days_of_cover" else (lambda v: f"{v:.0%}")
        tbl[col] = [f"{RAG_ICON[rg]} {fmt(v) if pd.notna(v) else '–'}" for v, rg in zip(tbl[col], tbl[rcol])]
    tbl["overall"] = tbl.overall.map(lambda s: f"{RAG_ICON[s]} {s}")
    tbl = tbl.sort_values("net_t_per_kiln_week")
    st.dataframe(tbl[["overall", "site_id", "district", "archetype", "net_t", "net_t_per_kiln_week", "utilisation",
                      "batches_per_kiln_day", "evidence_completeness", "acceptance", "days_of_cover", "payment_sla", "return_completion"]],
                 hide_index=True, width="stretch", height=380,
                 column_config={"overall": "RAG", "site_id": "Site", "net_t": st.column_config.NumberColumn("Net t", format="%,.0f"),
                                "net_t_per_kiln_week": st.column_config.NumberColumn("Net t / kiln-wk", format="%.2f"),
                                "batches_per_kiln_day": st.column_config.NumberColumn("Batches / kiln-day", format="%.2f"),
                                "utilisation": "Utilisation", "evidence_completeness": "Evidence", "acceptance": "Acceptance",
                                "days_of_cover": "Cover (days)", "payment_sla": "Paid ≤ SLA", "return_completion": "Biochar returned"})
    worst = sc.sort_values("net_t_per_kiln_week").head(3)
    so_what(f"Lowest productivity: {', '.join(worst.site_id + ' (' + worst.archetype + ')')}. Red on cover means feedstock; "
            "red on evidence means MRV training; red on paid ≤ SLA means escalate to finance today.")
with r:
    geo = sites[sites.site_id.isin(sel)].merge(sc[["site_id", "overall", "net_t"]], on="site_id")
    fig = px.scatter_geo(geo, lat="lat", lon="lon", color="overall", size="net_t", hover_name="site_id",
                         hover_data={"district": True, "archetype": True, "net_t": ":,.0f", "lat": False, "lon": False},
                         color_discrete_map=RAG_COLOR, size_max=18)
    fig.update_geos(fitbounds="locations", showcountries=True, countrycolor="#9CA3AF", showland=True, landcolor="#F9FAFB",
                    showsubunits=True, subunitcolor="#E5E7EB", resolution=50)
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
    st.plotly_chart(fig, width="stretch")
    so_what("Red sites cluster by archetype, not by geography, so the fixes are operational rather than regional.")

# ------------------------------------------------------------------ weekly trend + Pareto
l, r = st.columns(2)
with l:
    st.subheader("Weekly acceptance vs share of batches by new operators")
    w = b.assign(week=b.date.dt.to_period("W").dt.start_time, new=b.lead_tenure_days <= 14)
    wg = w.groupby("week").agg(acceptance=("accepted", "mean"), new_share=("new", "mean"), n=("batch_id", "size")).reset_index()
    wg = wg[wg.n >= 30]
    fig = go.Figure()
    fig.add_bar(x=wg.week, y=wg.new_share, name="Batches by operators ≤14 days in role", marker_color=ACCENT_LIGHT, yaxis="y2")
    fig.add_scatter(x=wg.week, y=wg.acceptance, name="Acceptance", line=dict(color=ACCENT, width=2.5))
    fig.update_layout(height=330, yaxis=dict(tickformat=".0%", title="Acceptance", range=[0.6, 1]),
                      yaxis2=dict(tickformat=".0%", overlaying="y", side="right", range=[0, 0.8], showgrid=False, title="New-operator share"))
    st.plotly_chart(fig, width="stretch")
    new_acc = b[b.lead_tenure_days <= 14].accepted.mean()
    mat_acc = b[b.lead_tenure_days > 60].accepted.mean()
    so_what(f"Acceptance dips when new operators join: {new_acc:.0%} in their first two weeks vs {mat_acc:.0%} for experienced "
            "operators. Pair every new lead operator with a buddy for 14 days.")
with r:
    st.subheader("Batch rejections by reason (Pareto)")
    rej = b[~b.accepted].rejection_reason.astype(str).value_counts()
    rej = rej[rej.index != ""]
    cum = rej.cumsum() / rej.sum()
    fig = go.Figure()
    fig.add_bar(x=rej.index, y=rej.values, marker_color=ACCENT, name="Rejected batches")
    fig.add_scatter(x=rej.index, y=cum.values, yaxis="y2", name="Cumulative %", line=dict(color=GREY))
    fig.update_layout(height=330, yaxis_title="Batches", yaxis2=dict(overlaying="y", side="right", tickformat=".0%", range=[0, 1.05], showgrid=False),
                      xaxis_tickangle=-30)
    st.plotly_chart(fig, width="stretch")
    top2 = cum.iloc[min(1, len(cum) - 1)] if len(cum) else 0
    so_what(f"The top two reasons ({', '.join(rej.index[:2].str.lower())}) cause {top2:.0%} of rejections. Both are fixable with "
            "hardware checks and a capture checklist, not a methodology change.")

# ------------------------------------------------------------------ operators
st.subheader("Operator league table vs learning curve")
ops = kpis.operator_productivity_vs_cohort(b, T["operators"])
ops = ops[ops.days >= 10]
l, r = st.columns([1, 1.3])
with l:
    cv = kpis.operator_learning_curve(b).reset_index()
    fig = go.Figure()
    fig.add_scatter(x=cv.tenure_wk, y=cv.curve_acc, name="Acceptance", line=dict(color=ACCENT, width=2.5))
    fig.add_scatter(x=cv.tenure_wk, y=cv.curve_bpd / cv.curve_bpd.max(), name="Batches/day (index)", line=dict(color=GREY, dash="dot"))
    fig.update_layout(height=300, xaxis_title="Weeks since lead operator started", yaxis_tickformat=".0%")
    st.plotly_chart(fig, width="stretch")
    so_what("Most of the learning happens in the first 3–4 weeks. That is how long new operators need close supervision.")
with r:
    league = ops.sort_values("acceptance_vs_curve")
    show = pd.concat([league.head(8), league.tail(4)])
    st.dataframe(show[["operator_id", "site_id", "cohort", "tenure_wk", "days", "bpd", "acceptance", "productivity_vs_curve", "acceptance_vs_curve"]],
                 hide_index=True, width="stretch", height=300,
                 column_config={"tenure_wk": "Tenure (wk)", "bpd": st.column_config.NumberColumn("Batches/day", format="%.2f"),
                                "acceptance": st.column_config.NumberColumn("Acceptance", format="percent"),
                                "productivity_vs_curve": st.column_config.NumberColumn("Prod. vs curve", format="%.2f×"),
                                "acceptance_vs_curve": st.column_config.NumberColumn("Accept. vs curve", format="%.2f×")})
    so_what(f"{(ops.acceptance_vs_curve < 0.85).sum()} operators sit below 0.85× of the curve on acceptance. They are the coaching list "
            "for the weekly site review. The bottom 8 and top 4 are shown.")

# ------------------------------------------------------------------ cover alerts + kiln table
l, r = st.columns(2)
with l:
    st.subheader(f"Biomass days of cover · as of {end:%d %b}")
    cov = kpis.biomass_days_of_cover(sub["biomass_deliveries"], sub["batches"], as_of=end).reset_index()
    cov["status"] = cov.days_of_cover.apply(lambda v: kpis.rag(v, p["kpi_cover_green"], p["kpi_cover_amber"]))
    cov = cov.sort_values("days_of_cover")
    fig = go.Figure(go.Bar(x=cov.site_id, y=cov.days_of_cover, marker_color=[RAG_COLOR[s] for s in cov.status]))
    fig.add_hline(y=p["kpi_cover_green"], line_dash="dot", line_color=GREY, annotation_text="green")
    fig.add_hline(y=p["kpi_cover_amber"], line_dash="dot", line_color="#B91C1C", annotation_text="stockout risk")
    fig.update_layout(height=300, yaxis_title="Days of feedstock on hand")
    st.plotly_chart(fig, width="stretch")
    so_what("Sites under the red line stop burning within days. Pull deliveries forward from neighbouring catchments or plan the next relocation now.")
with r:
    st.subheader("Kilns needing attention")
    kk = b.groupby(["kiln_id", "site_id"]).agg(batches=("batch_id", "size"), acceptance=("accepted", "mean"),
                                               net_t=("net_tco2e", "sum"), dry_t=("dry_feedstock_t", "mean")).reset_index()
    kk["bpd"] = kk.kiln_id.map(kpis.batches_per_kiln_day(b, by="kiln_id"))
    kk["rag"] = kk.acceptance.apply(lambda v: RAG_ICON[kpis.rag(v, p["kpi_acceptance_green"], p["kpi_acceptance_amber"])])
    st.dataframe(kk.sort_values("acceptance").head(15)[["rag", "kiln_id", "site_id", "batches", "bpd", "dry_t", "acceptance", "net_t"]],
                 hide_index=True, width="stretch", height=300,
                 column_config={"rag": "", "bpd": st.column_config.NumberColumn("Batches/day", format="%.2f"),
                                "dry_t": st.column_config.NumberColumn("Dry t/batch", format="%.2f"),
                                "acceptance": st.column_config.NumberColumn("Acceptance", format="percent"),
                                "net_t": st.column_config.NumberColumn("Net t", format="%,.0f")})
    so_what("The 15 kilns with the lowest acceptance. Check their thermocouples and scales first, because hardware faults repeat batch after batch.")
footer()

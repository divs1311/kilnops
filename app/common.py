"""Shared app plumbing: paths, theme, cached model calls, formatting, captions, disclaimer.

Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from model import economics, kpis, tonnes
from model.assumptions import load_params, meta, scenario_params, scenarios

ACCENT = "#0F766E"
ACCENT_LIGHT = "#99D5CC"
GREY = "#6B7280"
GREY_LIGHT = "#D1D5DB"
INK = "#111827"
RAG_COLOR = {"Green": "#15803D", "Amber": "#D97706", "Red": "#B91C1C", "Grey": "#9CA3AF"}
RAG_ICON = {"Green": "🟢", "Amber": "🟠", "Red": "🔴", "Grey": "⚪"}
DISCLAIMER = meta()["disclaimer"]
TARGET = meta()["target_net_tco2e"]
TABLES = ("sites", "kilns", "kiln_status", "operators", "villages", "batches", "biomass_deliveries",
          "biochar_returns", "payouts")

pio.templates["kilnops"] = go.layout.Template(layout=go.Layout(
    font=dict(family="Inter, Segoe UI, Helvetica, Arial, sans-serif", size=12, color=INK),
    colorway=[ACCENT, GREY, ACCENT_LIGHT, "#374151", GREY_LIGHT],
    plot_bgcolor="white", paper_bgcolor="white",
    xaxis=dict(showgrid=False, linecolor=GREY_LIGHT, ticks="outside", tickcolor=GREY_LIGHT),
    yaxis=dict(gridcolor="#F0F1F3", zeroline=False, linecolor=GREY_LIGHT),
    margin=dict(l=10, r=10, t=40, b=10), hoverlabel=dict(bgcolor="white"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
))
pio.templates.default = "kilnops"

CSS = """
<style>
.block-container {padding-top: 2.2rem; max-width: 1280px;}
[data-testid="stMetricValue"] {font-size: 1.55rem; color: #111827;}
[data-testid="stMetricLabel"] p {font-size: 0.8rem; color: #4B5563;}
.ko-disclaimer {font-size: 0.75rem; color: #6B7280; border-top: 1px solid #E5E7EB; padding-top: .5rem; margin-top: 1.5rem;}
.ko-banner {background:#F0FDFA; border-left: 4px solid #0F766E; padding:.6rem .9rem; font-size:.85rem; color:#134E4A; margin-bottom:.8rem;}
.ko-sowhat {font-size: .82rem; color:#374151; margin-top:-.4rem; margin-bottom: 1rem;}
.ko-sowhat b {color:#0F766E;}
.ko-chip {display:inline-block; padding:1px 8px; border-radius:10px; font-size:.75rem; color:white; font-weight:600;}
h1 {font-size: 1.7rem !important;} h2 {font-size: 1.25rem !important;} h3 {font-size: 1.05rem !important;}
</style>
"""


def page_setup(title: str, icon: str = "🔥") -> None:
    st.set_page_config(page_title=f"KilnOps · {title}", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f'<div class="ko-banner">{DISCLAIMER} Modelled on a 450-kiln distributed network like the '
                f'publicly announced Agnisparsh project. All operational data is synthetic.</div>', unsafe_allow_html=True)


def footer() -> None:
    st.markdown(f'<div class="ko-disclaimer">{DISCLAIMER} Every number traces to <code>assumptions.yaml</code>; '
                f'see the Assumptions &amp; Method page.</div>', unsafe_allow_html=True)


def so_what(text: str) -> None:
    """One-line decision caption under every chart and table."""
    st.markdown(f'<div class="ko-sowhat"><b>So what:</b> {text}</div>', unsafe_allow_html=True)


def chip(status: str) -> str:
    return f'<span class="ko-chip" style="background:{RAG_COLOR.get(status, GREY)}">{status}</span>'


# --------------------------------------------------------------------------- formatting
def fmt_t(x: float, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    if abs(x) >= 1000:
        return f"{x / 1000:,.{digits}f}k t"
    return f"{x:,.0f} t"


def fmt_inr(x: float, digits: int = 1) -> str:
    """Indian units: ₹ crore (1e7) / lakh (1e5)."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e7:
        return f"{sign}₹{x / 1e7:,.{digits}f} cr"
    if x >= 1e5:
        return f"{sign}₹{x / 1e5:,.{digits}f} lakh"
    return f"{sign}₹{x:,.0f}"


def fmt_pct(x: float, digits: int = 0) -> str:
    return "–" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{digits}%}"


# --------------------------------------------------------------------------- cached data & model calls
@st.cache_data(show_spinner=False)
def load_tables() -> dict[str, pd.DataFrame]:
    return {n: pd.read_parquet(ROOT / "data" / f"{n}.parquet") for n in TABLES}


@st.cache_data(show_spinner=False)
def scenario_list() -> dict[str, dict]:
    return scenarios()


@st.cache_data(show_spinner=False)
def params_for(scenario: str) -> dict:
    return scenario_params(scenario)


@st.cache_data(show_spinner=False)
def mc(scenario: str) -> dict:
    return tonnes.monte_carlo(scenario)


@st.cache_data(show_spinner=False)
def scenario_table() -> pd.DataFrame:
    df = tonnes.scenario_summary()
    rows = [mc(s) for s in df.scenario]
    df["p10"], df["p50"], df["p90"] = [r["p10"] for r in rows], [r["p50"] for r in rows], [r["p90"] for r in rows]
    df["prob_hit"] = [r["prob_hit"] for r in rows]
    return df


@st.cache_data(show_spinner=False)
def tornado(scenario: str) -> pd.DataFrame:
    df = tonnes.tornado(scenario)
    df.attrs = {}
    return df


@st.cache_data(show_spinner=False)
def drift(scenario: str) -> pd.DataFrame:
    df = tonnes.p50_drift_decomposition(scenario)
    df.attrs = {}
    return df


@st.cache_data(show_spinner=False)
def levers(scenario: str = "plan_implied") -> pd.DataFrame:
    df = tonnes.lever_simulator(scenario_params(scenario), reference_net=mc(scenario)["p50"])
    df.attrs = {}
    return df


@st.cache_data(show_spinner=False)
def scorecard(start: str = "2027-01-01", end: str = "2027-12-31") -> pd.DataFrame:
    return kpis.site_scorecard(load_tables(), start=start, end=end)


@st.cache_data(show_spinner=False)
def risks() -> pd.DataFrame:
    return kpis.risk_register(load_tables())


@st.cache_data(show_spinner=False)
def cost_stack(scenario: str) -> pd.DataFrame:
    df = economics.cost_buckets(scenario_params(scenario))
    df.attrs = {}
    return df


@st.cache_data(show_spinner=False)
def cash(scenario: str) -> tuple[pd.DataFrame, float, str]:
    df = economics.cash_timeline(scenario_params(scenario))
    wc, trough = df.attrs["working_capital_need_inr"], df.attrs["trough_month"]
    df.attrs = {}
    return df, wc, trough


@st.cache_data(show_spinner=False)
def delivery_vs_plan() -> pd.DataFrame:
    return kpis.cumulative_delivery_vs_plan(load_tables()["batches"])


@st.cache_data(show_spinner=False)
def param_table() -> pd.DataFrame:
    return pd.DataFrame([vars(p) for p in load_params().values()])

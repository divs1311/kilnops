"""Assumptions & Method.

Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from common import DISCLAIMER, footer, page_setup, param_table, scenario_list
from model.assumptions import meta

page_setup("Assumptions & Method")
st.title("Assumptions and method")

pt = param_table()
BADGE = {"PUBLIC": "🟢 PUBLIC", "LITERATURE": "🔵 LITERATURE", "ASSUMPTION – VERIFY": "🟠 ASSUMPTION – VERIFY"}
counts = pt.status.value_counts()
c = st.columns(4)
c[0].metric("Parameters", f"{len(pt)}")
for col, s in zip(c[1:], BADGE):
    col.metric(BADGE[s], f"{counts.get(s, 0)}")
st.markdown("Every number in the app, memo and SOP comes from **`assumptions.yaml`**. Each entry has a default, a plausible "
            "low/high range, a unit, a source and a status. Nothing is hard-coded elsewhere.")

f = st.columns([1, 1, 2])
groups = f[0].multiselect("Group", sorted(pt.group.unique()), default=[g for g in ["network", "kiln_physics", "carbon_accounting", "dmrv", "economics"] if g in pt.group.unique()])
status = f[1].multiselect("Status", list(BADGE), default=list(BADGE))
q = f[2].text_input("Search name / source / note")
view = pt[pt.group.isin(groups) & pt.status.isin(status)]
if q:
    m = view.name.str.contains(q, case=False) | view.source.str.contains(q, case=False) | view.note.str.contains(q, case=False)
    view = view[m]
view = view.assign(status=view.status.map(BADGE), lever=view.lever.map({True: "⚙️", False: ""}))
st.dataframe(view[["lever", "name", "group", "default", "low", "high", "unit", "status", "source", "note"]], hide_index=True,
             width="stretch", height=420,
             column_config={"lever": st.column_config.TextColumn("", width="small"),
                            "note": st.column_config.TextColumn(width="large"), "source": st.column_config.TextColumn(width="medium")})
st.caption("⚙️ = solver lever. 🟠 parameters are the first things to replace with real data.")

st.subheader("Scenarios")
for key, spec in scenario_list().items():
    ov = ", ".join(f"`{k}`={v}" for k, v in (spec.get("overrides") or {}).items()) or "none (all defaults)"
    st.markdown(f"**{spec['label']}**: {spec['description']}  \nOverrides: {ov}")

st.subheader("Method")
st.markdown(rf"""
**Tonne bridge (monthly).** kilns online (linear ramp) × (operating days − relocation downtime) × feedstock availability
× batches per kiln-day × dry t per batch × yield → biochar t. Gross = biochar × C<sub>org</sub> × 44/12 × persistence.
Then subtract dMRV rejections (1 − pass rate), project emissions on credited biochar (CH₄ × GWP₁₀₀ + other) and the buffer.

**dMRV pass rate.** P(all six evidence elements) → plus the remediated share of incomplete batches → × (1 − quality rejection)
× (1 − audit rejection). Elements are assumed independent.

**“What has to be true” solver.** Net tonnes are affine in each lever, so the required value is solved in closed form
(x\* = x₀ + (T − net(x₀)) ÷ slope). The tests check every lever hits 100k within 0.5%. Two stacks are reported: the fewest-lever
path, and the uniform stretch of every operational lever toward its good bound.

**Monte Carlo.** {int(meta()["mc_runs"]):,} independent triangular draws per scenario (low, mode = scenario value, high from `assumptions.yaml`, or
the scenario's own `mc_ranges`). Outputs P10/P50/P90, P(≥100k) and cumulative bands. The drift chart shows why P50 sits
below the design point: most nominal values sit at the favourable end of their range. Inputs are drawn independently,
which likely **understates** the spread, because a bad monsoon hits supply, moisture and operating days together.

**Lever simulator.** Re-runs the bridge and the full cost model with each lever applied. ₹ per incremental tonne = Δcost ÷ Δnet,
including the variable cost of extra batches.

**Synthetic data.** `data/generate.py` is seeded. It builds 30 sites in 4 archetypes, operator attrition and learning curves,
monsoon collapse, a new-operator evidence spike and a site whose village payments run late. Supply there falls 4–6 weeks later
because villages react to lags on earlier deliveries.

**KPIs.** One function per KPI in `model/kpis.py`, each with its formula and decision use in the docstring.
""", unsafe_allow_html=True)

st.subheader("Limitations")
st.markdown("""
- **Synthetic operations data.** Patterns are designed to be realistic and discoverable. They are not observations.
- **Not public:** the network's kiln size, throughput and operating calendar. These dominate the tornado and are the first things to measure.
- **Methodology-dependent parameters** (persistence, CH₄ treatment, buffer, H/Corg threshold) are taken from literature ranges and not
  from the text of the methodology in use.
- **Independence in Monte Carlo** understates correlated downside (weather).
- **Economics** exclude financing cost, tax and corporate overhead outside the programme, and use a single average credit price.
- **The pathway benchmark** is qualitative, with weights the user can change. It is not a recommendation.
- **What the public 2027 figure counts** (issuances that may include late-2026 production, or 2027 vintage) is unknown.
""")
st.subheader("Disclaimer")
st.markdown(f"**{DISCLAIMER}** No logo, branding or insider data is used. The project is referred to as *a 450-kiln distributed "
            "network modelled on Agnisparsh*, using only publicly reported facts. District names are illustrative.")
footer()

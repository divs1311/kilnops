"""Phase 1 outputs: solver table, lever stacks, sensitivity, implied footprint, static charts.

Run:  python -m tools.phase1_report
Writes docs/phase1/*.csv, *.md, *.png and key_numbers.json (numbers quoted in PHASE1_FINDINGS.md).
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from model import tonnes as t
from model.assumptions import ROOT, defaults, load_params, meta

OUT = ROOT / "docs" / "phase1"
ACCENT, GREY, LIGHT, RED = "#0F766E", "#6B7280", "#E5E7EB", "#B91C1C"
DISCLAIMER = meta()["disclaimer"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": GREY, "axes.labelcolor": "#111827"})


def _footer(fig, so_what: str):
    fig.text(0.01, 0.015, DISCLAIMER, fontsize=6.5, color=GREY)
    fig.text(0.01, 0.955, so_what, fontsize=9.5, color="#111827", weight="bold")


def _fmt_val(v: float, unit: str) -> str:
    if unit in ("kilns", "days/yr"):
        return f"{v:,.0f}"
    if unit in ("share of batches", "fraction"):
        return f"{v:.0%}"
    return f"{v:,.2f}" if abs(v) < 100 else f"{v:,.0f}"


def chart_solver(st, path):
    """Position of default and required value relative to each lever's plausible range."""
    higher_is_better = {r.key: r.key != "ch4_ef_g_per_kg_biochar" for r in st.itertuples()}
    fig, ax = plt.subplots(figsize=(9, 4.6))
    labels = []
    clip = 3.2
    for i, r in enumerate(st.itertuples()):
        lo, hi = r.plausible_low, r.plausible_high
        pos = lambda v: ((v - lo) / (hi - lo)) if higher_is_better[r.key] else ((hi - v) / (hi - lo))
        d, q = pos(r.default), pos(r.required)
        y = len(st) - i
        ax.barh(y, 1, left=0, color=LIGHT, height=0.55)
        ax.plot([d, min(q, clip)], [y, y], color=GREY, lw=1, zorder=2)
        ax.scatter(d, y, color=GREY, s=36, zorder=3)
        ax.scatter(min(q, clip), y, color=RED if q > 1 else ACCENT, marker="D", s=46, zorder=4)
        if r.key == "ch4_ef_g_per_kg_biochar" and r.required < 0:
            txt = "needs < 0 g/kg (impossible)  ▶"
        else:
            txt = f"needs {_fmt_val(r.required, r.unit)}" + ("  ▶" if q > clip else "")
        ax.text(min(q, clip) + 0.06, y, txt, va="center", fontsize=8, color=RED if q > 1 else ACCENT)
        labels.append((y, f"{r.lever}\n(default {_fmt_val(r.default, r.unit)})"))
    ax.set_yticks([y for y, _ in labels], [l for _, l in labels], fontsize=8)
    ax.axvline(0, color=GREY, lw=0.6, ls=":")
    ax.axvline(1, color=GREY, lw=0.6, ls=":")
    ax.set_xlim(-0.35, clip + 1.1)
    ax.set_xticks([0, 1], ["bad end of\nplausible range", "good end of\nplausible range"], fontsize=8)
    ax.set_xlabel("● default    ◆ value required to deliver 100k t net with all other levers at default", fontsize=8)
    _footer(fig, "No single lever closes the gap inside its plausible range — the plan needs a stack of levers.")
    fig.subplots_adjust(left=0.27, right=0.98, top=0.9, bottom=0.17)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def chart_iso(p, path):
    """Iso-target curves: dry t/batch × batches/kiln-day that deliver 100k t, by CH4 EF."""
    target = meta()["target_net_tco2e"]
    params = load_params()
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.linspace(0.5, 4.5, 200)
    base_prod = p["dry_biomass_per_batch_t"] * p["batches_per_kiln_day"]
    styles = [(params["ch4_ef_g_per_kg_biochar"].low, "-", "CH4 5 g/kg (dry feedstock)"),
              (p["ch4_ef_g_per_kg_biochar"], "--", "CH4 15 g/kg (default)"),
              (params["ch4_ef_g_per_kg_biochar"].high, ":", "CH4 30 g/kg (std default)")]
    for ef, ls, lab in styles:
        net = t.annual_net({**p, "ch4_ef_g_per_kg_biochar": ef})
        k = base_prod * target / net
        ax.plot(x, k / x, color=ACCENT, ls=ls, lw=1.8, label=f"100k frontier, {lab}: {k:.1f} t dry/kiln-day")
    lo_d, hi_d = params["dry_biomass_per_batch_t"].low, params["dry_biomass_per_batch_t"].high
    lo_b, hi_b = params["batches_per_kiln_day"].low, params["batches_per_kiln_day"].high
    ax.add_patch(plt.Rectangle((lo_d, lo_b), hi_d - lo_d, hi_b - lo_b, color=LIGHT, zorder=0, label="Plausible range (assumptions.yaml)"))
    c1, c2 = t.cycle_ceiling_batches_per_day(p, 1), t.cycle_ceiling_batches_per_day(p, 2)
    ax.axhline(c1, color=GREY, lw=0.8, ls="-.")
    ax.text(4.45, c1 + 0.05, f"1-shift cycle ceiling ({c1:.1f})", ha="right", fontsize=7.5, color=GREY)
    ax.axhline(c2, color=GREY, lw=0.8, ls="-.")
    ax.text(4.45, c2 + 0.05, f"2-shift ceiling ({c2:.1f})", ha="right", fontsize=7.5, color=GREY)
    for vol in (params["kiln_volume_m3"].default, params["kiln_volume_m3"].high):
        dmax = vol * p["biochar_bulk_density_t_m3"] / p["biochar_yield_dry_frac"]
        ax.axvline(dmax, color=GREY, lw=0.8, ls=(0, (1, 2)))
        ax.text(dmax + 0.03, 0.62, f"{vol:g} m³ kiln full", rotation=90, fontsize=7.5, color=GREY, va="bottom")
    ax.scatter(p["dry_biomass_per_batch_t"], p["batches_per_kiln_day"], color=GREY, s=50, zorder=5)
    ax.annotate("default", (p["dry_biomass_per_batch_t"], p["batches_per_kiln_day"]), xytext=(6, -12),
                textcoords="offset points", fontsize=8, color=GREY)
    ax.set_xlim(0.5, 4.5)
    ax.set_ylim(0.6, 4.2)
    ax.set_xlabel("Dry biomass per batch (t)")
    ax.set_ylabel("Batches per kiln per operating day")
    ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False)
    _footer(fig, "100k t needs 4-5 t dry per kiln-day: more than one shift on a 2 m³ kiln. Dry feedstock moves the frontier.")
    fig.subplots_adjust(left=0.09, right=0.98, top=0.9, bottom=0.27)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def chart_stack(stack, stretch, path):
    target = meta()["target_net_tco2e"]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    prev = 0
    for i, r in enumerate(stack.itertuples()):
        if i == 0:
            ax.bar(i, r.net_tco2e, color=GREY)
            lab = f"{r.net_tco2e/1000:.0f}k"
        else:
            ax.bar(i, r.net_tco2e - prev, bottom=prev, color=ACCENT)
            lab = f"+{(r.net_tco2e-prev)/1000:.0f}k\n({r.fraction_of_range_used:.0%} of range)"
        ax.text(i, r.net_tco2e + 1500, lab, ha="center", fontsize=8)
        prev = r.net_tco2e
    ax.axhline(target, color=RED, lw=1, ls="--")
    ax.text(-0.4, target + 1500, "100k target", color=RED, fontsize=8, ha="left")
    ax.set_xticks(range(len(stack)), [s.replace(" ", "\n", 1) for s in stack["step"]], fontsize=8)
    ax.set_ylabel("Annual net tCO2e")
    ax.set_ylim(0, target * 1.25)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    _footer(fig, f"Fewest levers: bigger batches + more batches/day. Or every ops lever {stretch:.0%} of the way to its good bound.")
    fig.subplots_adjust(left=0.1, right=0.98, top=0.88, bottom=0.2)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def chart_oat(oat, path, n=12):
    d = oat.head(n).iloc[::-1]
    base = oat.attrs["base_net"]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for i, r in enumerate(d.itertuples()):
        lo, hi = sorted([r.net_at_low, r.net_at_high])
        ax.barh(i, hi - lo, left=lo, color=ACCENT if r.status != "ASSUMPTION – VERIFY" else "#F59E0B", height=0.6)
    ax.axvline(base, color=GREY, lw=1)
    ax.axvline(meta()["target_net_tco2e"], color=RED, lw=1, ls="--")
    ax.set_yticks(range(len(d)), d["parameter"], fontsize=8)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    ax.set_xlabel("Annual net tCO2e, input moved low → high (others at default)\nteal = public / literature   amber = analyst assumption (verify first)", fontsize=8)
    _footer(fig, "Kiln throughput, an unverified assumption, dominates. Carbon-accounting inputs form the next tier.")
    fig.subplots_adjust(left=0.33, right=0.98, top=0.9, bottom=0.19)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p = defaults()
    target = meta()["target_net_tco2e"]
    bridge = t.monthly_bridge(p)
    st = t.solver_table(p)
    stack = t.greedy_stack(p)
    stretch = t.uniform_stretch(p)
    oat = t.oat_sensitivity(p)
    imp = t.implied_requirements(p)
    req_dry = float(st.loc[st.key == "dry_biomass_per_batch_t", "required"].iloc[0])

    bridge.to_csv(OUT / "monthly_bridge_defaults.csv", index=False)
    st.to_csv(OUT / "solver_table.csv", index=False)
    stack.to_csv(OUT / "greedy_stack.csv", index=False)
    oat.to_csv(OUT / "sensitivity_oat.csv", index=False)

    md = ["| Lever | Default | Required for 100k t | Change | Plausible range | Verdict |", "|---|---:|---:|---:|---|---|"]
    for r in st.itertuples():
        req = "< 0 (impossible)" if r.required < 0 else _fmt_val(r.required, r.unit)
        chg = "n/a" if r.required < 0 else f"{r.change_pct:+.0f}%"
        md.append(f"| {r.lever} | {_fmt_val(r.default, r.unit)} | {req} | "
                  f"{chg} | {_fmt_val(r.plausible_low, r.unit)} – {_fmt_val(r.plausible_high, r.unit)} | {r.feasibility} |")
    (OUT / "solver_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    chart_solver(st, OUT / "solver_chart.png")
    chart_iso(p, OUT / "iso_target.png")
    chart_stack(stack, stretch, OUT / "lever_stack.png")
    chart_oat(oat, OUT / "sensitivity_oat.png")

    gross_char = t.gross_t_per_t_biochar(p)
    key = {
        "target": target,
        "base_net": bridge.net_tco2e.sum(),
        "base_share_of_target": bridge.net_tco2e.sum() / target,
        "gross_tco2e": bridge.gross_tco2e.sum(),
        "rejected_tco2e": bridge.rejected_tco2e.sum(),
        "project_emissions_tco2e": bridge.project_emissions_tco2e.sum(),
        "buffer_tco2e": bridge.buffer_tco2e.sum(),
        "h1_share_of_net": bridge.net_tco2e.iloc[:6].sum() / bridge.net_tco2e.sum(),
        "monsoon_share_of_net": bridge.net_tco2e.iloc[5:9].sum() / bridge.net_tco2e.sum(),
        "pass_rate": t.dmrv_pass_rate(p),
        "evidence_completeness": t.evidence_completeness(p),
        "gross_per_t_biochar": gross_char,
        "project_em_per_t_biochar": t.project_em_t_per_t_biochar(p),
        "ch4_share_of_gross": p["ch4_ef_g_per_kg_biochar"] / 1000 * p["ch4_gwp100"] / gross_char,
        "ch4_share_of_gross_at_30": 30 / 1000 * p["ch4_gwp100"] / gross_char,
        "ch4_share_of_gross_at_5": 5 / 1000 * p["ch4_gwp100"] / gross_char,
        "cycle_ceiling_1_shift": t.cycle_ceiling_batches_per_day(p, 1),
        "cycle_ceiling_2_shift": t.cycle_ceiling_batches_per_day(p, 2),
        "fill_ratio_default": t.kiln_fill_ratio(p),
        "fill_ratio_at_required_dry": t.kiln_fill_ratio(p, req_dry),
        "required_throughput_t_dry_per_kiln_day": p["dry_biomass_per_batch_t"] * p["batches_per_kiln_day"] * target / bridge.net_tco2e.sum(),
        "default_throughput_t_dry_per_kiln_day": p["dry_biomass_per_batch_t"] * p["batches_per_kiln_day"],
        "uniform_stretch": stretch,
        "greedy_steps": stack.to_dict(orient="records"),
        "direct_labour_inr_per_kg_char": p["operator_pay_inr_per_batch"] / (p["dry_biomass_per_batch_t"] * p["biochar_yield_dry_frac"] * 1000),
        **imp,
    }
    (OUT / "key_numbers.json").write_text(json.dumps(key, indent=2, default=float), encoding="utf-8")
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in key.items() if k != "greedy_steps"}, indent=1))
    print(stack)


if __name__ == "__main__":
    main()

"""Regenerate docs/assumptions_table.md from assumptions.yaml. Run: python -m tools.build_assumptions_table"""
from __future__ import annotations

from collections import Counter

from model.assumptions import ROOT, load_params, meta

OUT = ROOT / "docs" / "assumptions_table.md"
BADGE = {"PUBLIC": "🟢 PUBLIC", "LITERATURE": "🔵 LITERATURE", "ASSUMPTION – VERIFY": "🟠 ASSUMPTION – VERIFY"}


def _fmt(x: float) -> str:
    if float(x).is_integer() and abs(x) >= 1:
        return f"{int(x):,}"
    return f"{x:,.4g}"


def build() -> str:
    params = load_params()
    counts = Counter(p.status for p in params.values())
    lines = [
        "# Assumptions table",
        "",
        f"> {meta()['disclaimer']}",
        "",
        "Auto-generated from `assumptions.yaml` by `tools/build_assumptions_table.py`. Do not edit by hand.",
        "",
        f"**{len(params)} parameters**: " + ", ".join(f"{BADGE[s]} {counts.get(s, 0)}" for s in BADGE),
        "",
    ]
    group = None
    for p in params.values():
        if p.group != group:
            group = p.group
            lines += ["", f"## {group.replace('_', ' ').title()}", "",
                      "| Parameter | Default | Low | High | Unit | Status | Source | Note |",
                      "|---|---:|---:|---:|---|---|---|---|"]
        name = f"**{p.name}** ⚙️" if p.lever else p.name
        note = p.note.replace("|", "/")
        lines.append(f"| {name} | {_fmt(p.default)} | {_fmt(p.low)} | {_fmt(p.high)} | {p.unit} | "
                     f"{BADGE[p.status]} | {p.source} | {note} |")
    lines += ["", "⚙️ = solver lever in the \"what has to be true\" analysis.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")

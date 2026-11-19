"""Docs tests: every quoted number is current, and the disclaimer is present everywhere.
Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha."""
from pathlib import Path

from tools.build_docs import compute, render

ROOT = Path(__file__).resolve().parents[1]
DISCLAIMER = "Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha."


def test_docs_are_fresh():
    """Re-render templates from current model outputs; committed docs must match exactly."""
    for dest, text in render(compute()).items():
        assert dest.read_text(encoding="utf-8") == text, f"{dest.name} is stale: run python -m tools.build_docs"


def test_disclaimer_everywhere():
    files = ["README.md", "REVIEW.md", "PHASE1_FINDINGS.md", "assumptions.yaml", "docs/memo.tex",
             "docs/sop_site_launch.md", "docs/talk_track.md", "docs/assumptions_table.md"]
    for f in files:
        assert DISCLAIMER in (ROOT / f).read_text(encoding="utf-8"), f
    for f in list((ROOT / "app").rglob("*.py")) + list((ROOT / "model").glob("*.py")) + [ROOT / "data" / "generate.py"]:
        if f.name in ("__init__.py",) and f.parent.name == "pages":
            continue
        assert "Not affiliated with or endorsed by Varaha" in f.read_text(encoding="utf-8"), f


def test_pdfs_exist():
    assert (ROOT / "docs" / "memo.pdf").stat().st_size > 10_000
    assert (ROOT / "docs" / "sop_site_launch.pdf").stat().st_size > 20_000

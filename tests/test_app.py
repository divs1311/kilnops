"""App smoke tests: every page renders without exceptions.
Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app"
PAGES = [APP / "Home.py"] + sorted((APP / "pages").glob("*.py"))
DISCLAIMER = "Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha."


@pytest.mark.parametrize("page", PAGES, ids=[p.stem for p in PAGES])
def test_page_runs_and_carries_disclaimer(page):
    at = AppTest.from_file(str(page), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
    text = " ".join(m.value for m in at.markdown)
    assert DISCLAIMER in text

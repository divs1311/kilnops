"""Tonne bridge and solver tests. Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha."""
import numpy as np
import pytest

from model import tonnes as t
from model.assumptions import defaults, meta, with_overrides

TARGET = meta()["target_net_tco2e"]


def test_bridge_reconciles_sum_of_parts():
    b = t.monthly_bridge(defaults())
    parts = b.gross_tco2e - b.rejected_tco2e - b.project_emissions_tco2e - b.buffer_tco2e
    assert np.allclose(parts, b.net_tco2e)
    assert np.isclose(b.cum_net_tco2e.iloc[-1], b.net_tco2e.sum())
    assert np.isclose(b.plan_cum_tco2e.iloc[-1], TARGET)


def test_bridge_hand_calculation_single_month():
    """Flat ramp, no relocation, no deductions: net = kilns·days·bpd·dry·yield·C·44/12·perm."""
    p = with_overrides(ramp_start_share=1.0, relocation_downtime_days=0, buffer_deduction_frac=0,
                       ch4_ef_g_per_kg_biochar=0, other_project_emissions_t_per_t_biochar=0)
    b = t.monthly_bridge(p, pass_rate=1.0)
    expected_jan = (p["kilns_total"] * p["op_days_jan"] * p["batches_per_kiln_day"] * p["dry_biomass_per_batch_t"]
                    * p["biochar_yield_dry_frac"] * p["biochar_corg_frac"] * p["co2_per_c"] * p["persistence_factor"])
    assert b.net_tco2e.iloc[0] == pytest.approx(expected_jan)


def test_brief_arithmetic_anchor():
    assert TARGET / 450 == pytest.approx(222.2, abs=0.1)
    assert TARGET / 450 / 0.85 == pytest.approx(261.4, abs=0.1)


def test_pass_rate_formula():
    p = defaults()
    c = t.evidence_completeness(p)
    expected = (c + (1 - c) * p["evidence_remediation_frac"]) * (1 - p["quality_rejection_frac"]) * (1 - p["audit_rejection_frac"])
    assert t.dmrv_pass_rate(p) == pytest.approx(expected)
    assert 0.80 < t.dmrv_pass_rate(p) < 0.92  # near the brief's 85% anchor


@pytest.mark.parametrize("lever", [lv.key for lv in t.LEVERS])
def test_solver_hits_target_within_half_percent(lever):
    p = defaults()
    x = t.solve_lever(p, lever, TARGET)
    assert t._eval(p, lever, x) == pytest.approx(TARGET, rel=0.005)


def test_solver_table_reports_every_lever():
    st = t.solver_table(defaults())
    assert len(st) == len(t.LEVERS)
    assert np.allclose(st.check_net_at_required, TARGET, rtol=0.005)


def test_greedy_stack_reaches_target():
    s = t.greedy_stack(defaults())
    assert s.net_tco2e.iloc[-1] == pytest.approx(TARGET, rel=0.005)


def test_uniform_stretch_between_zero_and_one():
    st = t.uniform_stretch(defaults())
    assert 0 < st < 1


def test_monotonicity():
    p = defaults()
    base = t.annual_net(p)
    assert t.annual_net({**p, "ch4_ef_g_per_kg_biochar": 30}) < base
    assert t.annual_net({**p, "batches_per_kiln_day": 2.0}) > base
    assert t.annual_net({**p, "ramp_full_month": 9}) < base

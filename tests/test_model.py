"""Phase 3 tests: scenarios, Monte Carlo, economics, KPIs on hand-built fixtures.
Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha."""
import numpy as np
import pandas as pd
import pytest

from model import economics as e
from model import kpis as k
from model import tonnes as t
from model.assumptions import defaults, load_params, meta, scenario_params, scenarios

TARGET = meta()["target_net_tco2e"]


# --------------------------------------------------------------------------- scenarios & MC
def test_scenario_overrides_reference_real_parameters():
    params = load_params()
    for name, spec in scenarios().items():
        for key in list((spec.get("overrides") or {})) + list((spec.get("mc_ranges") or {})):
            assert key in params, f"{name}: {key}"
        for key, (lo, mode, hi) in (spec.get("mc_ranges") or {}).items():
            assert lo <= mode <= hi
            assert params[key].low <= lo and hi <= params[key].high, f"{name}:{key} MC range outside yaml bounds"


def test_plan_implied_hits_target_deterministically():
    assert t.annual_net(scenario_params("plan_implied")) == pytest.approx(TARGET, rel=0.06)


def test_scenarios_order_sensibly():
    s = t.scenario_summary().set_index("scenario").net_tco2e
    assert s["upside"] > s["plan_implied"] > s["slow_ramp"]
    assert s["plan_implied"] > s["biomass_shock"] and s["plan_implied"] > s["mrv_slippage"]
    assert s["literature"] < s["plan_implied"]


def test_vectorised_core_matches_scalar():
    p = scenario_params("plan_implied")
    draws = t.sample_params("plan_implied", 50, 1)
    vec = t.bridge_arrays(draws)["net_tco2e"].sum(axis=-1)
    i = 17
    scalar = t.annual_net({k_: (v[i] if isinstance(v, np.ndarray) else v) for k_, v in draws.items()})
    assert vec[i] == pytest.approx(scalar)
    assert t.annual_net(p) == pytest.approx(float(t.bridge_arrays(p)["net_tco2e"].sum()))


def test_monte_carlo_properties():
    mc = t.monte_carlo("plan_implied", n=5000)
    assert mc["n"] >= 5000
    assert mc["p10"] < mc["p50"] < mc["p90"]
    assert 0 <= mc["prob_hit"] <= 1
    assert mc["prob_hit"] == pytest.approx((mc["annual"] >= TARGET).mean())
    assert mc["cum_p50"][-1] == pytest.approx(np.percentile(mc["annual"], 50), rel=0.02)
    again = t.monte_carlo("plan_implied", n=5000)
    assert again["p50"] == mc["p50"]  # seeded


def test_tornado_and_drift():
    tor = t.tornado("plan_implied")
    assert (tor.swing.diff().dropna() <= 1e-9).all()
    drift = t.p50_drift_decomposition("plan_implied")
    assert drift["pct_change"].iloc[0] <= drift["pct_change"].iloc[-1]


def test_lever_simulator_ranked_and_costed():
    lv = t.lever_simulator(scenario_params("plan_implied"))
    eff = lv[~lv.no_effect]
    assert (eff.delta_net_t > 0).all() and (eff.delta_cost_inr > 0).all()
    assert eff.inr_per_incremental_t.is_monotonic_increasing


# --------------------------------------------------------------------------- economics
def test_cost_buckets_reconcile():
    p = scenario_params("plan_implied")
    cb = e.cost_buckets(p)
    assert cb.inr.sum() == pytest.approx(e.total_cost_inr(p))
    assert (cb.inr_per_net_t * cb.attrs["net_t"]).sum() == pytest.approx(cb.inr.sum())
    assert e.breakeven_price_usd(p) == pytest.approx(e.cost_per_net_t(p) / p["inr_per_usd"])


def test_biomass_cost_hand_check():
    p = scenario_params("plan_implied")
    cb = e.cost_buckets(p).set_index("bucket")
    dry = float(t.bridge_arrays(p)["dry_feed_t"].sum())
    expected = dry / (1 - p["biomass_moisture_frac"]) * 1000 * p["biomass_price_inr_per_kg"]
    assert cb.loc["Biomass purchase", "inr"] == pytest.approx(expected)


def test_margin_and_cash():
    p = scenario_params("plan_implied")
    m = e.margin_table(p).set_index("case")
    assert m.loc["High", "full_margin_inr_per_t"] > m.loc["Default", "full_margin_inr_per_t"] > m.loc["Low", "full_margin_inr_per_t"]
    cash = e.cash_timeline(p)
    assert cash.revenue_inr.sum() == pytest.approx(t.annual_net(p) * p["credit_price_usd"] * p["inr_per_usd"])
    assert cash.attrs["working_capital_need_inr"] > 0


def test_pathway_weights_change_ranking_score():
    base = e.pathway_matrix()
    cost_only = e.pathway_matrix({c: 0.0 for c in e.CRITERIA} | {"cost": 1.0})
    assert cost_only.iloc[0].pathway == "Regenerative agriculture"
    assert set(base.pathway) == set(e.PATHWAYS.values())


# --------------------------------------------------------------------------- KPIs on hand-built fixtures
@pytest.fixture
def fx():
    d = pd.Timestamp
    batches = pd.DataFrame({
        "batch_id": ["b1", "b2", "b3", "b4"], "kiln_id": ["k1", "k1", "k1", "k2"], "site_id": ["s1", "s1", "s1", "s2"],
        "operator_id": ["o1", "o1", "o1", "o2"],
        "date": [d("2027-01-04"), d("2027-01-04"), d("2027-01-05"), d("2027-01-04")],
        "dry_feedstock_t": [2.0, 2.0, 2.0, 1.0], "biochar_t": [0.4, 0.5, 0.5, 0.2],
        "ev_photo": [True, True, True, False], "ev_temp_log": [True, False, True, True], "ev_feed_weight": [True] * 4,
        "ev_char_weight": [True] * 4, "ev_geotag": [True] * 4, "ev_timestamp": [True] * 4,
        "accepted": [True, False, True, False], "net_tco2e": [0.6, 0.0, 0.7, 0.0], "lead_tenure_days": [5, 5, 6, 40],
    })
    deliveries = pd.DataFrame({"site_id": ["s1", "s1", "s2", "s2"], "date": [d("2027-01-01")] * 4,
                               "dry_t": [10.0, 0.0, 3.0, 0.0], "payment_lag_days": [5, 20, 10, 30]})
    returns = pd.DataFrame({"site_id": ["s1", "s2"], "village_id": ["v1", "v2"], "kg": [700.0, 100.0],
                            "produced_kg_period": [1400.0, 200.0]})
    return batches, deliveries, returns


def test_kpi_yield_acceptance_evidence(fx):
    b, _, _ = fx
    assert k.yield_pct(b) == pytest.approx(1.6 / 7.0)
    assert k.batch_acceptance_pct(b) == pytest.approx(0.5)
    assert k.evidence_completeness_pct(b) == pytest.approx(0.5)
    assert k.batch_acceptance_pct(b, by="site_id")["s1"] == pytest.approx(2 / 3)


def test_kpi_batches_per_kiln_day(fx):
    b, _, _ = fx
    assert k.batches_per_kiln_day(b) == pytest.approx(4 / 3)  # 3 kiln-days with ≥1 batch


def test_kpi_payments(fx):
    _, d, _ = fx
    assert k.village_payment_sla(d, 14) == pytest.approx(0.5)
    assert k.median_payment_lag(d) == pytest.approx(15)
    assert k.village_payment_sla(d, 14, by="site_id")["s2"] == pytest.approx(0.5)


def test_kpi_return_completion(fx):
    b, _, r = fx
    assert k.biochar_return_completion(r, b) == pytest.approx(800 / 1600)
    assert k.biochar_return_completion(r, b, by="site_id")["s1"] == pytest.approx(700 / 1400)


def test_kpi_days_of_cover(fx):
    b, d, _ = fx
    cover = k.biomass_days_of_cover(d, b, as_of="2027-01-05")
    # s1: delivered 10, used 6 → stock 4; used 6 over 2 running days → 3/day → 1.33 days
    assert cover.loc["s1", "stock_dry_t"] == pytest.approx(4.0)
    assert cover.loc["s1", "days_of_cover"] == pytest.approx(4 / 3)


def test_kpi_attrition():
    d = pd.Timestamp
    ops = pd.DataFrame({"operator_id": ["a", "b", "c", "d"],
                        "training_date": [d("2026-12-01")] * 4,
                        "attrition_date": [d("2027-03-10"), pd.NaT, pd.NaT, d("2027-02-01")]})
    assert k.operator_attrition(ops, month=3) == pytest.approx(1 / 3)
    assert k.operator_attrition(ops, month=2) == pytest.approx(1 / 4)


def test_rag():
    assert k.rag(0.95, 0.9, 0.8) == "Green"
    assert k.rag(0.85, 0.9, 0.8) == "Amber"
    assert k.rag(0.05, 0.04, 0.06, higher_is_better=False) == "Amber"
    assert k.rag(float("nan"), 0.9, 0.8) == "Grey"


def test_cumulative_vs_plan(fx):
    b, _, _ = fx
    df = k.cumulative_delivery_vs_plan(b)
    assert df.cum_plan.iloc[-1] == pytest.approx(TARGET)
    assert df.cum_actual.iloc[-1] == pytest.approx(1.3)

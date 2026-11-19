"""Schema tests for assumptions.yaml. Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha."""
from model.assumptions import MONTHS, VALID_STATUS, defaults, load_params, meta


def test_every_param_has_valid_schema():
    params = load_params()
    assert len(params) >= 60
    for p in params.values():
        assert p.status in VALID_STATUS
        assert p.low <= p.default <= p.high
        assert p.unit and p.source


def test_required_brief_parameters_present():
    params = load_params()
    required = [
        "kilns_total", "sites_total", "kilns_per_site", "ramp_start_share", "relocation_interval_days",
        "kiln_volume_m3", "dry_biomass_per_batch_t", "biomass_moisture_frac", "biochar_yield_dry_frac",
        "biochar_corg_frac", "h_corg_mean", "batches_per_kiln_day", "burn_time_h", "quench_time_h",
        "co2_per_c", "persistence_factor", "ch4_ef_g_per_kg_biochar", "buffer_deduction_frac",
        "lab_sample_frac", "village_dry_biomass_t_per_season", "farmer_supply_share", "collection_radius_km",
        "biomass_cover_days_target", "operators_per_kiln", "operator_attrition_monthly", "training_weeks_to_full",
        "biomass_price_inr_per_kg", "operator_pay_inr_per_batch", "water_l_per_batch", "transport_inr_per_t_km",
        "kiln_capex_inr", "site_setup_inr", "dmrv_device_inr_per_kiln", "lab_test_inr_per_sample",
        "verification_inr_per_year", "credit_price_usd", "inr_per_usd",
    ] + [f"op_days_{m}" for m in MONTHS]
    missing = [r for r in required if r not in params]
    assert not missing, missing


def test_public_anchors_match_brief():
    p = defaults()
    assert p["kilns_total"] == 450
    assert 1.7 <= p["biomass_price_inr_per_kg"] <= 2.2
    assert p["water_l_per_batch"] == 500
    assert p["credit_price_usd"] == 120
    assert meta()["target_net_tco2e"] == 100_000


def test_schmidt_values():
    params = load_params()
    assert params["biochar_yield_dry_frac"].default == 0.22
    assert params["burn_time_h"].default == 3.0
    assert params["co2_per_c"].default == params["co2_per_c"].low == params["co2_per_c"].high


def test_network_reconciles():
    p = defaults()
    assert abs(p["sites_total"] * p["kilns_per_site"] - p["kilns_total"]) / p["kilns_total"] < 0.01


def test_monsoon_collapse_in_calendar():
    p = defaults()
    monsoon = [p[f"op_days_{m}"] for m in ("jun", "jul", "aug", "sep")]
    peak = [p[f"op_days_{m}"] for m in ("oct", "nov", "dec")]
    assert max(monsoon) < min(peak)

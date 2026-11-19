"""Synthetic-data tests. Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha."""
import numpy as np
import pandas as pd
import pytest

from data.generate import generate
from model.assumptions import defaults


@pytest.fixture(scope="module")
def tables():
    return generate()


def test_reproducible_with_seed(tables):
    again = generate()
    for name in ("batches", "biomass_deliveries", "operators"):
        pd.testing.assert_frame_equal(tables[name], again[name])


def test_different_seed_differs(tables):
    other = generate(seed=7)
    assert not np.isclose(other["batches"].net_tco2e.sum(), tables["batches"].net_tco2e.sum())


def test_archetypes_and_network_shape(tables):
    s = tables["sites"]
    p = defaults()
    assert len(s) == p["sites_total"]
    assert tables["kilns"].shape[0] == p["kilns_total"]
    assert set(s.archetype) == {"Strong", "Average", "Biomass-constrained", "MRV-weak"}
    assert s.late_payer.sum() == 1


def test_net_equals_zero_for_rejected(tables):
    b = tables["batches"]
    assert (b.loc[~b.accepted, "net_tco2e"] == 0).all()
    assert (b.loc[b.accepted, "rejection_reason"] == "").all()


def test_monsoon_collapse(tables):
    b = tables["batches"]
    by_m = b.groupby(b.date.dt.month).size()
    assert by_m.loc[[7, 8]].mean() < 0.2 * by_m.loc[[10, 11, 12]].mean()


def test_new_operator_evidence_spike(tables):
    b = tables["batches"]
    new = b[b.lead_tenure_days <= 14].accepted.mean()
    mature = b[b.lead_tenure_days > 60].accepted.mean()
    assert new < mature - 0.04


def test_mrv_weak_sites_have_lower_acceptance(tables):
    b = tables["batches"].merge(tables["sites"][["site_id", "archetype"]], on="site_id")
    acc = b.groupby("archetype").accepted.mean()
    assert acc["MRV-weak"] < acc["Strong"] - 0.1


def test_late_payer_supply_falls_after_lag(tables):
    d, s = tables["biomass_deliveries"], tables["sites"]
    lp = s.loc[s.late_payer, "site_id"].iloc[0]
    peers = s[(s.archetype == "Average") & (s.launch_date < "2027-01-01") & ~s.late_payer].site_id
    p = defaults()
    start = pd.Timestamp("2027-01-01") + pd.Timedelta(days=p["late_payer_start_day"])
    lag_lp_after = d[(d.site_id == lp) & (d.date >= start) & (d.date < start + pd.Timedelta(days=60))].payment_lag_days.mean()
    assert lag_lp_after > 3 * p["normal_payment_lag_days"]

    def ratio(a, b_):
        w = lambda sid: d[(d.site_id == sid) & (d.date >= a) & (d.date < b_)].dry_t.sum()
        return w(lp) / np.mean([w(x) for x in peers])

    before = ratio(start - pd.Timedelta(days=45), start)
    after = ratio(start + pd.Timedelta(days=42), start + pd.Timedelta(days=84))
    assert after < 0.75 * before

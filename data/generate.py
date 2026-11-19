"""Seeded synthetic operations data for a 450-kiln distributed network, Jan–Dec 2027.

Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.
ALL DATA PRODUCED HERE IS SYNTHETIC. District names are used generically for realism only.

Design (all parameters from assumptions.yaml; design point = meta.generator_scenario):
  * 4 site archetypes: strong, average, biomass-constrained, MRV-weak.
  * Operators: attrition, backfill vacancies, learning curves; new operators raise evidence failures
    and lower peak temperatures in their first weeks (evidence spike at site launch and after churn).
  * Calendar: monsoon collapse, festival dips; seasonal residue supply.
  * One 'average' site pays villages late from late_payer_start_day; villages react to lags on deliveries
    made 4–6 weeks earlier, so supply falls with a lag (the causal story the ledger page surfaces).

Run: python -m data.generate   → writes data/*.parquet
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from model.assumptions import MONTHS, meta, scenario_params
from model.tonnes import CAL_DAYS_2027

OUT = Path(__file__).resolve().parent
YEAR_START = pd.Timestamp("2027-01-01")
DAYS = pd.date_range("2027-01-01", "2027-12-31", freq="D")
ARCHES = ("strong", "average", "biomass", "mrvweak")
ARCH_LABEL = {"strong": "Strong", "average": "Average", "biomass": "Biomass-constrained", "mrvweak": "MRV-weak"}
EV_COLS = ("ev_photo", "ev_temp_log", "ev_feed_weight", "ev_char_weight", "ev_geotag", "ev_timestamp")
EV_REASON = {"ev_temp_log": "Missing temperature log", "ev_photo": "Missing / unusable photos",
             "ev_feed_weight": "Missing feedstock weight", "ev_char_weight": "Missing biochar weight",
             "ev_geotag": "Missing geotag", "ev_timestamp": "Missing timestamp"}
# How strongly a new operator's inexperience hits each evidence element (relative weights).
NEW_OP_EV_WEIGHT = {"ev_photo": 0.6, "ev_temp_log": 1.0, "ev_feed_weight": 0.5, "ev_char_weight": 0.5,
                    "ev_geotag": 0.2, "ev_timestamp": 0.1}

# Generic western-India districts (approximate centroids) and typical residues — illustrative only.
DISTRICTS = [
    ("Kutch", "Gujarat", 23.25, 69.67), ("Banaskantha", "Gujarat", 24.17, 72.43), ("Patan", "Gujarat", 23.85, 72.12),
    ("Mehsana", "Gujarat", 23.60, 72.38), ("Surendranagar", "Gujarat", 22.72, 71.64), ("Rajkot", "Gujarat", 22.30, 70.80),
    ("Amreli", "Gujarat", 21.60, 71.22), ("Bhavnagar", "Gujarat", 21.76, 72.15), ("Junagadh", "Gujarat", 21.52, 70.46),
    ("Morbi", "Gujarat", 22.82, 70.84), ("Botad", "Gujarat", 22.17, 71.67), ("Bharuch", "Gujarat", 21.70, 72.98),
    ("Vadodara", "Gujarat", 22.31, 73.18), ("Sabarkantha", "Gujarat", 23.60, 73.00),
    ("Jalna", "Maharashtra", 19.84, 75.88), ("Beed", "Maharashtra", 18.99, 75.76), ("Yavatmal", "Maharashtra", 20.39, 78.12),
    ("Akola", "Maharashtra", 20.71, 77.00), ("Amravati", "Maharashtra", 20.93, 77.75), ("Jalgaon", "Maharashtra", 21.00, 75.56),
    ("Nanded", "Maharashtra", 19.15, 77.31), ("Washim", "Maharashtra", 20.11, 77.13), ("Buldhana", "Maharashtra", 20.53, 76.18),
    ("Parbhani", "Maharashtra", 19.27, 76.77), ("Wardha", "Maharashtra", 20.74, 78.60), ("Dhule", "Maharashtra", 20.90, 74.77),
    ("Latur", "Maharashtra", 18.40, 76.56), ("Nashik", "Maharashtra", 20.00, 73.79),
    ("Barmer", "Rajasthan", 25.75, 71.39), ("Jodhpur", "Rajasthan", 26.24, 73.02),
]
RESIDUES = {"Gujarat": ["Cotton stalk", "Castor stalk", "Pigeon pea stalk"],
            "Maharashtra": ["Cotton stalk", "Pigeon pea stalk", "Maize stover", "Soybean straw"],
            "Rajasthan": ["Mustard stalk", "Cotton stalk"]}
RESIDUE_CORG = {"Cotton stalk": 0.71, "Pigeon pea stalk": 0.72, "Castor stalk": 0.69, "Maize stover": 0.64,
                "Soybean straw": 0.63, "Mustard stalk": 0.67}
SIZE_CLASSES = (("3.0 m³", 1.00, 0.8), ("2.5 m³", 0.85, 0.2))  # label, batch-size factor, share


def _ramp_month_for_site(i: int, n_sites: int, p: dict) -> int:
    for m in range(1, 13):
        start, full = p["ramp_start_share"], p["ramp_full_month"]
        share = 1.0 if full <= 1 else min(1.0, start + (1 - start) * (m - 1) / (full - 1))
        if i < round(share * n_sites):
            return m
    return 12


def _ch4_from_moisture(m: np.ndarray, p: dict) -> np.ndarray:
    lo, hi = p["moisture_dry_threshold"], p["moisture_wet_threshold"]
    frac = np.clip((m - lo) / (hi - lo), 0, 1)
    return p["ch4_ef_dry_g_per_kg"] + frac * (p["ch4_ef_wet_g_per_kg"] - p["ch4_ef_dry_g_per_kg"])


def generate(seed: int | None = None, scenario: str | None = None) -> dict[str, pd.DataFrame]:
    m = meta()
    seed = m["random_seed"] if seed is None else seed
    p = scenario_params(scenario or m["generator_scenario"])
    rng = np.random.default_rng(seed)
    n_sites = int(p["sites_total"])
    kps = int(p["kilns_per_site"])
    ops_per_kiln = int(p["operators_per_kiln"])
    sla = p["payment_sla_days"]

    # ------------------------------------------------------------------ sites
    arch_list = sum(([a] * int(p[f"arch_{a}_sites"]) for a in ARCHES), [])
    assert len(arch_list) == n_sites, "archetype counts must sum to sites_total"
    arch_list = list(rng.permutation(arch_list))
    order = rng.permutation(n_sites)  # launch order
    late_payer = next(i for i in range(n_sites) if arch_list[i] == "average" and _ramp_month_for_site(int(np.where(order == i)[0][0]), n_sites, p) == 1)
    sites = []
    for i in range(n_sites):
        dname, state, lat, lon = DISTRICTS[i]
        rank = int(np.where(order == i)[0][0])
        month = _ramp_month_for_site(rank, n_sites, p)
        if month == 1:
            launch = pd.Timestamp("2026-11-10") + pd.Timedelta(days=int(rng.integers(0, 40)))
        else:
            launch = pd.Timestamp(2027, month, 1) + pd.Timedelta(days=int(rng.integers(0, 10)))
        moves, d = [], launch
        while True:
            d = d + pd.Timedelta(days=int(p["relocation_interval_days"] + rng.integers(-20, 21)))
            if d > DAYS[-1]:
                break
            if d >= YEAR_START:
                moves.append(d)
        sites.append({"site_id": f"S{i + 1:02d}", "district": dname, "state": state,
                      "lat": lat + rng.normal(0, 0.12), "lon": lon + rng.normal(0, 0.12),
                      "archetype": ARCH_LABEL[arch_list[i]], "arch_key": arch_list[i],
                      "launch_date": launch, "relocation_dates": ",".join(x.strftime("%Y-%m-%d") for x in moves),
                      "n_relocations": len(moves), "kilns": kps, "supervisor": f"SUP-{i + 1:02d}",
                      "late_payer": i == late_payer})
    sites_df = pd.DataFrame(sites)

    # ------------------------------------------------------------------ villages (per site location)
    villages = []
    for s in sites:
        for loc in range(s["n_relocations"] + 1):
            nv = max(4, int(rng.normal(p["villages_per_location"], 2)))
            for _ in range(nv):
                villages.append({"village_id": f"V{len(villages) + 1:04d}", "site_id": s["site_id"], "location_idx": loc,
                                 "farmer_count": int(rng.triangular(p["farmers_per_village"] * 0.55,
                                                                    p["farmers_per_village"], p["farmers_per_village"] * 2)),
                                 "residue_type": rng.choice(RESIDUES[s["state"]]),
                                 "peak_season": rng.choice(["Kharif (Oct–Dec)", "Rabi (Mar–May)", "Both"], p=[0.45, 0.25, 0.30])})
    villages_df = pd.DataFrame(villages)

    # ------------------------------------------------------------------ kilns
    K = n_sites * kps
    k_site = np.repeat(np.arange(n_sites), kps)
    size_idx = rng.choice(len(SIZE_CLASSES), size=K, p=[c[2] for c in SIZE_CLASSES])
    k_size_factor = np.array([SIZE_CLASSES[j][1] for j in size_idx])
    commission = np.array([sites[s]["launch_date"] + pd.Timedelta(days=int(rng.integers(0, 6))) for s in k_site])
    commission_day = np.array([(c - YEAR_START).days for c in commission])
    kilns_df = pd.DataFrame({"kiln_id": [f"K{j + 1:03d}" for j in range(K)], "site_id": sites_df.site_id.values[k_site],
                             "commission_date": commission, "size_class": [SIZE_CLASSES[j][0] for j in size_idx]})

    arch_k = np.array([arch_list[s] for s in k_site])
    k_prod = np.array([p[f"arch_{a}_productivity"] for a in arch_k])
    k_evmult = np.array([p[f"arch_{a}_evidence_fail_mult"] for a in arch_k])
    s_moist = np.array([p[f"arch_{a}_moisture"] for a in arch_list])
    s_supply_ratio = np.array([p[f"arch_{a}_supply_ratio"] for a in arch_list])
    s_return = np.array([p[f"arch_{a}_return_completion"] for a in arch_list])
    site_residue = villages_df.groupby("site_id")["residue_type"].agg(lambda x: x.mode().iloc[0])
    s_corg = np.array([RESIDUE_CORG[site_residue[s["site_id"]]] for s in sites])

    # ------------------------------------------------------------------ operators (slots per kiln)
    operators = []
    slot_op = np.empty((K, ops_per_kiln), dtype=object)
    slot_start = np.zeros((K, ops_per_kiln))          # hire day (relative to 2027-01-01)
    slot_vacant_until = np.full((K, ops_per_kiln), -1e9)

    def hire(k: int, j: int, day: float):
        oid = f"OP{len(operators) + 1:05d}"
        hire_date = YEAR_START + pd.Timedelta(days=float(day))
        operators.append({"operator_id": oid, "kiln_id": kilns_df.kiln_id[k], "site_id": kilns_df.site_id[k],
                          "role": "Lead operator" if j == 0 else "Crew", "training_date": hire_date.normalize(),
                          "attrition_date": pd.NaT, "cohort": hire_date.strftime("%Y-%m")})
        slot_op[k, j] = len(operators) - 1
        slot_start[k, j] = day

    for k in range(K):
        for j in range(ops_per_kiln):
            hire(k, j, commission_day[k] - int(rng.integers(3, 10)))  # trained just before commissioning

    tau = p["training_weeks_to_full"] * 7 / 3.0     # e-folding days: ~95% productive at training_weeks
    p0 = p["new_operator_productivity"]
    hazard = p["operator_attrition_monthly"] / 30.4

    # ------------------------------------------------------------------ daily state
    reloc_days = [set() for _ in range(n_sites)]
    loc_idx_by_day = np.zeros((n_sites, len(DAYS)), dtype=int)
    for i, s in enumerate(sites):
        moves = [pd.Timestamp(x) for x in s["relocation_dates"].split(",") if x]
        for mv in moves:
            d0 = (mv - YEAR_START).days
            reloc_days[i].update(range(d0, d0 + int(p["relocation_downtime_days"] * 7 / 5)))
            loc_idx_by_day[i, d0:] += 1
    stock = np.zeros(n_sites)
    trust = np.ones(n_sites)
    deliv_kg = np.zeros((n_sites, len(DAYS)))
    deliv_lag = np.zeros((n_sites, len(DAYS)))
    month_of_day = DAYS.month.values - 1
    op_prob = np.array([p[f"op_days_{m}"] / CAL_DAYS_2027[i] for i, m in enumerate(MONTHS)])
    supply_idx = np.array([p[f"supply_index_{m}"] for m in MONTHS])
    full_demand_site = kps * p["batches_per_kiln_day"] * p["dry_biomass_per_batch_t"] * op_prob.mean()
    vill_by_site_loc = {k: g for k, g in villages_df.groupby(["site_id", "location_idx"])}

    batch_rows: list[dict[str, np.ndarray]] = []
    deliveries, status_events = [], []
    for k in range(K):
        status_events.append((kilns_df.kiln_id[k], commission[k].normalize(), "Commissioned"))
    for i, s in enumerate(sites):
        for mv in [x for x in s["relocation_dates"].split(",") if x]:
            for k in np.where(k_site == i)[0]:
                status_events.append((kilns_df.kiln_id[k], pd.Timestamp(mv), "Relocating"))
                status_events.append((kilns_df.kiln_id[k], pd.Timestamp(mv) + pd.Timedelta(days=int(p["relocation_downtime_days"] * 7 / 5)), "Active"))

    for d, day in enumerate(DAYS):
        mi = month_of_day[d]
        # --- attrition and backfill
        leave = (rng.random((K, ops_per_kiln)) < hazard) & (slot_vacant_until < d) & (commission_day[:, None] <= d)
        for k, j in zip(*np.nonzero(leave)):
            operators[slot_op[k, j]]["attrition_date"] = day
            slot_vacant_until[k, j] = d + rng.integers(max(1, p["operator_vacancy_days"] - 3), p["operator_vacancy_days"] + 4)
        refill = (slot_vacant_until >= d - 0.5) & (slot_vacant_until < d + 0.5)
        for k, j in zip(*np.nonzero(refill)):
            hire(k, j, d)
            slot_vacant_until[k, j] = -1e9
        vacant = slot_vacant_until > d

        # --- which kilns can run today
        site_open = (rng.random(n_sites) < op_prob[mi]) & np.array([d not in reloc_days[i] for i in range(n_sites)])
        active = (commission_day <= d) & site_open[k_site] & (rng.random(K) > 0.03)  # 3% ad-hoc maintenance
        tenure = d - slot_start                        # days per slot
        prod_slot = 1 - (1 - p0) * np.exp(-np.maximum(tenure, 0) / tau)
        crew_prod = np.where(vacant, 0.0, prod_slot).mean(axis=1)
        lead_tenure = np.where(vacant[:, 0], 0, tenure[:, 0])
        expected = p["batches_per_kiln_day"] * k_prod * np.clip(crew_prod / 1.0, 0, 1) * active
        n_b = np.floor(expected) + (rng.random(K) < (expected - np.floor(expected)))
        n_b = np.minimum(n_b, np.ceil(p["batches_per_kiln_day"]))

        # --- biomass constraint per site
        dry_need = n_b * p["dry_biomass_per_batch_t"] * k_size_factor
        need_site = np.bincount(k_site, weights=dry_need, minlength=n_sites)
        ratio = np.where(need_site > 0, np.minimum(1.0, stock / np.maximum(need_site, 1e-9)), 1.0)
        keep_prob = ratio[k_site]
        n_b = np.where(rng.random(K) < keep_prob, n_b, np.maximum(n_b - 1, 0))
        n_b = np.where(keep_prob < 0.35, 0, n_b)

        # --- batches
        idx = np.repeat(np.arange(K), n_b.astype(int))
        if idx.size:
            nb = idx.size
            dry_t = p["dry_biomass_per_batch_t"] * k_size_factor[idx] * rng.lognormal(0, p["dry_batch_cv"], nb)
            used = np.bincount(k_site[idx], weights=dry_t, minlength=n_sites)
            scale = np.where(used > stock, stock / np.maximum(used, 1e-9), 1.0)
            dry_t = dry_t * scale[k_site[idx]]
            used = np.bincount(k_site[idx], weights=dry_t, minlength=n_sites)
            stock -= used
            newness = np.exp(-lead_tenure[idx] / 15.0)
            monsoon_wet = 0.04 if mi in (5, 8) else (0.07 if mi in (6, 7) else 0.0)
            moist = np.clip(rng.normal(s_moist[k_site[idx]] + monsoon_wet, 0.025), 0.06, 0.35)
            yld = np.clip(rng.normal(p["biochar_yield_dry_frac"], p["yield_sd"], nb) - 0.02 * newness, 0.12, 0.32)
            char_t = dry_t * yld
            corg = np.clip(s_corg[k_site[idx]] + rng.normal(0, 0.03, nb), 0.5, 0.85)
            temp = rng.normal(p["peak_temp_mean_c"], p["peak_temp_sd_c"], nb) - p["new_operator_temp_penalty_c"] * newness
            hcorg = np.clip(rng.normal(p["h_corg_mean"], p["h_corg_sd"], nb) + 0.004 * np.maximum(0, 640 - temp), 0.1, 0.95)
            water = np.clip(rng.normal(p["water_l_per_batch"], p["water_l_per_batch"] * 0.15, nb), 150, 1200)
            ev = {}
            for e in EV_COLS:
                fail = (1 - p[e]) * k_evmult[idx] + p["new_operator_evidence_penalty"] * NEW_OP_EV_WEIGHT[e] * newness
                ev[e] = rng.random(nb) >= np.clip(fail, 0, 0.9)
            complete = np.logical_and.reduce([ev[e] for e in EV_COLS])
            remediated = ~complete & (rng.random(nb) < p["evidence_remediation_frac"])
            quality_fail = (hcorg > p["h_corg_max_eligible"]) | (temp < 520) | (rng.random(nb) < p["quality_rejection_frac"] * 0.75)
            audit_fail = rng.random(nb) < p["audit_rejection_frac"]
            accepted = (complete | remediated) & ~quality_fail & ~audit_fail
            reason = np.full(nb, "", dtype=object)
            for e in ("ev_temp_log", "ev_photo", "ev_feed_weight", "ev_char_weight", "ev_geotag", "ev_timestamp"):
                reason = np.where((reason == "") & ~ev[e] & ~remediated, EV_REASON[e], reason)
            reason = np.where((reason == "") & quality_fail, "Quality (H/Corg or low temperature)", reason)
            reason = np.where((reason == "") & audit_fail, "Disallowed at audit sample", reason)
            reason = np.where(accepted, "", reason)
            ch4 = _ch4_from_moisture(moist, p)
            gross = char_t * corg * p["co2_per_c"] * p["persistence_factor"]
            pe = char_t * (ch4 / 1000 * p["ch4_gwp100"] + p["other_project_emissions_t_per_t_biochar"])
            net = np.where(accepted, (gross - pe) * (1 - p["buffer_deduction_frac"]), 0.0)
            batch_rows.append({
                "kiln_idx": idx, "operator_idx": np.array([slot_op[k, 0] if not vacant[k, 0] else slot_op[k, 1] for k in idx]),
                "day": np.full(nb, d), "dry_feedstock_t": dry_t, "moisture": moist, "biochar_t": char_t, "corg": corg,
                "peak_temp_c": temp, "quench_water_l": water, **ev, "remediated": remediated,
                "lab_sample": rng.random(nb) < p["lab_sample_frac"], "h_corg": hcorg, "ch4_g_per_kg": ch4,
                "accepted": accepted, "rejection_reason": reason, "gross_tco2e": gross, "net_tco2e": net,
                "lead_tenure_days": lead_tenure[idx]})

        # --- trust update (villages react to payment lags on deliveries made 4–6 weeks ago)
        w0, w1 = d - int(p["trust_window_start_days"]), d - int(p["trust_window_end_days"])
        if w1 > 0:
            w0 = max(w0, 0)
            kg = deliv_kg[:, w0:w1]
            lag = deliv_lag[:, w0:w1]
            age = d - np.arange(w0, w1)
            excess = np.maximum(np.minimum(lag, age) - sla, 0)
            mean_excess = np.where(kg.sum(1) > 0, (excess * kg).sum(1) / np.maximum(kg.sum(1), 1e-9), 0)
            target = np.clip(1 - p["trust_sensitivity"] * mean_excess / sla, p["trust_floor"], 1)
            recovered = np.minimum(trust + p["trust_recovery_per_day"], target)
            recovered = np.where(kg.sum(1) > 0, recovered, trust)   # no deliveries in window → no new evidence
            trust = np.where(target < trust, trust - np.minimum(trust - target, 0.04), recovered)

        # --- deliveries
        demand_est = np.bincount(k_site, weights=(commission_day <= d) * p["batches_per_kiln_day"] * k_prod
                                 * p["dry_biomass_per_batch_t"] * k_size_factor, minlength=n_sites) * op_prob[mi]
        cap = s_supply_ratio * full_demand_site * supply_idx[mi] * trust * rng.lognormal(0, 0.25, n_sites)
        want = np.maximum(0, p["biomass_cover_days_target"] * demand_est + demand_est - stock)
        launched = np.array([sites[i]["launch_date"] <= day for i in range(n_sites)])
        delivered = np.where(launched & np.array([d not in reloc_days[i] for i in range(n_sites)]),
                             np.minimum(cap, want), 0)
        for i in np.nonzero(delivered > 0.05)[0]:
            vil = vill_by_site_loc[(sites[i]["site_id"], int(loc_idx_by_day[i, d]))]
            nv = int(min(len(vil), rng.integers(1, 5)))
            chosen = rng.choice(len(vil), size=nv, replace=False, p=vil.farmer_count.values / vil.farmer_count.sum())
            split = rng.dirichlet(np.ones(nv)) * delivered[i]
            late = sites[i]["late_payer"] and p["late_payer_start_day"] <= d < p["late_payer_end_day"]
            mean_lag = p["late_payer_lag_days"] if late else p["normal_payment_lag_days"]
            for v, dry in zip(chosen, split):
                moist = np.clip(rng.normal(s_moist[i], 0.03), 0.06, 0.35)
                kg_ar = dry / (1 - moist) * 1000
                price = round(float(p["biomass_price_inr_per_kg"] * rng.uniform(0.9, 1.08)), 2)
                lag_days = int(max(1, rng.gamma(4, mean_lag / 4)))
                deliveries.append({"site_id": sites[i]["site_id"], "village_id": vil.village_id.values[v], "date": day,
                                   "kg": kg_ar, "dry_t": dry, "price_inr_per_kg": price, "amount_inr": kg_ar * price,
                                   "payment_due_date": day + pd.Timedelta(days=int(sla)),
                                   "payment_date": day + pd.Timedelta(days=lag_days), "payment_lag_days": lag_days})
                deliv_kg[i, d] += kg_ar
                deliv_lag[i, d] += kg_ar * lag_days
            deliv_lag[i, d] /= max(deliv_kg[i, d], 1e-9)
        stock += delivered

    # ------------------------------------------------------------------ assemble batches
    cols = {k: np.concatenate([r[k] for r in batch_rows]) for k in batch_rows[0]}
    b = pd.DataFrame(cols)
    b.insert(0, "batch_id", [f"B{j + 1:06d}" for j in range(len(b))])
    b["kiln_id"] = kilns_df.kiln_id.values[b.kiln_idx]
    b["site_id"] = kilns_df.site_id.values[b.kiln_idx]
    b["operator_id"] = [operators[j]["operator_id"] for j in b.operator_idx]
    b["date"] = YEAR_START + pd.to_timedelta(b.day, unit="D")
    b = b.drop(columns=["kiln_idx", "operator_idx", "day"])
    float_cols = b.select_dtypes("float64").columns
    b[float_cols] = b[float_cols].astype("float32")
    b["rejection_reason"] = b.rejection_reason.astype("category")
    lead = ["batch_id", "date", "site_id", "kiln_id", "operator_id"]
    b = b[lead + [c for c in b.columns if c not in lead]]

    deliveries_df = pd.DataFrame(deliveries)
    deliveries_df.insert(0, "delivery_id", [f"D{j + 1:06d}" for j in range(len(deliveries_df))])

    # ------------------------------------------------------------------ biochar returns
    returns = []
    interval = int(p["biochar_return_interval_days"])
    char_by_site_day = b.groupby(["site_id", b.date.dt.dayofyear - 1])["biochar_t"].sum()
    for i, s in enumerate(sites):
        sid = s["site_id"]
        if sid not in char_by_site_day.index.get_level_values(0):
            continue
        cs = char_by_site_day.loc[sid].reindex(range(len(DAYS)), fill_value=0).values
        dv = deliveries_df[deliveries_df.site_id == sid]
        for start in range(0, len(DAYS), interval):
            produced = cs[start:start + interval].sum()
            ret_day = start + interval + int(rng.integers(0, 5))
            if produced <= 0 or ret_day >= len(DAYS):
                continue
            ret_kg = produced * 1000 * np.clip(rng.normal(s_return[i], 0.06), 0.3, 1.0)
            win = dv[(dv.date >= DAYS[start]) & (dv.date < DAYS[min(start + interval, len(DAYS) - 1)])]
            if win.empty:
                continue
            share = win.groupby("village_id")["kg"].sum()
            share = share / share.sum()
            fc = villages_df.set_index("village_id").farmer_count
            for vid, sh in share.items():
                returns.append({"site_id": sid, "village_id": vid, "date": DAYS[ret_day], "kg": ret_kg * sh,
                                "produced_kg_period": produced * 1000 * sh,
                                "recipient_count": int(max(1, fc[vid] * rng.uniform(0.15, 0.4) * min(1, sh * 4)))})
    returns_df = pd.DataFrame(returns)

    # ------------------------------------------------------------------ payouts
    vp = deliveries_df.rename(columns={"village_id": "payee_id"})[["site_id", "payee_id", "amount_inr", "payment_due_date", "payment_date"]]
    vp = vp.assign(payee_type="Village committee", date=deliveries_df.date)
    b_week = b.assign(week=b.date.dt.to_period("W-SUN").dt.end_time.dt.normalize())
    op_pay = (b_week.groupby(["site_id", "operator_id", "week"]).size().rename("batches").reset_index())
    op_pay["amount_inr"] = op_pay.batches * p["operator_pay_inr_per_batch"] / ops_per_kiln
    op_pay["payment_due_date"] = op_pay.week + pd.Timedelta(days=3)
    op_pay["payment_date"] = op_pay.payment_due_date + pd.to_timedelta(rng.integers(-1, 4, len(op_pay)), unit="D")
    op_pay = op_pay.rename(columns={"operator_id": "payee_id", "week": "date"}).assign(payee_type="Operator")
    payouts = pd.concat([vp, op_pay[["site_id", "payee_id", "amount_inr", "payment_due_date", "payment_date", "payee_type", "date"]]],
                        ignore_index=True)
    payouts["lag_days"] = (payouts.payment_date - payouts.date).dt.days
    payouts["days_late"] = (payouts.payment_date - payouts.payment_due_date).dt.days.clip(lower=0)

    status_df = pd.DataFrame(status_events, columns=["kiln_id", "date", "status"]).sort_values(["kiln_id", "date"])
    operators_df = pd.DataFrame(operators)
    sites_df = sites_df.drop(columns=["arch_key"])
    return {"sites": sites_df, "kilns": kilns_df, "kiln_status": status_df, "operators": operators_df,
            "villages": villages_df, "batches": b, "biomass_deliveries": deliveries_df,
            "biochar_returns": returns_df, "payouts": payouts}


def write(tables: dict[str, pd.DataFrame], out: Path = OUT) -> None:
    for name, df in tables.items():
        df.to_parquet(out / f"{name}.parquet", index=False, compression="zstd")


if __name__ == "__main__":
    import time

    t0 = time.time()
    tables = generate()
    write(tables)
    for name, df in tables.items():
        print(f"{name:20s} {len(df):>8,} rows")
    b = tables["batches"]
    print(f"net tCO2e {b.net_tco2e.sum():,.0f} | acceptance {b.accepted.mean():.1%} | {time.time() - t0:.1f}s")

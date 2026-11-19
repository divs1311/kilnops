# Assumptions table

> Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.

Auto-generated from `assumptions.yaml` by `tools/build_assumptions_table.py`. Do not edit by hand.

**89 parameters**: 🟢 PUBLIC 5, 🔵 LITERATURE 9, 🟠 ASSUMPTION – VERIFY 75


## Network

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| **kilns_total** ⚙️ | 450 | 380 | 480 | kilns | 🟢 PUBLIC | Agnisparsh public announcement (Nov 13, 2026) | ~450 Kon-Tiki kilns is public. Low = deployment slip; high = top-up kilns. |
| sites_total | 30 | 20 | 45 | mobile sites | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Public: 'multiple mobile sites in western India'. Count not disclosed. |
| kilns_per_site | 15 | 10 | 22 | kilns/site | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Must reconcile with kilns_total / sites_total (tested). |
| ramp_start_share | 0.45 | 0.25 | 0.7 | share of kilns online in Jan 2027 | 🟠 ASSUMPTION – VERIFY | Analyst estimate | First issuance planned Jan 2027 (public) implies some kilns produced in late 2026. |
| ramp_full_month | 5 | 3 | 9 | month index (1=Jan) at which 100% of kilns are online | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Linear ramp from ramp_start_share in Jan. low = faster ramp (good case). |
| relocation_interval_days | 120 | 60 | 180 | calendar days between site moves | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Sites move as residue within the collection radius is exhausted. |
| relocation_downtime_days | 5 | 2 | 10 | operating days lost per move | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

## Kiln Physics

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| kiln_volume_m3 | 2 | 1 | 3 | m³ | 🟠 ASSUMPTION – VERIFY | Default = 2 m³ flame-curtain kiln described in Schmidt et al. 2016 (2.4 m top diameter); range is analyst estimate | Agnisparsh kiln size is not public. Used for a fill-consistency check only (implied char volume vs kiln volume). |
| biochar_bulk_density_t_m3 | 0.2 | 0.15 | 0.25 | t biochar / m³ | 🟠 ASSUMPTION – VERIFY | Schmidt et al. 2016 (2 m³ kiln → ~500 kg biochar dry ⇒ ≤0.25 at full fill); crop-residue char assumed lighter |  |
| **dry_biomass_per_batch_t** ⚙️ | 1.5 | 0.6 | 2.5 | t dry feedstock / batch | 🟠 ASSUMPTION – VERIFY | Analyst estimate; high ≈ Schmidt 2016 2 m³ kiln (500 kg char ÷ 22% yield ≈ 2.3 t) | Single biggest unknown. Not public for Agnisparsh. |
| biomass_moisture_frac | 0.18 | 0.1 | 0.3 | fraction (wet basis, as received) | 🟠 ASSUMPTION – VERIFY | Schmidt et al. 2016 (feedstock 15-25%); Lotz & Schmidt 2026 (≤15% ⇒ low CH4; ≥25% ⇒ up to 10x CH4) | Drives procurement weight and, via CH4, net tonnes. |
| biochar_yield_dry_frac | 0.22 | 0.17 | 0.27 | t biochar / t dry feedstock | 🔵 LITERATURE | Schmidt et al. 2016, PLOS ONE 11(5):e0154617, doi:10.1371/journal.pone.0154617 | Schmidt 2016: 22 ± 5% (observed range 13-32%); low/high = ±1 SD. |
| **biochar_corg_frac** ⚙️ | 0.7 | 0.55 | 0.8 | t organic C / t biochar | 🔵 LITERATURE | Schmidt et al. 2016 (75.5 ± 9%, woody; 54-55% high-ash residue mixes); IPCC 2019 Fc: wood 0.77, herbaceous 0.65 | Default shaded below the woody mean for semi-woody crop stalks with higher ash. |
| h_corg_mean | 0.25 | 0.22 | 0.4 | molar ratio | 🔵 LITERATURE | Schmidt et al. 2016 (H/Corg 0.22-0.28) | High bound represents a poorly run (early-quenched / smouldering) tail. |
| h_corg_sd | 0.05 | 0.03 | 0.1 | molar ratio (batch-to-batch SD) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| h_corg_max_eligible | 0.7 | 0.4 | 0.7 | molar ratio threshold | 🔵 LITERATURE | EBC / IBI common eligibility threshold (H/Corg < 0.7); stricter classes use 0.4 | Verify the exact threshold in Rainbow Distributed Open-Kiln v1.0. |
| **batches_per_kiln_day** ⚙️ | 1.5 | 1 | 2.5 | batches / kiln / operating day | 🟠 ASSUMPTION – VERIFY | Analyst estimate; cycle-time check uses Schmidt 2016 ~3 h burn | Above ~1.8 needs a second shift (see cycle-time parameters). |
| burn_time_h | 3 | 2.5 | 4 | hours / batch | 🔵 LITERATURE | Schmidt et al. 2016 (~3 h for a 2 m³ kiln) |  |
| quench_time_h | 1 | 0.5 | 1.5 | hours / batch | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| handling_time_h | 1.5 | 1 | 2.5 | hours / batch (prep, unload, weigh, evidence capture) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| working_hours_per_shift | 10 | 8 | 12 | hours | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| shifts_per_kiln_day | 1 | 1 | 2 | crews / kiln / day | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

## Calendar

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| op_days_jan | 23 | 20 | 25 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Cotton / pigeon-pea stalk clearing season. |
| op_days_feb | 22 | 19 | 24 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| op_days_mar | 21 | 17 | 24 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Holi; rabi harvest begins. |
| op_days_apr | 23 | 19 | 25 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Rabi residue peak. |
| op_days_may | 21 | 16 | 24 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Heat and wedding-season labour dip. |
| op_days_jun | 9 | 4 | 15 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Monsoon onset mid-June. |
| op_days_jul | 3 | 0 | 8 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Monsoon: wet biomass, no open burns. |
| op_days_aug | 3 | 0 | 8 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| op_days_sep | 7 | 2 | 14 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Monsoon withdrawal; early kharif (maize) stover. |
| op_days_oct | 21 | 17 | 24 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Kharif residue peak; Dussehra. |
| op_days_nov | 19 | 15 | 23 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Diwali window. |
| op_days_dec | 24 | 21 | 26 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

## Carbon Accounting

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| co2_per_c | 3.667 | 3.667 | 3.667 | t CO2 / t C (44/12) | 🔵 LITERATURE | Molar mass ratio |  |
| **persistence_factor** ⚙️ | 0.8 | 0.65 | 0.89 | fraction of biochar C remaining (100-yr basis) | 🔵 LITERATURE | IPCC 2019 Refinement Fperm: low-temp 0.65, medium 0.80, high-temp (>600 °C) 0.89 | METHODOLOGY-DEPENDENT. Kon-Tiki main zone reaches 680-750 °C (Schmidt 2016), which would support 0.89; default 0.80 reflects mixed temperature histories and warm soils. Verify against Rainbow v1.0. |
| **ch4_ef_g_per_kg_biochar** ⚙️ | 15 | 5 | 30 | g CH4 / kg biochar | 🔵 LITERATURE | Schmidt et al. 2016 (30 ± 60, used as a common standard default); Lotz & Schmidt 2026 (<5 when feedstock ≤15% moisture) | Default assumes partial moisture control. Whether the methodology credits measured rather than default emission factors is the key question. |
| ch4_gwp100 | 28 | 27 | 29.8 | t CO2e / t CH4 | 🔵 LITERATURE | IPCC AR5 (28) / AR6 (27.0 non-fossil, 29.8 fossil) |  |
| other_project_emissions_t_per_t_biochar | 0.05 | 0.02 | 0.1 | t CO2e / t biochar | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Biomass and biochar transport, pumps, field vehicles, embodied kiln steel. |
| buffer_deduction_frac | 0.05 | 0 | 0.15 | fraction of net removals withheld | 🟠 ASSUMPTION – VERIFY | Analyst estimate | METHODOLOGY-DEPENDENT uncertainty or buffer deduction. |

## Dmrv

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| ev_photo | 0.97 | 0.9 | 0.995 | probability | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Load, flame-curtain, quench and char photos. |
| ev_temp_log | 0.95 | 0.85 | 0.99 | probability | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Thermocouple / IR log; most hardware-dependent element. |
| ev_feed_weight | 0.97 | 0.9 | 0.995 | probability | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Isometric module requires measured feedstock mass per batch. |
| ev_char_weight | 0.97 | 0.9 | 0.995 | probability | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Isometric module requires measured biochar mass per batch. |
| ev_geotag | 0.98 | 0.93 | 0.998 | probability | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| ev_timestamp | 0.99 | 0.95 | 0.999 | probability | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| evidence_remediation_frac | 0.3 | 0 | 0.6 | share of incomplete batches recovered by re-submission | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| quality_rejection_frac | 0.02 | 0.005 | 0.06 | share of batches failing quality (H/Corg, lab, visual char quality) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| audit_rejection_frac | 0.01 | 0 | 0.03 | share disallowed at verification sampling | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lab_sample_frac | 0.05 | 0.02 | 0.1 | share of batches lab-sampled | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

## Supply

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| village_dry_biomass_t_per_season | 300 | 120 | 600 | t dry surplus residue / village / season | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Residue left after fodder and fuel use. |
| farmer_supply_share | 0.35 | 0.15 | 0.6 | share of available residue actually supplied | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Sensitive to payment reliability. Phase 2 links this to payment lag. |
| farmers_per_village | 150 | 80 | 300 | farmers | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| harvest_seasons_per_year | 2 | 1 | 2 | seasons (kharif, rabi) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| collection_radius_km | 10 | 5 | 20 | km | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| avg_haul_km | 8 | 4 | 15 | km (village → site) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| biomass_cover_days_target | 7 | 3 | 14 | days of feedstock on site | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

## People

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| operators_per_kiln | 3 | 2 | 4 | operators / kiln / shift | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| trained_operator_availability | 0.9 | 0.75 | 0.98 | share of shifts with a trained lead operator | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| operator_attrition_monthly | 0.04 | 0.02 | 0.08 | share / month | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| training_weeks_to_full | 3 | 2 | 6 | weeks | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| new_operator_productivity | 0.6 | 0.4 | 0.8 | share of full productivity in week 1 | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| new_operator_evidence_penalty | 0.1 | 0.05 | 0.2 | extra evidence-failure probability in first month | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

## Economics

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| biomass_price_inr_per_kg | 2 | 1.7 | 2.5 | ₹ / kg raw biomass (as received) | 🟢 PUBLIC | Public reporting on Banni (Kutch) Kon-Tiki project: Newslaundry (Sep 2026), Mongabay (Aug 2026) | Public anchor ₹1.7-2.2/kg paid to village committees; high allows for inflation and competition. |
| operator_pay_inr_per_batch | 800 | 500 | 1,200 | ₹ / batch (whole crew) | 🟠 ASSUMPTION – VERIFY | Analyst estimate | ≈3 operators at rural day-wage, 1.5 batches/day. |
| partner_fee_inr_per_kg_biochar | 10 | 8 | 12 | ₹ / kg biochar | 🟢 PUBLIC | Public reporting on Banni (Kutch) Kon-Tiki project: Newslaundry (Sep 2026), Mongabay (Aug 2026) | CALIBRATION ANCHOR ONLY (partner-implemented model). Compare with the direct-ops cost per kg biochar; not added to the cost stack. |
| water_l_per_batch | 500 | 300 | 800 | L / burn | 🟢 PUBLIC | Public reporting on Banni (Kutch) Kon-Tiki project: Newslaundry (Sep 2026), Mongabay (Aug 2026) | Public anchor ~500 L per burn. |
| water_cost_inr_per_l | 0.12 | 0.05 | 0.3 | ₹ / L (tanker) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| transport_inr_per_t_km | 15 | 8 | 25 | ₹ / t-km (tractor-trolley) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kiln_capex_inr | 80,000 | 40,000 | 150,000 | ₹ / kiln | 🟠 ASSUMPTION – VERIFY | Analyst estimate; Schmidt 2016 reports €30 (soil pit) to €5,000 per kiln |  |
| kiln_life_years | 3 | 2 | 5 | years | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| site_setup_inr | 300,000 | 150,000 | 600,000 | ₹ / site | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Scales, water storage, shade, fencing, signage. |
| relocation_cost_inr | 50,000 | 20,000 | 100,000 | ₹ / move | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| dmrv_device_inr_per_kiln | 25,000 | 15,000 | 40,000 | ₹ / kiln (phone | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| dmrv_platform_inr_per_year | 4,000,000 | 2,000,000 | 8,000,000 | ₹ / year | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lab_test_inr_per_sample | 6,000 | 3,000 | 12,000 | ₹ / sample | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| verification_inr_per_year | 6,000,000 | 3,000,000 | 12,000,000 | ₹ / year (VVB) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| registry_fee_usd_per_t | 1 | 0.3 | 2 | USD / credit issued | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| rating_fee_inr_per_year | 1,500,000 | 500,000 | 3,000,000 | ₹ / year | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| supervisor_inr_per_month | 35,000 | 25,000 | 50,000 | ₹ / supervisor / month (loaded) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| supervisors_per_site | 1 | 1 | 2 | supervisors / site | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| program_overhead_inr_per_year | 20,000,000 | 10,000,000 | 40,000,000 | ₹ / year (cluster managers | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| biochar_return_inr_per_t | 500 | 300 | 1,000 | ₹ / t biochar returned | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Public: most biochar is returned free to the farmers who supplied residue. |
| community_benefit_inr_per_net_t | 250 | 0 | 800 | ₹ / net tCO2e | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Disclosed benefit-share on top of biomass payments. Treated as part of the integrity moat. |
| credit_price_usd | 120 | 90 | 160 | USD / tCO2e | 🟢 PUBLIC | Public reporting on Banni (Kutch) Kon-Tiki project: Newslaundry (Sep 2026), Mongabay (Aug 2026) | Public anchor: pilot credits sold at ~$120. Low/high range is an analyst estimate. |
| inr_per_usd | 88 | 84 | 92 | ₹ / USD | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| production_to_issuance_months | 3 | 2 | 6 | months | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| issuance_to_cash_months | 1 | 0 | 3 | months | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| payment_sla_days | 14 | 7 | 30 | days (target village payment lag) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

⚙️ = solver lever in the "what has to be true" analysis.

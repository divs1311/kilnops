# Assumptions table

> Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.

Auto-generated from `assumptions.yaml` by `tools/build_assumptions_table.py`. Do not edit by hand.

**218 parameters**: 🟢 PUBLIC 5, 🔵 LITERATURE 15, 🟠 ASSUMPTION – VERIFY 198


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

## Network

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| biomass_availability_factor | 1 | 0.7 | 1 | share of planned kiln-days with feedstock on hand | 🟠 ASSUMPTION – VERIFY | Analyst estimate | 1.0 = no stockouts. Used in the biomass-shock scenario. |

## Carbon Accounting

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| ch4_ef_dry_g_per_kg | 5 | 2 | 8 | g CH4/kg biochar at moisture ≤ dry threshold | 🔵 LITERATURE | Lotz & Schmidt 2026, 'Methane Emission from Artisanal Biochar Production – A White Paper', the Biochar Journal, pp 86-110 | Lotz & Schmidt 2026: <5 g/kg at ≤15% moisture. |
| ch4_ef_wet_g_per_kg | 30 | 20 | 50 | g CH4/kg biochar at moisture ≥ wet threshold | 🔵 LITERATURE | Lotz & Schmidt 2026 (up to 10x at ≥25% moisture); Schmidt 2016 mean 30 |  |
| moisture_dry_threshold | 0.15 | 0.12 | 0.18 | fraction | 🔵 LITERATURE | Lotz & Schmidt 2026, 'Methane Emission from Artisanal Biochar Production – A White Paper', the Biochar Journal, pp 86-110 |  |
| moisture_wet_threshold | 0.25 | 0.22 | 0.3 | fraction | 🔵 LITERATURE | Lotz & Schmidt 2026, 'Methane Emission from Artisanal Biochar Production – A White Paper', the Biochar Journal, pp 86-110 |  |

## Synthetic Data

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| arch_strong_sites | 8 | 8 | 8 | sites | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_average_sites | 12 | 12 | 12 | sites | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_biomass_sites | 5 | 5 | 5 | sites | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_mrvweak_sites | 5 | 5 | 5 | sites | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_strong_supply_ratio | 1.35 | 1.2 | 1.5 | supply capacity ÷ full demand | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_average_supply_ratio | 1.15 | 1 | 1.3 | supply capacity ÷ full demand | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_biomass_supply_ratio | 0.72 | 0.6 | 0.85 | supply capacity ÷ full demand | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_mrvweak_supply_ratio | 1.15 | 1 | 1.3 | supply capacity ÷ full demand | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_strong_evidence_fail_mult | 0.6 | 0.4 | 0.8 | × per-element failure probability | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_average_evidence_fail_mult | 1 | 1 | 1 | × per-element failure probability | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_biomass_evidence_fail_mult | 1 | 0.8 | 1.2 | × per-element failure probability | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_mrvweak_evidence_fail_mult | 2.6 | 2 | 3.5 | × per-element failure probability | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_strong_productivity | 1 | 0.95 | 1.05 | × batches per kiln-day | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_average_productivity | 0.94 | 0.9 | 1 | × batches per kiln-day | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_biomass_productivity | 0.92 | 0.85 | 1 | × batches per kiln-day | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_mrvweak_productivity | 0.9 | 0.85 | 1 | × batches per kiln-day | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_strong_moisture | 0.12 | 0.1 | 0.14 | mean feedstock moisture | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_average_moisture | 0.14 | 0.12 | 0.16 | mean feedstock moisture | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_biomass_moisture | 0.17 | 0.14 | 0.2 | mean feedstock moisture | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_mrvweak_moisture | 0.15 | 0.12 | 0.18 | mean feedstock moisture | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_strong_return_completion | 0.95 | 0.9 | 1 | share of biochar returned | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_average_return_completion | 0.86 | 0.8 | 0.92 | share of biochar returned | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_biomass_return_completion | 0.78 | 0.7 | 0.85 | share of biochar returned | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| arch_mrvweak_return_completion | 0.8 | 0.7 | 0.9 | share of biochar returned | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| late_payer_start_day | 60 | 45 | 120 | day of 2027 when payments start running late | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| late_payer_lag_days | 48 | 30 | 60 | days mean payment lag once late | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| late_payer_end_day | 200 | 160 | 240 | day of 2027 when the payment backlog is cleared | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| normal_payment_lag_days | 9 | 5 | 14 | days mean payment lag | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| trust_window_start_days | 42 | 35 | 49 | days before today (window start) | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice | Villages react to payment lag on deliveries made 4-6 weeks earlier. |
| trust_window_end_days | 28 | 21 | 35 | days before today (window end) | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| trust_sensitivity | 0.55 | 0.3 | 1 | supply drop per SLA-multiple of excess lag | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| trust_floor | 0.4 | 0.3 | 0.6 | minimum supply willingness | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| trust_recovery_per_day | 0.006 | 0.003 | 0.02 | willingness regained per day once paid on time | 🟠 ASSUMPTION – VERIFY | Synthetic-data design choice |  |
| supply_index_jan | 1.1 | 0.9 | 1.3 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Cotton / pigeon-pea stalk clearing. |
| supply_index_feb | 1.05 | 0.9 | 1.2 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| supply_index_mar | 1.2 | 1 | 1.4 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| supply_index_apr | 1.3 | 1.1 | 1.5 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Rabi peak. |
| supply_index_may | 1.05 | 0.8 | 1.2 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| supply_index_jun | 0.5 | 0.3 | 0.7 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| supply_index_jul | 0.2 | 0.1 | 0.4 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| supply_index_aug | 0.2 | 0.1 | 0.4 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| supply_index_sep | 0.5 | 0.3 | 0.8 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| supply_index_oct | 1.3 | 1.1 | 1.5 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Kharif peak. |
| supply_index_nov | 1.3 | 1.1 | 1.5 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| supply_index_dec | 1.2 | 1 | 1.4 | index | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| dry_batch_cv | 0.1 | 0.05 | 0.2 | coefficient of variation | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| yield_sd | 0.03 | 0.02 | 0.05 | absolute SD of yield | 🟠 ASSUMPTION – VERIFY | Schmidt et al. 2016 (±5% across feedstocks; within-feedstock assumed narrower) |  |
| peak_temp_mean_c | 700 | 650 | 750 | °C | 🔵 LITERATURE | Schmidt et al. 2016 (680-750 °C main zone) |  |
| peak_temp_sd_c | 35 | 20 | 60 | °C | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| new_operator_temp_penalty_c | 45 | 20 | 80 | °C lower peak temp in first month | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| operator_vacancy_days | 6 | 2 | 14 | days to backfill a leaver | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| biochar_return_interval_days | 14 | 7 | 30 | days between return runs | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| operator_pay_interval_days | 7 | 7 | 14 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| villages_per_location | 11 | 6 | 20 | villages within radius per site location | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

## Levers

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| lever_dmrv_step_pp | 5 | 2 | 8 | pp pass-rate gain | 🟠 ASSUMPTION – VERIFY | Analyst estimate | QA review desk, thermocouple upgrade, evidence refresher training. |
| lever_dmrv_cost_inr | 6,000,000 | 3,000,000 | 12,000,000 | ₹ / year | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lever_kilns_added | 45 | 15 | 90 | kilns (3 sites) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lever_kilns_from_month | 4 | 3 | 7 | month index online | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lever_extra_op_days_per_month | 2 | 1 | 3 | extra days in non-monsoon months | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Covered feedstock storage + relief crews. |
| lever_op_days_cost_inr_per_site | 150,000 | 80,000 | 300,000 | ₹ / site / year fixed | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lever_drying_cost_inr_per_site | 100,000 | 50,000 | 200,000 | ₹ / site (drying yard | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lever_drying_cost_inr_per_t_dry | 150 | 80 | 300 | ₹ / t dry handled | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lever_second_shift_share | 0.25 | 0.1 | 0.5 | share of kilns on 2 shifts | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lever_second_shift_uplift | 0.6 | 0.4 | 0.9 | extra batches/day ÷ single-shift batches/day | 🟠 ASSUMPTION – VERIFY | Analyst estimate | Below 1.0: night burns are slower and some days lack feedstock. |
| lever_second_shift_fixed_inr_per_kiln | 60,000 | 30,000 | 120,000 | ₹ / kiln / year (lighting | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lever_ramp_months_saved | 2 | 1 | 3 | months earlier to full fleet | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| lever_ramp_cost_inr | 4,000,000 | 2,000,000 | 8,000,000 | ₹ (pre-hiring | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

## Economics

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| dmrv_device_life_years | 2 | 1 | 3 | years | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| site_asset_life_years | 3 | 2 | 5 | years | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

## Kpi Thresholds

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| kpi_utilisation_green | 0.85 | 0.8 | 0.9 | share | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_utilisation_amber | 0.7 | 0.6 | 0.8 | share | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_acceptance_green | 0.9 | 0.88 | 0.95 | share | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_acceptance_amber | 0.82 | 0.75 | 0.88 | share | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_evidence_green | 0.9 | 0.88 | 0.95 | share | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_evidence_amber | 0.8 | 0.75 | 0.88 | share | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_cover_green | 5 | 4 | 7 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_cover_amber | 2 | 1 | 3 | days | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_payment_sla_green | 0.9 | 0.85 | 0.95 | share paid within SLA | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_payment_sla_amber | 0.75 | 0.6 | 0.85 | share paid within SLA | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_return_green | 0.9 | 0.85 | 0.95 | share | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_return_amber | 0.75 | 0.6 | 0.85 | share | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_vs_plan_green | 0.95 | 0.9 | 1 | actual ÷ plan | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_vs_plan_amber | 0.85 | 0.75 | 0.9 | actual ÷ plan | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_attrition_green | 0.04 | 0.03 | 0.05 | monthly share (≤ green) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| kpi_attrition_amber | 0.06 | 0.05 | 0.08 | monthly share (≤ amber) | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

## Pathway

| Parameter | Default | Low | High | Unit | Status | Source | Note |
|---|---:|---:|---:|---|---|---|---|
| pw_cost_usd_low_distributed | 50 | 50 | 50 | USD/t | 🟠 ASSUMPTION – VERIFY | Analyst range; cross-check with this model's ₹/t |  |
| pw_cost_usd_high_distributed | 120 | 120 | 120 | USD/t | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_cost_usd_low_industrial | 90 | 90 | 90 | USD/t | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_cost_usd_high_industrial | 180 | 180 | 180 | USD/t | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_cost_usd_low_regenag | 15 | 15 | 15 | USD/t | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_cost_usd_high_regenag | 45 | 45 | 45 | USD/t | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_cost_usd_low_erw | 120 | 120 | 120 | USD/t | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_cost_usd_high_erw | 300 | 300 | 300 | USD/t | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_permanence_distributed | 4 | 3 | 4 | score | 🔵 LITERATURE | Persistence factor 0.65-0.89 (IPCC 2019) |  |
| pw_permanence_industrial | 4 | 4 | 5 | score | 🟠 ASSUMPTION – VERIFY | Controlled high-temperature pyrolysis |  |
| pw_permanence_regenag | 2 | 1 | 2 | score | 🟠 ASSUMPTION – VERIFY | Soil carbon is reversible |  |
| pw_permanence_erw | 5 | 4 | 5 | score | 🟠 ASSUMPTION – VERIFY | Geologic carbonate / bicarbonate storage |  |
| pw_time_to_cash_distributed | 5 | 4 | 5 | score | 🟠 ASSUMPTION – VERIFY | Per-batch dMRV, months from burn to issuance |  |
| pw_time_to_cash_industrial | 3 | 2 | 3 | score | 🟠 ASSUMPTION – VERIFY | Plant build 12-24 months first |  |
| pw_time_to_cash_regenag | 2 | 1 | 2 | score | 🟠 ASSUMPTION – VERIFY | Multi-year sampling / modelling cycles |  |
| pw_time_to_cash_erw | 1 | 1 | 2 | score | 🟠 ASSUMPTION – VERIFY | Slow weathering, measurement lag |  |
| pw_delivery_risk_distributed | 3 | 2 | 3 | score (5 = low risk) | 🟠 ASSUMPTION – VERIFY | Biomass, labour, evidence across many sites |  |
| pw_delivery_risk_industrial | 3 | 2 | 4 | score (5 = low risk) | 🟠 ASSUMPTION – VERIFY | Commissioning, uptime, feedstock contracts |  |
| pw_delivery_risk_regenag | 3 | 2 | 3 | score (5 = low risk) | 🟠 ASSUMPTION – VERIFY | Practice adoption, reversal |  |
| pw_delivery_risk_erw | 2 | 1 | 3 | score (5 = low risk) | 🟠 ASSUMPTION – VERIFY | Measurement uncertainty, rock logistics |  |
| pw_mrv_simplicity_distributed | 2 | 2 | 3 | score (5 = simplest) | 🟠 ASSUMPTION – VERIFY | dMRV on every batch, 450 units |  |
| pw_mrv_simplicity_industrial | 4 | 4 | 5 | score (5 = simplest) | 🟠 ASSUMPTION – VERIFY | Metered, few units |  |
| pw_mrv_simplicity_regenag | 2 | 1 | 2 | score (5 = simplest) | 🟠 ASSUMPTION – VERIFY | Soil sampling + models |  |
| pw_mrv_simplicity_erw | 1 | 1 | 2 | score (5 = simplest) | 🟠 ASSUMPTION – VERIFY | Field geochemistry |  |
| pw_cobenefits_distributed | 5 | 4 | 5 | score | 🟠 ASSUMPTION – VERIFY | Avoided residue burning, farmer income, biochar returned free |  |
| pw_cobenefits_industrial | 3 | 3 | 4 | score | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_cobenefits_regenag | 4 | 4 | 5 | score | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_cobenefits_erw | 3 | 3 | 4 | score | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_scalability_distributed | 3 | 2 | 4 | score | 🟠 ASSUMPTION – VERIFY | Labour, biomass logistics, supervision span |  |
| pw_scalability_industrial | 3 | 2 | 4 | score | 🟠 ASSUMPTION – VERIFY | Capex, permitting |  |
| pw_scalability_regenag | 5 | 4 | 5 | score | 🟠 ASSUMPTION – VERIFY | Acreage-driven |  |
| pw_scalability_erw | 4 | 3 | 4 | score | 🟠 ASSUMPTION – VERIFY | Rock supply, spreading logistics |  |
| pw_weight_cost | 0.25 | 0 | 1 | weight | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_weight_permanence | 0.2 | 0 | 1 | weight | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_weight_time_to_cash | 0.15 | 0 | 1 | weight | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_weight_delivery_risk | 0.15 | 0 | 1 | weight | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_weight_mrv_simplicity | 0.1 | 0 | 1 | weight | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_weight_cobenefits | 0.1 | 0 | 1 | weight | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |
| pw_weight_scalability | 0.05 | 0 | 1 | weight | 🟠 ASSUMPTION – VERIFY | Analyst estimate |  |

⚙️ = solver lever in the "what has to be true" analysis.

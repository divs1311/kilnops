# REVIEW: self-review of KilnOps

> Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.

Figures quoted in the README, memo, SOP and talk track are regenerated from the model by `tools/build_docs.py`. `tests/test_docs.py` fails if any document drifts from the current model output. Current values are in `docs/key_numbers.json`.

## Self-review checklist (done before submission)

| Check | How | Result |
|---|---|---|
| Every number in the memo, README, SOP and talk track matches the model | Rendered from templates; `test_docs_are_fresh` re-renders and compares with the files on disk | Pass |
| No parameter hard-coded outside `assumptions.yaml` | Model, app and docs read the yaml; scenario keys validated by tests; thresholds, lever costs and generator settings are all yaml entries | Pass (display-only constants such as chart colours excepted) |
| Claims about Varaha restricted to the brief's public context | Manual pass over every file. Used only: ~450 Kon-Tiki kilns at mobile sites in western India; Rainbow methodology with mandatory dMRV; first issuance Jan 2027; >100k t planned for 2027; Banni anchors (₹1.7–2.2/kg biomass, ~₹10/kg biochar partner fee, ~500 L/burn, ~$120 pilot price); ~170–175k farmers (TechCrunch); public offtakes for the pathway context | Pass. The BeZero rating and CEO quote are not used, to keep the claims minimal |
| Benefit-sharing framed as a moat, not an accusation | Ledger page, memo risk 3 and SOP §3 and §8 frame on-time payment as a delivery control and a buyer and rating asset; the Banni figures appear only as calibration anchors | Pass |
| Target never called "unrealistic" | Every gap is expressed as a required lever value, a contingency or a cost per tonne | Pass |
| Disclaimer everywhere | `test_disclaimer_everywhere` (docs) and `test_page_runs_and_carries_disclaimer` (every app page) | Pass |
| Uncertainty surfaced | P10/P50/P90, P(≥100k), tornado, drift decomposition, two calibration lenses | Pass |

## What's strong

- **The "what has to be true" logic is explicit and exact.** Net tonnes are affine in each lever, so the solver is closed-form and tested to 0.5%. It also checks results against physical limits (cycle-time ceiling, kiln fill) instead of returning impossible values without comment.
- **Two lenses, honestly separated.** Literature defaults give the calibration risk. The plan-implied design point is what the control tower tracks. Defaults were not tuned to hit the target; the plan scenario is labelled as an inference.
- **Decision-ranked levers.** The ₹-per-incremental-tonne ranking turns the analysis into a priority call: recovering rejected tonnes costs far less than producing new ones.
- **A discoverable causal story.** The ledger page lets a reviewer find the late-paying site and see supply fall weeks later, from the data rather than from a caption.
- **Integrity treated as operations.** Payment SLA, return completion and the published ledger are KPIs with owners and thresholds.
- **Reproducible end to end.** A seeded generator, a single yaml, regenerated docs and one command per step.

## What a sceptical COO would attack

1. **"Your design point is reverse-engineered from our target."** True by construction. It is labelled *plan-implied*, and the literature lens sits next to it. The real defence is the week-1 plan: measure throughput and replace the inference.
2. **"P50 well below target? Your ranges are pessimistic."** Partly fair. Most nominal values sit at the favourable end of their ranges, which is a modelling choice; the drift chart shows exactly which assumptions cause it. Independent sampling also understates correlated downside, so the true spread is probably wider in *both* directions. Ranges should be re-fit on real data.
3. **"Synthetic data proves nothing."** Agreed for levels. It proves the control tower would *detect* the failure modes that matter. The schema is designed so real batch logs can replace the parquet files.
4. **"Methodology numbers are guesses."** Persistence, CH₄ treatment and buffer come from literature ranges, not from the text of the methodology in use. They are tagged and quantified as a calibration risk, and confirming them is a dated Q1 action.
5. **"Lever costs are deterministic and don't interact."** Each lever is costed alone against the design point. Stacked levers interact, for example a second shift needs more feedstock, which strains supply. The "% of gap" figures should not simply be added up.
6. **"Supply isn't in the tonne model."** The bridge treats feedstock availability as one factor. The payment-to-supply feedback lives only in the synthetic data and the KPIs, not in the forecast.
7. **"Economics are thin."** Feedstock dominates, and margin at the anchor price is small. Financing cost, tax, price variance across buyers and the biochar's value to farmers are excluded. The partner-fee comparison shows the cost structure could differ a lot under a partner-implemented model.
8. **"The pathway matrix flatters distributed biochar."** The default weights favour time-to-cash and co-benefits. Users can change them, and with cost-only weights regen-ag ranks first. The matrix is a discussion aid, not a verdict.

## What I'd fix with one more day

- **Correlated Monte Carlo.** Add a shared weather factor (or a Gaussian copula) linking operating days, feedstock availability and moisture, and report how the P10 moves.
- **Supply feedback in the forecast.** Make feedstock availability depend on the payment SLA through the lag estimated from the ledger, so a payment backlog shows up in forecast tonnes.
- **Bayesian throughput update.** As batch logs arrive, update the batch-size and batches-per-day distributions weekly. The control tower then shows P50 tightening.
- **Interacting lever stacks.** Compute the cost curve of the cheapest *combination* of levers that reaches P50 = 100k, instead of costing levers one at a time.
- **Stochastic credit price in the economics.** A joint tonnes × price distribution for revenue and working capital.
- **An as-of date in the app.** Replay the year week by week, so the exec summary shows what the COO would have known in March.
- **CI.** A GitHub Actions workflow to run tests and rebuild the docs, plus a smoke deploy to Streamlit Cloud. The geographic map was not checked offline, because Plotly loads its outlines from a CDN.

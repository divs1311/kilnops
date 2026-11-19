# KilnOps: a delivery control tower for distributed biochar

> Independent analysis using public information and synthetic data. Not affiliated with or endorsed by Varaha.

**Question:** can a ~450-kiln distributed Kon-Tiki network, modelled on Agnisparsh, deliver 100,000 tCO₂e of removals in 2027? What has to be true, which levers matter most, and what should ops do in Q1 2027?

**Status:** Phase 1 (assumptions and "what has to be true") is complete. See [`PHASE1_FINDINGS.md`](PHASE1_FINDINGS.md). The full README arrives in Phase 5.

```bash
pip install -r requirements-dev.txt
python -m tools.build_assumptions_table   # regenerate docs/assumptions_table.md
python -m tools.phase1_report             # solver table, charts, key numbers
pytest -q
```

Every numeric input lives in [`assumptions.yaml`](assumptions.yaml), each with a source and a status: PUBLIC, LITERATURE or ASSUMPTION – VERIFY.

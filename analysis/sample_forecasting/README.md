# Sample forecasting investigation

Research-only analysis of the 25 labeled sample requests. This is not the final submission pipeline.

- `scripts/` — reproducible investigations and audits.
- `reports/` — findings and limitations.
- `artifacts/` — generated CSV, JSON, and text evidence, including the 90-date baseline.

From the repository root:

```text
python analysis/sample_forecasting/scripts/investigate.py
python analysis/sample_forecasting/scripts/audit.py
python analysis/sample_forecasting/scripts/latent_budgets.py
```

Start with [the initial report](reports/REPORT.md), then [the latent-budget follow-up](reports/LATENT_BUDGET_REPORT.md). The scripts read only participant-facing data in `dataset/` and keep results in `artifacts/`.

The focused [three-case verification gate](reports/LEDGER_GATE.md) records the earlier pause and subsequent user acceptance of an explicit payroll persistence policy. [Complete ledgers](reports/LEDGER_VERIFICATION.md) and their CSV/JSON files live under `artifacts/ledger_verification/`. The representative implementation lives separately in the root `prototype/` folder.

```text
python analysis/sample_forecasting/scripts/verify_ledgers.py
python -m unittest discover -s analysis/sample_forecasting/scripts -p test_ledger_verification.py -v
```

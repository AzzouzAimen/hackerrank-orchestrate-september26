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

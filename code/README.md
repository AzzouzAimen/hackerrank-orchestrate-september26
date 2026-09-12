# Buy or Wait code and research

The shared implementation lives directly in this directory: `evidence.py` defines
the seven semantic fact types, `finance.py` resolves evidence and projects cash with
Decimal, and `plans.py` builds, checks, and ranks payment plans. `evidence.schema.json`
is the canonical exported contract. Python already has a standard-library module
named `code`, so import these modules from a process launched in this directory (or
with this directory on `PYTHONPATH`), rather than importing a `code` package.

`main.py` currently offers an explicit replay of the five reviewed representative
cases. It uses the trusted bundles in `prototype/facts/` and writes research artifacts
only. The full-dataset prediction command and model integration belong to later work.

`evaluation/main.py` gives a read-only summary of saved shadow experiments. The final
full-run usage report remains pending in `evaluation/usage_report.md` until that run
exists; no costs or metrics have been fabricated for it.

From the repository root:

```text
python -m pip install -r code/requirements.txt
python code/main.py --help
python code/main.py representative
python code/evaluation/main.py saved-summary
python -m unittest discover -s code/tests -t code -v
```

Research and audit tests run from `code/`:

```text
cd code
python -m unittest prototype.test_extraction_experiment prototype.test_evaluation_audit -v
```

The independent ledger-audit tests run from `code/analysis/sample_forecasting/scripts`:

```text
python -m unittest test_ledger_verification -v
```

`prototype/` holds reviewed fact bundles, representative and extraction research
runners, reports, annotations, and saved API responses. `analysis/` holds sample
forecasting research. The original source-response artifacts, trusted facts, and
representative output remain unchanged. See the [corrected extraction audit](prototype/reports/EVALUATION_AUDIT_V2.md)
and [unexecuted next-experiment proposal](prototype/reports/NEXT_EXPERIMENT_V2.md).

# Shared Buy or Wait implementation

`buy_or_wait/` is the single implementation of the strict seven-fact evidence model,
deterministic resolver/Decimal financial engine, and payment-plan generation,
verification, ranking, and output validation. These modules were moved byte-for-byte
from `prototype/`; the arithmetic, policy, recurrence, and trusted facts are unchanged.

The package is named `buy_or_wait` because `code` is a Python standard-library module.
Do not add `code/__init__.py` or import `code.finance`. The existing empty `main.py`,
`evaluation/main.py`, and `evaluation/usage_report.md` starter files remain untouched.
This relocation does not create a full-dataset or submission runner.

From the repository root:

```text
python -m pip install -r code/requirements.txt
python -m unittest discover -s code/buy_or_wait/tests -t code -v
python -m unittest prototype.test_extraction_experiment prototype.test_evaluation_audit -v
python -m prototype.run
```

The representative runner reads the five existing assistant-reviewed reference bundles
from `prototype/facts/`. It remains a research runner; sample labels are used only in
its comparison report. Model-generated facts remain exclusively in evaluation artifacts.
The final command regenerates only representative research artifacts, not output.csv.

The old test command still works through thin compatibility imports:

```text
python -m unittest prototype.test_prototype prototype.test_boundary prototype.test_extraction_experiment prototype.test_evaluation_audit -v
```

Ledger-audit tests remain separate; from `analysis/sample_forecasting/scripts`:

```text
python -m unittest test_ledger_verification -v
```

For an application launched from `code/`, use `from buy_or_wait.finance import resolve`.
Root-level research commands add the sibling `code/` directory via `prototype/__init__.py`.
There is one class/module identity and no second engine implementation in `prototype/`.
The schema artifact is `buy_or_wait/evidence.schema.json`; it is not rewritten by runs.

Reports, reviewed references, representative runner/artifacts, saved model responses,
extraction harness, and annotations stay in `prototype/`. See
[the corrected audit](../prototype/EVALUATION_AUDIT_V2.md) and
[the unexecuted next-experiment proposal](../prototype/NEXT_EXPERIMENT_V2.md).

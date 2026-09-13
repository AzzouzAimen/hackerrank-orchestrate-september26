# Buy or Wait? — runnable submission

This directory is the complete production solution. AI is used only to extract
scoped, provenance-bearing evidence from messages and images. Python validates and
guards the seven-type `EvidenceBundle`, resolves financial state, forecasts the
90-day ledger, generates eligible payment candidates, verifies reserve safety, and
ranks the final recommendation deterministically.

The runtime fails closed when financially material evidence cannot be resolved. Text
and image extraction are separate; the image scope may emit only labeled
`image_financial_value` facts. No prompt or model output can directly choose a plan.

## Requirements

- Python 3.11 or newer
- dependencies from `code/requirements.txt`
- `FEATHERLESS_API_KEY` for fresh inference only
- the provided `dataset/` directory beside `code/`

The key may be set in the process environment. For local use, the runner also reads
an uncommitted `.env` beside the repository root or code directory. Secrets are never
packaged.

## Commands

Run from the directory that contains both `code/` and `dataset/`:

```text
python -m pip install -r code/requirements.txt
python code/main.py preflight
python -m pytest code/tests -q
python code/main.py run --artifact run_artifacts/final --workers 4
python code/main.py audit --artifact run_artifacts/final --output output.csv
```

`run` writes `output.csv` beside `dataset/`. It records raw requests/responses,
validated composed bundles, decisions, and usage under the selected artifact path.
Reusing that path resumes completed requests; using a new path performs fresh
inference. Saved artifacts are not required by production and are not included in
`code.zip`.

## Production modules

- `main.py`, `submission_runner.py`: command line and orchestration
- `input_preparation.py`: same-user, request-time evidence selection
- `semantic_extractor.py`, `live_extraction.py`, `scoped_extraction.py`: model calls,
  scoped extraction, recording, and deterministic composition
- `evidence.py`, `evidence.schema.json`: strict seven-type semantic contract
- `target_identity.py`, `semantic_boundary.py`: identity validation, guards, and
  abstention
- `finance.py`: state resolution, recurrence, FX, and 90-day projection
- `plans.py`: candidate generation, safety verification, ranking, and output schema
- `submission_preflight.py`, `submission_audit.py`: no-model validation and persisted
  run audit
- `evaluation/usage_report.md`: actual accounting for the accepted 250-request run

Known limitation: semantic extraction is model-dependent. Schema/identity validation,
scoped image restrictions, conservative cash rules, and fail-closed blockers limit
the financial impact of unusable or ambiguous extraction rather than claiming perfect
semantic accuracy.

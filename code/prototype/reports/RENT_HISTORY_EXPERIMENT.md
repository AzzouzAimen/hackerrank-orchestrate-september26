# Controlled rent-history experiment

Integration follow-up: future runs now use 32768 tokens, a 600-second timeout and
omit API JSON mode, while retaining strict local validation. See
[the integration diagnostic](INTEGRATION_BUDGET_RESULT.md). The frozen settings
described below document the original experiment; new manifests identify the new
integration version. The original completed run is documented in RENT_HISTORY_RESULT.md.

Implementation ready; live experiment has not been executed. This operationalizes
the post-audit review and refines NEXT_EXPERIMENT_V2.md without changing old artifacts.

Run from `code/`. Prepare a complete offline plan without reading credentials:

```text
python -m prototype.rent_history_experiment --output prototype/extraction_artifacts/rent_plan.json
```

After a human has approved the conventions below, execute explicitly, using a new
output directory and the actual reviewer identity:

```text
python -m prototype.rent_history_experiment --run --approved-by REVIEWER --output prototype/extraction_artifacts/rent_run_01
```

The approval flag records an actual decision; it must not be supplied on someone's
behalf without that approval. FEATHERLESS_API_KEY uses the existing environment/.env
loader. No model output enters the financial engine or overwrites latest.json.

## Frozen design

Six logical runs alternate control/treatment, with at most one retry per run (12
calls maximum). Both payloads retain rep_user16 as their case ID; arm names occur
only in artifact metadata. The only evidence intervention appends the six reviewed
Monthly rent rows, checked against the current dataset in file order. All original
rows, messages and images are retained. Provider, model, actual SYSTEM_PROMPT,
generated schema, settings and retry correction mechanism come from the existing
extractor unchanged. EXTRACTION_PROMPT.md is not the runtime prompt.

Requests (including image bytes), parsed provider responses, finish reasons, usage,
latencies and errors are retained per attempt. The configured API key is redacted;
authorization headers are never saved. These artifacts contain financial evidence
and should receive the same access protection as the dataset. Original audit files
and historical references remain untouched. Files are created exclusively, and
completed attempts survive a later interrupted run. Do not resume by overwriting
or automatically retry an entire interrupted experiment.

## Human decisions before execution

1. The 12% amendment targets the renewed Monthly rent stream, not event_1442.
   Missing-context control abstention is distinct from wrong targeting.
2. Accept ongoing or unknown scope for the primary targeting comparison; report
   scope separately. Neither invented calendar bounds nor one-cycle limitation
   is supported. No model-calculated absolute amended rent is requested.
3. Image02 Balance Due INR 100000 is linked to event_1442 by metadata. Preserve its
   structured settlement date. Neither gross total nor received amount establishes
   current debt; the historical receipt period does not amend settlement timing.

The manifest records these exact conventions, their hash and the approving human.
This is approval of the rubric, not automatic approval of model facts.

## Measurement and review

summary.json separates first-attempt availability, final availability, retry
recoveries, empty output and provider failure by arm. At least two usable logical
runs per arm are needed for the minimal descriptive comparison. Otherwise the
result is operationally inconclusive. Even adequate availability leaves semantic
review pending. An empty facts array is a valid response; empty content is not.

Use claim_review_template.json to review every attempt against supplied evidence.
Write adjudication to a separate new file. Classify target as correct supported
stream, unsupported balance linkage, ambiguous target, or abstention. Review
percentage, scope, bounds, image typing/target and extras separately. Cite evidence
and identify the reviewer; assistant judgments remain assistant judgments. Correct
targeting plus harmful extras is not whole-bundle success. Do not require exact
reference serialization, and do not automatically treat extras as hallucinations.
Report first-attempt semantic results separately from retry-assisted results.

Treatment success with mislinked controls supports context contribution in this
case. Treatment success with abstaining controls shows improved recoverability.
Both succeeding fails to reproduce the historical error. Both failing semantically
shows that the added context is insufficient. Mixed results warrant a field-level
account, not a forced verdict. Missing outputs can bias usable-only comparisons.

Stop after six logical runs and one review, even if inconclusive. This is not a
statistical reliability estimate or readiness test for trusted integration. Do not
automatically tune prompts, switch models, expand the schema or run more cases.
If context is resolved, a separate pending_credit definition experiment is a
reasonable next question; retain a genuine pending-credit control.

## Corrections retained from the independent review

The current resolver shares a branch for settlement_of and retry_of: the wrong
relationship is a semantic error, but a different cash consequence was not proved
for the saved case. The amount_paid guard cannot independently detect a model's
false current_amount_due label. Independent ledger replay checks arithmetic on
emitted flows, not completeness of those flows or correctness of semantic inputs.

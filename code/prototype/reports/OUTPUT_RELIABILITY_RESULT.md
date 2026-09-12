# Output reliability: high versus low

Follow-up: [budget/API-mode diagnostic](INTEGRATION_BUDGET_RESULT.md) subsequently
found a promising same-model workaround by omitting API JSON mode. Its findings
supersede model switching as the immediate recommendation; this experiment's
historical results remain unchanged.

**Lower reasoning did not restore final JSON in this diagnostic.**

Four calls, high/low/high/low, two per arm, no retries. Each uses the exact saved
rent_run_01/01_control_attempt1_request.json body, changing only reasoning_effort.
The semantic prompt, schema, model, provider, image and other generation settings
remain fixed. This is a single-input availability test, not a rent comparison.

Featherless documents low as supported for this model:
https://webflowcms.featherless.ai/blog/glm-5-3-flash-is-live-on-featherless

| Measure | High | Low |
|---|---:|---:|
| Calls | 2 | 2 |
| Nonempty final content | 0/2 | 0/2 |
| Schema-valid final JSON | 0/2 | 0/2 |
| Nonempty reasoning, empty final | 2/2 | 2/2 |
| Provider exceptions | 0 | 0 |
| Finish reason | stop, stop | stop, stop |
| Completion tokens per call | 1314, 1323 | 605, 429 |
| Latency seconds per call | 35.69, 19.40 | 12.20, 8.10 |

Low used fewer completion tokens and was faster, but neither call produced final
JSON. Cache state differed: first high call had no cached tokens; each later call
reported 6611 cached tokens. Latency differences cannot be attributed solely to effort.

There are no usable outputs to assess semantically. Missing output is not a semantic
failure, a valid empty facts array, or permission to substitute internal reasoning
for final JSON. Full envelopes remain preserved without reproducing reasoning here.

This does not establish population reliability or distinguish a model defect from
provider integration or their interaction. The recorded stop reasons do not establish
token-limit truncation. Low is not a demonstrated stable setting, so the conditional
rent rerun was not triggered.

Smallest next experiment: a tiny availability test of one alternative model supporting
the same multimodal JSON input, preferably on the same provider, preserving evidence,
prompt, schema and compatible generation settings. Disclose any required compatibility
changes. Review usable outputs separately for target and gross-versus-balance mistakes.
A stronger model is a candidate, not a guaranteed remedy. No switch was executed.

Recorded usage: 26444 prompt tokens (19833 cached), 3671 completion tokens, 30115 total.
This is diagnostic usage, not a final-dataset usage report or provider billing total.

Artifacts: [manifest](../extraction_artifacts/output_reliability_01/manifest.json)
and [summary](../extraction_artifacts/output_reliability_01/summary.json), alongside
all four request/response/result sets. Stopped after four calls; no rent rerun,
semantic tuning, financial-engine changes or trusted integration.

# Featherless budget and JSON-mode diagnostic

Increasing the budget alone did not restore output. At the same larger budget,
omitting API response_format produced two valid final JSON bundles out of two;
JSON mode produced zero out of two. This small test supports a provisional
integration workaround, not a guarantee of reliability or proof of server root cause.

The user authorized generous limits and investigation of API integration. Live
model metadata reported 262144 context tokens, 32768 maximum completion tokens,
vision support and active status. Four calls alternated JSON mode / omitted mode
twice, using the original saved control request, 32768 max_tokens, high reasoning,
and a 600-second timeout. No retries. All message, schema and image content stayed
identical; between these two arms only response_format differed.

| Mode | Valid final JSON | Empty final | Completion tokens per call |
|---|---:|---:|---|
| API JSON object mode | 0/2 | 2/2 | 1319, 776 |
| response_format omitted | 2/2 | 0/2 | 2111, 1624 |

All calls returned finish_reason=stop; none raised a provider exception or timed
out. Empty responses ended well below 32768 tokens. This does not support the
configured token cap as the sufficient explanation. Timeout extension was common
to both arms, and none approached either the old or new timeout.

Saved provider envelopes already have empty choices[0].message.content; the client
is not discarding an alternate final-answer field. reasoning is a separate field,
not a substitute for final content. No custom stops, forced minimum token counts,
or unsupported thinking toggles were introduced.

## Applied integration change

Future shadow extraction uses integration_version
featherless-generous-plain-json-v1: 32768 max_tokens, 600-second timeout and no API
response_format parameter. The existing system prompt still requests one JSON
object, and local EvidenceBundle validation remains strict. Empty/malformed output
still fails validation; retry behavior is unchanged. Model, semantic prompt, seven
fact types, images and financial engine are unchanged.

The rent manifest now records integration version and timeout. A future rent run
will use the new profile and must be identified accordingly; it is not a reproduction
of the historical 8192-token JSON-mode configuration. Historical artifacts remain
unchanged. No rent comparison or full-dataset run was executed here.

Both usable diagnostic outputs still mislink the amendment to event_1442 and
misclassify gross 200000 as current debt, despite also extracting balance_due 100000.
One additionally asserts unsupported one_cycle scope. Restored output is not
semantic correctness; model facts remain outside trusted recommendations.

Validation: all four saved requests were compared with the original payload;
only max_tokens and the documented response_format omission differ. Twenty-five
targeted transport/extraction/audit/experiment tests pass, including a mocked-wire
assertion for the new budget, timeout, omitted JSON mode and unchanged system prompt.

Artifacts: [manifest](../extraction_artifacts/integration_budget_01/manifest.json),
[summary](../extraction_artifacts/integration_budget_01/summary.json), and all four
request/response/result sets in that directory. Four inference calls recorded
26442 prompt tokens, 5830 completion tokens and 32272 total tokens, none cached.

Sources: [Featherless completions](https://featherless.ai/docs/completions) documents
max_tokens and message.content; [model metadata](https://featherless.ai/docs/api-reference-models)
documents the output ceiling. Neither source establishes why this deployment
returned empty content with JSON mode; that remains an experimental inference.

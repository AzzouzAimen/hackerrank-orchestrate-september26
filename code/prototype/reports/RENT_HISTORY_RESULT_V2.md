# Rent-history rerun with the provisional plain-JSON profile

Availability is sufficient for this comparison: control 3/3 and treatment 3/3
usable after one control retry. Semantic classification: **mixed/inconclusive**.
Treatment correctly separates the renewed Monthly rent stream in 1/3 runs versus
0/3 controls, but fails separation in the other two. History alone is not a
reliable fix under this extractor. These are descriptive case results, not a
statistically established treatment effect or a general reliability estimate.

## Integration validation and execution

The prior diagnostic envelopes support a provisional trial, not a provider root
cause claim. The runner correctly uses featherless-generous-plain-json-v1:
32768 max_tokens, 600-second timeout, response_format omitted. Final content still
must pass json.loads and EvidenceBundle.model_validate; reasoning is never a
substitute. No blocking client bug was found and no runtime code was changed.
Twenty-five targeted transport, extraction, audit and runner tests passed.

Exactly six logical runs alternated control/treatment, using seven API calls.
Only run3 retried, once. All seven responses ended with finish_reason=stop.
Saved requests match the previous experiment except the approved integration
profile; retry input adds only the existing validation correction. Model,
temperature, seed, high reasoning, semantic prompt/schema, images, rubric and
six treatment rows are unchanged. Historical artifacts were hash-checked and
preserved. No financial engine execution or trusted fact integration occurred.

## Availability first

| Measure | Control | Treatment |
|---|---:|---:|
| First-attempt usable | 2/3 | 3/3 |
| Retry recoveries | 1/1 retry | 0; no retry |
| Final usable | 3/3 | 3/3 |
| API attempts | 4 | 3 |
| Empty final content | 0 | 0 |
| Nonempty schema-invalid | 1 | 0 |
| Provider exceptions | 0 | 0 |
| Mean attempt latency, seconds | 20.49 | 112.69 |
| Median attempt latency, seconds | 20.36 | 33.17 |
| Attempt latency range, seconds | 15.80–25.43 | 18.17–286.73 |
| Prompt tokens | 26,529 | 21,846 |
| Completion tokens | 8,156 | 6,106 |
| Total tokens | 34,685 | 27,952 |
| Cached prompt tokens (included above) | 13,220 | 7,282 |

Total usage: 48,375 prompt + 14,262 completion = 62,637 tokens, including
20,502 cached prompt tokens. These are recorded experiment usage, not billing.
The schema-invalid attempt supplied a money object with null value together with
12 percent, violating the exclusive amount-or-percentage rule. Strict validation
rejected it; the normal retry recovered. It is excluded from semantic counts.

Compared with rent_run_01, first-attempt usable rose from 3/6 to 5/6, final usable
from 3/6 to 6/6, and empty attempts fell from 5/9 to 0/7. The arms improved from
control 1/3 and treatment 2/3 final usable to 3/3 each. This supports the profile
as usable for this small evaluation. It is a historical comparison, not a concurrent
randomized transport test. One treatment response took 286.73 seconds, exceeding
the old 180-second timeout; the extended timeout matters operationally here.
We cannot attribute every gain to response_format omission alone or prove what
would have happened under the old timeout. No server root cause is established.

## Semantic review of all six usable bundles

| Run | Arm / attempt | Rent amendment target | Scope | False gross debt |
|---|---|---|---|---|
| 1 | Control / first | Wrong explicit event_1442 | unknown, accepted | Yes |
| 2 | Treatment / first | Correct Monthly rent selector, no explicit IDs | unknown, accepted | Yes |
| 3 | Control / retry | Wrong explicit event_1442 | unknown, accepted | No |
| 4 | Treatment / first | Broad rent selector includes both streams | one_cycle, unsupported | Yes |
| 5 | Control / first | Wrong event_1442, uncertain confirmation | unknown, accepted | Yes |
| 6 | Treatment / first | Wrong explicit event_1442 | ongoing, accepted | Yes |

All six extract 12% correctly with money=null and no calculated absolute amended
rent. All six leave amendment calendar bounds null. Control run5's uncertainty
does not erase its unsupported explicit balance linkage, although it can affect
downstream applicability. No control abstains from naming a target.

Treatment run2 is a real targeting success: its Monthly rent selector excludes
Outstanding rent balance. Run4 leaves the description null; the existing target
matcher then includes both rent descriptions, so this is ambiguous/broad targeting,
not successful separation or safe abstention. Run6 explicitly chooses event_1442;
its separate correct rent-history status fact does not repair the amendment.
The observed treatment failures are not both the earlier exact pattern of naming
Monthly rent while explicitly selecting event_1442; their encodings differ.

Balance Due INR100000 is correctly linked to event_1442 in all six bundles.
Amount Received INR100000 is correctly emitted as amount_paid in 5/6, omitted
in run3's retry. Gross INR200000 is falsely current_amount_due in control 2/3
and treatment 3/3. Correct OCR alongside false financial typing is not a correct
whole-bundle interpretation. No output substitutes the historical 2022 receipt
period for the settlement date.

Other consequential assertions: run1 sets payment_date to event/receipt date
2023-08-11 instead of structured settlement 2023-08-16. Runs2/3/4/5 retain the
settlement date; run6 emits no date override. Run4 incorrectly groups event_1442
into an ongoing recurring rent status with the six historical rows, and asserts
unsupported one_cycle amendment duration. Its confirmed salary continuity is an
evaluation ambiguity: history supports recurrence but the rubric does not settle
future confirmation strength. Other salary stream emissions preserve uncertainty.
No usable output emits pending_credit or an invented future salary amount/date.
Observed historical stream start dates and supplied event-date bounds are not
invented lease bounds. Null future-amount restatements alongside a known image
balance are redundant and do not establish safe bundle composition.

Both arms consistently extract 12% and the correct balance. Control consistently
mislinks rent, but differs on confirmation, date and image extras. Treatment is
inconsistent on target, duration and salary certainty, while consistently emitting
false gross debt. Neither arm has consistent complete semantic correctness.
First-attempt-only semantics give targeting control 0/2, treatment 1/3; including
the control retry gives 0/3 versus 1/3. The conclusion remains mixed.

## What the evidence establishes

- Proven within these saved runs: six usable outputs, zero empty finals, strict
  validation retained, one retry recovery, one correct treatment target, and five
  gross-as-debt errors. Every usable fact has an assistant review under the approved
  rubric; these judgments are not independent human ground truth.
- Supported: the provisional integration provides a usable experimental surface;
  restoring history can help identification but does not reliably separate streams.
  Repeated semantic failures remain even with complete treatment context.
- Uncertain: broad availability, provider root cause, magnitude of the history
  effect, and whether definitions or model capability primarily limit accuracy.

## Single recommended next experiment — proposed, not executed

Choose **1: integration is now usable → one targeted semantic/prompt experiment**.
Rank failure clusters by repetition, consequence and ease of isolation:

1. Gross versus outstanding debt: 5/6, across both arms and earlier diagnostics;
   can overstate the obligation by INR100000; one field-definition change isolates it.
2. Stream versus event targeting: five failures of separation out of six, including
   broad run4 targeting; potentially amends the wrong liability; important but
   context and target representation create more interacting interpretations.
3. Scope and timing: one unsupported one_cycle and one wrong payment date; materially
   changes duration/reservation timing but less repeated in this rerun.
4. Salary certainty: one ambiguous confirmed-continuity assertion; pending_credit
   was absent here, so that historical cluster is not prioritized by this case.

Change exactly one variable: append one general definition sentence to the semantic
system prompt: “When an image separately states a balance due, a gross invoice or
receipt total is not current_amount_due; use the stated balance as the outstanding
amount and keep amounts received separate as amount_paid.” Compare the unchanged
prompt with this one-sentence variant on the exact frozen treatment input, using
the same profile/model/schema and three alternating runs per arm with the existing
retry cap. Score gross-debt errors first and target/scope regressions separately.
Do not add case IDs or amounts to the rule. This tests definition sensitivity before
changing models; it is not evidence of a generally improved model. No such calls or
prompt edits were made in this session.

Artifacts: [manifest](../extraction_artifacts/rent_run_02/manifest.json),
[availability](../extraction_artifacts/rent_run_02/summary.json),
[metrics](../extraction_artifacts/rent_run_02/review_metrics.json),
[all claim reviews](../extraction_artifacts/rent_run_02/claim_review.json),
[verification](../extraction_artifacts/rent_run_02/review_verification.json).
Raw requests, full provider envelopes and logical results remain in rent_run_02.

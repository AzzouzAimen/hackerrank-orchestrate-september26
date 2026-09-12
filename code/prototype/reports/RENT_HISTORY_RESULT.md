# Controlled rent-history result

**Classification: operationally inconclusive because of unavailable outputs.**

Restoring the six rent-history rows did not demonstrate successful target separation
in the usable outputs. Both usable treatments name Monthly rent but still explicitly
target event_1442. The sole usable control also targets event_1442. Insufficient
control availability prevents the predeclared comparative conclusion; this is not
evidence that the two inputs are equivalent or that context can never help.

## Execution and availability

Executed the approved runner once: three control and three treatment logical runs,
alternating C/T/C/T/C/T. Nine API calls, three retries, no additional runs. Provider,
model, runtime prompt, schema, settings, retry behavior, image payloads and financial
code were unchanged. First-attempt requests match the saved manifest. Treatment
differs only by the six approved appended event rows.

| Measure | Control | Treatment |
|---|---:|---:|
| Logical runs | 3 | 3 |
| First-attempt usable | 1/3 | 2/3 |
| Retry recoveries | 0/2 retries | 0/1 retries |
| Final usable | 1/3 | 2/3 |
| API attempts | 5 | 4 |
| Empty-content attempts | 3 | 2 |
| Nonempty schema-invalid attempts | 1 | 0 |
| Provider exceptions | 0 | 0 |

All three usable responses were first attempts. There are no retry-assisted semantic
results. The first control response supplied both a money object and a percentage,
violating the existing exclusive amount-amendment payload rule; its retry was empty.
That nonempty invalid response is retained diagnostically, excluded from the usable
semantic denominator. Empty output is not a valid empty facts array.

All nine saved responses have finish_reason=stop. The five empty-content envelopes
contain a nonempty reasoning field but no final content. This is an observed output
delivery pattern, not proof of a particular provider/model cause. No reasoning text
was substituted for a valid final bundle. A simple max-token truncation explanation
is not established by these stop reasons.

## Every usable output

| Logical run | Arm | Rent target | Percentage | Scope | Lease bounds | Image debt |
|---|---|---|---|---|---|---|
| 2 | Treatment | Incorrect: event_1442 plus Monthly rent selector | 12, correct | ongoing, accepted | null, accepted | Correct balance 100000 plus false current due 200000 |
| 5 | Control | Incorrect: event_1442 / Outstanding rent balance | 12, correct | ongoing, accepted | Unsupported lease effective_from 2023-08-16 | Correct balance 100000 plus false current due 200000 |
| 6 | Treatment | Incorrect: event_1442 plus Monthly rent selector | 12, correct | unknown, accepted | null, accepted | Correct balance 100000 plus false current due 200000 |

These are assistant judgments under the user's explicitly approved conventions.
All 16 facts across the three usable outputs have individual reviews in
[claim_review.json](../extraction_artifacts/rent_run_01/claim_review.json), derived from
the existing template without overwriting it. All nine attempts have review rows;
unavailable attempts are explicitly excluded from primary semantic scoring.

The treatment's Monthly rent description is lexical recognition, not a correct
operational target: finance.py targets() uses explicit affected_event_ids whenever
present. Both treatment outputs retain event_1442 there. No usable output abstained
or left the target unresolved; all three amendments were confirmed.

All usable outputs transcribe 12% with money=null and do not calculate amended rent.
Treatment scopes differ between ongoing and unknown, both allowed for the primary
comparison. None asserts one_cycle. The control copies the outstanding settlement
date into lease applicability without evidence that the renewal starts that day.

All correctly extract image02 Balance Due INR 100000 for event_1442 and Amount
Received INR 100000 as amount_paid. All also incorrectly type the gross 200000 total
as current_amount_due. Paid evidence remains a supported extra, not permission to
overwrite outstanding debt. No output substitutes the old receipt rental period for
the structured settlement date. Control image bounds copy the visible receipt date
2023-08-11; these are not invented dates or a settlement-date amendment.

Control run 5 and treatment run 6 additionally restate the scheduled event with a
null amount alongside the quantified image balance. The raw-row null is supported
as a restatement, but this is not a consolidated, resolved obligation or proof of
safe bundle composition. Control's salary history and cash restatements are grounded;
its uncertain continuation is not an invented confirmed future income. None of
these extras repairs the wrong rent target or false gross-debt assertion.

## Consistency and interpretation

Control consistency is unassessable: only one usable run. The two usable treatments
are consistent on wrong explicit rent target, correct 12%, correct balance due and
false gross current debt. They differ on accepted scope and on the additional null
future confirmation. Thus primary target behavior is stable among usable treatments,
but whole-bundle semantic identity or resolver equivalence is not established.

Correct target separation: control 0/1 usable; treatment 0/2 usable. These conditional
counts describe saved outputs only. Missingness may select which outputs are usable.
The required two usable runs in each arm was not met, so do not classify the overall
experiment as both arms fail semantically, despite the observed semantic failures.

The result weakens the hypothesis that adding history alone is sufficient under the
current extractor. It does not establish that missing history was irrelevant to the
historical failure. No trusted model integration is justified.

## Smallest next experiment proposed, not executed

Prioritize output availability before another rent-target comparison: use one fixed
original control payload in a small paired diagnostic, changing only high reasoning
effort to one lower provider-supported setting, retaining final-content validation
and capturing the same full envelopes. Freeze prompt, schema, model, images and retry
policy. Score availability first, with semantic review separate; do not parse the
reasoning field as replacement output. Nonempty reasoning plus empty final content
motivates this hypothesis but does not prove reducing reasoning will help.

No prompt, model, schema or engine changes were made. No further API calls were run.

## Evidence and usage

Artifacts: [run manifest](../extraction_artifacts/rent_run_01/manifest.json),
[availability summary](../extraction_artifacts/rent_run_01/summary.json),
[verification and hashes](../extraction_artifacts/rent_run_01/review_verification.json).
Per-attempt request/response and per-logical-run result files remain in the same
directory. Review verification checks all six first requests, all nine settings,
identical images and the exact six-row input difference; frozen tracked code has
no git diff. No financial engine execution or full-dataset inference occurred.

Recorded provider usage across nine calls: 62,337 prompt tokens (14,035 cached),
12,900 completion tokens, 75,237 total tokens. These are experiment usage records,
not a final-dataset usage report or provider billing statement.

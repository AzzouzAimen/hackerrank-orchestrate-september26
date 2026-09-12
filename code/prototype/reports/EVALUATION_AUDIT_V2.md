# Saved extraction audit v2

Repository organization changed after this audit: the shared modules now live directly
in `code/`, and the research folders live under `code/prototype/` and `code/analysis/`.
Prototype Markdown files are now collected in `code/prototype/reports/`.
Historical paths below describe the layout at the time of the audit.

This report supersedes the semantic headlines and next-action recommendation in
`REAL_MODEL_EXTRACTION_REPORT.md`. It does not replace any saved response. The audit
used no API calls, sample output labels, organizer files, or financial engine tuning.
All judgments below are **assistant adjudication, pending human review**. Existing
reference bundles were assistant-reviewed in prior sessions; no independent human
approval of the complete annotation set is documented.

## Corrected assessment

For the latest saved baseline (`20260912T160401Z`), the original 15 reference slots
break down as follows. These are an inspectable inventory, not a claim that the
reference set is exhaustive or unquestionable ground truth.

| Status | Slots | Meaning |
|---|---:|---|
| Recovered | 5 | user21/user25 ongoing payroll; image03 amount paid; unknown obligation; possible duplicate |
| Partially recovered | 4 | Refund meaning with wrong child set; user07 ongoing history with uncertain confirmation; correct payday with unsupported one-cycle scope; Dinner correction with unresolved selector scope |
| Missed | 1 | Prorated first salary's one-time classification |
| Incorrect interpretation | 1 | Authorization settlement labeled retry |
| Output unavailable | 3 | All user16 reference slots; no usable response |
| Reference ambiguous | 1 | user01 ongoing salary inferred from one prorated payment and one confirmed future salary |

Thus 5 complete and 4 partial recoveries are visible in the original 15 slots.
Among the 12 slots with usable output, one reference is itself ambiguous; the
remaining 11 have 5 complete, 4 partial, 1 missed, and 1 incorrect interpretation.
This replaces **3/15 exact-reference matches** as the substantive assessment.
It does not turn a partially correct or ambiguously scoped fact into a trusted input.

Every one of the latest baseline's 22 emitted facts has a separate field-level
review: **9 supported, 2 supported redundant, 6 incorrect, 1 unsupported, 4 ambiguous**.
These are mutually exclusive overall fact judgments; a mixed fact can contain a
correct amount and an incorrect target or financial interpretation. The former
**19 unsupported/unmatched emissions** cannot be interpreted as 19 hallucinations.

The 6 incorrect facts are the refund's child set, retry relationship plus child set,
three scheduled/confirmed salaries classified `pending_credit` (users07/21/25), and
image03's paid total interpreted as current debt. The unsupported baseline fact
asserts one-cycle payday duration. The four ambiguous facts concern user07 stream
confirmation, two user25 observation-as-amendment encodings, and Dinner target scope.
The supported/redundant facts include explicit future salaries and settled/cancelled
cash-state restatements absent from the reference. They are not automatically safe
to combine in a resolver bundle merely because their evidence is supported.

## Evidence and field adjudication

- **Values and currencies:** numeric OCR of image03's 41,272 is correct; `41272`,
  `41272.0`, and `41272.00` are exactly equal. No observed wrong currency or numerically
  mistranscribed amount in the latest usable baseline. One payroll repeat copies
  historical INR149,000 into a confirmed future amount not stated by message05.
  That is unsupported future confirmation, not erroneous historical OCR.
- **Dates and bounds:** 2024-09-23 is explicitly stated. The message does not establish
  that the old phase resumes afterward, so `one_cycle` is unsupported. An occurrence
  date or the first observed salary date is not automatically an invented effective
  bound. Whether the payday amendment starts applying on its payment date remains
  `EVALUATION_AMBIGUITY`, separately from the supported payment date.
- **Unknown preservation:** all three latest unknown-obligation runs preserve null
  amount/date. Two added null amendments in repeat2 are redundant financial meanings,
  not hallucinations. Payroll duration is incorrectly narrowed in all three runs;
  future salary amount is null in two, asserted from history in one. Uncertain ongoing
  payroll is conservative, but differs materially from the resolver's confirmed gate.
  The reference certainty convention requires approval.
- **Targets:** current resolver event IDs restrict a selector; they do not union or
  broaden it. For users21/25, explicit IDs include the confirmed next salary despite
  a narrower description, so that description does not remove its event membership.
  For user07, supplied history establishes that `Payroll credit` denotes the intended
  stream. Null descriptions are never unconditional wildcards. Refund parent-in-child
  targets are incorrect. Dinner identity is correct, but historical-ID scope versus
  an open stream selector needs adjudication; the old description of it as broadened
  was wrong.
- **Images:** direct visual inspection confirms image03 Cash Paid 41,272 and image02
  Balance Due 100,000. Earlier run 155852 extracted both Amount Received and Balance
  Due correctly, but also treated gross Total Amount to be Received 200,000 as current
  debt. Supported paid fields must not be used to overwrite scheduled outstanding debt.
  The latest user16 empty final response is an output failure, not evidence of failed
  image perception. The historical receipt period does not replace the structured
  future settlement date.
- **Input defect:** user16's supplied events are five payroll rows and event1442
  Outstanding rent balance. All six Monthly rent history rows are omitted, while its
  reference requires precisely that stream. The earlier usable run applies the 12%
  amendment to the outstanding balance. This has mixed input/reference/model ownership;
  rescoring cannot tell us what a complete input would have produced. The percentage
  is correct; renewed lease suggests ongoing duration, while explicit effective dates
  are absent. The trusted reference bundle remains unchanged.

## Consistency, coverage, and controls

Semantic consistency is assistant comparison of supported meaning **and material
incorrect/uncertain assertions**, ignoring redundant decompositions and identifiers.
It is not serialized structure equality and does not imply engine equivalence.

| Latest repeated case | Usable | Semantic result |
|---|---:|---|
| user07 | 3/3 | Inconsistent: null versus confirmed future amount; pending-credit classification appears once; effective bounds also vary |
| image03 | 1/3 | Not assessable: fewer than two usable runs |
| unknown obligation | 3/3 | Consistent: same confirmed unknown amount/date; redundant null amendments add no financial assertion |

The corrected result is **1 consistent of 2 assessable repeated cases**, with a third
unassessable. This supersedes 0/3. It is a tiny descriptive result, not a population
reliability estimate. The earlier155852 run also has stable unknown meaning, unstable
payroll, and unassessable image03 (0 usable). The initial all-failure run has no
assessable semantic consistency; its recorded 3/3 was the all-null equality bug.

The injection control returns a valid empty facts array in both usable experiments.
No injected balance or buying recommendation appears. This one control demonstrates
only its own success, not general injection robustness.

## Operations and provenance

Automatically recomputed from preserved attempt records:

| Saved run | Baseline first valid / usable | All usable | Calls | Provider failures | Recorded total tokens |
|---|---|---:|---:|---:|---:|
| 155758 | 0/10 / 0/10 | 0/16 | 32 | 32 | 0 |
| 155852 | 9/10 / 9/10 | 13/16 | 19 | 1 | 92,698 |
| 160401 | 9/10 / 9/10 | 13/16 | 19 | 0 | 101,590 |

For 160401: all-run first-attempt validity is 13/16, with 3 retries, none recovering the
three failed logical runs. All 6 unsuccessful attempts are HTTP-success empty final
content. They are not successful empty bundles. Text-only baseline availability is 8/8.
The earlier run contains five empty successful responses and one recorded connection
failure. The initial run records 23 HTTP 403 errors and 9 connection errors. The
exception wrapper is broad, so error labels were checked against safely categorized
recorded messages; no raw error bodies were republished.

Latest recorded usage: 88,352 prompt tokens, of which 42,710 cached; 13,238 completion
tokens; 101,590 total. Mean attempt latency 15.20 s, median 11.97 s. Estimated cost
USD 0.0147466 uses the previously recorded rates (USD 0.15/0.03/0.50 per million
uncached/cached/output tokens). Rates were not reverified and this is not provider
billing. Smoke/diagnostic calls may not have complete retained usage or responses;
zero recorded tokens in the initial failure run is not proof of zero session billing.
Cloudflare 403/code 1010 and connection problems are operational observations; the
user's VPN explanation is plausible but unproven. No networking change was made.

All three timestamped artifacts and `latest.json` are byte-preserved against the
pre-audit manifest. 160401 already records an evaluation revision; the old rescore
function wrote both latest and its timestamped source. Missing earlier score history
cannot be reconstructed. The artifacts retain final response content/attempt usage,
not necessarily complete provider envelopes or original request bodies. Inputs here
are reconstructed from the unchanged case builder and current dataset, with image
hashes; this is not byte-for-byte historical request reproducibility. Neither settings
nor inference prompt were intentionally tuned between the runs, but missing original
request snapshots limit independent verification of that history.

## Evaluator corrections and review artifacts

Automatic v2 comparisons enforce maximum one-to-one reference matching; require
evidence for selector equivalence; compare fields separately; avoid first-of-type
pairing unless relevance is mutually unique; classify unmatched extras as unadjudicated;
separate output failure from semantic misses; and use exact decimal normalization
without Decimal-context rounding. Reference uncertainty disagreements are diagnostic
differences, not proof of unsupported evidence. Structural fingerprints are only a
diagnostic; semantic consistency requires the claim review above. Rescoring writes a
new exclusive versioned file and never overwrites source artifacts.

- [Claim review](../extraction_artifacts/audit_v2/claim_review.json): every emitted fact
  in every baseline and selected repeat across all three saved runs; target, value,
  uncertainty, bounds, category, ownership, rationale, and reviewer provenance.
- [Reference review](../extraction_artifacts/audit_v2/reference_review.json): all original
  critical slots, including unavailable, partial, input-limited and ambiguous slots.
- [Evidence snapshot](../extraction_artifacts/audit_v2/evidence_snapshot.json): supplied
  evidence reconstructed without sample labels; image paths/hashes for direct review.
- [Automatic comparisons](../extraction_artifacts/audit_v2/automatic_comparisons.json),
  [operations](../extraction_artifacts/audit_v2/operations.json), and
  [pre-audit hashes](../extraction_artifacts/audit_v2/before_hashes.json).
- [Next-experiment proposal](NEXT_EXPERIMENT_V2.md): repair one input variable before
  prompt tuning. Not executed.

Human review should approve or correct the exact claim/reference rows, especially
user01 ongoing status, user07 certainty/applicability, Dinner scope, observed salary
amendments, and the separation of lease renewal from outstanding rent. No annotations
were promoted to trusted facts. No observed case demonstrates that a required financial
meaning cannot be represented by the seven types. Schema validity alone does not prove
contract sufficiency; this narrow incomplete evaluation cannot establish it generally.

## Promotion and verification

Stable components now live directly in `code/`; see [code/README.md](../../README.md).
The three module files and exported schema match their pre-move hashes exactly.
Engine/boundary tests moved with the implementation; original imports remain thin
compatibility wrappers. Both runners import the same shared model/engine objects.
Research inputs, experiments, artifacts, and annotations stay under `prototype/`.
The existing empty code entry points and usage-report placeholder are unchanged.

Before edits: 28 prototype + 21 boundary + 7 extraction + 6 ledger tests passed.
After edits: those tests plus 12 evaluator/integrity checks pass: **74 unique tests**.
The new package discovery command independently passes the same 49 engine/boundary
tests; this is compatibility verification, not 49 additional unique tests. New checks
cover one-to-one matching, irrelevant same-type pairing, nullable bounds/selectors,
exact long decimals, missing-output consistency, redundant facts, immutable rescoring,
saved raw-response validation, complete annotation coverage, and shared class/schema
identity. No browser checks or additional model calls were used.

The representative runner was replayed after relocation. Output SHA256 remains:

`2007B834DE8D1F0E6EED703D422FCF0A459C3EFE2B3B58525B4AB85A02E4D703`

The [verification record](../extraction_artifacts/audit_v2/verification.json) records source,
module, schema, reference and representative-output hash checks and safe ignore/secret
checks. `.env` and `log.txt` remain ignored. No full-dataset run, packaging, commit,
deployment, prompt tuning, or trusted model integration was performed.

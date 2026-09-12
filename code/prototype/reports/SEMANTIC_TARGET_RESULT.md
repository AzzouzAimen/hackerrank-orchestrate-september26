# Stream-versus-event targeting experiment

Classification: **mixed/inconclusive**.

The treatment appended only this general sentence: “When a message announces a
renewed recurring rent stream, target the matching recurring `Monthly rent`
stream/history; treat a separately scheduled outstanding balance event as distinct
unless the evidence directly links the amendment to that event.” The exact frozen
rent treatment input, model, plain-JSON integration, high reasoning, schema, images,
settings, validation and retry policy were unchanged.

## Availability

Six logical runs produced seven API attempts. Control was usable 3/3 first attempt.
Treatment was usable 2/3; its third run failed both attempts strict schema validation
(one invalid amount-amendment payload and one invalid image payload). There were no
empty finals or provider exceptions. Retry did not recover the treatment failure.

| Measure | Control | Treatment |
|---|---:|---:|
| First-attempt usable | 3/3 | 2/3 |
| Retry recoveries | 0 | 0 |
| Final usable | 3/3 | 2/3 |
| Empty final content | 0 | 0 |
| Nonempty schema-invalid attempts | 0 | 2 |
| Provider exceptions | 0 | 0 |

All usable outputs passed `json.loads` and strict `EvidenceBundle` validation. No
reasoning content was treated as final output.

## Targeting result

Among usable outputs, control correctly selected the recurring Monthly rent stream
in 0/3 runs. Treatment correctly selected it in 2/2 usable runs. The unavailable
treatment run is not counted as a semantic failure. The two treatment successes used
the Monthly rent selector with no explicit event IDs, cleanly excluding event_1442.

The control outputs explicitly targeted event_1442, the separate outstanding balance.
This supports a targeting benefit from the definition, but the treatment denominator
is incomplete and therefore does not establish a stable 3/3 rate.

## Regression and secondary checks

All five usable bundles extracted 12% and left the absolute rent amount unresolved.
Scope was `unknown` in the assessed amendment facts; no one-cycle claim appeared in
usable outputs. No invented lease bounds were emitted. One control image output copied
the receipt date as a bound; treatment preserved the structured 2023-08-16 settlement
date where it emitted a future confirmation.

Image behavior did not improve consistently. Balance Due INR100000 was correctly
extracted in 5/5 usable outputs. Amount Received INR100000 was kept separate in 5/5.
The gross INR200000 total was still incorrectly emitted as current debt in control
1/3 and treatment 2/2. That prior image clarification was not included in this
targeting experiment, so this result is a regression check against the current
runtime prompt, not a test of combining both sentences.

Treatment run 2 and run 6 show the intended targeting behavior. The failed treatment
run cannot establish whether the sentence would have preserved that behavior there.
The sentence did not prevent all harmful extras: treatment still made the gross-debt
error in both usable outputs, while control did so once. Targeting and image value
interpretation remain separable semantic clusters.

## Interpretation and next step

The clarification appears promising for stream/event targeting, conditional on usable
output: 2/2 versus 0/3. However, treatment availability fell to 2/3 with two schema
invalid attempts, so the overall result is mixed rather than a clean success. This
does not justify switching models yet; the model followed the targeting definition
in both complete treatment bundles.

The smallest next step is not another broad prompt rewrite. Preserve this evidence,
then run one confirmation with the same targeting sentence and the already successful
image-value sentence together, changing only the prompt composition, to test whether
both definitions can coexist without schema or semantic regressions. Keep the six-run
cap and score availability, targeting and gross-debt interpretation separately. Do
not integrate model facts into trusted recommendations.

Artifacts: [manifest](../extraction_artifacts/semantic_target_01/manifest.json),
[summary](../extraction_artifacts/semantic_target_01/summary.json),
[claim review](../extraction_artifacts/semantic_target_01/claim_review.json),
[verification](../extraction_artifacts/semantic_target_01/review_verification.json),
and all raw request/response/result files in that directory.

# Image-value semantic clarification experiment

Classification: **clarification clearly improves the targeted error without
material regression** on this six-run frozen-case comparison.

The treatment prompt appended exactly one general sentence distinguishing a stated
balance due from a gross receipt/invoice total. Everything else was frozen: same
Featherless model, plain-JSON integration, 32768 max tokens, 600-second timeout,
high reasoning, temperature, seed, schema, images and the completed rent treatment
input. Six alternating logical runs made six API calls; no retry was needed.

## Availability

| Measure | Control | Treatment |
|---|---:|---:|
| First-attempt usable | 3/3 | 3/3 |
| Retry recoveries | 0 | 0 |
| Final usable | 3/3 | 3/3 |
| Empty final content | 0 | 0 |
| Nonempty schema-invalid | 0 | 0 |
| Provider exceptions | 0 | 0 |
| Latency range (seconds) | 28.45–66.63 | 18.56–24.72 |
| Prompt tokens | 21,846 | 21,966 |
| Completion tokens | 6,520 | 4,605 |
| Total tokens | 28,366 | 26,571 |

All output was parsed with `json.loads` and passed strict `EvidenceBundle` validation.
No reasoning field was used as a substitute for final content. The treatment added
about 40 prompt tokens per call, as expected.

## Primary image measurement

| Image02 behavior | Control | Treatment |
|---|---:|---:|
| Balance Due INR100000 correctly extracted and linked to event_1442 | 3/3 | 3/3 |
| Amount Received INR100000 kept separate as amount_paid | 3/3 | 3/3 |
| Gross INR200000 incorrectly emitted as current_amount_due | 1/3 | 0/3 |

The clarification therefore removed the targeted gross-debt error in this sample.
The control error appeared once; two control runs omitted a gross-debt claim. This
is evidence of a treatment difference on this frozen case, not a general model
accuracy estimate.

## Secondary regression checks

Rent amendment targeting did not improve: one control and one treatment run cleanly
selected the recurring Monthly rent stream (1/3 each). Other outputs were ambiguous
or explicitly included/selected event_1442. The clarification did not solve stream
versus event targeting.

All six extracted 12% and did not calculate an absolute amended rent. Scope was
`unknown` or unsupported `one_cycle` in both arms (one_cycle occurred once per arm);
the sentence did not create a new scope improvement or regression. No invented
lease bounds appeared. One control output omitted the structured settlement date;
treatment outputs preserved it. This is a small timing difference, not attributable
confidently to the sentence.

Harmful extras were reduced for the targeted image meaning: no treatment output
called the gross total current debt. Treatment still included one explicit
event_1442 amendment target and one `one_cycle` claim, so it is not safe as a whole
bundle. The model consistently retained the correct balance and paid amount.

## What this establishes

Within these six saved runs, the explicit general definition is sufficient to test
and remove the repeated gross-total interpretation on this input, without reducing
availability or 12% extraction. It does not establish generalization beyond image02,
nor does it show that the model can reliably target the renewed rent stream.

The next smallest justified experiment is one similarly narrow general definition
for stream targeting: clarify that a message about a renewed recurring rent stream
must target the matching `Monthly rent` stream/history, while a separately scheduled
outstanding balance event remains a distinct obligation unless the evidence directly
links the amendment to that event. Keep the same model, input, schema, transport and
six-run cap. Score explicit affected IDs and selector scope separately. Do not run
that experiment in this session. A stronger-model comparison is not yet required:
the current model responded to the image clarification, and targeting remains a
cleanly separable semantic test.

Model facts remain shadow/evaluation only; no trusted recommendation integration was
performed.

Artifacts: [manifest](../extraction_artifacts/semantic_prompt_01/manifest.json),
[summary](../extraction_artifacts/semantic_prompt_01/summary.json),
[claim review template](../extraction_artifacts/semantic_prompt_01/claim_review_template.json),
and all raw request/response/result files in that directory.

# Proposed controlled experiment: restore rent history

**Status: proposal only; no model calls authorized or executed.**

Observation: `rep_user16` omitted all Monthly rent history but required a Monthly rent
selector in its reference. In saved 155852 the model recovered 12% but targeted the
separate event1442 Outstanding rent balance. Saved 160401 has no usable output and
cannot adjudicate the same targeting question. This input flaw precedes prompt tuning.

Ownership: case construction/reference context. The model's wrong linkage may also
reflect inference error; current evidence cannot isolate these causes.

Hypothesis: supplying the actual recurring rent history lets the unchanged extractor
distinguish the renewed lease stream from the separate outstanding balance.

One variable: append exactly event_1337, event_1344, event_1351, event_1358, event_1365, event_1371 to `rep_user16.events`.
The exact rows are in [proposed_input_addition.json](extraction_artifacts/audit_v2/proposed_input_addition.json).
Keep all existing event rows, message12, image02, and their order unchanged; append the
six rows in file order. Do not insert an explanatory hint or change the prompt.

Frozen: provider Featherless; API identifier `zai-org/GLM-5.3-Flash`; schema 1.0 and seven
types; prompt `semantic-extractor-v1.0-frozen`; temperature 0; seed 20260912; high reasoning;
8192 max tokens; JSON object mode; image bytes; retry policy; evidence other than the
added rows. No financial engine invocation or trusted integration.

Before a future run: human review the attached annotations and freeze a narrow rubric:
12% applies to the renewed Monthly rent stream, not the separate outstanding balance;
Balance Due 100000 comes from image02 for event1442; unknown bounds remain unresolved;
no absolute amended rent calculation is requested. Approve or revise the ongoing-scope
interpretation before scoring, without changing trusted facts in this audit.

Design after separate authorization: a paired input-only experiment, three logical
runs per arm. Original input is the control; original plus six rows is treatment.
Alternate control/treatment; keep one visible retry. This is 6 logical runs and at most
12 calls. Save complete sanitized request snapshots, image hashes, all response content,
finish reasons, usage, latency, and evaluator/annotation versions before any rescoring.
Do not fold other case or prompt changes into this experiment.

Evaluation: strict schema validity and output availability separately; then assistant
claim review with human-approved rubric. Compare lease target, percentage, scope and
unknown bounds separately from image amount/value type and event target. Count supported
extra fields separately. At least two usable runs in each arm are needed for a minimal
descriptive comparison; otherwise report operationally inconclusive.

Support: treatment consistently names the observed Monthly rent stream and keeps the
outstanding balance separate, while usable controls retain the linkage confusion.
Reject/weaken: usable treatment continues to attach 12% to event1442, invents an unrelated
stream, or shows no targeting improvement. If both arms are correct, the earlier error
is not reproduced; if both fail to return content, targeting is unassessable. Three runs
per arm provide diagnostic evidence, not a statistical guarantee.

Recommended next action now: review the v2 claim/reference annotations and approve this
input-only design. Do not tune the prompt or execute the proposal in this session.

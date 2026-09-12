# Decisions

This file records major project choices. Keep entries short and evidence-based. Add a new entry when a decision changes the architecture, forecasting policy, validation approach, or submission strategy.

## 2026-09-12 — Separate semantic evidence resolution from deterministic finance logic

Decision:
Use semantic interpretation for ambiguous messages and images, then pass structured facts to deterministic Python for dates, currency conversion, cash-flow simulation, payment-plan verification, ranking, and output validation.

Reason:
The data contains salary amendments, delayed paydays, contract endings, refunds, lifecycle links, and image-only amounts. Arithmetic and safety constraints must be reproducible and auditable.

Alternative:
Let an agent or language model produce the complete recommendation, including arithmetic.

Rejected because:
It would make balance safety, payment totals, and date constraints difficult to verify reliably.

Evidence:
The investigation found 215 messages, 16 image references, 25,342 financial events, and multiple linked transaction lifecycles, while the output contract requires exact numeric and chronological fields.

Tradeoff:
Requires a clear schema between semantic extraction and the finance engine, plus extra implementation work for evidence normalization.

## 2026-09-12 — Infer recurrence from cadence and context

Decision:
Infer recurring streams from supported calendar-month or fixed-day cadence, using category/context evidence and semantic exclusions rather than description repetition alone.

Reason:
Variable groceries, transport, and dining descriptions change even when their intervals remain regular; salary and other income descriptions include one-time exceptions.

Alternative:
Group exact descriptions and continue every repeated event.

Rejected because:
Description-only grouping reduced date agreement to 12/25 samples, and it would incorrectly continue final payroll, arrears, bonuses, commissions, and seasonal income.

Evidence:
Observed sample gaps include 5, 7, 10, 14, and 21 days plus monthly cadence. Description-only grouping performed substantially worse than observed-cadence grouping.

Tradeoff:
Category/context grouping can merge independent streams, so stream identity and semantic evidence need careful handling.

## 2026-09-12 — Retain all recurring expenses in baseline capacity

Decision:
Include recurring expenses in baseline affordability before applying optional spending changes.

Reason:
`amount_safe_to_pay` is defined before optional changes, and protected or flexible expenses still represent expected cash outflows unless a verified plan changes them.

Alternative:
Exclude stoppable/reducible expenses from the baseline.

Rejected because:
The fixed-only and flexible-exclusion variants introduced optimistic bias and raised uncapped normalized error from 3.575% to 7.740% on the 90-date experiment.

Evidence:
Fifteen sample amounts regressed under flexible-expense exclusion, and the specification defines spending changes as optional plan actions rather than automatic baseline assumptions.

Tradeoff:
The baseline may be more conservative than hidden labels that use a different budget convention, but it is safer and specification-aligned.

## 2026-09-12 — Keep the literal 90-date horizon as the primary policy

Decision:
Use the request date through request date plus 89 days as the primary 90-day simulation window; retain the calendar-month endpoint only as a diagnostic sensitivity variant.

Reason:
The literal window follows the challenge contract and avoids changing the safety definition to fit a few labels.

Alternative:
Forecast through the end of the request month plus two calendar months.

Rejected because:
That endpoint spans roughly 80–91 days after the request across samples and slightly worsened uncapped amount error despite improving some boundary dates.

Evidence:
Plain mean achieved 19/25 date matches and 3.575% uncapped normalized MAE on the literal window; the calendar endpoint achieved 22/25 dates but 3.608% uncapped normalized MAE.

Tradeoff:
Some labeled boundary dates remain unexplained, especially where an occurrence falls just outside the calendar-style endpoint.

## 2026-09-12 — Treat latent-budget rounding as sensitivity analysis

Decision:
Keep all-history mean as the working variable-expense estimator and evaluate median, trimmed, winsorized, and significant-digit variants only as diagnostics.

Reason:
Historical variable amounts show moderate variation, but no tested latent-center rule substantially reduces uncapped error.

Alternative:
Adopt a rounded robust center as the forecast budget.

Rejected because:
The best literal-window improvement was negligible, and the one uncapped exact match from rounded winsorization did not generalize across samples.

Evidence:
Plain mean: 3.575% uncapped normalized MAE; three-significant-digit mean: 3.568%; rounded winsorization matched one uncapped sample but regressed several others.

Tradeoff:
The mean is sensitive to outliers and may not represent an underlying budget, but changing it now would add complexity without reliable evidence.

## 2026-09-12 — Build a small auditable vertical prototype before scaling

Decision:
Next implementation phase should connect structured evidence extraction, deterministic projection, plan verification, and explanation for a few representative cases before running the full dataset.

Reason:
The investigation has exposed unresolved horizon, hold timing, stream membership, and semantic-duration questions that are easier to diagnose in a complete trace than in aggregate sample scores.

Alternative:
Continue broad sample-fitting experiments or immediately build the full submission pipeline.

Rejected because:
More estimator tuning has not resolved uncapped residuals, while a full pipeline would make it harder to isolate semantic and ledger errors.

Evidence:
Arithmetic and label-isolation checks pass, but 21 uncapped safe amounts remain unexplained and six labeled plans breach the tested baseline reserve.

Tradeoff:
The vertical prototype delays full-dataset coverage briefly, but produces an inspectable foundation and clearer failure taxonomy.

## 2026-09-12 — Stop the verification gate on unconfirmed payroll persistence

Decision:
Complete the three-case audit and pause architecture implementation under the session's explicit stop instruction. Keep later amended paydays labeled as modeling policy rather than semantic facts.

Reason:
message_05 confirms September 23 but does not establish how long the payday change lasts. Continuing it indefinitely is plausible, not an explicitly confirmed schedule.

Alternative:
Promote the default persistent phase directly into the prototype, or revert to the earlier phase.

Rejected because:
Neither duration is established by the source; matching the October 23 label cannot settle the semantic question. The user explicitly requested stopping on unsupported assumptions.

Evidence:
Both phase diagnostics give user_07 safe amount INR 86,237.22, but earliest full-payment dates differ: October 23 versus October 15. The three ledgers replay exactly; six research tests pass. A separate hardcoded-day-15 bug in the one-cycle diagnostic was corrected using observed history.

Tradeoff:
The evidence contract and vertical prototype remain deferred until this modeling policy is resolved. Broad estimator tuning stays stopped: user_12 has an identified boundary bill, while user_21 has no evidence justifying extra occurrences.

## 2026-09-12 — Accept explicit payroll persistence and resume the prototype

Decision:
Payroll amendment duration is unknown from evidence; the forecasting engine applies a documented persistence policy. Unknown-scope date changes persist through the horizon with MODELING_POLICY provenance. The user accepted this policy and released the earlier gate.

Reason:
Separate source meaning from a deterministic forecast convention without silently asserting duration.

Alternative:
Treat later amended dates as confirmed facts or continue blocking on this known uncertainty.

Rejected because:
The source does not confirm duration, while the user explicitly authorized proceeding with documented persistence.

Evidence:
The date-amendment fact retains scope unknown; the representative test checks September SEMANTIC_FACT and October MODELING_POLICY.

Tradeoff:
Later payroll timing remains a modeling assumption. No estimator, horizon or label-fitting research is reopened.

## 2026-09-12 — Prove the financial path with reviewed semantic facts

Decision:
Use a strict seven-type evidence contract and replay five session-reviewed fact bundles through a separate Decimal prototype. Python owns all financial consequences and blocks unresolved amounts rather than converting them to zero.

Reason:
Provenance, unknown values, lifecycle handling and plan safety can be tested independently of automated extraction reliability.

Alternative:
Integrate a model API and broader extraction coverage before checking the financial boundary.

Rejected because:
It would combine extraction errors with implementation errors before either is auditable.

Evidence:
28 prototype tests pass; five cases produce validated outputs, three selected plans verify and two correctly carry no selected plan under the implemented assumptions. Image_02 fills an actual future INR 100,000 obligation. Independent extraction accuracy remains unmeasured.

Tradeoff:
This is a reviewed-fact replay, not an automated semantic API pipeline. First-job cadence and intraday ordering produce documented label regressions; no samples are patched. Expenses-before-income is an explicit conservative intraday convention, and sufficient recurrence history is required even for payroll.

## 2026-09-12 — Harden the evidence boundary without expanding the schema

Decision:
Retain all seven fact types and fix only consequences exposed by synthetic boundary tests. Possible duplicates preserve history; unknown transfer scope, paid-only outstanding evidence and unquantified obligations block capacity. Explicit conflicts do not use fact order as precedence.

Reason:
Validly shaped semantic facts must not silently suppress obligations or broaden their targets. The existing fields represent the tested distinctions; transfer cash scope must come from trusted structured context, not the word internal.

Alternative:
Add more semantic types or connect model outputs before establishing deterministic boundary behavior.

Rejected because:
The observed failures were resolver consequences, not missing fact types for safe handling. Missing account-scope metadata can remain explicitly unresolved.

Evidence:
The first 16 challenge tests exposed 11 failures. After narrow fixes, 21 boundary tests plus all 28 existing prototype tests pass, including permutations and hand-calculated ledger assertions. The five representative output CSV hash is unchanged.

Tradeoff:
Account scope absent from the supplied dataset prevents internal-transfer exclusion. Some ambiguous targets/conflicts conservatively block; general stream identity and source precedence remain outside this experiment. No model API has been connected.

## 2026-09-12 — Keep real-model facts in shadow mode

Decision:
Do not promote Featherless GLM-5.3-Flash output into the trusted resolver path. Keep the seven-fact contract and run one targeted prompt-only emission-rubric experiment next.

Reason:
The clean frozen baseline matched only 3 of 15 reviewed facts on all financially meaningful fields, emitted unsupported/redundant facts, converted uncertainty into certainty, and was inconsistent across all three repeated cases. Vision calls intermittently returned billed but empty final content.

Alternative:
Integrate now, redesign the contract, silently map malformed output to no facts, or immediately benchmark several models.

Rejected because:
The evidence points to model/prompt use of an expressive contract and intermittent output reliability. No case proves that the deterministic engine or seven fact types must change; permissive fallback would hide missing obligations.

Evidence:
Experiment `20260912T160401Z` used 10 baseline cases and 6 repeat runs. Baseline first-attempt validity was 9/10 and 0/3 repeated cases were meaning-equivalent. All 21 boundary, 28 prototype, 7 extraction-evaluator, and 6 ledger-audit tests pass; representative CSV SHA256 remains `2007B834DE8D1F0E6EED703D422FCF0A459C3EFE2B3B58525B4AB85A02E4D703`.

Tradeoff:
There is still no trusted automated extraction path. A single prompt experiment delays integration while isolating whether emission and uncertainty errors can be reduced without contract or engine changes.

## 2026-09-12 — Supersede strict extraction metrics with evidence adjudication

Decision:
Keep saved model facts in shadow mode; replace automatic reference-equality headlines with versioned assistant claim reviews and propose a paired input-only rent-history experiment before prompt tuning.

Reason:
The scorer reused emissions, treated unmatched facts as unsupported, compared unrelated same-type facts, and confused missing output/serialization with semantic quality. user16 input omitted Monthly rent history required by its reference. All 63 saved emissions were audited without model calls.

Alternative:
Retain 3/15, 19 unsupported and 0/3 as semantic truth, tune the emission prompt immediately, or silently rewrite source scores.

Rejected because:
Those conclusions conflate supported extras, ambiguous annotations, partial meanings and operational failures. Missing context and unapproved annotation conventions should be resolved before attributing every mismatch to the model.

Evidence:
prototype/EVALUATION_AUDIT_V2.md and extraction_artifacts/audit_v2 contain source hashes, evidence snapshots and every claim. Latest baseline: 5 recovered, 4 partial, 1 missed, 1 incorrect, 3 unavailable and 1 ambiguous reference slot. One of two assessable repeat groups is semantically consistent; image consistency is unassessable.

Tradeoff:
Manual assistant judgments remain pending human review and do not establish population accuracy or resolver-equivalent bundles. No proposed experiment was executed; original response artifacts and trusted references are preserved.

## 2026-09-12 — Promote deterministic components without behavior changes

Decision:
Move evidence.py, finance.py, plans.py and evidence.schema.json into code/buy_or_wait, with engine/boundary tests in its tests package and thin prototype compatibility imports. Retain research materials and runners in prototype.

Reason:
code is a Python standard-library module; buy_or_wait avoids that import collision. Existing code entry points were empty and remain untouched. A single shared implementation avoids engine drift.

Alternative:
Copy the engine, move all prototype research into code, or integrate the shadow model into a new submission runner.

Rejected because:
These expand scope or permit divergence and would violate the behavior-preserving/trusted-input boundary.

Evidence:
Three source modules and schema match pre-move hashes. All 74 unique regression/evaluator/ledger tests pass; both old commands and new package discovery pass. Representative output SHA256 remains 2007B834DE8D1F0E6EED703D422FCF0A459C3EFE2B3B58525B4AB85A02E4D703.

Tradeoff:
The main implementation is reusable under code, but code/main.py is still the original empty starter, not a full submission runner. No full-dataset prediction, packaging, commit or model integration occurred.

## 2026-09-12 — Flatten the code layout and relocate research folders

Decision:
Place the canonical seven-fact schema/models, deterministic financial engine, plan logic, and their tests directly under code/. Move the existing prototype/ and analysis/ trees to code/prototype/ and code/analysis/. Use code/main.py for the already-reviewed representative replay and code/evaluation/main.py for read-only saved-experiment summaries.

Reason:
The user requested one coherent code directory with working entry points. Python's standard-library code module makes a nested importable code package inappropriate. The existing full-dataset and final usage stages are not implemented yet, so the entry points expose only completed behavior and clearly reserve later evaluation.

Alternative:
Keep a nested buy_or_wait package, duplicate the engine, leave both entry points empty, or build a full-dataset/online evaluator now.

Rejected because:
A nested package and empty entry points do not match the requested organization; duplication risks drift; full-dataset and model integration exceed the current tidy-up scope.

Evidence:
The 49 engine/boundary, 19 extraction/audit, and 6 ledger tests pass after relocation. The representative CSV SHA256 remains 2007B834DE8D1F0E6EED703D422FCF0A459C3EFE2B3B58525B4AB85A02E4D703. All saved research artifacts and fact bundles match pre-move hashes. The offline audit regenerates identically. No model calls were made.

Tradeoff:
Old root-level research import paths and commands are replaced by code/ paths. Git displays the unstaged moves as deletions plus new paths until a later stage/commit; historical artifacts remain byte-preserved and no final prediction runner is claimed.

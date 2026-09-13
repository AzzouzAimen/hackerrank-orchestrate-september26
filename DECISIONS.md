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

## 2026-09-12 — Implement the controlled rent-context diagnostic

Decision:
Add a separate shadow runner with offline preparation, three alternating runs per arm, one existing retry per run, and explicit narrow rubric approval for live execution.

Reason:
The review identified a verified six-row input omission and required separating target recovery, abstention, availability, retry recovery and whole-bundle quality.

Alternative:
Tune the extraction prompt or automatically score against the historical reference.

Rejected because:
Those approaches confound missing context with model behavior and repeat the prior annotation problems.

Evidence:
24 targeted extraction/audit/experiment tests pass, including capped calls, retry feedback, failure retention, immutable artifact creation and key redaction. No live API calls were made.

Tradeoff:
Semantic adjudication remains a separately recorded review; the new harness does not establish model accuracy or trusted integration readiness.

## 2026-09-12 — Stop rent-history comparison as operationally inconclusive

Decision:
Do not claim a targeting improvement or promote model facts. Propose a small output-availability diagnostic next, without executing it.

Reason:
Only one control and two treatments were usable, below the two-per-arm rule. All usable amendments still explicitly target event_1442.

Alternative:
Declare both arms equivalent/failing from usable-only counts, or repeat until enough outputs appear.

Rejected because:
Unavailable outputs prevent the planned comparison, and the user capped the experiment at six logical runs.

Evidence:
code/prototype/reports/RENT_HISTORY_RESULT.md and extraction_artifacts/rent_run_01: nine calls, five empty responses, one nonempty schema-invalid response, no provider exceptions. All 16 usable facts reviewed.

Tradeoff:
The targeting hypothesis remains unresolved; observed targeting and gross-debt errors remain documented. No frozen component changed.

## 2026-09-12 — Adopt provisional generous plain-JSON transport

Decision:
Use 32768 output tokens and 600-second timeout, omit API response_format, retain unchanged JSON prompt and strict local schema validation. Version the transport explicitly.

Reason:
Low reasoning did not restore output (0/2 versus high 0/2). At generous limits, API JSON mode produced 0/2 valid final outputs and omission produced 2/2.

Alternative:
Switch models immediately, only raise the token cap, or parse reasoning as final output.

Rejected because:
Same-model API-mode evidence warrants a narrower workaround; larger limits alone failed, and reasoning is not final JSON.

Evidence:
OUTPUT_RELIABILITY_RESULT.md and INTEGRATION_BUDGET_RESULT.md; eight total diagnostic inference calls across the two experiments; 25 targeted tests pass.

Tradeoff:
Two successes are not a reliability guarantee. Rent/debt semantic errors persist. Historical experiment configurations are preserved in artifacts; future runs identify a new integration version.

## 2026-09-12T18:41:13.744619+00:00 — Plain-JSON rent rerun

Decision: Keep provisional integration and propose one gross-versus-balance definition experiment; do not execute it yet.
Reason: Six of six final outputs usable, but five gross-debt errors; rent targeting mixed (control0/3, treatment1/3).
Alternative: Switch models or broadly rewrite prompt.
Rejected because: Output delivery is now usable on this case and a single semantic definition remains cleanly testable.
Evidence: code/prototype/reports/RENT_HISTORY_RESULT_V2.md and rent_run_02 artifacts; seven calls, one retry, no empty finals.
Tradeoff: Small historical comparison cannot establish general reliability; one response required286.73 seconds.

## 2026-09-12T18:50:30+00:00 — Semantic image clarification

Decision: Treat the one-sentence image definition as a targeted improvement and keep it out of trusted integration pending broader validation.
Reason: Gross-total-as-current-debt fell from 1/3 control to 0/3 treatment with six usable outputs and no availability regression.
Alternative: Switch models or broaden the prompt rewrite.
Rejected because: The current model responds to a narrow definition; rent targeting remains a separate failure cluster suitable for its own one-variable test.
Evidence: code/prototype/reports/SEMANTIC_PROMPT_RESULT.md and semantic_prompt_01 artifacts; all claims reviewed, six calls, strict validation.
Tradeoff: Six runs on one frozen input do not establish generalization; targeting and scope errors remain.

## 2026-09-12T19:12:50+00:00 — Stream/event targeting definition

Decision: Keep the targeting clarification as a promising but unconfirmed semantic intervention; do not promote it or switch models.
Reason: Usable treatment outputs targeted Monthly rent 2/2 versus control 0/3, but one treatment run failed strict validation twice.
Alternative: Combine prompt changes immediately or benchmark stronger models.
Rejected because: The paired result is mixed and treatment availability regressed; composition needs a controlled confirmation first.
Evidence: code/prototype/reports/SEMANTIC_TARGET_RESULT.md and semantic_target_01 artifacts; seven attempts, five usable outputs, all claims reviewed.
Tradeoff: Conditional targeting improvement is encouraging, while gross-debt errors persisted and the incomplete treatment denominator limits confidence.

## 2026-09-12 — Create a frozen semantic evaluation benchmark

Decision:
Create a source-verified development/holdout split and development-only reference annotation drafts for evaluating semantic extraction independently of the deterministic financial engine.

Reason:
The project needs reviewable, real-data evidence references before semantic model quality can be measured.

Alternative:
Use sample labels, model outputs, or end-to-end recommendation results as evaluation data.

Rejected because:
Those sources would mix semantic evidence with labels, model behavior, or downstream affordability decisions.

Evidence:
The frozen v5 split contains 14 development and 8 holdout cases with canonical source IDs and zero template overlap. Development drafts map evidence to the seven contract fact types and pass offline Pydantic/evidence-integrity validation.

Tradeoff:
Only development references are drafted now; holdout remains unseen and semantic ground truth, model scoring, inference, and end-to-end evaluation are intentionally deferred.

## 2026-09-12 — Freeze development semantic references with quoted source targets

Decision:
Approve a 14-case development reference v4 bound to exact runtime-input v2 hashes. Add an optional quoted source target and nullable unresolved lifecycle parent while keeping the seven fact types.

Reason:
Five meaningful development cases lacked an event or currency-bearing structured stream target; requiring empty facts would make semantic misses look successful, while guessing currencies or event IDs would fabricate evidence.

Alternative:
Assign profile currency or unrelated event IDs to those meanings, or leave them unscoreable.

Rejected because:
Neither follows the supplied evidence, and vacuous references cannot measure extraction quality.

Evidence:
The source-verified messages, event history, image_02, saved request hashes, offline validator, and 127 passing Python tests are summarized in code/prototype/reports/SEMANTIC_DEV_REFERENCE_COMPLETION.md.

Tradeoff:
Source-only facts with unresolved financial details remain semantically scoreable but cannot identify or remove a concrete transfer event; actual model quality and holdout generalization remain unmeasured.

## 2026-09-12 — Freeze the eight holdout semantic references

Decision:
Annotate all eight frozen holdout cases under the unchanged development conventions, with byte-exact offline inputs and one required semantic fact per case.

Reason:
The holdout must evaluate the same seven-type semantic contract without selecting easier cases or borrowing currencies and targets from unrelated streams.

Alternative:
Use only split-linked events or choose case-specific history after writing references.

Rejected because:
Several cases have no linked event; a case-neutral all-same-user event selection avoids reference-driven evidence cherry-picking while preserving the exact extractor request format.

Evidence:
The frozen holdout manifest, source/image hashes, reference validator, and 132 passing offline tests are recorded in code/prototype/reports/SEMANTIC_HOLDOUT_REFERENCE_COMPLETION.md.

Tradeoff:
Holdout requests contain more unrelated same-user history than development requests; the validator therefore requires precise targets and preserves unknown FX/prize details. Model performance remains unmeasured.

## 2026-09-12 — Do not adopt target-exclusivity treatment after paired test

Decision:
Preserve the frozen active extractor and retain the exclusivity suffix only as experimental evidence. Run a separate confirmation-semantics prompt experiment against the frozen control.

Reason:
Three paired repetitions eliminated target conflicts and improved validity, but case passes fell from 4/42 to 3/42; the declared semantic no-regression gate did not pass.

Alternative:
Adopt the sentence solely for first-attempt schema validity, then stack more instructions.

Rejected because:
Format reliability does not establish semantic integration readiness and would obscure single-variable attribution.

Evidence:
code/prototype/reports/SEMANTIC_TARGET_EXCLUSIVITY_EXPERIMENT_20260912.md and its immutable paired artifacts.

Tradeoff:
The active extractor retains a known format weakness while the proven local fix is preserved for review; semantic benefit and model variability remain unresolved.

## 2026-09-13 — Reject confirmation treatment and escalate target identity

Decision:
Keep the frozen active extractor unchanged, reject the confirmation-semantics treatment, stop local prompt experiments, and request a control-tower decision on semantic target identity and evaluator/consumer equivalence.

Reason:
The treatment fixes expected-invoice certainty locally but increases unsupported facts from 84 to 93, harmful flags from 6 to 9, and unknown-error flags from 77 to 101 across three paired development repetitions. Six frozen required facts also use semantic selector descriptions that match no supplied event, while the scorer and deterministic consumer apply materially different target equivalence rules.

Alternative:
Stack the confirmation and target-exclusivity sentences or tune selector names to the frozen development references.

Rejected because:
Both isolated prompt treatments fail their semantic safety gates, and benchmark-derived names would optimize examples before the identity contract is approved.

Evidence:
`code/prototype/reports/SEMANTIC_CONFIRMATION_EXPERIMENT_20260913.md`, `code/prototype/reports/SEMANTIC_TARGET_IDENTITY_STRATEGIC_REVIEW_20260912.md`, and their immutable development-only artifacts.

Tradeoff:
The extraction boundary is not approved for full-pipeline integration. The control tower must choose a general existing-event, existing-stream, and new-entity policy before another target experiment; no holdout inference, scoring, diagnosis, or tuning was performed.

## 2026-09-13 — Align target identity and stop current-model prompt iteration

Decision:
Adopt `target-identity-v1` as the development semantic boundary, keep only the minimality and expected-settlement prompt treatments as experimental evidence, and escalate to a controlled model comparison before integration.

Reason:
The executable contract now distinguishes exact supplied events, existing supplied streams, and new/unidentified entities. Three repetitions show target binding near-perfect under this contract, but semantic coverage remains 22/57 at the target-v1 baseline and 29/57 under the best tested prompt treatment, far below the practical integration gate.

Alternative:
Continue stacking prompt rules or adopt the highest-coverage treatment as production.

Rejected because:
Unknown enumeration increased harmful claims, and the confirmation-state definition still produced a direct gross-total-as-due harm. Prompt-only gains have not established a safe, stable boundary.

Evidence:
`code/target_identity.py`, the versioned development reference and review ledger, and `code/prototype/reports/SEMANTIC_TARGET_V1_RESEARCH_REVIEW_20260913.md` with paired artifacts for target-v1, minimality, unknown enumeration, and confirmation-state experiments.

Tradeoff:
The current model remains outside full-pipeline integration. A model comparison is now the smallest experiment that can distinguish capability limits from the corrected representation; no production model switch or holdout use is authorized by this decision.

## 2026-09-13 — Enforce target identity at deterministic resolution

Decision:
Make `target_identity.validate_target_identity` a precondition of `finance.resolve`, with a narrowly scoped compatibility path for legacy exact-ID facts carrying a selector that binds the same events.

Reason:
The approved target convention must have one executable meaning from extraction through deterministic financial binding. Previously the new validator was used by extraction and scoring but not by the resolver.

Alternative:
Leave resolver validation implicit in `finance.targets` and rely on extractor-side checks.

Rejected because:
A manually supplied or legacy mixed bundle could bypass the corrected boundary and still alter financial state.

Evidence:
The resolver now validates before event materialization; 46 named development/prototype tests pass. Five representative legacy bundles were reduced to authoritative exact IDs. The compatibility branch accepts only a selector whose selected events contain the explicit IDs; strict target-v1 extraction/scoring remains mutually exclusive.

Tradeoff:
Backward compatibility remains for existing internally redundant fixtures, while new semantic outputs cannot use the mixed form. A future cleanup can remove the compatibility path after all callers migrate.

## 2026-09-13 — Reject DeepSeek-V4.1-Flash for semantic extraction

Decision:
Reject Featherless `deepseek-ai/DeepSeek-V4.1-Flash`; retain GLM research state and the accepted target-v1 prompt configuration.

Reason:
Coverage improved only 17/57 to 20/57 meanings and 7/42 to 8/42 cases, while target correctness fell 53/56 to 49/51, first-attempt validity fell 41/42 to 39/42, and one final output was unavailable after retries.

Alternative:
Keep DeepSeek or run a model-specific prompt follow-up.

Rejected because:
Existing-stream binding regressed, image composition remained invalid/unsafe, and completion tokens increased 50,271 to 375,495.

Evidence:
Artifacts: `code/prototype/extraction_artifacts/semantic_target_v1_model_comparison_20260913T010444Z/`; report: `code/prototype/reports/SEMANTIC_TARGET_V1_MODEL_COMPARISON_20260913.md`.

Tradeoff:
Unknown-preservation errors improved 20 to 8 and unsupported facts 51 to 44, but safety, target binding, reliability, and cost gates dominate.

## 2026-09-13 — Accept guarded partial semantic boundary

Decision:
Adopt scoped extraction plus deterministic validation/composition plus explicit semantic abstention as the accepted boundary for the next vertical-integration phase. Keep the monolithic GLM target-v1 extractor as the current production baseline until that phase explicitly wires the guard.

Reason:
The guard removed all observed harmful trusted claims in the repeated message-treatment replay while retaining 22/57 required meanings, with one false reject. Image scoping reliably fixed the repeated gross-total/image-label composition failure.

Alternative:
Promote message-scoped extraction without a guard, continue prompt tuning, or require near-complete semantic coverage before proceeding.

Rejected because:
Message scoping still produced three harmful certainty claims, lower first-attempt validity, and unstable fact types. Broad prompt tuning and general model comparison already plateaued. Universal abstention would destroy useful reconstruction.

Evidence:
`code/prototype/reports/SEMANTIC_PHASE_FINAL_HANDOFF_20260913.md` and the corrected development-only guard replay show 0 false accepts, 1 false reject, 22/57 trusted meanings, 32 remaining unsupported non-harmful claims, 28 unknown-preservation errors, and 46/46 target-correct retained matched facts.

Tradeoff:
Coverage remains low and scoped extraction costs about 20% more calls than monolithic extraction. The boundary is safe enough for a guarded vertical prototype, not a claim of full semantic integration readiness.

## 2026-09-13 — Accept guarded finance-boundary integration

Decision:
Use `code/semantic_boundary.py` as the canonical guard-to-resolver adapter. Only trusted facts enter `finance.resolve`; blocked possible obligations prevent capacity, while known-invalid gross-total and paid-as-due interpretations are omitted without creating debt.

Reason:
The vertical development replay proved that no blocked fact reached the finance state and all 42 saved outputs resolved deterministically. Capacity remained available in 32 cases and was conservatively blocked in 10.

Alternative:
Pass all schema-valid model facts into finance, or block every case containing any abstention.

Rejected because:
The first permits known harmful claims to affect cash, while the second discards safe useful facts and unnecessarily blocks capacity.

Evidence:
`GUARDED_VERTICAL_INTEGRATION_REVIEW_20260913.md`; 57 targeted tests pass, target correctness is 46/46 for retained matched facts, harmful trusted facts and false accepts are zero, and one false reject remains.

Tradeoff:
The live scoped caller remains research-only and 10/42 development traces cannot calculate capacity because unresolved obligations or bindings remain. This is deliberate conservative behavior.

## 2026-09-13 — Accept deterministic scoped preparation and composition

Decision:
Use `input_preparation.py` and `scoped_extraction.py` as the offline front half of the guarded submission runner. Evidence is request/user/date scoped, image outputs may contain only image facts, and any unavailable or invalid scope fails closed.

Reason:
These modules isolate selection and composition from the model provider, preserve all same-user structured history for target candidates, reject future/cross-request messages, and make scope behavior independently testable.

Alternative:
Keep request preparation embedded in experimental runners or let one model call reconstruct all evidence.

Rejected because:
Experimental runners are not reusable submission interfaces, and monolithic reconstruction reintroduces the cross-evidence contamination already measured.

Evidence:
Seven focused scoped/guard tests and 53 core deterministic tests pass; the guarded development CLI completes 42/42 traces.

Tradeoff:
The preparation keeps all same-user events, increasing prompt size. Live provider integration, usage persistence, and full-run orchestration remain separate gates.

## 2026-09-13 — Correct scoped protocol and freeze guarded partial architecture

Decision:
Supersede the original scoped-extraction and guarded-boundary metrics. Keep only image-scoped extraction; revert message scoping. Freeze the accepted architecture as monolithic accepted-prefix GLM-5.3-Flash text extraction plus an image-only GLM-5.3-Flash call when needed, deterministic composition/target validation, semantic guard, and deterministic finance.

Reason:
The original scoped harness omitted `accepted_certainty_minimality_unknowns_v1.txt` even though its reports claimed the accepted prefix was fixed. Corrected paired runs show image scoping removes the recurring gross-total-as-due harm, while message scoping materially regresses coverage, target correctness, unsupported output, and cost.

Alternative:
Retain the earlier message-scoped conclusion or rerun broad prompt tuning.

Rejected because:
Those earlier measurements are protocol-invalid, and the corrected message treatment falls from 21/57 to 17/57 meanings and 57/58 to 51/58 target matches.

Evidence:
`code/prototype/reports/SEMANTIC_SCOPED_PROTOCOL_CORRECTION_20260913.md`; corrected immutable image/message artifacts; corrected guard replay (21/57 trusted meanings, 0 harmful trusted claims, 0 false accepts, 0 false rejects, 50/51 retained target matches).

Tradeoff:
Trusted development coverage remains only 36.8%, so this is explicitly a guarded partial architecture rather than a high-coverage semantic boundary.

## 2026-09-13 — Reject full GLM as a text specialist and end semantic tuning

Decision:
Reject `zai-org/GLM-5.3` for the text-semantic subtask, retain GLM-5.3-Flash, and end the semantic research phase with the guarded partial architecture.

Reason:
In a three-repetition paired development experiment where only the text model changed and image results were shared, full GLM scored 21/57 meanings versus Flash 22/57, final availability 40/42 versus 42/42, and target correctness 46/54 versus 55/58. Its improvement in unsupported facts (37 versus 49) and case passes (12 versus 7) does not outweigh lost binding, availability, and roughly 8.6x text-call cost.

Alternative:
Promote full GLM, try another general model, or continue prompt iteration.

Rejected because:
The specialist did not improve the primary semantic measure, repeated the same schema failure twice, and introduced more target errors. Further broad comparisons are no longer evidence-driven within this bounded phase.

Evidence:
`code/prototype/extraction_artifacts/semantic_target_v1_text_specialist_glm53_20260913T081322Z/` and `code/prototype/reports/SEMANTIC_PHASE_CONSOLIDATED_FINAL_20260913.md`.

Tradeoff:
The shipped boundary deliberately abstains on unresolved obligations and misses useful facts. It prioritizes preventing unsafe financial capacity over aggressive reconstruction.

## 2026-09-13 — Accept resumable guarded submission runner and audit

Decision:
Use `code/main.py run` with persisted per-request artifacts and `code/main.py audit` as the runnable integration boundary. Classify safety abstentions separately from ordinary verified no-plan outcomes.

Reason:
The independent saved-run audit verified 250/250 rows, exact contract/order, bounds, plan sums/dates, supplied installment schedules, decision equivalence, and semantic-guard replay with zero pipeline exceptions. The prior `fail_closed` summary counter incorrectly combined 30 safety abstentions with 200 ordinary no-eligible-plan results and is superseded.

Alternative:
Treat every zero/not-recommended output as a pipeline failure or ship the prototype runner directly.

Rejected because:
That headline misstates valid deterministic outcomes and the prototype entry point did not provide a stable documented submission CLI.

Evidence:
`code/submission_runner.py`, `code/submission_audit.py`, `code/live_extraction.py`, `code/prototype/extraction_artifacts/full_run_03/`, and the consolidated final report.

Tradeoff:
The evaluation run has no semantic ground truth. Passing the operational audit proves contract and guard behavior, not correctness of every trusted model fact.

## 2026-09-13 — Count structured scheduled salary deterministically

Decision:
Count a structured credit with `status=scheduled` and `category=salary` on its supplied settlement date. Continue excluding pending credits and scheduled non-salary credits unless confirmed by trusted semantic evidence.

Reason:
Integration review found the engine discarded all structured “Next confirmed salary” rows unless the model redundantly emitted a fact. This violated the project rule to count confirmed salary on settlement and made structured-only requests unnecessarily pessimistic.

Alternative:
Require the model to restate every scheduled salary or count every scheduled credit.

Rejected because:
Structured evidence is authoritative and should not require semantic duplication; counting bonuses, commissions, and refunds before settlement would violate the conservative cash policy.

Evidence:
All 47 scheduled credits in the dataset are salary rows labeled “Next confirmed salary.” The new two-sided regression test passes, all 54 core tests pass, and cached-bundle replay `full_run_05` passes the 250-row independent audit with zero pipeline exceptions and zero new inference calls.

Tradeoff:
Five requests now expose positive but insufficient current capacity and one becomes a verified full-payment plan. The rule is intentionally category-specific to the contract.
## 2026-09-13 — Freeze a prototype-free production package

Decision:
Move the accepted semantic transport and target-identity extractor into active
`code/semantic_extractor.py`, keep only the two accepted prompt additions under
`code/prompts/`, and archive all prototype, research-analysis, and shadow-evaluation
material under the existing ignored root archive convention.

Reason:
The final runtime previously imported two modules and prompts from `code/prototype/`,
which obscured the source of truth and caused research-only files to enter `code.zip`.
The production migration preserves the exact provider, model, settings, system prompt,
schema, retry behavior, and scoped composition used by the accepted run.

Alternative:
Continue shipping the small subset of `prototype/` used by live extraction.

Rejected because:
It leaves an avoidable runtime dependency on experimental structure and makes the
submission harder to audit for reference leakage.

Evidence:
All 200 text prompts and 11 image prompts in the accepted saved run match the active
production prompt byte-for-byte after UTF-8 decoding. Every usable scoped bundle
matches its recorded raw response, deterministic composition reproduced all 200
composed artifacts, and a fresh 250-request deterministic replay reproduced
`output.csv` byte-for-byte with zero pipeline exceptions.

Tradeoff:
Research utilities are no longer immediately runnable from active `code/`; they remain
preserved and understandable in `archive/cleanup_20260913/`.

## 2026-09-13 — Admit event-linked and user-level images generically

Decision:
Select same-user images that are unassigned or assigned to the current request, so an
image may enter through a request, related event, or user scope.

Reason:
The problem contract explicitly supports all three image link types, while the prior
input join required an exact request ID.

Alternative:
Keep the exact-request join because all 11 evaluation images happen to have request IDs.

Rejected because:
That would encode an unnecessary dataset-shape assumption and weaken generality.

Evidence:
A new event-linked-image regression passes; preflight still selects exactly the same
11 evaluation images; the 250-row audit remains valid; `output.csv` is unchanged.

Tradeoff:
An unassigned same-user image is treated as user-level evidence for each of that user's
requests, matching the supplied linking contract and still excluding other-request and
cross-user images.

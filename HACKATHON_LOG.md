# HackerRank Orchestrate — Working Log

Concise project history for review and interview preparation. Record the action, what it established, and the next move. Keep sensitive data and full file contents out of this log.

## 2026-09-12 — Repository and contract review

- Action: Read `AGENTS.md`, `problem_statement.md`, and the participant-facing dataset schemas.
- Result: Confirmed the required output contract, 90-day safety requirement, lifecycle/status rules, and prohibition on using organizer-only data.
- Next: Profile the samples and build a research-only simulator.

## 2026-09-12 — Sample data investigation

- Action: Inspected 25 labeled requests, 2,288 sample-user events, 17 messages, and five sample images.
- Result: Found recurring cadences at 5/7/10/14/21 days and monthly intervals; identified payroll exceptions, pending obligations, lifecycle links, and image-only amounts.
- Next: Compare general recurrence and amount-forecasting rules.

## 2026-09-12 — Observed-cadence baseline

- Action: Built `analysis/sample_forecasting/scripts/investigate.py` and simulated status-aware cash flow with all-history mean expenses.
- Result: The literal 90-date baseline matched 3/25 safe amounts (all capped) and 19/25 earliest-full-payment dates. Settlement-date timing and persistent user_07 payday shift were supported.
- Next: Test whether residuals came from latent budgets, stream inclusion, or horizon choice.

## 2026-09-12 — Lifecycle, options, and evidence audit

- Action: Added `analysis/sample_forecasting/scripts/audit.py` to inspect linked events, statuses, image facts, spending-change permissions, and payment options.
- Result: Verified 71 sample option totals/fees, documented refund/authorization/investment lifecycle patterns, and confirmed labeled spending changes use permitted event flexibility and minimum amounts.
- Next: Decompose uncapped safe-amount residuals.

## 2026-09-12 — Latent-budget and structural experiments

- Action: Ran `analysis/sample_forecasting/scripts/latent_budgets.py` across robust centers, significant-digit rounding, expense-inclusion variants, hold timing, and two horizon definitions.
- Result: No general estimator substantially reduced uncapped error. Calendar endpoints improved a few boundary dates but slightly worsened uncapped amount error; removing flexible expenses introduced optimistic bias. Several residuals resembled missing or earlier variable-stream occurrences.
- Next: Stop sample-specific fitting and define an auditable semantic-to-ledger interface.

## 2026-09-12 — Initial implementation direction

- Action: Chose to preserve the specification-aligned baseline and plan a small vertical prototype before scaling.
- Result: The architecture remains semantic evidence resolution followed by deterministic projection, verification, ranking, and output validation. Remaining uncertainties are explicitly documented rather than patched by request ID.
- Next: Implement the evidence contract and traceable ledger for representative cases, then validate before full-dataset execution.

## 2026-09-12 — Tidy research artifacts

- Action: Grouped the sample forecasting scripts, reports, and generated outputs under `scripts/`, `reports/`, and `artifacts/`, with a short index at the analysis root.
- Result: All three research scripts run from the new locations; all generated CSVs match their pre-move hashes. The investigation logic and reported results remain unchanged.
- Next: Use the organized research record for the focused ledger verification and evidence contract.

## 2026-09-12 — Three-case verification and explicit stop gate

- Action: Produced provenance-tagged ledgers and independent Decimal replay for users 07, 21 and 12. Fixed the one-cycle diagnostic's universal day-15 reset and added six passing audit tests.
- Result: user_12 differs because July 1 rent is inside the literal horizon; user_21's labeled changes are allowed but unnecessary under this baseline, and advancing the existing fuel hold does not explain the residual. user_07's later payday phase remains an unresolved modeling assumption.
- Correction: The earlier log's statement that persistent user_07 timing was supported referred to label agreement and recent timing, not evidence of an indefinite amendment. September 23 is explicit; later dates are policy.
- Next: Resolve that duration/persistence policy before the evidence contract and representative prototype. Implementation paused under the user's final stop instruction; no estimator tuning or evaluation-request run occurred. Contract design, extraction metrics and prototype results remain pending, not completed.

## 2026-09-12 — Gate accepted; representative prototype completed

- Action: Accepted the user's explicit payroll persistence policy; implemented a strict evidence schema, deterministic resolution/Decimal ledger, candidate generation, safety verification, ranking and validated output in `prototype/`. Replayed reviewed semantic facts for payroll (07), image obligation (16), lifecycle (01), flexible spending (21) and regular-payroll/FX control (25).
- Result: 28 prototype tests pass, five outputs validate, all three selected payment plans verify, and two cases select no payment. The image supplies INR 100,000 Balance Due, while Python calculates the separate 12% rent amendment. Semantic extraction is session-reviewed replay; automated extraction correctness is not claimed.
- Failure handled: user_01 lacks sufficient historical salary cadence and user_25 breaches the reserve before same-day salary under the declared intraday convention. Both regress against labels and remain documented, with no invented income or label-fitting changes. Unknown future values block output; nested executable fields are rejected.
- Next: Connect schema-constrained semantic extraction for the same five cases and compare facts independently before expanding coverage. Broad estimator/horizon tuning remains stopped; no evaluation requests were run.

## 2026-09-12 — Boundary challenge before model integration

- Action: Added tests first for possible duplicates, transfer scope, paid-versus-due image values, unknown future obligations, stream targeting and standalone date amendments. Captured 11 failures across the initial 16 tests before editing the resolver.
- Result: Narrow fixes now pass 21 boundary tests and all 28 prototype tests. Fact permutations produce the same material state, hand-calculated ledgers agree, and the representative output CSV hash is unchanged. Seven fact types remain unchanged; trusted transfer-account scope is optional structured context, not a model assertion.
- Lesson: Preserving cash rows is insufficient if uncertain duplicate handling removes recurrence history. Valid JSON also cannot establish outstanding amounts, account scope or conflict precedence.
- Next: Review the completed boundary report. Stopped as requested without connecting any model API, starting extraction experiments or tuning sample labels.

## 2026-09-12 — Separate observed evidence from forecasting assumptions

- Before:

  > "We found the salary shift and used it."

- After:

  > "We discovered that the dataset supported the next salary date but not the duration of the change. We separated evidence from assumptions by making the semantic model report the observed change and the deterministic engine apply a documented forecasting policy."

## 2026-09-12 — Frozen Featherless extraction baseline completed

- Action: Added a shadow-only `zai-org/GLM-5.3-Flash` extractor, 10 reviewed cases, three-case repetition, strict scoring tests, and reproducible usage artifacts. Reviewed facts remain the only trusted resolver input.
- Result: Baseline first-attempt validity was 9/10; 3/15 references matched all meaningful fields; 0/3 repeat cases were stable. Unknown, possible-duplicate, and injection controls passed, while over-production, certainty, lifecycle, and vision reliability failed.
- Verification: 21 boundary, 28 prototype, 7 extraction, and 6 ledger-audit tests pass; representative-output SHA256 is unchanged.
- Next: Run one prompt-only emission/nullable-field rubric experiment with model, schema, cases, and settings frozen. Do not integrate or hide empty responses.

## 2026-09-12 — Audit semantic metrics, then relocate stable components

- Action: Audited all 63 saved emissions and original reference slots; corrected one-to-one comparison, field diagnostics, decimal normalization, availability handling and non-destructive rescoring. Added 12 deterministic evaluation/integrity checks.
- Result: Prior 3/15, 19 unsupported and 0/3 claims are superseded. Latest baseline has 5 complete and 4 partial recovered reference meanings; 1 of 2 assessable repeat cases is consistent. Missing user16 rent history and assistant-only reference approval remain explicit limitations.
- Action: Moved the shared schema/models, resolver, Decimal engine, plans and their tests to code/buy_or_wait; preserved compatibility commands and original empty entry points.
- Verification: 74 unique tests pass. Modules/schema are byte-preserved and representative CSV hash remains 2007B834DE8D1F0E6EED703D422FCF0A459C3EFE2B3B58525B4AB85A02E4D703. Source responses and reviewed facts were not overwritten; no new model calls.
- Next: Review v2 claim/reference annotations and the single-variable rent-history proposal. The proposal is not executed; prompt tuning, full-dataset runs, packaging and submission remain outside this task.

## 2026-09-12 — Repository layout tidy-up

- Action: Moved analysis/ and prototype/ beneath code/, flattened the single shared implementation and tests directly into code/, and updated imports, dataset paths, current reproduction commands, and Git ignore paths.
- Result: code/main.py replays five reviewed cases; code/evaluation/main.py reads saved audit usage/availability. The final usage report is a clearly marked pending template. No online evaluation or full-dataset runner was added.
- Verification: 74 unique tests pass. Existing fact bundles, saved API artifacts, analysis artifacts, and the five-case representative CSV retain their pre-move hashes. Offline audit regeneration succeeds without model calls.
- Next: Continue from the organized code layout; review the previously prepared evidence annotations before the separate proposed input-only experiment.

## 2026-09-12 — Implement reviewed rent-history experiment

- Action: Added offline preparation and capped shadow execution with attempt snapshots and a narrow review template.
- Result: 24 targeted tests pass; frozen extractor, schema, engine and saved outputs remain unchanged. No live inference executed.
- Next: Approve the three documented rubric conventions before a separately invoked live run.

## 2026-09-12 — Execute approved rent-history diagnostic

- Action: Ran six alternating logical runs, nine API calls; reviewed all three usable bundles.
- Result: Operationally inconclusive (control 1/3, treatment 2/3); all usable bundles mislink rent amendment and assert gross total as debt.
- Next: Consider only a small output-availability diagnostic; stopped without further calls or trusted integration.

## 2026-09-12 — Diagnose empty output and adjust transport

- Action: Four high/low reasoning calls, then four generous-budget JSON-mode comparisons.
- Result: Reasoning effort alone failed; omitted response_format produced 2/2 valid outputs versus JSON-mode 0/2 at 32768 tokens. Applied versioned transport update; 25 tests pass.
- Next: Validate availability beyond this small diagnostic before interpreting trusted semantic quality; no rent rerun performed.

- 2026-09-12T18:41:13.744619+00:00: Completed six alternating rent trials under provisional plain-JSON integration (seven calls). Final availability6/6; target separation control0/3, treatment1/3; gross-debt error5/6. Preserved envelopes and reviewed all37 usable facts. Next: propose one image-value definition change, not executed.
- 2026-09-12T18:50:30+00:00: Ran six frozen-input prompt comparison calls with one general image-value clarification. Availability6/6; gross-debt error control1/3 versus treatment0/3; no material availability or 12% regression. Next: one narrow stream/event targeting definition experiment may be considered; not executed.
- 2026-09-12T19:12:50+00:00: Ran six frozen-input targeting-definition calls. Control availability3/3, treatment2/3; usable targeting control0/3 versus treatment2/2; gross-debt errors persisted. Next: controlled composition confirmation only if desired; no trusted integration.

## 2026-09-12 — Build semantic evaluation data

- Action: Created a source-verified frozen split and drafted semantic reference records for the 14 development cases using the seven-fact contract.
- Result: Evidence IDs, ownership, schema shape, and unknown values validate offline; the 8-case holdout remains untouched.
- Next: Review development references before any future semantic scoring or model evaluation. No model inference, sample labels, affordability outputs, or end-to-end evaluation were included in this milestone.

## 2026-09-12 — Freeze development semantic references

- Action: Resolved five source-target gaps, corrected user_12/user_04 empty references, and bound all 14 cases to exact offline extractor requests.
- Result: Approved development reference v4 passes provenance, Pydantic, unknown-preservation, and 127 Python tests without model calls or holdout access.
- Next: A later task may build a semantic scorer or run model inference; neither was done here.

## 2026-09-12 — Freeze holdout semantic references

- Action: Bound the eight frozen holdout cases to byte-exact offline requests and annotated them with unchanged development conventions.
- Result: All eight have nonempty grounded facts; provenance and 132 Python tests pass. Development reference hash is unchanged.
- Next: A later task may score model extraction against the frozen development and holdout references; no inference or scorer was run here.

## 2026-09-12 — Paired target-exclusivity experiment

- Action: Compared one prompt sentence against frozen baseline across 14 development cases, three repetitions per arm.
- Result: Target conflicts 29 to 0, first validity 10/42 to 36/42, meanings 8/57 to 13/57; case passes 4/42 to 3/42. Did not adopt; holdout and frozen files unchanged.
- Next: Evaluate only confirmation-semantics wording against the original control.

## 2026-09-13 — Confirmation experiment and semantic-boundary escalation

- Action: Tested one confirmation-semantics sentence against frozen control for three development repetitions and audited target representation offline.
- Result: Meanings improved 12/57 to 15/57, but unsupported facts rose 84 to 93, harmful flags 6 to 9, unknown flags 77 to 101, and final validity fell 40/42 to 39/42. Treatment rejected; six required selectors across four cases expose an unresolved new-entity identity convention.
- Next: Control tower decides target identity and scorer/consumer equivalence before any further prompt or model experiment. Holdout files remain unmodified; final broad test discovery caused disclosed read-only validation access, while experiments and tuning remained development-only.

## 2026-09-13 — Implement target-identity-v1 and complete current-model loop

- Action: Added the development-only executable target contract, versioned reference/scorer, deterministic target candidates, and repeated current-model baselines. Tested unknown enumeration, minimality, expected-settlement certainty, and confirmation-state wording as single-variable paired experiments.
- Result: Target binding reached 59/60 in the first target-v1 baseline; all exact-event and new/unresolved targets were preserved. The best treatment reached 29/57 meanings and 12/42 case passes, but a direct image gross-total harm remained; current model is not integration-ready.
- Next: Stop prompt tuning and obtain a control-tower decision for a fixed-protocol stronger-model comparison. Preserve the target-v1 contract and accepted prompt prefix; keep holdout closed.

## 2026-09-13 — Enforce target-v1 at finance resolution

- Action: Wired the shared target validator into `finance.resolve`, migrated five redundant representative exact-ID selectors, and added strict/compatibility regression tests.
- Result: Extraction, target-v1 scorer, and deterministic resolver now share target identity semantics. The resolver compatibility branch is limited to consistent legacy redundancy; 46 named development/prototype tests pass.
- Next: Keep the current model outside integration and await the already documented model-comparison decision; no additional prompt tuning or holdout use.

## 2026-09-13 — Controlled DeepSeek model comparison completed

- Action: Verified Featherless `deepseek-ai/DeepSeek-V4.1-Flash` and ran 14 frozen development cases × 3 repetitions against GLM under the identical target-v1 contract and accepted prompt stack.
- Result: DeepSeek 20/57 meanings and 8/42 cases versus GLM 17/57 and 7/42; target correctness 49/51 versus 53/56; first validity 39/42 versus 41/42; unknown flags 8 versus 20; completion tokens 375,495 versus 50,271. Image composition remained invalid in a DeepSeek repetition and one final output was unavailable after retries.
- Decision: REJECT DEEPSEEK. Semantic phase remains not integration-ready; holdout and full dataset untouched.
- Next: Return to control tower for the next capability or multimodal strategy; do not resume broad prompt tuning.

## 2026-09-13 — Test scoped semantic extraction

- Action: Audited accepted GLM target-v1 failures, then ran three-repetition paired image-scoped and message-scoped development experiments with deterministic composition. Holdout and evaluation data were not used.
- Result: Image scoping recovered the required image meaning 3/3 versus 1/3, eliminated unsupported image facts and image gross-total harms, and improved aggregate meanings 19/57 to 22/57. Message scoping improved meanings 22/57 to 24/57 and unknown errors 79 to 40, but reduced first-attempt validity (41/42 to 39/42), increased calls (43 to 51), and remained unstable with three harmful certainty claims.
- Next: Keep scoped extraction only as guarded experimental research; semantic integration is not ready. Control tower must choose a stronger/separate multimodal strategy or accept a partial abstaining architecture.

## 2026-09-13 — Finish semantic research with guarded boundary

- Action: Re-audited scoped failures and replayed a deterministic semantic safety guard over saved message-scoped development outputs. The guard blocks invalid targets, missing unknown markers, unsettled confirmed credits, contingent confirmed income, and unsafe image claims without choosing replacement interpretations.
- Result: Guarded treatment retained 22/57 meanings, blocked 10 meanings, missed 25, reduced harmful trusted claims 3→0, had 0 false accepts and 1 false reject, and preserved 47/47 target-correct retained facts. The semantic phase is not coverage-ready but is safe enough for a guarded vertical integration phase.
- Decision: ACCEPT GUARDED PARTIAL ARCHITECTURE. Keep scoped extraction and guard research-isolated until the next phase explicitly integrates them; do not use holdout or the full evaluation dataset.

## 2026-09-13 — Pass guarded facts through deterministic finance

- Action: Added the canonical semantic boundary adapter and replayed 42 saved development bundles through guard, resolver, projection, and capacity using synthetic requests. Corrected `amount_paid` so it remains historical/informational and cannot become or block a separate current obligation.
- Result: Resolution 42/42; capacity available 32/42 and safely blocked 10/42; no blocked fact reached finance. Guarded metrics are 22/57 meanings, 0 harmful trusted claims, 0 false accepts, 1 false reject, and 46/46 retained target matches. Fifty-seven targeted tests pass.
- Decision: KEEP the guarded finance boundary as a production candidate. Online scoped extraction and full-dataset execution remain deferred.
- Next: Harden the development command and explicit non-holdout regression gate, then hand off to a separately authorized submission-runner phase.

## 2026-09-13 — Harden guarded pipeline preparation

- Action: Promoted the deterministic guard/resolver adapter to `code/semantic_boundary.py`, exposed a guarded development CLI, and added request-scoped input preparation plus model-agnostic scoped composition.
- Result: Core tests pass (53 unittest), scoped/guard tests pass (7 pytest), the guarded CLI resolves 42/42 traces with capacity available 32/42 and safely blocked 10/42, and `git diff --check` reports no patch errors.
- Review: ACCEPT. The boundary and offline preparation are suitable for the submission-runner implementation; live model invocation remains deliberately separate.
- Next: Wire the live GLM scoped caller with immutable per-attempt usage artifacts and validate it on a tiny development smoke test before any full evaluation run.

## 2026-09-13 — Correct scoped protocol and finish semantic research

- Action: Found the accepted prompt suffix missing from the original scoped harness, fixed the protocol, reran paired image and message experiments, replayed the guard, and ran one final text-only GLM-5.3 specialist comparison with shared Flash image outputs.
- Result: Image scoping is retained for safety (harm 1→0); corrected message scoping is rejected (21/57→17/57 meanings); guarded trusted coverage is 21/57 with 0 false accepts/rejects and 50/51 retained target matches. Full GLM is rejected: 21/57 versus Flash 22/57, 40/42 versus 42/42 final availability, 46/54 versus 55/58 target correctness, and about 8.6x text-call cost.
- Decision: Freeze a GUARDED PARTIAL ARCHITECTURE and stop semantic tuning. Earlier decomposition/final-handoff metrics are superseded by `SEMANTIC_SCOPED_PROTOCOL_CORRECTION_20260913.md` and `SEMANTIC_PHASE_CONSOLIDATED_FINAL_20260913.md`.
- Next: Submission/package verification only; do not reopen models, prompts, or fact types without a new concrete defect.

## 2026-09-13 — Complete guarded submission integration and audit

- Action: Added bounded model context, resumable per-request extraction/decision artifacts, a canonical live entry point, deterministic output audit, and actual usage accounting. Two rejected launch artifacts preserve a missing-env failure and an over-broad-context run; the bounded run completed.
- Result: Final saved run: 250 requests, 217 GLM-5.3-Flash calls, six retries, 3,090,692 tokens, one extraction unavailable, and zero pipeline exceptions. Independent audit passes all 250 rows and guard replays; 20 verified plans, 200 verified no-plan outcomes, and 30 explicit safety abstentions. Six known harmful facts were blocked and zero were trusted.
- Review: ACCEPT operational integration with the documented guarded-partial limitation. Estimated model cost is $0.5387 total at provider rates checked 2026-09-13.
- Next: Run final tests, build `code.zip`, verify archive contents and hashes, then submit `code.zip`, `output.csv`, and `log.txt`.

## 2026-09-13 — Correct scheduled-salary integration defect

- Action: Investigated the unexpectedly low structured-only recommendation rate and found scheduled salary rows were discarded without redundant model confirmation. Added the contract-specific salary rule and a two-sided test that keeps scheduled non-salary credits excluded.
- Result: The first replay seed (`full_run_04`) placed caches one directory too high and accidentally began fresh inference; it was stopped after 63 decisions and rejected. The corrected `full_run_05` verified all 200 cache paths and used an intentionally invalid API token, proving zero additional provider calls. All 54 core tests pass. The accepted replay changed six outputs: five gained positive but insufficient capacity and one gained a verified full-payment plan. Final counts are 11 full, 10 installment, 199 verified no-plan, and 30 safety-abstained; the 250-row audit passes with zero pipeline exceptions.
- Review: KEEP. This fixes deterministic use of authoritative structured evidence and does not change the frozen semantic boundary.
- Next: Rebuild and verify the final archive, then submit.
- Date: 2026-09-13
  Action: Completed the final execution-path, anti-workaround, provenance, cleanup,
  output, abstention, package, and clean-room audits. Migrated accepted extraction out
  of `prototype/` and archived research without changing predictions.
  Result: Active tests pass (59/59); all 250 saved semantic decisions replay
  byte-identically; isolated package preflight and audit pass with zero exceptions.
  Next step: Freeze hashes and submit `code.zip`, `output.csv`, and the chat transcript.

- Date: 2026-09-13
  Action: Generalized image selection to include same-user event-linked and user-level
  evidence, with an explicit regression test.
  Result: Evaluation scope remains 11 images, predictions are byte-identical, all 60
  tests pass, and the rebuilt package passes a second isolated clean-room audit.
  Next step: Submit the frozen artifacts; do not continue optimization.

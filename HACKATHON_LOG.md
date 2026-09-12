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

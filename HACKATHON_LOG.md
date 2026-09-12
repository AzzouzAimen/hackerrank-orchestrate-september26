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

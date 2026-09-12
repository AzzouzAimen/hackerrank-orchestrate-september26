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


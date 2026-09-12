**No general latent-budget estimator substantially resolves the uncapped residuals.** The best literal-90-date estimator improves uncapped normalized MAE from 3.5746% to 3.5679%, with unchanged 19/25 date accuracy: too small to justify a policy change. A rounded winsorized estimator does recover one uncapped amount exactly, but this is isolated evidence after comparing many variants.

The more informative result is structural: several positive residuals are close to an entire variable-stream occurrence absent before the baseline minimum. This suggests investigating forecast phase/reservation conventions, rather than assuming every discrepancy is a noisy mean. It does not establish that the observed historical cadences are wrong.

**Experiment and metrics**

The experiment preserves the previous recurrence, semantic and FX assumptions. Four centers—mean, median, 20% trimmed mean, and 20% winsorized mean—are evaluated unchanged and rounded to 1, 2, or 3 significant digits. All 16 estimators run under both horizons. Rounding applies only to streams with differing historical amounts; fixed contractual amounts are preserved. Significant digits provide a magnitude-dependent rule with no currency or category constants. The 20% tail treatment is a conventional research choice, not an inferred property of this dataset.

Six further variants test three expense-inclusion policies under both horizons; one tests immediate pending-debit reservation. There are 39 variant rows, including equivalent inclusion policies. No label-derived center is used in a scored forecast.

There are **21 uncapped labels** and four capped labels. NMAE is the mean absolute safe-amount error divided by each requested amount; bias is the same mean with the sign retained (positive means overestimating safe capacity). These metrics are not divided by the labeled safe amount, which can be very small. “Exact” uses the prior 0.011 currency-unit tolerance. Improved/regressed counts compare absolute amount errors against the original mean/90-date baseline, with that same tolerance. All comparisons are exploratory and in-sample.

| Variant | All NMAE | Uncapped NMAE | Uncapped bias | Exact all / uncapped | Dates | Improved / regressed |
|---|---:|---:|---:|---:|---:|---:|
| mean/all/90dates | 3.297% | 3.575% | -0.346% | 3 / 0 | 19 | 0 / 0 |
| mean_sig3/all/90dates | 3.291% | 3.568% | -0.349% | 3 / 0 | 19 | 8 / 11 |
| mean_sig2/all/90dates | 3.324% | 3.621% | -0.302% | 3 / 0 | 19 | 6 / 13 |
| median/all/90dates | 3.492% | 3.690% | -0.413% | 3 / 0 | 20 | 8 / 11 |
| trimmed20/all/90dates | 3.381% | 3.644% | -0.344% | 3 / 0 | 19 | 7 / 12 |
| winsor20/all/90dates | 3.342% | 3.625% | -0.291% | 3 / 0 | 19 | 8 / 11 |
| trimmed20_sig2/all/90dates | 3.371% | 3.610% | -0.297% | 3 / 0 | 19 | 10 / 9 |
| winsor20_sig2/all/90dates | 3.336% | 3.635% | -0.239% | 4 / 1 | 19 | 12 / 7 |
| mean/all/calendar | 3.031% | 3.608% | +0.594% | 4 / 0 | 22 | 2 / 1 |
| trimmed20_sig2/all/calendar | 2.950% | 3.511% | +0.511% | 4 / 0 | 22 | 12 / 9 |
| winsor20_sig2/all/calendar | 2.963% | 3.527% | +0.560% | 5 / 1 | 22 | 13 / 8 |
| median/all/calendar | 3.079% | 3.665% | +0.468% | 4 / 0 | 23 | 10 / 11 |
| mean/fixed_only/90dates | 6.501% | 7.740% | +6.097% | 4 / 0 | 22 | 4 / 15 |
| mean/fixed_only/calendar | 7.855% | 9.351% | +8.162% | 4 / 0 | 22 | 4 / 16 |

The complete 39-row table is `latent_variant_scores.csv`; `latent_variant_samples.csv` records every amount/date regression. Mean rounded to three significant digits improves eight samples and worsens eleven. Trimming then rounding to two digits with the calendar horizon improves twelve and worsens nine. Winsorizing then rounding to two digits with the calendar horizon improves thirteen and worsens eight. None of those three variants loses a previously correct date, but their aggregate uncapped error improvements are small.

The winsorized/two-digit/calendar variant exactly matches sample 08's EUR 284.57 and April 15 date. Its amount regressions are samples **03, 04, 10, 13, 14, 17, 20, 23**. The trimmed/two-digit/calendar variant regresses **06, 07, 08, 10, 13, 14, 17, 22, 23**. These exceptions argue against interpreting one exact match as recovery of the label-generating policy.

**Residual decomposition**

For each uncapped label, `target = minimum_balance_to_keep + labeled_safe`. Define `R = simulated_minimum - target`. Positive R means the simulator leaves too much cash; negative R means it leaves too little. This differs materially from safe-amount error when the predicted amount is clipped: sample 05's minimum residual is −5,261.85, even though its clipped safe-amount error is only −737; sample 21's minimum residual is +129.78, although its capped predicted amount error is +31.05.

At a fixed binding date, the cash equation is:

```text
minimum = opening balance + credits - explicit obligations - sum(count_j * amount_j)
sum(count_j * change_in_amount_j) = R
```

The per-stream decomposition in `latent_residual_decomposition.csv` lists counts, cumulative debits, and the amount required if that category alone absorbed the residual. It also solves that one-category counterfactual by rerunning the whole path, allowing the minimum date to move. Empty global solutions mean a nonnegative amount in the searched range could not achieve the target. These are **label-conditioned diagnostic alternatives, not inferred budgets or proposed predictions**. Multiple categories can generally produce the same minimum: one scalar residual cannot identify a vector of latent budgets.

The table reports the implied and simulated minima, and the percentage adjustment to **all variable expenses together** that would reconcile the current binding-date equation. That percentage is local: it can move the minimum, and is not claimed to solve the full trajectory.

| Sample | Implied minimum | Simulated minimum | Residual R | Local uniform variable change |
|---|---:|---:|---:|---:|
| 02 | 46,387,539.20 | 47,495,165.49 | +1,107,626.29 | +16.54% |
| 03 | 3,541,700.00 | 3,640,437.00 | +98,737.00 | +12.40% |
| 04 | 39,088,400.00 | 41,295,886.07 | +2,207,486.07 | +29.55% |
| 05 | 13,837.00 | 8,575.15 | -5,261.85 | -30.56% |
| 06 | 1,403.30 | 1,323.82 | -79.48 | -25.27% |
| 07 | 180,170.56 | 179,237.22 | -933.34 | -4.05% |
| 08 | 1,084.57 | 1,085.20 | +0.63 | +0.43% |
| 10 | 238,100.00 | 188,826.85 | -49,273.15 | -15.14% |
| 11 | 46,651,245.00 | 46,460,466.62 | -190,778.38 | -2.00% |
| 13 | 1,733.40 | 1,790.78 | +57.38 | +2.72% |
| 14 | 2,797.74 | 2,816.29 | +18.55 | +3.53% |
| 15 | 1,283.05 | 1,205.08 | -77.97 | -25.07% |
| 17 | 409,949.58 | 409,123.67 | -825.91 | -1.87% |
| 18 | 1,862.00 | 1,946.05 | +84.05 | +20.81% |
| 19 | 121,620.00 | 117,976.15 | -3,643.85 | -10.97% |
| 20 | 69,900.00 | 73,351.68 | +3,451.68 | +23.23% |
| 21 | 3,343.35 | 3,473.13 | +129.78 | +39.66% |
| 22 | 975.46 | 964.62 | -10.84 | -11.19% |
| 23 | 36,152.00 | 35,360.17 | -791.83 | -8.90% |
| 24 | 64,420.00 | 64,539.29 | +119.29 | +0.82% |
| 25 | 24,804,100.00 | 23,755,183.40 | -1,048,916.60 | -15.65% |

Ten minimum residuals are positive and eleven negative. There is no consistent direction supporting a universal upward or downward budget correction. In many cases even attributing the discrepancy to the largest variable stream requires tens of percent of change: sample 02 needs utilities +54.4% if utilities alone explain it; sample 04 needs +110.2%; sample 21 needs shopping +106.0%. Small significant-digit rounding cannot explain those single-stream alternatives.

A different pattern emerges from streams whose first projected occurrence falls **after** the binding minimum:

| Sample | Counterfactual extra expense before minimum | Residual to explain | Extra expense | Residual remaining |
|---|---|---:|---:|---:|
| 02 | One dining occurrence | 1,107,626.29 | 1,083,819.45 | 23,806.84 |
| 03 | One transport occurrence | 98,737.00 | 91,041.06 | 7,695.94 |
| 18 | One dining occurrence | 84.05 | 85.63 | −1.58 |
| 20 | One dining occurrence | 3,451.68 | 3,423.79 | 27.89 |
| 21 | One transport and one dining occurrence | 129.78 | 124.64 | 5.14 |

This explains why changing centers alone can fail: these streams have zero weight in the current binding-date cash equation. Their amounts cannot lower that particular balance until an occurrence is added, moved, or reserved earlier. **This is a phase/reservation hypothesis, not evidence to add extra expenses per sample.** The complete one/two-missing-stream counterfactual enumeration is saved, including alternatives that fit poorly. No such label-selected occurrence is fed back into forecasts.

**Evidence for and against clean latent centers**

Across 126 variable streams, median within-stream coefficient of variation is **12.98%**, while median absolute first-half versus second-half mean drift is **4.42%**. A stable underlying center plus noise is plausible. However, rounding the full-history mean to two significant digits moves it by a median **0.54%**; virtually any mean can be made to look close to a sufficiently fine round number. This is not independent evidence that the generator used that grid.

As a label-independent diagnostic, fit each estimator on the chronological first half and predict the second-half mean. Average absolute center error, normalized by the full-history mean, is **5.892% for plain mean**, **5.887% for three-digit mean**, **5.990% for two-digit mean**, **6.188% for winsorized mean**, and **6.356% for two-digit winsorized mean**. One-digit mean is much worse at **11.740%**. The second-half average is itself noisy, so this is not a latent-budget ground truth or a calibrated significance test. It nevertheless provides no meaningful independent support for stronger quantization.

There is therefore weak support for a stable center, but **no identified round grid, noise distribution, or latent-budget recovery estimator**. Clean centers in one currency need not remain clean after conversion. The evidence does not justify currency-specific grids, category multipliers, or rounding toward labels.

**Expense inclusion and horizon effects**

“Fixed” means `flexibility == fixed`, not “historical amount never varies.” All explicit pending/scheduled debits remain included; the ablations remove only inferred recurring streams. `fixed + protected`, `fixed only`, and `exclude stoppable/reducible/reducible_or_stoppable` produce identical predictions in these samples. Their definitions are distinct, but the retained forecast groups coincide here.

On 90 dates, excluding flexible recurrence raises uncapped NMAE from **3.575% to 7.740%**, and uncapped bias from **−0.346% to +6.097%**. Fifteen sample amounts worsen. Date accuracy rises to 22, but loses sample 18's previously correct date. Under the calendar horizon, uncapped NMAE gets still worse, **9.351%**. Treating discretionary recurrence as free baseline savings is neither empirically supported nor consistent with reporting baseline capacity before optional changes.

For plain mean, the calendar endpoint changes **only five samples**:

- 05: safe error −737.00 → +431.85; improved.
- 10: safe error −12,700.00 → +19,826.85; worsened.
- 12: safe error −4,793.77 → 0; immediate full-payment date recovered. This is a capped sample.
- 08 and 13: recover the labeled full-payment dates; safe amounts do not change.

Thus the calendar endpoint is **not broadly superior for uncapped amounts**: their NMAE slightly worsens, 3.575% → 3.608%, even though all-sample NMAE improves and three dates are recovered. Its visible advantage is concentrated in boundary cases, particularly capped sample 12. All 16 center estimators were evaluated under both horizons; the strongest calendar combinations still leave almost all uncapped amounts inexact. The literal 90-date convention remains the specification-aligned baseline.

Moving all pending debit holds to request day produces identical safe amounts and earliest dates in all 25 samples. These obligations already fall before the relevant minima in this dataset. This rules out that particular hold-timing explanation for these residuals; it does not identify whether an available-balance snapshot already contains a hold.

**Most likely disagreement categories—not definitive diagnoses**

Labels identify neither daily balances nor stream budgets. The following classifications separate direct sensitivity evidence from tentative explanations. “Cadence” here includes projected phase or a reservation convention; the historical interval itself remains well supported.

| Sample(s) | Classification | Evidence/qualification |
|---|---|---|
| 02, 03, 18, 20, 21 | Cadence/phase error hypothesis | Missing-before-minimum occurrences explain much of the residual; no justified replacement schedule established |
| 05, 10, 12 | Horizon error hypothesis | Large minimum changes when boundary bills are excluded; 10's safe error actually worsens, and 05/10 remain inexact |
| 08 | Amount-estimation error plus horizon | Rounded winsorization matches amount; calendar boundary needed for labeled date |
| 07, 17, 24 | Amount-estimation error hypothesis | Relatively small variable-budget changes can reconcile minima; 17's date responds to estimator choice |
| 11 | Semantic-state error hypothesis plus amount uncertainty | Explicit base-pay amendment conflicts with the much later labeled full-capacity date; center changes do not fix that date |
| 13 | Horizon for date; amount estimation unresolved | Calendar boundary fixes date, not amount |
| 14 | Unexplained; semantic state incomplete | Childcare is announced without an amount, so no quantitative attribution is justified |
| 04, 06, 15, 19, 22, 23, 25 | Unexplained | Neither center recovery nor the tested hold/horizon changes establishes a general explanation; same-day phase and stream membership remain possible |

Samples 01, 09, and 16 already match both requested fields but are capped and offer little information about the exact baseline minimum. Sample 12 is capped too, so `floor + labeled_safe` is only a lower bound there; it is intentionally excluded from the implied-minimum equality table.

**Policy currently supported and remaining identification limits**

Keep observed cadences, all recurring expenses before optional changes, explicit semantic amendments, and plain mean as the working diagnostic policy under 90 dates. Retain median and robust-center variants for sensitivity analysis, not as a newly validated latent-budget model. Three-digit mean is effectively indistinguishable in practical performance. The best calendar combination lowers uncapped NMAE only from 3.5746% to 3.5114% while changing the horizon; that is not a substantial general resolution.

The samples fundamentally do not identify: each stream's true budget; a noise model or round-number grid; whether some variable expenses were reserved earlier by the label generator; the exact horizon convention; unquantified childcare or ambiguous future salary duration; or the snapshot's hold treatment. Aggregated minima supply too few equations, and alternative changes can move the binding date. The next useful evidence would be reference daily balances/forecast events or clarification of these conventions, not more sample-specific fitting.

Reproduce with `python code/analysis/sample_forecasting/scripts/latent_budgets.py`. Research artifacts are in `../artifacts/` and prefixed `latent_`; previous baseline tables and the original report are preserved. The simulator extension adds experimental hooks and stream-history diagnostics only. No final submission pipeline or evaluation predictions were implemented.

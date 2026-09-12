The investigation supports the proposed separation between semantic evidence resolution and deterministic forecasting, but **does not identify a general rule that reproduces the sample amounts**. With the observed cadences, explicit payroll amendments, and an all-history mean expense forecast, the 90-date baseline matches **3/25 safe amounts and 19/25 full-payment dates**. All three exact amounts are capped at the requested amount. No tested estimator exactly reproduces an uncapped safe amount.

The strongest unresolved issue is the forecast boundary. Ending at the last day of the request month plus two further calendar months raises date agreement to **22/25** and amount agreement to **4/25**. That is an explanatory hypothesis, not a replacement for the stated 90-day contract. Forecast amount, timing, and semantic uncertainty remain confounded; these results do not prove the labels are wrong.

Only participant-facing data and the public specification were used. No evaluation predictions, final pipeline, external model calls, browser verification, or organizer-file inspection were performed. All numerical results below were computed in Python. Identifiers in analysis tables identify evidence; they are not prediction exceptions.

**1. Data structure and observed patterns**

The provided files contain 275 profiles, 25 labeled sample requests, 250 evaluation requests, 25,342 financial events, 215 messages, 16 image references, 790 payment options, and 134 exchange-rate rows. The sample users account for 2,288 events, 17 messages, five image references, and 71 payment options. Each request joins to its profile and financial history through `user_id`; messages can additionally target a request or a single event. A blank event link is not evidence that the message is irrelevant.

Sample event statuses are 2,265 settled, nine pending, eight scheduled, two failed, two cancelled, and two unrealized. All-data counts and lifecycle counts are in `evidence_counts.json`.

Observed adjacent gaps in the samples' amount-populated, settled groceries/transport/dining histories are **617 seven-day, 228 fourteen-day, 187 ten-day, 104 twenty-one-day, and 104 five-day gaps**. There are no other gaps in those filtered streams. Descriptions vary across these regular category streams. This is strong evidence for category-level cadence inference in these particular spending categories, not for treating each merchant description as a separate subscription.

The baseline detects 153 monthly expense streams, 25 seven-day streams, 19 fourteen-day streams, 11 ten-day streams, 13 twenty-one-day streams, and three five-day streams. These are algorithm outputs, not supplied ground-truth stream annotations.

Important limits of the evidence:

- There are **no sample settled rows with settlement date equal to request date**. Same-day settled snapshot semantics cannot be empirically settled here.
- The internal-transfer message for user_18 has no matching debit/credit pair in that user's supplied event history. Do not invent the pair.
- The childcare announcement for user_14 supplies neither an amount nor a precise debit schedule, and no childcare event exists in that user's history. It cannot become a numeric forecast without inventing facts.
- All exchange-rate values are constant within a currency pair, despite their dated rows. The samples cannot distinguish correct date selection from an incorrect selection that happens to use the same rate.

**2. Best-supported recurrence mechanism**

Use a small hierarchy rather than a single grouping rule:

1. Resolve status, transaction lifecycle, and semantic exclusions before inferring recurrence. A refund, incidental purchase, commission, final payroll, or image receipt does not become a recurring stream because its category is repeated.
2. For routine variable groceries, transport, and dining, group compatible records by user, category, currency, and flexibility. Descriptions are evidence about membership, not necessarily stream identifiers.
3. For subscriptions and fixed commitments, use counterparty/description plus category where available. A category may contain independent obligations; the category-only grouping used in this investigation is not a universal production rule.
4. Compare calendar-month recurrence with fixed-day gaps. Advance monthly obligations by calendar month, preserving the day with end-of-month clamping. Advance five/seven/ten/fourteen/twenty-one-day streams by their observed interval.
5. Keep independent income sources separate. A primary household salary and uncertain second income must not be averaged into one salary stream. Apply an explicit amendment to the affected stream, with its effective date and duration.

The exploratory implementation requires at least three expense observations, at least 70% monthly day-of-month support or 70% support for the modal fixed gap, and handles obvious off-calendar monthly incidental rows separately. **Those thresholds are hypotheses, not learned constants established by 25 labels.** The routine sample variable streams are much cleaner than the thresholds require. Confirmed new salaries need a different evidence path; three historical payments cannot be a universal prerequisite.

Evidence against shortcuts: description-only grouping matches just 12/25 dates with 13.08% normalized amount error. Forcing all variable streams to seven days gives 14/25 dates and 13.82% error; forcing fourteen days gives 18/25 and 6.55%. The observed-cadence baseline gives 19/25 and 3.30%.

**3. Recurring amount experiments**

The table below varies only the expense amount estimator. Fixed streams retain their fixed amount; payroll uses the latest relevant amount plus explicit amendments. Predictions are compared to labels only after simulation. Mean normalized absolute error is the average of `abs(predicted_safe - labeled_safe) / requested_amount`, so currencies are not pooled as if their units were comparable. Exact means a difference below 0.011 home-currency units. This is in-sample descriptive evaluation, not a held-out accuracy estimate.

<!-- AMOUNT_TABLE -->
| Estimator | Exact safe amounts | Exact dates | Normalized MAE |
|---|---:|---:|---:|
| mean | 3/25 | 19/25 | 3.297% |
| median | 3/25 | 20/25 | 3.492% |
| recent2 | 3/25 | 19/25 | 3.710% |
| recent3 | 3/25 | 19/25 | 3.325% |
| recent4 | 3/25 | 19/25 | 3.692% |
| recent5 | 3/25 | 19/25 | 3.814% |
| recent6 | 3/25 | 19/25 | 3.571% |
| recent8 | 3/25 | 19/25 | 3.361% |
| recent90 | 3/25 | 19/25 | 3.448% |
| trimmed_mean | 3/25 | 19/25 | 3.381% |
| p75 | 1/25 | 13/25 | 5.271% |
| last | 3/25 | 20/25 | 3.910% |
| max | 1/25 | 11/25 | 9.705% |
<!-- END_AMOUNT_TABLE -->

All-history mean has the lowest normalized amount error of these candidates. Recent-three mean is close. Median and last amount each explain user_17's March 15 full-payment date where mean gives April 15, but neither reproduces that user's exact safe amount. No estimator is an identified ground-truth rule. Taking the maximum or 75th percentile does not solve the discrepancies and often makes full-payment dates too late.

**Recommendation from evidence:** retain all-history mean as the simplest diagnostic baseline, median/recent-three as sensitivity checks, and exact current contractual amounts for fixed commitments. Do not present the mean as a guaranteed conservative bound for variable necessities. The specification's word “conservative” does not identify an exact percentile, margin, or estimator. The sample amounts remain insufficiently explained to lock that policy down.

**4. Cash-flow timing, state, and the forecast boundary**

Start from `current_available_balance`. Historical settled cash explains streams and lifecycle state; replaying it into this current balance would double-count it. Keep pending obligations separate from historical transactions.

| Row state | Baseline treatment | Evidence level |
|---|---|---|
| Historical settled cash | Already represented by current balance; use for history and semantic context | Snapshot interpretation supported by profile definition |
| Confirmed scheduled salary | Credit on settlement date; replace the inferred occurrence rather than adding a duplicate | Explicit contract |
| Scheduled debit | Debit on settlement date, including known one-time commitments | Contract and supplied dates |
| Pending debit | Reserve the obligation; baseline posts it on settlement date, or today if overdue | Reservation required; exact hold timing remains partly unidentifiable |
| Pending credit/refund | No spendable credit until settlement confirmation | Explicit contract |
| Failed or cancelled | No cash movement from that row; inspect any successor | Explicit contract |
| Unrealized/non-cash | No available cash; never convert portfolio value to money | Explicit contract |

For a pending debit due after an intervening salary, merely posting at settlement may allow more spending now than immediately subtracting a hold. The current samples do not isolate that situation sufficiently. A final design needs an explicit available-balance/hold convention and must avoid reserving the same hold twice. The research baseline does not silently claim that question is solved.

Generate obligations due on `request_date` unless a settled row proves they are already included in the snapshot. The dataset contains inferred due-today expenses even though it contains no settled-today sample rows. Excluding all forecast expenses on request day drops date agreement from 19 to 17 and raises normalized error from 3.30% to 3.94%. This supports including unpaid inferred obligations, not replaying already-settled same-day cash.

The simulator uses daily net balances. With no intraday timestamps for cash settlement, whether a same-day credit is usable before a debit is not empirically resolved. A verifier should declare its ordering convention; daily netting is the convention behind these tables.

For baseline balances `B[t]`, reserve `F`, and requested amount `Q`, the deterministic capacity calculation is:

```text
safe_today = max(0, min(Q, min(opening_balance, all daily balances) - F))
capacity_at_t = min(B[t:]) - F
earliest_full = first t with capacity_at_t >= Q
```

Check the prefix and the complete payment schedule too: a suffix-capacity calculation cannot excuse an earlier baseline reserve breach. The earliest-full field is calculated without optional spending changes and independently of payment-method preferences. The main experiment uses **90 dates, request date through request date + 89 days**. The alternative including date +90 is recorded as an ablation; it contains 91 calendar dates when the request day is included.

| Boundary | Exact safe amounts | Exact dates | Normalized amount error |
|---|---:|---:|---:|
| 90 dates, through +89 | 3/25 | 19/25 | 3.30% |
| Through +90, including request day | 2/25 | 18/25 | 6.56% |
| Through end of request month plus two months | 4/25 | 22/25 | 3.03% |

The +90 variant adds an October 2 rent debit for user_09, reducing predicted safe capacity to EUR 30.76 and losing the immediate-full label. The +89 convention excludes that extra date and reproduces the capped EUR 166.61 request. Thus endpoint inclusivity alone matters materially.

The three-calendar-month hypothesis additionally resolves the date failures for users 08, 12, and 13. It does so by excluding early-next-month expenses still inside their rolling 90-date windows. It also improves the no-income reserves for users 05 and 10, without exactly matching them. Its endpoints range from 80 to 91 days after request among the samples, so **it is not equivalent to 90 days and must not be adopted merely for label agreement**. This is evidence of an unresolved horizon/forecast mismatch, not proof of how the labels were generated.

User_07 provides a much cleaner timing result. The August salary has `event_date=2024-08-15`, `settlement_date=2024-08-23`; message_05 confirms September 23. Using the latest settlement-day phase for subsequent months gives the labeled **2024-10-23** earliest date. Reverting to the 15th after one delayed cycle gives **2024-10-15**. Ignoring messages and using event-date phase also gives October 15. The baseline predicts INR 86,237.22 versus the labeled INR 87,170.56, so payday inference is supported while expense amounts remain unresolved. The message explicitly changes the next payday; persistent monthly phase is additionally supported by the label, not explicitly stated for every future month.

**5. Income semantics and message effects**

| Evidence/case | Baseline interpretation | What remains uncertain |
|---|---|---|
| user_01: prorated first salary; next confirmed salary | Use confirmed ZAR 23,320 going forward, not prorated ZAR 12,826 | Extrapolation beyond the one confirmed cycle relies on ordinary ongoing payroll semantics |
| user_02, message_01 | Monthly pay becomes IDR 42,750,000 from August 15 | Clear amount/date amendment; labeled safe amount still differs |
| user_03: payroll, arrears, payslip; message_02 | Keep regular IDR 4,365,000; arrears are one-time; historical net pay is not new cash | Payslip net matches historical salary; do not create a second recurring month-end salary |
| user_04, message_03 | Continue regular pay; exclude an unapproved quarterly bonus | A prior bonus settlement does not confirm a future bonus |
| user_05: final employer payroll | End payroll extrapolation | Baseline reserve falls below the floor, unlike the positive labeled headroom; do not restart salary to force a match |
| user_06, message_04 | EUR 1,037.52 is the affected next payroll; baseline retains this latest regime | Message does not specify all later pay cycles; no justified automatic restoration date |
| user_07, message_05 | Shift next payday to September 23; persistent phase tested separately | Persistent versus one-cycle delay distinguished by labeled October date |
| user_08, message_06 | Next EUR 1,422.85 overrides last historical EUR 782.57 | Message calls this a reduction although it exceeds the last row; comparison likely concerns another reference salary, not arithmetic evidence of a different amount |
| user_09: varying freelance payments twice monthly | Do not treat project payments as confirmed future cash | Full payment is safe under the 90-date baseline without forecasting this income, so that label does not prove freelance recurrence |
| user_10, message_07: app earnings | Do not count unwithdrawable or unconfirmed future gig earnings | Repeated payouts alone do not confirm future payouts; positive labeled headroom remains unexplained |
| user_11, message_08 | Explicitly confirmed base IDR 38,760,000; exclude unapproved commissions | History says IDR 23,256,000. Amendment gives May 15 capacity; label says July 15. Ignoring amendment gives June 15, still not July 15 |
| user_12, message_09 | Seasonal contract ended; no renewal/off-season income | Immediate full capacity label is horizon-sensitive; don't invent seasonal renewal |
| user_13: primary and second household income | Continue confirmed primary EUR 1,343.54; exclude variable second income that stopped appearing in February | Absence alone is not a formal cancellation; continuing secondary income needs evidence. Label does not establish an amount forecast for it |
| user_14, message_10 | Regular EUR 2,717 resumes August 15 | New childcare is unquantified; numeric debit cannot be reconstructed |
| user_15, message_11 | Confirm EUR 1,661 January 15; don't add a separate “first” salary over the existing stream | “First salary” wording conflicts with two historical first-job payrolls; exact future duration not stated |
| user_16, message_12 | Increase recurring rent by 12% at the next occurrence | Distinguish this new rent from the separate outstanding rent receipt |
| user_18, message_13 | Treat any actually matched same-owner transfer as internal | No pair supplied here; message creates no numeric event |
| user_20, message_14 | Pending refund contributes zero | No settlement date confirmation for usable credit |
| user_22, message_15 | Portfolio valuation contributes zero cash | A valuation is not proceeds |
| user_23, message_16 | Prize still processing contributes zero | Verification is not settlement |
| user_24, message_17 | Settled prize is historical and one-time | Already in opening balance; no repeated prize income |

This supports explicit semantic facts such as `recurring`, `one_time`, `ended`, `amount_override`, `date_override`, `effective_date`, and `duration_unknown`, each with evidence references. It does not support handing arithmetic to a language model or treating every salary-category row as recurring.

**6. Image evidence and reusable lifecycle rules**

The five sample images were visually inspected. `IMAGE_FACTS` in the script contains financial-field transcriptions with their source image, not label-derived values:

- image_01: net pay IDR 4,365,000, rather than gross earnings. Historical settled event, used as corroboration.
- image_02: outstanding balance INR 100,000, not total receipt INR 200,000 or a new INR 200,000 recurring rent. Scheduled for August 16 in the event row.
- image_03: paid grocery receipt INR 41,272. Historical one-time bulk purchase; do not add it to current cash outflows or automatically redefine the recurring grocery budget.
- image_04: visible item bill INR 2,854; the bottom is cropped, so the final payable total is uncertain. The associated purchase is historical. Baseline excludes this isolated receipt from cadence/amount learning rather than claiming the cropped total is definitive.
- image_05: INR 704.05 through February 6, INR 822.05 after February 6. The request is February 7 and expected settlement February 9, so baseline reserves INR 822.05. Using INR 704.05 would change headroom by only INR 118 and cannot explain the larger sample discrepancy.

The all-data lifecycle inventory contains 14 settled charge/refund links, eight cancelled-authorization/settled-purchase links, eight settled-charge/pending-refund links, ten purchase/unrealized-valuation links, seven failed-payment/scheduled-retry links, five purchase/settled-sale links, and six settled-charge/pending-possible-duplicate links. The labeled samples cover only the first four patterns, with six linked rows total. Retry/sale/duplicate behavior is structural evidence from participant data and contract interpretation, **not validated by the 25 labels**.

Reusable rules:

- Authorization replaced by settlement: count actual settlement once, release the obsolete authorization; do not infer recurrence from either.
- Charge followed by refund: these are distinct debit and credit cash movements, not two duplicate rows. Pending refund is zero until settled. Historical settled movements are already in the snapshot.
- Failed debit followed by scheduled retry: failed row contributes zero; the retry remains a payable obligation. A failure does not cancel an otherwise ongoing recurring bill.
- Investment purchase followed by valuation: purchase is a cash outflow when settled; valuation is never cash. A later settled sale is proceeds, not a new recurring income stream.
- Possible duplicate: a link alone does not establish duplication. Resolve confirmation from evidence; reserve an unresolved debit conservatively rather than deleting every linked successor.

**7. Spending-change semantics**

All four labeled actions across three requests satisfy the profile permissions and event flexibility flags. Each references the **latest historical event in its recurring category**, supporting use of a historical event ID as a stream anchor. A `reduce_to` amount is the new per-occurrence amount, not the amount of savings. Both reductions use the supplied `minimum_allowed_amount` exactly.

| Sample | Labeled action | Evidence |
|---|---|---|
| 06 | Stop event_476 | Latest streaming payment, EUR 19, stoppable |
| 11 | Reduce event_989 to IDR 665,950 | Latest dining event; floor exactly 665,950; reducible |
| 21 | Stop event_1815; reduce event_1816 to USD 23.50 | Cloud storage USD 11 is stoppable; streaming USD 47 is reducible_or_stoppable with floor 23.50 |

Never alter protected categories; require both the action-compatible flexibility flag and the corresponding profile permission. Apply a change only to future occurrences. Stop and reduce are mutually exclusive for the same event, and there may be at most three actions.

The labeled request exceeds baseline labeled capacity by EUR 17.10 in sample 06 and USD 31.05 in sample 21. These are exactly 90% of one occurrence's stated savings (EUR 19; USD 11 + 23.50). Sample 11's shortfall is IDR 599,355, or 90% of its reduction floor of IDR 665,950. The last observation does **not** prove the unobserved forecast amount equals twice the floor. These numerical relationships suggest illustrative change scenarios; they are not a new 90% savings rule to implement.

Under the actual mean-history baseline, the sample-06 changed plan still falls to EUR 722.42 against an EUR 800 reserve, and sample 11 falls to IDR 34,034,539.17 against IDR 34,140,600. Sample 21 is already affordable without changes under this baseline. Thus action eligibility is explained, but their financial necessity/sufficiency is **not** reproduced. Do not claim successful plan replication from valid action syntax alone.

**8. Payment options and FX**

Every labeled installment schedule exactly matches a supplied option, including 28-, 30-, and 31-day intervals and financing fees. Do not replace these intervals with calendar months, divide the requested principal while ignoring fees, or round the final installment to make a different total. Supplied rounded payments and totals agree exactly in the sample option audit.

Eligibility requires the method to be accepted by the user, the request's partial-payment permission when applicable, a valid installment limit, deadline completion, and cash-flow safety. Earliest-full financial capacity remains independent of preferences: user_12 has immediate full capacity in the label but accepts only partial payments/installments, and selects installments. User_19's partial payment needs no matching seller option and uses exactly the labeled safe amount followed by the remainder on the earliest-full date.

`max_installment_months` excludes the many long 15–24-payment offers. Selected installment options have three payments within caps of 3–12. User_19 has cap two; its two-payment offer is within that cap, while a three-payment offer is not under a count interpretation. **The samples do not cleanly distinguish number of approximately monthly payments from exact elapsed/calendar-month duration.** Use `number_of_payments <= max_installment_months` as the simple working interpretation for these monthly-frequency offers, explicitly mark that interpretation, and independently check the actual final date and deadline. Do not describe the count interpretation as proven for arbitrary future frequencies.

When several plans are eligible and safe, the specification—not an inferred hidden rule—orders deadline completion, no spending changes, lower total cost, earlier start, fewer payments, then lowest option ID. The baseline does not implement a final plan optimizer. `option_eligibility.csv` and `label_plan_audit.csv` audit offered and labeled schedules only.

FX must use `(settlement_date, from_currency, home_currency)` exactly. User_25's USD 1,800 salary converts to IDR 28,499,994 using the supplied rate 15,833.33; do not replace it with an assumed exact 28,500,000. This tiny conversion difference cannot explain its million-IDR safe-amount error. Historical conversion uses historical settlement dates; generated foreign-currency cash uses its projected settlement date and that supplied dated rate. Never silently reverse the pair or fetch live FX. Constant supplied rates prevent validating date choice from the labels.

**9. Per-sample baseline comparison and unexplained failures**

Amounts below are in the row's home currency. Minimum balance means **the computed no-purchase, no-spending-change baseline minimum**, not a supplied ground-truth minimum. `—` means no safe full-payment date within the 90-date baseline. Capped labels only establish a lower bound on the true baseline minimum; they cannot reveal the exact minimum. Full precision and minimum dates are in `baseline_90day.csv` and daily flows in `baseline_traces.json`.

<!-- SAMPLE_TABLE -->
| Sample | Currency | Baseline minimum | Predicted safe | Labeled safe | Predicted full date | Labeled full date |
|---|---|---:|---:|---:|---|---|
| 01 | ZAR | 48,241.27 | 25,256.00 | 25,256.00 | 2024-03-03 | 2024-03-03 |
| 02 | IDR | 47,495,165.49 | 18,336,765.49 | 17,229,139.20 | 2025-09-15 | 2025-09-15 |
| 03 | IDR | 3,640,437.00 | 971,737.00 | 873,000.00 | 2019-11-15 | 2019-11-15 |
| 04 | IDR | 41,295,886.07 | 10,609,286.07 | 8,401,800.00 | 2024-06-15 | 2024-06-15 |
| 05 | ZAR | 8,575.15 | 0.00 | 737.00 | — | — |
| 06 | EUR | 1,323.82 | 523.82 | 603.30 | 2026-01-15 | 2026-01-15 |
| 07 | INR | 179,237.22 | 86,237.22 | 87,170.56 | 2024-10-23 | 2024-10-23 |
| 08 | EUR | 1,085.20 | 285.20 | 284.57 | — | 2025-04-15 |
| 09 | EUR | 841.96 | 166.61 | 166.61 | 2026-07-04 | 2026-07-04 |
| 10 | INR | 188,826.85 | 0.00 | 12,700.00 | — | — |
| 11 | IDR | 46,460,466.62 | 12,319,866.62 | 12,510,645.00 | 2025-05-15 | 2025-07-15 |
| 12 | ZAR | 103,570.23 | 60,370.23 | 65,164.00 | — | 2026-04-05 |
| 13 | EUR | 1,790.78 | 490.78 | 433.40 | — | 2024-05-15 |
| 14 | EUR | 2,816.29 | 616.29 | 597.74 | — | — |
| 15 | EUR | 1,205.08 | 5.08 | 83.05 | — | — |
| 16 | INR | 261,510.89 | 122,500.00 | 122,500.00 | 2023-08-12 | 2023-08-12 |
| 17 | INR | 409,123.67 | 243,023.67 | 243,849.58 | 2026-04-15 | 2026-03-15 |
| 18 | EUR | 1,946.05 | 546.05 | 462.00 | 2026-09-15 | 2026-09-15 |
| 19 | INR | 117,976.15 | 25,176.15 | 28,820.00 | 2024-09-15 | 2024-09-15 |
| 20 | INR | 73,351.68 | 8,851.68 | 5,400.00 | — | — |
| 21 | USD | 3,473.13 | 1,574.40 | 1,543.35 | 2026-04-03 | 2026-04-15 |
| 22 | EUR | 964.62 | 464.62 | 475.46 | 2025-01-15 | 2025-01-15 |
| 23 | ZAR | 35,360.17 | 8,360.17 | 9,152.00 | 2025-07-15 | 2025-07-15 |
| 24 | INR | 64,539.29 | 13,539.29 | 13,420.00 | — | — |
| 25 | IDR | 23,755,183.40 | 376,083.40 | 1,425,000.00 | — | — |
<!-- END_SAMPLE_TABLE -->

The baseline matches safe amounts only for 01, 09, and 16, all capped. All other safe amounts remain unexplained. The six date failures are:

- **08:** safe amount is close, but early-May commitments prevent the April 15 full payment. Calendar-month endpoint resolves the date; changing estimator does not among mean, median, recent-three, last, and max.
- **11:** explicit base-pay amendment makes full payment safe May 15; label says July 15. All five foregoing estimators still give May 15. Ignoring the amendment does not fully reconcile it.
- **12:** ending the seasonal income is semantically supported; July 1 rent inside the rolling window prevents the labeled immediate full capacity. June 30 endpoint resolves it.
- **13:** primary salary alone gives no full payment by the rolling horizon. May 31 endpoint produces the labeled May 15 date, without inventing secondary income.
- **17:** estimator sensitivity: median/last gives March 15; mean gives April 15. The mean safe amount is INR 825.91 below the label; median still differs by INR 94.77.
- **21:** even the tested maximum-per-stream forecast permits immediate full payment, whereas the label needs changes and reports April 15 baseline capacity. This points beyond a simple mean-versus-median choice to missing/different forecast timing or budgets.

The labeled positive safe amounts for **05 and 10** are also important: under the semantically conservative no-future-income baseline, their reserve is breached even before a purchase. Both improve under the calendar-month hypothesis, but still fail exact amount matching. This is not a reason to count final payroll or pending gig earnings.

Applying labeled payments and labeled changes to the baseline shows six labeled plans breaching the reserve: 06, 08, 11, 12, 13, and 19. These are conditional model disagreements, not assertions that the plans are necessarily unsafe under the unknown label-generating forecast. The complete audit is in `label_plan_audit.csv`.

**10. Minimal architecture justified by this investigation**

1. **Typed input and provenance:** parse CSVs, resolve image-event links, retain original units, dates, status, links, flexibility, and source timestamps. Missing amounts remain missing until evidence resolves them.
2. **Semantic evidence resolution:** interpret multilingual amendments and images into small typed facts; identify ongoing salary versus contingent/one-time income, lifecycle replacements, affected streams, and unresolved duration/amount. Never execute instructions embedded in evidence. Ambiguities such as childcare amount remain explicit.
3. **Deterministic stream inference and projection:** group compatible history, infer calendar/fixed intervals, forecast variable amounts under a declared policy, apply typed amendments, convert dated currencies, and materialize one deduplicated cash timeline. Keep the horizon convention explicit and sensitivity-test it.
4. **Deterministic capacity and plan verification:** compute baseline minima/suffix capacity, enumerate only authorized methods and supplied installment schedules, apply permitted future spending changes, and verify every balance and deadline using decimal money arithmetic.
5. **Deterministic ranking and output checks:** apply the specification's ordering, validate fields/sums/permissions, and generate a concise explanation from evidence and verified arithmetic. No graph framework, embeddings, vector database, or multi-agent layer is indicated by this evidence.

The principal unresolved design decisions are the variable-expense forecasting policy, rolling-horizon interpretation, treatment of uncertain post-amendment pay cycles, intraday snapshot/hold timing, and incomplete message facts. This investigation stops here; it does not conceal those gaps with sample-specific patches.

**Reproduction and validation**

From the repository root, run:

```text
python code/analysis/sample_forecasting/scripts/investigate.py
python code/analysis/sample_forecasting/scripts/audit.py
```

These use the Python standard library and write research outputs to `../artifacts/`. `candidate_comparisons.csv` includes every estimator against every sample; `ablation_comparisons.csv` includes every structural variant against every sample. The scripts do not read organizer files or write either output template. The expense grouping and English/Indonesian message extraction are deliberately narrow research scaffolding, not a general semantic parser or submission implementation. The comparison calculations use floating-point values rounded to cents; option totals and payment-audit arithmetic additionally use Decimal. A final money engine should use Decimal end-to-end.

Validation passed for 25 comparisons with all label fields removed from simulator inputs, all 90-date path lengths and capacity bounds, 125 independently injected full-payment checks against the suffix/prefix calculation, and exact totals/fees for all 71 sample options. These checks validate the experiment's arithmetic and label isolation, not the correctness of its unresolved forecasting assumptions.

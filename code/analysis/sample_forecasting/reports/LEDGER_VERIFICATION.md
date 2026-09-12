# Three-case ledger verification

Research audit only. Historical gate: STOP — unresolved modeling assumption about future payroll phase. No evidence contradiction establishes a different horizon or estimator. The user subsequently accepted a documented Python persistence policy; see LEDGER_GATE.md for current status.

| user | currency | predicted_safe | labeled_safe | predicted_earliest | labeled_earliest |
| --- | --- | --- | --- | --- | --- |
| user_07 | INR | 86237.22 | 87170.56 | 2024-10-23 | 2024-10-23 |
| user_21 | USD | 1574.4 | 1543.35 | 2026-04-03 | 2026-04-15 |
| user_12 | ZAR | 60370.23 | 65164 |  | 2026-04-05 |

Each CSV contains date, source/event, debit/credit, amount, running balance, provenance and evidence IDs. Opening snapshot treatment and later amended payroll phases are labeled MODELING_POLICY. A scheduled salary emitted by the old recurrence loop is correctly attributed to STRUCTURED_EXPLICIT. Row ordering reproduces the existing sorted trace (debits before credits on a shared date); the simulator itself tests daily net balances, not intraday ordering. Decimal replay validates those emitted cent-rounded flows, not production money precision.

## user_07

| opening | floor | request_date | endpoint | binding_date | minimum |
| --- | --- | --- | --- | --- | --- |
| 218945.56 | 93000 | 2024-09-05 | 2024-12-03 | 2024-09-20 | 179237.22 |

Inferred streams (anchor is a historical evidence ID, not a new future event):

| category | anchor | n | cadence | amount | first |
| --- | --- | --- | --- | --- | --- |
| rent | event_583 | 6 | monthly | 34200.0 | 2024-10-04 |
| utilities | event_580 | 5 | monthly | 6789.44 | 2024-09-08 |
| debt_repayment | event_581 | 5 | monthly | 15650.0 | 2024-09-13 |
| music_subscription | event_582 | 5 | monthly | 1005.0 | 2024-09-13 |
| groceries | event_596 | 13 | 14 | 7116.46 | 2024-09-12 |
| transport | event_605 | 9 | 21 | 3220.13 | 2024-09-20 |
| dining | event_614 | 9 | 21 | 5927.31 | 2024-09-16 |
| salary | event_578 | 5 | monthly | 149000.0 | 2024-09-23 |

Future explicit events:

None.

Semantic source evidence:

- message_05: BrightPath Media has updated your payroll record. Your confirmed salary is now expected on 2024-09-23. This replaces the payroll date shown in the earlier update. Please use the revised date for anything you normally pay around payday. Payroll ref EMP-0005.

[Complete ledger](../artifacts/ledger_verification/user_07_ledger.csv) and [90 daily balances](../artifacts/ledger_verification/user_07_daily.csv).

| date | source_event | direction | amount | running_balance | provenance |
| --- | --- | --- | --- | --- | --- |
| 2024-09-05 | opening profile snapshot | opening | 218945.56 | 218945.56 | MODELING_POLICY |
| 2024-09-08 | recurring:utilities | debit | 6789.44 | 212156.12 | INFERRED_RECURRENCE |
| 2024-09-12 | recurring:groceries | debit | 7116.46 | 205039.66 | INFERRED_RECURRENCE |
| 2024-09-13 | recurring:debt_repayment | debit | 15650.0 | 189389.66 | INFERRED_RECURRENCE |
| 2024-09-13 | recurring:music_subscription | debit | 1005.0 | 188384.66 | INFERRED_RECURRENCE |
| 2024-09-16 | recurring:dining | debit | 5927.31 | 182457.35 | INFERRED_RECURRENCE |
| 2024-09-20 | recurring:transport | debit | 3220.13 | 179237.22 | INFERRED_RECURRENCE |
| 2024-09-23 | recurring:salary | credit | 149000.0 | 328237.22 | SEMANTIC_FACT |
| 2024-09-26 | recurring:groceries | debit | 7116.46 | 321120.76 | INFERRED_RECURRENCE |
| 2024-10-04 | recurring:rent | debit | 34200.0 | 286920.76 | INFERRED_RECURRENCE |
| 2024-10-07 | recurring:dining | debit | 5927.31 | 280993.45 | INFERRED_RECURRENCE |
| 2024-10-08 | recurring:utilities | debit | 6789.44 | 274204.01 | INFERRED_RECURRENCE |
| 2024-10-10 | recurring:groceries | debit | 7116.46 | 267087.55 | INFERRED_RECURRENCE |
| 2024-10-11 | recurring:transport | debit | 3220.13 | 263867.42 | INFERRED_RECURRENCE |
| 2024-10-13 | recurring:debt_repayment | debit | 15650.0 | 248217.42 | INFERRED_RECURRENCE |
| 2024-10-13 | recurring:music_subscription | debit | 1005.0 | 247212.42 | INFERRED_RECURRENCE |
| 2024-10-23 | recurring:salary | credit | 149000.0 | 396212.42 | MODELING_POLICY |
| 2024-10-24 | recurring:groceries | debit | 7116.46 | 389095.96 | INFERRED_RECURRENCE |
| 2024-10-28 | recurring:dining | debit | 5927.31 | 383168.65 | INFERRED_RECURRENCE |
| 2024-11-01 | recurring:transport | debit | 3220.13 | 379948.52 | INFERRED_RECURRENCE |
| 2024-11-04 | recurring:rent | debit | 34200.0 | 345748.52 | INFERRED_RECURRENCE |
| 2024-11-07 | recurring:groceries | debit | 7116.46 | 338632.06 | INFERRED_RECURRENCE |
| 2024-11-08 | recurring:utilities | debit | 6789.44 | 331842.62 | INFERRED_RECURRENCE |
| 2024-11-13 | recurring:debt_repayment | debit | 15650.0 | 316192.62 | INFERRED_RECURRENCE |
| 2024-11-13 | recurring:music_subscription | debit | 1005.0 | 315187.62 | INFERRED_RECURRENCE |
| 2024-11-18 | recurring:dining | debit | 5927.31 | 309260.31 | INFERRED_RECURRENCE |
| 2024-11-21 | recurring:groceries | debit | 7116.46 | 302143.85 | INFERRED_RECURRENCE |
| 2024-11-22 | recurring:transport | debit | 3220.13 | 298923.72 | INFERRED_RECURRENCE |
| 2024-11-23 | recurring:salary | credit | 149000.0 | 447923.72 | MODELING_POLICY |

## user_21

| opening | floor | request_date | endpoint | binding_date | minimum |
| --- | --- | --- | --- | --- | --- |
| 3911.35 | 1800 | 2026-04-03 | 2026-07-01 | 2026-04-12 | 3473.13 |

Inferred streams (anchor is a historical evidence ID, not a new future event):

| category | anchor | n | cadence | amount | first |
| --- | --- | --- | --- | --- | --- |
| rent | event_1818 | 6 | monthly | 718.8 | 2026-05-02 |
| utilities | event_1814 | 5 | monthly | 121.18 | 2026-04-06 |
| cloud_storage | event_1815 | 5 | monthly | 11.0 | 2026-04-12 |
| streaming | event_1816 | 5 | monthly | 47.0 | 2026-04-09 |
| shopping | event_1817 | 5 | monthly | 122.41 | 2026-04-12 |
| groceries | event_1836 | 18 | 10 | 83.63 | 2026-04-06 |
| transport | event_1845 | 9 | 21 | 41.2 | 2026-04-16 |
| dining | event_1854 | 9 | 21 | 83.44 | 2026-04-17 |
| salary | event_1858 | 6 | monthly | 2256.0 | 2026-04-15 |

Future explicit events:

| event_id | description | status | settlement_date | amount |
| --- | --- | --- | --- | --- |
| event_1857 | Pending fuel authorization | pending | 2026-04-05 | 53 |
| event_1858 | Next confirmed salary | scheduled | 2026-04-15 | 2256 |

Semantic source evidence:

None.

[Complete ledger](../artifacts/ledger_verification/user_21_ledger.csv) and [90 daily balances](../artifacts/ledger_verification/user_21_daily.csv).

| date | source_event | direction | amount | running_balance | provenance |
| --- | --- | --- | --- | --- | --- |
| 2026-04-03 | opening profile snapshot | opening | 3911.35 | 3911.35 | MODELING_POLICY |
| 2026-04-05 | event_1857 | debit | 53.0 | 3858.35 | STRUCTURED_EXPLICIT |
| 2026-04-06 | recurring:utilities | debit | 121.18 | 3737.17 | INFERRED_RECURRENCE |
| 2026-04-06 | recurring:groceries | debit | 83.63 | 3653.54 | INFERRED_RECURRENCE |
| 2026-04-09 | recurring:streaming | debit | 47.0 | 3606.54 | INFERRED_RECURRENCE |
| 2026-04-12 | recurring:shopping | debit | 122.41 | 3484.13 | INFERRED_RECURRENCE |
| 2026-04-12 | recurring:cloud_storage | debit | 11.0 | 3473.13 | INFERRED_RECURRENCE |
| 2026-04-15 | recurring:salary | credit | 2256.0 | 5729.13 | STRUCTURED_EXPLICIT |
| 2026-04-16 | recurring:groceries | debit | 83.63 | 5645.50 | INFERRED_RECURRENCE |
| 2026-04-16 | recurring:transport | debit | 41.2 | 5604.30 | INFERRED_RECURRENCE |
| 2026-04-17 | recurring:dining | debit | 83.44 | 5520.86 | INFERRED_RECURRENCE |
| 2026-04-26 | recurring:groceries | debit | 83.63 | 5437.23 | INFERRED_RECURRENCE |
| 2026-05-02 | recurring:rent | debit | 718.8 | 4718.43 | INFERRED_RECURRENCE |
| 2026-05-06 | recurring:utilities | debit | 121.18 | 4597.25 | INFERRED_RECURRENCE |
| 2026-05-06 | recurring:groceries | debit | 83.63 | 4513.62 | INFERRED_RECURRENCE |
| 2026-05-07 | recurring:transport | debit | 41.2 | 4472.42 | INFERRED_RECURRENCE |
| 2026-05-08 | recurring:dining | debit | 83.44 | 4388.98 | INFERRED_RECURRENCE |
| 2026-05-09 | recurring:streaming | debit | 47.0 | 4341.98 | INFERRED_RECURRENCE |
| 2026-05-12 | recurring:shopping | debit | 122.41 | 4219.57 | INFERRED_RECURRENCE |
| 2026-05-12 | recurring:cloud_storage | debit | 11.0 | 4208.57 | INFERRED_RECURRENCE |
| 2026-05-15 | recurring:salary | credit | 2256.0 | 6464.57 | INFERRED_RECURRENCE |
| 2026-05-16 | recurring:groceries | debit | 83.63 | 6380.94 | INFERRED_RECURRENCE |
| 2026-05-26 | recurring:groceries | debit | 83.63 | 6297.31 | INFERRED_RECURRENCE |
| 2026-05-28 | recurring:transport | debit | 41.2 | 6256.11 | INFERRED_RECURRENCE |
| 2026-05-29 | recurring:dining | debit | 83.44 | 6172.67 | INFERRED_RECURRENCE |
| 2026-06-02 | recurring:rent | debit | 718.8 | 5453.87 | INFERRED_RECURRENCE |
| 2026-06-05 | recurring:groceries | debit | 83.63 | 5370.24 | INFERRED_RECURRENCE |
| 2026-06-06 | recurring:utilities | debit | 121.18 | 5249.06 | INFERRED_RECURRENCE |
| 2026-06-09 | recurring:streaming | debit | 47.0 | 5202.06 | INFERRED_RECURRENCE |
| 2026-06-12 | recurring:shopping | debit | 122.41 | 5079.65 | INFERRED_RECURRENCE |
| 2026-06-12 | recurring:cloud_storage | debit | 11.0 | 5068.65 | INFERRED_RECURRENCE |
| 2026-06-15 | recurring:groceries | debit | 83.63 | 4985.02 | INFERRED_RECURRENCE |
| 2026-06-15 | recurring:salary | credit | 2256.0 | 7241.02 | INFERRED_RECURRENCE |
| 2026-06-18 | recurring:transport | debit | 41.2 | 7199.82 | INFERRED_RECURRENCE |
| 2026-06-19 | recurring:dining | debit | 83.44 | 7116.38 | INFERRED_RECURRENCE |
| 2026-06-25 | recurring:groceries | debit | 83.63 | 7032.75 | INFERRED_RECURRENCE |

## user_12

| opening | floor | request_date | endpoint | binding_date | minimum |
| --- | --- | --- | --- | --- | --- |
| 193089.89 | 43200 | 2026-04-05 | 2026-07-03 | 2026-07-01 | 103570.23 |

Inferred streams (anchor is a historical evidence ID, not a new future event):

| category | anchor | n | cadence | amount | first |
| --- | --- | --- | --- | --- | --- |
| rent | event_1018 | 6 | monthly | 11792.0 | 2026-05-01 |
| utilities | event_1014 | 5 | monthly | 3509.72 | 2026-04-05 |
| cloud_storage | event_1015 | 5 | monthly | 447.7 | 2026-04-11 |
| streaming | event_1016 | 5 | monthly | 1504.8 | 2026-04-08 |
| shopping | event_1017 | 5 | monthly | 1255.89 | 2026-04-11 |
| groceries | event_1036 | 18 | 10 | 2134.89 | 2026-04-07 |
| transport | event_1045 | 9 | 21 | 1436.23 | 2026-04-17 |
| dining | event_1054 | 9 | 21 | 2257.6 | 2026-04-18 |

Future explicit events:

None.

Semantic source evidence:

- message_09: A note from Cobalt Systems about your upcoming pay. The current seasonal contract has ended. No off-season income or renewal has been confirmed. We’ll contact you separately if another shift block or contract is approved. Payroll ref EMP-0009.

[Complete ledger](../artifacts/ledger_verification/user_12_ledger.csv) and [90 daily balances](../artifacts/ledger_verification/user_12_daily.csv).

| date | source_event | direction | amount | running_balance | provenance |
| --- | --- | --- | --- | --- | --- |
| 2026-04-05 | opening profile snapshot | opening | 193089.89 | 193089.89 | MODELING_POLICY |
| 2026-04-05 | recurring:utilities | debit | 3509.72 | 189580.17 | INFERRED_RECURRENCE |
| 2026-04-07 | recurring:groceries | debit | 2134.89 | 187445.28 | INFERRED_RECURRENCE |
| 2026-04-08 | recurring:streaming | debit | 1504.8 | 185940.48 | INFERRED_RECURRENCE |
| 2026-04-11 | recurring:shopping | debit | 1255.89 | 184684.59 | INFERRED_RECURRENCE |
| 2026-04-11 | recurring:cloud_storage | debit | 447.7 | 184236.89 | INFERRED_RECURRENCE |
| 2026-04-17 | recurring:groceries | debit | 2134.89 | 182102.00 | INFERRED_RECURRENCE |
| 2026-04-17 | recurring:transport | debit | 1436.23 | 180665.77 | INFERRED_RECURRENCE |
| 2026-04-18 | recurring:dining | debit | 2257.6 | 178408.17 | INFERRED_RECURRENCE |
| 2026-04-27 | recurring:groceries | debit | 2134.89 | 176273.28 | INFERRED_RECURRENCE |
| 2026-05-01 | recurring:rent | debit | 11792.0 | 164481.28 | INFERRED_RECURRENCE |
| 2026-05-05 | recurring:utilities | debit | 3509.72 | 160971.56 | INFERRED_RECURRENCE |
| 2026-05-07 | recurring:groceries | debit | 2134.89 | 158836.67 | INFERRED_RECURRENCE |
| 2026-05-08 | recurring:streaming | debit | 1504.8 | 157331.87 | INFERRED_RECURRENCE |
| 2026-05-08 | recurring:transport | debit | 1436.23 | 155895.64 | INFERRED_RECURRENCE |
| 2026-05-09 | recurring:dining | debit | 2257.6 | 153638.04 | INFERRED_RECURRENCE |
| 2026-05-11 | recurring:shopping | debit | 1255.89 | 152382.15 | INFERRED_RECURRENCE |
| 2026-05-11 | recurring:cloud_storage | debit | 447.7 | 151934.45 | INFERRED_RECURRENCE |
| 2026-05-17 | recurring:groceries | debit | 2134.89 | 149799.56 | INFERRED_RECURRENCE |
| 2026-05-27 | recurring:groceries | debit | 2134.89 | 147664.67 | INFERRED_RECURRENCE |
| 2026-05-29 | recurring:transport | debit | 1436.23 | 146228.44 | INFERRED_RECURRENCE |
| 2026-05-30 | recurring:dining | debit | 2257.6 | 143970.84 | INFERRED_RECURRENCE |
| 2026-06-01 | recurring:rent | debit | 11792.0 | 132178.84 | INFERRED_RECURRENCE |
| 2026-06-05 | recurring:utilities | debit | 3509.72 | 128669.12 | INFERRED_RECURRENCE |
| 2026-06-06 | recurring:groceries | debit | 2134.89 | 126534.23 | INFERRED_RECURRENCE |
| 2026-06-08 | recurring:streaming | debit | 1504.8 | 125029.43 | INFERRED_RECURRENCE |
| 2026-06-11 | recurring:shopping | debit | 1255.89 | 123773.54 | INFERRED_RECURRENCE |
| 2026-06-11 | recurring:cloud_storage | debit | 447.7 | 123325.84 | INFERRED_RECURRENCE |
| 2026-06-16 | recurring:groceries | debit | 2134.89 | 121190.95 | INFERRED_RECURRENCE |
| 2026-06-19 | recurring:transport | debit | 1436.23 | 119754.72 | INFERRED_RECURRENCE |
| 2026-06-20 | recurring:dining | debit | 2257.6 | 117497.12 | INFERRED_RECURRENCE |
| 2026-06-26 | recurring:groceries | debit | 2134.89 | 115362.23 | INFERRED_RECURRENCE |
| 2026-07-01 | recurring:rent | debit | 11792.0 | 103570.23 | INFERRED_RECURRENCE |

## Diagnostic results

Existing diagnostics only; none selected to improve labels.

| user | diagnostic | min_balance | safe | earliest |
| --- | --- | --- | --- | --- |
| user_07 | one_cycle | 179237.22 | 86237.22 | 2024-10-15 |
| user_07 | reserve_pending_now | 179237.22 | 86237.22 | 2024-10-23 |
| user_07 | calendar_endpoint | 179237.22 | 86237.22 | 2024-10-23 |
| user_21 | one_cycle | 3473.13 | 1574.4 | 2026-04-03 |
| user_21 | reserve_pending_now | 3473.13 | 1574.4 | 2026-04-03 |
| user_21 | calendar_endpoint | 3473.13 | 1574.4 | 2026-04-03 |
| user_12 | one_cycle | 103570.23 | 60370.23 |  |
| user_12 | reserve_pending_now | 103570.23 | 60370.23 |  |
| user_12 | calendar_endpoint | 115362.23 | 65164.0 | 2026-04-05 |

Literal-only boundary cash flows for user_12:

| date | signed_amount | source |
| --- | --- | --- |
| 2026-07-01 | -11792.0 | recurring:rent |

user_21 supplied spending actions (audit only):

| action | permission_valid | minimum_allowed |
| --- | --- | --- |
| stop:event_1815 | True |  |
| reduce_to:event_1816:23.50 | True | 23.5 |

Full payment minimum without changes: 1898.73; with supplied changes: 1933.23.

See [interpretation and verification gate](LEDGER_GATE.md) for classifications and next step.

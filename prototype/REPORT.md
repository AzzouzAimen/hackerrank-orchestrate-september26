# Representative prototype results

The replayable semantic-fact-to-output path runs for all five selected cases. Twenty-eight
prototype tests pass. All three selected payment plans pass deterministic verification;
two cases return no recommendation. There are zero invalid selected plans and zero output
schema violations. This establishes the audited integration path, not general extraction
accuracy or leaderboard improvement.

| Case | Why selected | Predicted safe | Labeled safe | Predicted earliest | Labeled earliest | Recommendation |
| --- | --- | ---: | ---: | --- | --- | --- |
| user_07, INR | Explicit payroll date amendment | 86,237.20 | 87,170.56 | 2024-10-23 | 2024-10-23 | Installments |
| user_16, INR | Image supplies missing future debit | 122,500.00 | 122,500.00 | 2023-08-12 | 2023-08-12 | Full payment |
| user_01, ZAR | Linked refund and authorization settlement | 8,849.12 | 25,256.00 | None | 2024-03-03 | Not recommended |
| user_21, USD | Permitted stop/reduction alternatives | 1,574.40 | 1,543.35 | 2026-04-03 | 2026-04-15 | Full payment, no changes |
| user_25, IDR | Regular payroll, no messages/images; dated FX control | 0 | 1,425,000 | None | None | Not recommended |

Selection used source characteristics rather than score. These five are not a statistical
evaluation sample. Normalized MAE (absolute safe error / requested amount, averaged) is
13.9526%; exact safe amounts 1/5; exact earliest dates 3/5. No cross-currency raw MAE is
reported. user_21 predicts capacity 12 days earlier; user_01 is a missing-date disagreement.
Semantic extraction was reviewed in-session, not independently scored; model-runtime
calls/tokens/cost are 0. Interactive assistant tokens/cost are unavailable.

## Facts, consequences and findings

- **07:** message_05 supplies September 23 with unknown duration. Structured payroll
  history supplies the amount. Python persists the phase through October/November as
  MODELING_POLICY. The chosen option is payment_option_19: September 12, October 10 and
  November 7, INR 68,432 each, including its supplied fee. Residual −933.36 remains;
  the two-cent research difference comes from unrounded Decimal means/output floor.
- **16:** image_02 explicitly shows Balance Due INR 100,000. It fills event_1442 and
  produces a debit on August 16. The same image also has total and received amounts;
  those were not mistaken for the selected value. The receipt's printed rental period
  is old; the dataset's explicit image/event link and scheduled event provide the current
  obligation context and settlement date. message_12 supplies a 12% lease increase;
  Python calculates the amended recurring rent. No absolute rent amount was invented by
  the semantic model. Unknown image amount instead blocks output, demonstrated by tests.
  The outstanding balance and monthly rent remain separate with unresolved overlap logged.
- **01:** event_99 is a refund of event_98, so the charge is not deleted; event_101 settles
  the cancelled authorization event_100. Historical cash is already in the profile, and
  these lifecycle rows do not become recurring expenses. A new limitation surfaced:
  event_25 is a prorated first salary; event_103 confirms the next salary but does not
  provide three historical cadence observations. The explicit salary is counted once.
  The research simulator repeated it monthly without that history threshold. We retained
  the stated history-supported inference rule and documented the resulting large label
  disagreement instead of adding unsupported recurring income. Future first-job salary
  handling needs explicit cadence evidence/policy before broader coverage.
- **21:** pending fuel is reserved once, valuation remains noncash, scheduled salary
  replaces the matching inferred occurrence through semantic stream membership. Stoppable
  and reducible candidates are enumerated and permission-checked. The baseline already
  supports full payment, so ranking selects no changes. A synthetic low-balance test
  demonstrates that a valid change candidate can enable a payment when necessary.
- **25:** supplied USD→IDR rates are used on each payroll settlement date. A minimum of
  IDR 23,162,672.2583 occurs before March 15 salary, below the 23,379,100 floor. The daily
  closing balance recovers, but later recovery does not erase the reserve breach.
  This differs from the research net-daily convention. It remains a documented intraday
  ordering assumption, not a discovered real-world breach or a label correction.

## Contract and responsibility boundary

Seven fact types: stream_status, amount_amendment, date_or_schedule_amendment,
future_event_confirmation, lifecycle_relationship, image_financial_value,
cash_classification. Every fact has version, ID, evidence references, event/stream target,
nullable effective dates, confirmation state and unresolved fields. Money includes currency;
unknown values stay null. Nested extra fields, malformed dates, unsupported types and
numeric rather than decimal-string amounts are rejected. The exported schema and five
fact bundles provide complete runnable examples.

The semantic layer identifies meanings and supplied values. Python determines cash status,
recurrence, lifecycle consequences, overlap, percentage multiplication, FX, ledger minima,
capacity, candidates, permissions, safety, ranking and output consistency. Uncertain
financial facts do not acquire values automatically. Accepted persistence is a Python policy.

## Tests and limitations

Run `python -m unittest prototype.test_prototype -v`: 28 tests, passing. Coverage includes
schema/provenance rejection, unknown values, Decimal arithmetic, literal horizon, fixed-day
and monthly/EOM recurrence, explicit overlap versus category-only similarity, pending credit
and debit treatment, failed/cancelled/noncash exclusions, lifecycle replacement/refund/
possible duplicate, dated FX, intraday minimum and prefix invariants, exact option/fee/
duration checks, partial structure, deadlines/preferences, spending permissions and limits,
ranking, semantic-output consistency, and all representative cases.

Remaining limits are explicit in README: replayed extraction rather than automated API;
category-based historical grouping; first-job cadence; snapshot/hold and intraday conventions;
duration interpretation; incomplete source-conflict precedence; bounded cadence-amendment
support; and spending reductions limited to supplied minima. No estimator or horizon
tuning was performed, no frameworks/agents were added, and no evaluation requests ran.

**Single next step:** add a schema-constrained semantic extraction call for these same five
cases, comparing its facts against the reviewed bundles and reporting extraction errors
separately from financial forecast disagreements before expanding coverage.

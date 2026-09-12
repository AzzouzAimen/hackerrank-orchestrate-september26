# Ledger verification gate — 2026-09-12

**Current status: accepted by the user; implementation resumed.** Payroll amendment
duration is unknown from evidence; the forecasting engine applies a documented persistence
policy. The stop outcome below is the historical verification result, superseded by that
acceptance. See `prototype/README.md` at the repository root for implementation policies.

**Outcome: phase 1 completed; stop before phases 2–5 under the user's final stop instruction.**
The payroll persistence assumption is unresolved, not an established evidence contradiction.
The source supports September 23 for the next payment; it does not establish a permanent
change or a return date. The default simulator was not silently changed. No estimator
search, evaluation-request run, model API call, or final submission implementation occurred.

The request says both to document assumption/label disagreements and continue, and finally
to stop if a current assumption is unsupported. This audit follows the latter instruction
for the unestablished duration of the payroll change. It does not claim the vertical
prototype is complete. The semantic contract, resolver, financial engine, representative
image/lifecycle/control cases and their production tests remain deferred.

## Evidence and classifications

### user_07 — unresolved modeling assumption; separate diagnostic implementation bug

- **Observed:** payroll events event_558/563/568/573 have event and settlement dates on
  April–July 15. event_578 has August 15 event date and August 23 settlement date.
  message_05, sent August 29, explicitly replaces the upcoming payroll date with September 23.
  It supplies neither a new amount nor an effective-until date. Amount INR 149,000 comes
  from structured payroll history. There is no structured future payroll row in this case.
- **Evidence-backed semantic amendment:** the September payment occurs September 23.
  August settlement on the 23rd is corroborating context, not proof of an indefinite schedule.
- **Policy:** September 23 is tagged SEMANTIC_FACT; October/November 23 are tagged
  MODELING_POLICY. Persisting the phase is plausible and later than the prior day-15 phase,
  but neither that persistence nor eventual reversion is explicitly confirmed.
- **Measurement:** both existing phase diagnostics have minimum INR 179,237.22 on
  September 20 and safe amount INR 86,237.22, versus label INR 87,170.56 (error −933.34).
  Persistent phase gives October 23; one-cycle shift gives October 15. Only the former
  matches the label, which does not turn persistence into an evidence fact.
- **Bug fixed:** the one-cycle diagnostic previously returned to literal day 15 for every
  stream. It now uses the modal historical settlement day. Without settled history, it
  stops extrapolating that diagnostic and records the unknown prior phase. Synthetic day-10
  history verifies the fix. The default persistent behavior is unchanged. This modal phase
  remains a diagnostic assumption, not a new production inference policy.
- **Correction to prior documentation:** HACKATHON_LOG's earlier statement that the
  persistent shift was "supported" was too strong if read as source confirmation. It was
  supported by label agreement and recent timing, not a stated duration. An appended entry
  corrects that interpretation without rewriting history.

### user_21 — phase/reservation hypothesis, no justified extra occurrence

- **Observed:** the trace reaches USD 3,473.13 on April 12 after pending fuel USD 53,
  utilities 121.18, groceries 83.63, streaming 47, shopping 122.41 and cloud storage 11.
  The label-implied minimum is USD 3,343.35; the minimum gap is 129.78. The reported safe
  amount gap is only 31.05 because predicted safe capacity is capped at the request.
- **Cadence/phase:** transport's last settled occurrence is March 26, so its supported
  21-day continuation starts April 16. Dining's last is March 27, continuing April 17.
  Neither contributes to the April 12 minimum. Their mean amounts, 41.20 and 83.44,
  cannot change that balance merely by selecting another center. Prior research's extra
  occurrence counterfactual totals 124.64, near the minimum gap, but no source establishes
  those extra or earlier obligations. None were added or moved.
- **Pending convention:** the old simulator charges event_1857 once, on April 5, and
  assumes the opening profile needs that additional debit. Moving its reservation to
  April 3 gives exactly the same minimum, safe amount and earliest date. The source does
  not identify whether the available-balance snapshot already includes this hold.
  event_1857 has no lifecycle link or message tying it to the transport recurrence;
  category alone does not establish overlap. Keeping both is conservative under the
  opening-balance convention. This is not a general deduplication implementation.
- **Explicit salary:** event_1858 supplies April 15 salary. It appears once in the old
  salary loop, though the loop calls it recurring. The audit corrects its provenance to
  STRUCTURED_EXPLICIT. May/June continuations are inferred. event_1856 is an unrealized
  investment valuation and contributes no cash.
- **Spending:** supplied stop:event_1815 and reduce_to:event_1816:23.50 satisfy profile
  permissions, flexibility, protection rules and the supplied reduction minimum. They
  affect separate future streams (two actions). At the binding minimum, they save 34.50.
  Full payment leaves USD 1,898.73 without changes and 1,933.23 with changes, both above
  the 1,800 reserve under this model. Therefore the labeled need for changes and April 15
  earliest date remain unexplained; a production ranker under this baseline would prefer
  no changes. No 90% savings rule is used.

### user_12 — horizon sensitivity; retain literal 90 dates

- **Observed:** request April 5; literal endpoint July 3 inclusive (90 dates).
  Calendar diagnostic endpoint June 30 (87 dates). The only cash row in the literal
  trace absent from the calendar trace is July 1 inferred rent, ZAR 11,792, anchored
  to event_1018 and supported by monthly first-of-month history.
- **Semantic state:** message_09 says the seasonal contract has ended and no off-season
  income or renewal is confirmed. No future salary is projected. The message supplies
  no exact contract-end date; the audit does not manufacture one. Utilities on the
  request date are included under the current opening-snapshot convention.
- **Measurement:** calendar minimum ZAR 115,362.23 becomes literal minimum 103,570.23
  after July 1 rent. Literal safe amount 60,370.23 is 4,793.77 below the capped label
  65,164; no full payment is safe. Calendar capacity is capped at 65,164 and permits
  April 5. The label gives only a lower bound of 108,364 on the baseline minimum.
- **Classification:** label/model horizon disagreement, not evidence contradicting the
  literal policy. Excluding a supported July obligation to match the label is not justified.

## Verification and limits

Commands:

```text
python analysis/sample_forecasting/scripts/verify_ledgers.py
python -m unittest discover -s analysis/sample_forecasting/scripts -p test_ledger_verification.py -v
```

Six tests pass: Decimal replay and inclusive horizon; provenance and running balances;
label isolation; synthetic historical payday regression; preservation of default
persistence; and unknown prior phase. The report generator additionally checks the
three replayed results and the supplied spending permissions. These are research audit
tests, not the requested production-engine suite.

The original simulator uses float means rounded to cents. Independent Decimal replay
checks the resulting emitted cash rows; it does not validate unrounded Decimal forecasting.
Its safety path nets flows by day. Row-level display uses its sorted debit-first trace;
the dataset does not establish intraday ordering or exact snapshot timing. Future
production verification must explicitly state those conventions.

**No source contradiction requiring a new estimator, horizon or architectural design
was found.** No model extraction quality, invalid-plan count or production schema
validation metric can be claimed: those phases were not run. External model calls: 0;
API tokens/cost: not applicable. Interactive assistant usage is not measured here.

## Responsibility boundary and single next step

The semantic layer should supply the September date, evidence ID, affected payroll
selector and unknown amendment duration. Python should own whatever explicit policy
governs subsequent cycles, with MODELING_POLICY provenance. Unknown duration must never
be silently upgraded to an evidence-backed permanent schedule.

**Next:** resolve and record the future-payday persistence policy, explicitly as a
modeling assumption, then resume the requested evidence-contract and vertical-prototype
session. This does not require broader estimator research. The current audit deliberately
does not choose a replacement policy or treat label agreement as authorization to do so.

Artifacts: [full ledgers and tables](LEDGER_VERIFICATION.md),
[machine-readable audit](../artifacts/ledger_verification/audit.json), and
[comparison CSV](../artifacts/ledger_verification/comparison.csv).

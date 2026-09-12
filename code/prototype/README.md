# Representative financial prototype

The stable implementation and its engine/boundary tests now live directly in
[`code/`](../../README.md). Local `evidence.py`, `finance.py`, `plans.py`
and old test modules are compatibility imports only. The canonical schema is
[`code/evidence.schema.json`](../../evidence.schema.json).
Reviewed facts, representative runs, and extraction experiments remain in the parent
`code/prototype/` folder; its Markdown documentation is collected here.
See [the corrected extraction audit](EVALUATION_AUDIT_V2.md); previous strict-match
semantic headlines are superseded. No model facts enter the trusted runner.

Run from the repository root:

```text
python -m pip install -r code/requirements.txt
python code/main.py representative
python -m unittest discover -s code/tests -t code -v
```

This runs five labeled representative cases only. It never reads evaluation requests
or writes either dataset output template. Labels enter comparison reporting only.
`artifacts/representative_output.csv` is a prototype artifact, not a submission.

`code/evidence.py` defines seven discriminated fact types (a type-specific payload selected
by fact_type). `code/evidence.schema.json` exports that contract. Every nested object forbids
extra fields. Dates are strict ISO dates; money is a nonnegative decimal string plus
currency. Unknown money/date/duration stays null. No decisions, computed balances or
executable fields are accepted. `percent_increase` preserves a quoted percentage without
inventing an absolute amount. Effective bounds are required nullable fields.

`facts/` contains session-extracted and reviewed facts. The assistant inspected raw
records/messages and image_02 directly, then recorded these facts. This is a replayable
semantic input boundary, **not an automated extraction API integration**. Runtime calls,
tokens and cost are zero; interactive assistant usage is unavailable. Independent
semantic extraction correctness remains unmeasured. `EXTRACTION_PROMPT.md` documents
the narrow extraction task for the next integration step.

`finance.py` validates provenance against the user’s raw data, resolves statuses and
linked lifecycles, updates streams, materializes dated cash, applies supplied FX and
calculates capacity using Decimal. `plans.py` generates and verifies plans, ranks safe
candidates and validates output against the resolved state. Unresolved financial
blockers raise an error rather than silently produce a fabricated safe amount.

## Explicit policies and limits

- **Payroll amendment duration is unknown from evidence; the forecasting engine applies
  a documented persistence policy.** Unknown-scope payday amendments persist through
  the horizon. Later payroll occurrences carry MODELING_POLICY provenance. Explicit
  one-cycle date amendments return to the stream's historical phase. Ranged or new
  cadence amendments are schema-valid but blocked as outside this slice, not ignored.
- Literal request_date through +89, inclusive. Expenses are included before optional
  changes. Variable native-currency amounts use the plain Decimal historical mean;
  constant amounts remain exact. No per-stream cent rounding is applied. Safe capacity
  is rounded down to cents only at the output boundary. This explains small differences
  from research floats rounded at stream level.
- Expense groups use category, currency, flexibility, direction and event type plus
  observed cadence. At least three observations and 70% cadence support are retained
  from the research approach. Calendar-month/EOM or observed 5/7/10/14/21-day cadence
  is supported. These thresholds are existing heuristics, not newly fitted constants.
  Grouping can still merge independent same-category streams; this is not a complete
  merchant/source identity solution. Explicit deduplication additionally requires
  description, linked identity or semantic membership and matching occurrence dates.
- Income recurrence additionally requires an ongoing semantic classification. A single
  confirmed salary without sufficient recurring history is counted once, not repeated.
  This exposes the first-job/prorated-income limitation in user_01. No future salary
  is invented to restore label agreement.
- Opening profile balance is a request-day snapshot. Earlier settled cash is not replayed.
  Same-day explicit settlements count. Pending debits are reserved once on request day,
  with FX from supplied settlement date; there is no second settlement debit. Whether
  the profile already includes holds is unidentifiable from the source. Potential
  obligation overlap is retained and reported unless identity/date evidence resolves it.
- **Intraday convention:** essential/recurring debits precede same-day credits; purchase
  payments follow settled credits. Check pre-credit and post-payment balances, including
  the prefix before any later purchase. Research used net daily balances. This conservative
  explicit convention exposes user_25's pre-payroll reserve breach and is not asserted
  as organizer ground truth. Missing intraday ordering remains a modeling uncertainty.
- Rent percentage amendments multiply the inferred rent amount in Python. An outstanding
  rent balance does not overlap a monthly rent occurrence merely by sharing its category.
  Multiple conflicting amount/schedule amendments block instead of applying list order.
  Full cross-source conflict resolution is outside the representative slice.
- Installments preserve count, first date, frequency, amount, total and fee exactly.
  Duration must fit max_installment_months measured from first through last payment
  against a calendar-month anniversary. This interpretation remains a declared assumption.
  Every installment must also fit the request deadline and forecast horizon.
- Partial payment uses exactly today's baseline safe amount followed by the remainder
  on the baseline earliest full-payment date, with a separate safety check.
- Spending changes affect inferred occurrences strictly after request day; explicit
  obligations and pending holds remain reserved. Enumerate stop or supplied minimum
  reductions for up to three distinct permitted unprotected streams. Stop/reduce of
  one event are mutually exclusive. No arbitrary percentage savings rule is used.
  Additional intermediate reduction amounts are not optimized in this slice.
- No safe eligible plan means not_recommended with no payment plan. Earliest capacity
  is independent of method preference; output status reflects that capacity where later.

The engine is intentionally bounded. Incomplete future financial values, missing FX,
unestablished amendment targets, unsupported cadence amendments and unresolved new-event
overlap block output. This is not complete support for all semantic facts in all datasets.

See [results](REPORT.md), [comparison](../artifacts/comparison.csv), and per-user JSON artifacts
for semantic facts, raw-to-resolved differences, projected flows, provenance, daily
minima, candidate checks and validated output.

The subsequent [boundary challenge report](BOUNDARY_REPORT.md) documents 21 additional
tests and the small resolver fixes they required. The seven-fact schema is unchanged.
Transfer exclusion now requires trusted structured account scope plus a balanced same-day
settled pair; without that metadata it blocks rather than assuming cash neutrality.
Possible duplicates preserve history, paid-only image evidence cannot fill scheduled
outstanding amounts, and standalone date amendments are resolved explicitly. Precise
semantic amendment selectors can partition history without a global grouping-policy change.

## Shadow real-model extraction experiment

With a local `.env` containing `FEATHERLESS_API_KEY`, run:

```text
python -m prototype.extraction_experiment
```

This uses Featherless `zai-org/GLM-5.3-Flash`, validates the unchanged `EvidenceBundle`,
scores reviewed references, and writes `code/prototype/extraction_artifacts/`. It never replaces
`code/prototype/facts/` or writes trusted recommendations. See
[REAL_MODEL_EXTRACTION_REPORT.md](REAL_MODEL_EXTRACTION_REPORT.md).

# Semantic fact → state boundary challenge

Completed without model/API integration, label tuning, new frameworks, or changes to
`evidence.py` / the seven-fact schema. Changes are confined to the resolver/targeted
history partitioning, synthetic tests and documentation.

## Test-first evidence

The initial 16 tests ran before any resolver edit: **11 failures**. The log is preserved
in [boundary_before.txt](artifacts/boundary_before.txt). Five additional coverage tests
were added during follow-up: **21 boundary tests now pass**, together with all **28
existing prototype tests** (49 total). See [boundary_after.txt](artifacts/boundary_after.txt).

The five representative outputs were regenerated and their CSV SHA256 remained identical:
`2007b834de8d1f0e6eed703d422fcf0a459c3efe2b3b58525b4ab85a02e4d703`.
No sample-label values enter the boundary tests. Existing research tests are separate.

Reproduce:

```text
python -m unittest prototype.test_boundary prototype.test_prototype -v
```

All fixture constructors and assertions are in [test_boundary.py](test_boundary.py).
They supply ordinary raw event dictionaries, validated semantic facts and provenance
records directly to the same resolver used by the representative runner.

## 1. Possible duplicate

**Input:** Three settled USD 20 monthly dining observations on January/February/March 5.
A lifecycle fact says March's event is `possible_duplicate_of` February's. Variants include
a raw `linked_event_id` and an uncertain confirmation state.

**Expected:** Possible duplication alone does not remove either history observation,
deduplicate cash, or suppress April/May/June obligations. Record the unresolved relation.

**Before:** Cash rows were nominally retained, but the lifecycle branch marked both
observations `history_excluded`. Three observations became one usable observation;
zero future obligations were inferred. The raw-link branch independently did the same.
Tests exposed a real defect in both paths.

**Smallest change:** Return from the possible-duplicate handling before history exclusion;
do not use a corresponding possible-duplicate raw link as grounds to exclude history.

**After:** April 5, May 5 and June 5 debits of USD 20 remain; minimum USD 940 from opening
1000. Confirmed possibility and uncertain possibility both preserve this history.

**Contract:** Sufficient, unchanged. `possible_duplicate_of` means possible, even when the
fact that a source raised that possibility is confirmed.

**Remaining uncertainty:** Whether the transactions really duplicate one obligation.
The resolver deliberately retains the obligations until stronger evidence exists.

## 2. Internal transfer

**Input:** Two settled same-day USD 80 legs, debit from checking and credit to savings,
with a confirmed `internal_transfer` relationship. Variants supply no modeled account scope,
only checking in scope, both accounts in scope, or different settlement dates.

**Expected:** A relationship alone does not prove cash neutrality within the modeled
balance. Only a matched pair inside the trusted aggregate scope, with equal currency/
amount and settled date, can be excluded as net-zero internal cash movement.

**Before:** Every internal-transfer relationship removed both legs, irrespective of
scope or settlement timing. Unknown/outside-scope tests failed. The known-scope positive
test passed, but the implementation had made no scope check.

**Smallest change:** Check trusted structured `modeled_cash_account_ids` on the profile
against `account_id` on both evidence records, together with opposite directions, distinct
accounts, equal known amounts/currency and same settled date/status. If any check fails,
retain both rows and add a capacity blocker. Do not invent account ownership or balances.

**After:** Known balanced in-scope pair has no net ledger row and preserves USD 1000.
Unknown scope, an out-of-scope account or settlement transit retains the rows, explicitly
blocks capacity and cannot produce validated payment output. Retained rows in a blocked
state are diagnostic, not a claim that both belong in the final modeled balance.

**Contract:** The relationship type is sufficient for safe handling; it does **not** encode
account scope. Scope in this positive test comes from trusted structured metadata, not a
new model field. The supplied dataset does not contain that metadata, so its ambiguous
internal-transfer cases cannot use this exclusion path. No schema expansion was necessary
to meet the fail-closed requirement. Extracting new account-scope assertions from natural
language remains outside this experiment and may require a future targeted contract change.

**Remaining uncertainty:** Dataset account scope and transfer settlement exposure. The
same-day netting policy applies only to the trusted aggregate-scope positive test.

## 3. Image amount paid versus amount due

**Input:** An image linked to a scheduled debit with missing amount says `amount_paid=30 USD`.
Positive controls use `balance_due=30 USD`, or a genuinely historical settled event.

**Expected:** A receipt's paid value does not establish the outstanding amount. Historical
paid evidence may corroborate history; a balance-due field can fill a future obligation.

**Before:** The scheduled missing amount became USD 30 and was projected as a future debit.
The test exposed a real semantic consequence defect. Historical-paid and future-due controls
already behaved correctly.

**Smallest change:** Only accept `amount_paid` as an amount for a settled event strictly
before the opening snapshot. For other cash states, retain the raw amount (including null)
and block the unresolved outstanding obligation rather than infer a new debit or cancellation.

**After:** Scheduled paid-only evidence keeps its amount null and blocks capacity. Historical
paid USD 30 creates no replayed cash. Future balance-due USD 30 produces one April 5 debit,
leaving minimum USD 970.

**Contract:** Sufficient, unchanged; the existing value types already distinguish the meanings.

**Remaining uncertainty:** Whether a paid amount settles all or part of a scheduled bill.
Neither settlement nor a remaining amount is inferred from the word "paid" alone.

## 4. Unknown future obligation

**Input:** A user message supports a new dining debit on April 8, with USD currency but
null amount and no corresponding raw event. Test both confirmed and uncertain fact states;
also test known amount with null date.

**Expected:** Preserve the fact and unknown fields; no zero substitution and no validated
capacity while a financially relevant obligation cannot be quantified or timed.

**Before:** Confirmed unknown amounts/dates already blocked. An uncertain fact without a
matching raw debit added only an issue, so an empty cash ledger could pass capacity.
That variant exposed a real defect.

**Smallest change:** The uncertainty branch checks a future confirmation's own debit
direction or debit stream selector, not only matching existing events. An uncertain
schedule also blocks rather than leaving an apparently resolved timeline.

**After:** All tested missing-amount/date debit variants block capacity. The semantic fact
retains null, no numeric cash row is fabricated, and no recommendation can be validated.

**Contract:** Sufficient, unchanged.

**Remaining uncertainty:** Actual amount/date and relevance of a genuinely contingent
obligation. This slice blocks conservatively instead of deriving a financial probability.

## 5. Stream targeting

**Input:** Two dining streams, same user/category/currency/direction: Dinner membership,
USD 20 on the 5th, and Second dining plan, USD 40 on the 12th. Each has January–March
history. A precise description selector changes only Dinner membership to USD 25.
Controls use a broad selector and an event ID paired with a broad selector.

**Expected:** Preserve both supported streams; apply USD 25 only to the selected stream.
If identity is not established, block rather than guess or broaden the amendment.

**Before:** Category grouping combined the histories, destroying recognizable cadence;
even the precise amendment blocked with "stream not established." That was a real
supported-target handling defect. The broad-selector and mixed-target controls already
blocked for these inputs; they did not demonstrate a safe widening in that baseline run.

**Smallest change:** Partition history only where a precise semantic amendment selector
provides a distinction. Do not globally switch variable spending to exact-description
grouping. Explicit event IDs restrict `targets()` instead of unioning with a broad selector.
Reject an amendment spanning inferred groups or only partially matching one group's history.

**After:** April/May/June each contain USD 25 on the 5th and USD 40 on the 12th; minimum
USD 805. Broad/unestablished targeting remains blocked, including the tested same-day
two-stream variant. A mixed event/stream scope cannot silently amend its neighbor.

**Contract:** Sufficient for the tested precise-description evidence, unchanged.

**Remaining uncertainty:** Distinct streams with identical descriptions, changing descriptions,
or insufficient identity metadata. The experiment does not solve general stream discovery.

## 6. Event-targeted date amendment

**Input:** One scheduled USD 20 debit due April 5; an event-targeted one-cycle date amendment
supplies April 9, with no recurring history. An unknown-date variant supplies null.

**Expected:** Move that explicit obligation once to April 9 with semantic provenance, or
block if the new date is unresolved. Do not create a recurring stream.

**Before:** The explicit event stayed on April 5; a null date amendment was also ignored
without a blocker. Both tests exposed real defects.

**Smallest change:** Resolve standalone one-cycle date amendments directly against pending/
scheduled events. Unsupported scopes, ranges, statuses or unknown dates block explicitly.
Pending debit reservation still happens once at opening; changing its settlement date
does not release the hold or create a second debit.

**After:** Scheduled event settles April 9 for USD 20; fact/evidence provenance is attached.
Unknown-date amendment blocks. No inferred recurrence is involved.

**Contract:** Sufficient, unchanged.

**Remaining uncertainty:** Multi-cycle or retrospective amendments outside this bounded
branch still require explicit resolution and are not silently treated as one-cycle changes.

## Fact order and explicit conflicts

Before: two explicit amount amendments, USD 30 and USD 40, were applied in input order;
the last one silently won. After: competing explicit amount/date writes are detected before
mutation; unresolved conflicts block rather than selecting by position. Fact-ID sorting
only canonicalizes processing/audit output; it does not establish evidence precedence.

Tests compare material event state, flows/provenance, blockers, issues and change logs:

- Both permutations of two conflicting amounts: same blocked state.
- Both permutations of image amount versus conflicting amendment: same blocked state.
- Both permutations of independent amount/date facts: one April 9 USD 30 debit.
- All six permutations of three independent facts: April 9 USD 30 and April 11 USD 10.

Competing representations may conservatively block even when fuller evidence would establish
precedence or equivalence. General source-priority reconciliation is not claimed here.

## Tiny manually checked ledger oracles

Every scenario starts April 1 with USD 1000 and a USD 100 reserve. End date is June 29.
These expected values are literal test assertions, not calculated by the production ledger.

| Scenario | Date | Debit | Expected running balance |
| --- | --- | ---: | ---: |
| Possible duplicate retained | April 5 | 20 | 980 |
| Same scenario | May 5 | 20 | 960 |
| Same scenario | June 5 | 20 | 940 |
| Image balance due, separate scenario | April 5 | 30 | 970 |
| Event date amendment, separate scenario | April 9 | 20 | 980 |
| Precise stream target, separate scenario | April 5 | 25 | 975 |
| Same scenario | April 12 | 40 | 935 |
| Same scenario | May 5 | 25 | 910 |
| Same scenario | May 12 | 40 | 870 |
| Same scenario | June 5 | 25 | 845 |
| Same scenario | June 12 | 40 | 805 |
| Three independent facts, separate scenario | April 9 | 30 | 970 |
| Same scenario | April 11 | 10 | 960 |

Balanced in-scope internal transfer preserves 1000, with neither leg counted again.
Unknown scope, paid-only outstanding evidence and unknown new obligations have **no
validated expected capacity**: their correct result is an explicit unresolved blocker,
not a numeric zero expense or a claim of a complete ledger.

## Scope of success

Supported test facts produce the intended consequence; the tested unsupported consequences
block; possible duplicates retain future obligations; permutation checks pass; seven fact
types are unchanged; existing tests and representative output remain intact. The result
validates these boundary cases, not arbitrary model output or complete lifecycle coverage.
This experiment stops here. No model API or semantic extraction experiment was started.

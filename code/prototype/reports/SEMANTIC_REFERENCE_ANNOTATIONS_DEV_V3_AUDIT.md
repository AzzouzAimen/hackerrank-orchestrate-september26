# Development reference annotation v3 audit

**Binding update:** The exact offline development request bodies and per-meaning reassessment are in [SEMANTIC_DEV_INPUT_BINDING_AUDIT.md](SEMANTIC_DEV_INPUT_BINDING_AUDIT.md). That reassessment supersedes the readiness and target-availability conclusions below: user_12 and user_04 are expressible with their bound history; user_26 and the childcare part of user_14 still have unsupported target assumptions. Keep these references as `assistant_draft` and do not use the empty required lists as successful semantic coverage.

Audited against `code/evidence.py` and the actual development evidence boundary. The v3 draft is minimal: a contract fact is required only when the supplied message/image/event evidence can support its target and currency. Descriptive meanings and raw-history assertions remain separate context.

| case | required meanings | allowed contract representations | unresolved fields | judgment note |
|---|---|---|---|---|
| user_16 | ongoing rent; 12% stream amendment; scheduled outstanding rent; paid/balance image values | `stream_status`; `amount_amendment`; `future_event_confirmation`; two `image_financial_value` facts | new rent amount, amendment timing/duration, event amount | Image Balance Due is linked to event_1442 without converting the raw event null; gross total stays contextual. |
| user_03 | next regular salary; separate one-time adjustment; settled net pay | two stream/future facts plus `image_financial_value` | salary/adjustment amount or date | One-time adjustment is `stream_status=one_time`, not an invented amount amendment. |
| user_06 | temporary reduced salary | `amount_amendment` | duration | Exact EUR amount is in the message; no permanent end date inferred. |
| user_12 | seasonal income ended | contextual only; future `stream_status=ended` if a currency-bearing target is supplied | end date, target currency | Message supports meaning but not the selector required by the contract. |
| user_28 | regular salary; separate arrears payment | two `future_event_confirmation` facts | payment dates | Both EUR amounts are explicit; arrears is a separate future credit. |
| user_04 | performance bonus contingent/pending | contextual only; future `stream_status=contingent` or `cash_classification=contingent_income` with a supported target | amount, date, currency | Prior settled bonus is context and cannot fill the current unknowns. |
| user_10 | payout pending and non-withdrawable | contextual only; future `cash_classification=pending_credit` with a supported target | amount, date, currency | Profile currency is deliberately not forced into model output. |
| user_26 | approved invoice future credit | `future_event_confirmation` | none in stated amount/date; settlement remains future | Unapproved invoices remain contextual and are not emitted as facts. |
| user_20 | refund-of relationship; pending credit; scheduled refund | `lifecycle_relationship`; `cash_classification`; `future_event_confirmation` | none for linked event values | Three facts are genuinely distinct: relationship, cash state, and scheduled payment. |
| user_18 | same-owner internal transfer | contextual only; `lifecycle_relationship=internal_transfer` if both event IDs are supplied | event IDs, amount, currency | No fabricated related event ID is allowed. |
| user_229 | failed debit and scheduled retry | `lifecycle_relationship`; `cash_classification`; `future_event_confirmation` | none for retry event values | Failed original and scheduled retry are distinct lifecycle/cash facts. |
| user_22 | unrealized investment valuation | `cash_classification=non_cash_valuation` | realized proceeds/date | Valuation amount remains raw context; no cash is inferred. |
| user_23 | verified but uncredited prize | contextual only; future `cash_classification=pending_credit` with a supported target | amount, date, currency | Message alone cannot satisfy the contract target without inventing currency. |
| user_14 | salary resumption; recurring childcare stream | `future_event_confirmation`; `stream_status` | childcare amount/start date | Salary date and amount are explicit; childcare is kept separate with a descriptive category. |

The v2 draft had redundant or unsupported required facts: it used `amount_amendment` for an unknown one-off adjustment, forced profile currencies into user_04/user_10/user_23 selectors, and required stream facts where no contract target was present. v3 removes those requirements while preserving the meanings as contextual assertions.

`code/prototype/validate_semantic_reference_annotations.py` now checks the v3 version, seven-type allowlist, Pydantic `EvidenceBundle` validity, unique fact IDs, exact development-only membership, evidence ownership, contextual source IDs, and that every required selector currency appears in extractor evidence rather than only in a profile. Validation passed for all 14 development cases; holdout was not inspected or annotated.

# Semantic split v5 metadata audit

This audit inspected the selected messages, linked events, image metadata, and the three selected image files directly. No model/API calls were made and no semantic reference annotations were created.

## Findings and corrections

The v4 holdout labels were assigned during placeholder replacement with broad/default keyword handling and were not checked against the earlier deterministic inventory. That caused settled prize evidence to be called pending, ended employment to be called salary arrears, foreign-currency purchase/refund cases to lose their FX distinction, and a payment receipt to be called a recurring expense. The same stale process left generic inclusion reasons on holdout cases.

The v5 manifest retains all 14 development and 8 holdout cases and corrects metadata as follows:

| User | v5 family | Evidence basis |
|---|---|---|
| user_02 | salary_change | employer salary increase with effective date |
| user_235 | fx_refund | foreign-currency refund pending settlement |
| user_48 | receipt | message, image, and settled property-maintenance payment |
| user_24 | prize_completed | proceeds reached account; claim closed; settled event |
| user_246 | ended_income | employment ended; no future regular salary |
| user_267 | fx_payment | foreign-currency purchase awaits settlement conversion |
| user_268 | prize_pending | verified prize not yet credited |
| user_274 | fx_refund | foreign-currency refund pending settlement |

Development evidence was also checked. The existing families remain supported: rent, salary arrears, temporary pay, ended income, arrears, pending income, pending payout, invoice, refund, transfer, failed retry, investment non-cash, prize pending, and recurring expense. Inclusion reasons and ambiguity notes now describe the actual evidence rather than template status.

## Deterministic guardrail

`code/prototype/validate_semantic_split_metadata.py` reads the manifest and source CSVs, classifies each selected case using ordered evidence predicates, and fails on a family mismatch, unresolved or mis-owned ID, placeholder metadata, duplicate case, template overlap, hash drift, or forbidden model/sample/dataset flags. Running it against v5 passed for all 22 cases.

Split integrity remains valid: user16 is the sole contaminated development case, development/holdout counts remain 14/8, normalized message-template overlap is zero, source hashes match, and `frozen` remains true.

# Development semantic reference annotation draft v1

Drafts cover the 14 development cases in `semantic_split_20260912_v5.json` only. They are evidence references, not model outputs or semantic ground truth. No affordability, recommendation, scorer, prompt, or model work was performed.

| User | Required meaning recorded | Main judgment |
|---|---|---|
| user_16 | rent amendment; separate outstanding balance; image gross/received/due fields | 12% amendment has no new amount; event_1442 amount remains unknown; image fields must not be merged |
| user_03 | regular salary plus separate one-off adjustment; settled payslip event | Adjustment amount/date are unknown; image supports settled net pay only |
| user_06 | temporary reduced pay | EUR 1037.52 applies to affected and next payroll only; no end date inferred |
| user_12 | seasonal income ended | No renewal or off-season income is confirmed |
| user_28 | regular salary and separate arrears adjustment | EUR 1452 and EUR 653.40 remain separate facts |
| user_04 | performance bonus pending | Amount and payment date are unknown despite prior bonus history |
| user_10 | pending non-withdrawable service payout | Displayed earnings are not settled cash; no amount/date supplied |
| user_26 | approved invoice settlement and unapproved invoice scope | IDR 30,780,000 and 2025-08-15 are explicit for the approved invoice only |
| user_20 | pending merchant refund lifecycle | INR 8640 and 2026-02-14 come from linked pending event; not available before settlement |
| user_18 | same-owner internal transfer | Matching debit/credit is not external income; amount is unknown |
| user_229 | failed debit with scheduled retry | EUR 73 failed event and separate scheduled retry are both retained |
| user_22 | unrealized investment valuation | EUR 369.60 is non-cash; no sale or realized gain inferred |
| user_23 | verified but uncredited prize | Amount and credit date are unknown; verification is not settlement |
| user_14 | salary resumption and new recurring childcare expense | EUR 2717 on 2025-08-15 is explicit; childcare amount/day are unknown |

Each record includes supporting IDs, fact type, target stream/event, explicit values or nulls, lifecycle/status, acceptable alternates, supported optional facts, unsupported interpretations, ambiguity notes, and `review_status: assistant_draft`.

`code/prototype/validate_semantic_reference_annotations.py` checks that exactly the 14 development users are represented, no holdout user is present, IDs match v5, every evidence ID resolves to the expected user, and required annotation fields are populated.

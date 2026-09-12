# Real-data semantic extraction benchmark proposal

## 1. Current evaluation weaknesses

The existing evidence is concentrated on user16 and one rent-history treatment. `rent_run_02` established availability under the plain-JSON profile, while `semantic_prompt_01` and `semantic_target_01` tested narrow definitions on the same frozen evidence. Those runs are useful debugging evidence, but repeated calls on one user cannot estimate cross-user generalization. The targeting treatment also had only 2/3 usable treatment runs and used wording that named renewed rent and Monthly rent, so it is not a validated production rule. The image clarification was tested on the same image case. Schema validity and delivery were measured separately from meaning, but there is no frozen, diverse semantic reference set or untouched holdout.

## 2. Dataset semantic inventory

The real dataset contains 275 users/profiles, 25,342 financial events, 215 messages and 16 images. Messages provide repeated, inspectable families: confirmed first salary and settlement date; salary increases and decreases; ended seasonal employment; ended household employment; regular salary plus one-time arrears; pending bonuses/commissions; pending service payouts; approved invoices with settlement dates; refunds pending or completed; foreign-currency settlement; internal transfers; failed debit with retry; open card dispute/reversal; investment market value with no cash; prize processing and completed prize; reimbursement separate from salary; recurring childcare deductions; renewed rent; and property-payment receipts. Images cover salary/arrears, rent/balance-due, refunds, transfers and payment receipts. The inventory supports most requested categories, but genuine unknowns are usually explicit (pending approval, no renewal, unsettled FX), not arbitrary missing data. Rare or absent categories requiring separate annotation are: a clean multi-stream amendment with unambiguous stream identity beyond rent, a defensible image instruction-injection case, and a clearly annotated duplicate event pair. Internal transfers, lifecycle links, cancellations and retries do exist and should be sampled from linked events plus their messages.

## 3. Proposed development cases

Select 12–16 cases after mechanical inventory, with at most one case per near-duplicate message template family per split. Suggested development cases:

| Case | Evidence and behavior | Prior influence | Use / difficulty |
|---|---|---|---|
| D01 | user16 message_12 + image_02 + linked rent events; recurring stream vs balance event, 12%, balance/paid/gross | heavily examined | Development only; high |
| D02 | confirmed first salary plus credit date (e.g. user15/message_11) | no | Development; low |
| D03 | salary increase with effective date (user02/message_01) | no | Development; medium |
| D04 | temporary reduced pay for affected cycle (user06/message_04) | no | Development; medium |
| D05 | ended seasonal contract/no renewal (user12/message_09) | no | Development; medium |
| D06 | ended household job, remaining salary (user42/message_30) | no | Development; medium |
| D07 | regular salary plus one-time arrears (user28/message_20) | no | Development; medium |
| D08 | bonus/commission pending amount and date unknown (user04/message_03 or user11/message_08) | no | Development; medium |
| D09 | pending payout not withdrawable (user10/message_07) | no | Development; medium |
| D10 | approved invoice with future settlement and other invoices unapproved (user26/message_18) | no | Development; medium |
| D11 | refund initiated/not credited, linked event (user20/message_14) | no | Development; medium |
| D12 | foreign-currency refund with settlement-rate uncertainty (user48 or user235) | no | Development; high |
| D13 | internal same-owner transfer, matching debit/credit (user18/message_13) | no | Development; medium |
| D14 | failed debit, bill remains open and retry expected (user229/message_179) | no | Development; high |
| D15 | investment value change with no sale/cash (user22/message_15) | no | Development; medium |
| D16 | prize processing versus completed prize/no future payments (user23 vs user24) | no | Development; high |

Cases should be finalized by evidence review, not by these example IDs alone; choose one representative per family and retain alternates for later additions.

## 4. Proposed holdout cases

Freeze 8–10 cases from different users and message families only after the development/holdout split is recorded. Candidate holdout strata are: salary effective-date change; ended income; pending variable income; approved invoice; pending refund; internal transfer; failed debit/retry; investment no-cash; completed prize; and one non-user16 image receipt. Use different user IDs and, where possible, different template language/language from development. Assignment is based on evidence characteristics and family, never on pilot model performance. User16 and every artifact used in the prior rent/image/targeting experiments remain development/debugging evidence and are excluded from holdout.

## 5. Cases rejected

Reject exact duplicates and near-duplicates from the same template family when they add no semantic coverage; organizer/sample output cases; cases whose event linkage conflicts with the supplied row and cannot be resolved; images lacking a readable or independently supported field; cases where amount/date meaning is only inferred from arithmetic; and cases with unresolved human disagreement about stream identity or lifecycle. Do not use user16 as a holdout. Do not force unsupported categories such as instruction-like image text, duplicate detection, or cancellation if no defensible real case exists.

## 6. Annotation format

Store one JSON record per case:

```json
{"case_id":"D07","users":["user_28"],"evidence_ids":{"messages":["message_20"],"images":[],"events":["event_..."]},"required_meanings":[{"meaning":"regular_salary","fact_type":"income_amendment","target":{"stream":"salary","event_ids":[]},"amount":{"value":1452,"currency":"EUR"},"date":"2024-06-15","uncertainty":"confirmed"}],"acceptable_alternates":["stream selector without event id"],"optional_supported":[],"unsupported_claims":["arrears is recurring salary","pending bonus is available cash"],"ambiguities":[],"review_status":"human_approved","source":"real_dataset"}
```

Use null/unknown explicitly. Record lifecycle (`pending`, `scheduled`, `settled`, `failed`, `cancelled`, `unrealized`), image field meaning (`balance_due`, `amount_paid`, `gross_total`), supporting evidence IDs, unacceptable interpretations, and ambiguity notes. References describe supported meaning only; they do not calculate affordability or recommendations.

## 7. Human-review requirements

Mechanical checks can verify IDs, currencies, dates, numeric transcription, status labels, linked-event existence, and schema/output availability. Human judgment is required for stream identity, whether a message amends or merely describes an event, duration/scope, lifecycle interpretation where multiple rows are linked, image balance versus gross/paid meaning, conflicts, and whether an assertion is unsupported. Two reviewers are needed only for disputed/high-consequence cases; otherwise one reviewer records a rationale. Assistant-proposed annotations must be marked `assistant_draft` and cannot become reference truth until the user approves them. Preserve disagreement and adjudication notes rather than silently collapsing them.

## 8. Scoring design

Score each case and arm in separate dimensions: usable final output and first-attempt availability; retry recovery; provider/empty versus nonempty schema failure; required meaning recovery; target correctness; amount/currency/date correctness; unknown preservation; lifecycle correctness; image-field interpretation; unsupported financial claims; harmful extras; and repeated-call consistency. Report counts and denominators by category and split. A critical-error table should flag wrong target, treating pending/unrealized money as available, gross total as balance due, and fabricated dates/amounts. Do not publish one aggregate accuracy number. Safety decisions should weight critical semantic errors and unsupported claims above cosmetic omissions, while availability remains a separate gate.

## 9. Holdout protocol

Freeze a manifest containing case IDs, evidence hashes, split, strata, annotation version, and reviewer status before any model run on holdout. Prompt development may inspect and rerun development cases. Holdout runs occur only at named checkpoints, with frozen model, settings, prompt, schema, integration profile and retry cap. Holdout results may trigger a decision or reveal an annotation defect, but must not trigger ad hoc tuning against individual cases. If a holdout annotation is wrong, quarantine that case, record the correction and version, and rerun the entire checkpoint only after the correction is approved; never replace a failing label silently. New cases enter a future version or development set first; they can join a later holdout only after a clean freeze. Prompts and harnesses must not contain case IDs, literal values, or expected answers.

## 10. Recommended implementation sequence

1. Build a read-only inventory script grouping messages/images/events by semantic family and user/template, without model calls.
2. Produce candidate rows and manually inspect evidence bundles.
3. Mark user16 and prior repeatedly examined cases as contaminated development evidence.
4. Select and annotate 12–16 development and 8–10 holdout cases; obtain human approval for disputed fields.
5. Freeze a versioned manifest and hashes, add mechanical annotation validation, and create a claim-review worksheet.
6. Add an offline scorer that consumes saved EvidenceBundle outputs; test it on existing artifacts only.
7. Run a pilot on development cases, then a single checkpoint on holdout. This is implementation work for a later session, not this session.

## 11. Decision gates

Prompt refinement is justified only when a repeated critical error appears on at least two independent development families and availability is adequate, with one narrowly stated variable. A stronger-model comparison is justified when the frozen checkpoint has adequate usable outputs but critical errors persist across multiple users/families after development prompt work, or when the current model fails the availability gate. Limited model-to-engine evaluation is justified only after critical semantic meanings pass predefined thresholds on both splits and unsupported-claim rate is acceptably low; model facts remain shadow until then. Stop semantic tuning when gains are confined to one case/template, regressions recur, or the holdout critical-error rate remains above the safety threshold.

## 12. Risks / anti-patterns

Main risks are optimizing user16, leaking holdout values through prompts or code, selecting only English/easy messages, counting schema validity as semantic accuracy, mixing provider failures with wrong meaning, overengineering annotation fields, treating assistant drafts as truth, using sample labels, and selecting only cases with obvious answers. Keep the benchmark small, evidence-backed and versioned; retain raw inputs and outputs; and report denominators.

## Smallest next action

In a later implementation session, create a read-only dataset inventory and candidate-case manifest (no model calls), then review and freeze the split before building the scorer. This is the smallest step that turns the proposal into an auditable benchmark without contaminating holdout evidence.

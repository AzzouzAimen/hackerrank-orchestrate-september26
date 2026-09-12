# Development semantic reference annotation v2 audit

The v1 draft used descriptive `fact_type` values such as `temporary_income_amendment`, `invoice_settlement`, and `pending_payout`. Those labels were useful prose but were not the extractor contract. v2 keeps prose in `descriptive_meanings` and `contextual_assertions`, while every model-required item is a concrete `EvidenceBundle` fact using only the seven Pydantic fact types from `code/evidence.py`.

The seven contract types are enforced literally: `stream_status`, `amount_amendment`, `date_or_schedule_amendment`, `future_event_confirmation`, `lifecycle_relationship`, `image_financial_value`, and `cash_classification`. Each contract fact includes the schema's required target, evidence, confirmation, unresolved fields, and payload shape. Unknown amounts/dates remain null and are listed in `unresolved_fields`.

User16 preserves the established boundary: the 12% amount amendment targets the recurring rent stream; `event_1442` is a separate scheduled outstanding balance with unknown amount; image `Balance Due` and `Amount Received` are each INR 100000; the INR 200000 gross/total field is retained only as a contextual raw-image assertion and is not mislabeled as `current_amount_due`.

Cases where the source cannot satisfy a contract target are explicitly separated. User18's same-owner transfer is a contextual assertion only because the message supplies no concrete related event ID, so no fabricated `lifecycle_relationship` is required. User10 uses `cash_classification=pending_credit` with the profile home currency in its stream selector because the message gives no payout currency; the amount and completion date remain unresolved.

`code/prototype/validate_semantic_reference_annotations.py` now parses every required fact through the actual `EvidenceBundle` Pydantic model, checks the allowed seven-type set, verifies exact development-only membership and evidence ownership against v5, and rejects any holdout annotation. Validation passed for all 14 development drafts. No holdout inspection or annotation, model/API call, scorer work, or split change occurred.

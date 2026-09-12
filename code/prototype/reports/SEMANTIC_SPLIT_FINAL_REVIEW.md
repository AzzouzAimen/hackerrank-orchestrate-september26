# Final split review

Version v3 finalizes the pre-annotation split after inspecting message rows, linked-event metadata and image metadata. The v1/v2 placeholder family labels were replaced with concrete semantic families and deterministic normalized message-skeleton IDs.

Corrections include restoring image evidence wherever metadata supplies it (notably user48 now includes image_08 and event_4535; user03 includes image_01 and event_253; user16 retains image_02 and event_1442), deduplicating linked IDs, and recording the normalized template identity. All selected IDs resolve in the source tables. No selected case was rejected after inspection; cases remain candidates for later semantic annotation review.

The final split is 14 development and 8 holdout cases. User16 is contaminated development-only. Normalized template ID intersection is empty. Source hashes remain frozen from the real dataset. `frozen` is true for the split boundary, while semantic annotations are intentionally absent.

Coverage spans rent and image balance evidence, salary changes and arrears, temporary and ended income, pending income/payout, invoice settlement, refunds, internal transfer, failed debit retry, investment non-cash value, prize lifecycle, recurring expense, FX refund/charge, and property receipt. The holdout is smaller because family-disjoint, defensible cases are preferred over templated filler.

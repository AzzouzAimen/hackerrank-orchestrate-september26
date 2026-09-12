# Holdout semantic references completed — 2026-09-12

The eight cases in the frozen v5 split are now annotated in `../extraction_artifacts/semantic_inventory_01/semantic_reference_annotations_holdout_20260912_v1_frozen.json`. The accompanying `holdout_runtime_inputs_v1/manifest.json` binds every case to the exact serialized extractor request and SHA-256. Inputs use the development request format, system prompt, model settings, JSON schema, and PNG data-URL attachment format. Evidence selection is deterministic and case-neutral: all same-user financial events plus the split's exact message and image IDs. Profiles, sample labels, and model outputs were not used.

| Case | Minimal required interpretation |
|---|---|
| user_02 | IDR 42750000 ongoing salary amendment effective 2025-08-15; the next credit date is unknown. |
| user_235 | Foreign-currency refund remains pending; currency, amounts, settlement date, and settlement-rate conversion remain unknown. |
| user_48 | The linked maintenance expense was paid; image_08 shows INR 15339 Total Amount Received. Its 2026-08-30 original due date is not a new debit. |
| user_24 | Settled prize claim is closed and one-time; no further prize payment is scheduled. |
| user_246 | Regular salary ended; any separate final settlement remains unspecified. |
| user_267 | Final home-currency amount for a singular foreign-currency charge is unresolved until settlement. The existing `amount_amendment` fact carries null money and explicit FX unknowns; it asserts no numeric change. |
| user_268 | Verified prize is still processing and uncredited, with no supported prize currency or amount. |
| user_274 | Foreign-currency refund remains pending with unknown currency, amounts, settlement date, and settlement-rate conversion. |

The holdout file copies the frozen development benchmark conventions and seven-type allowlist exactly. Every case has independently recorded required meanings, at least one Pydantic-valid canonical fact, exact evidence provenance, explicit harmful interpretations, and unknowns retained. Source quotes are used only where event/stream IDs and currencies are absent; unrelated payroll or purchase currencies never fill those gaps. Raw settled-event amounts and dates are not mandatory restatements. No development reference, schema, prompt, model, scorer, or financial-engine change was made.

Validation passed for all eight: frozen split membership, evidence ownership, quoted/structured target provenance, actual message amount/date support, image linkage and hash, Pydantic validity, non-vacuous facts, source hashes, and exact runtime payload bytes. The development reference SHA-256 remained `5cb962ed7062a9d1c0e177aea10d95f9581d30c0e445faac0480ac0e982f396`. The full Python suite passed **132/132** tests. No model/API call or dataset mutation occurred.

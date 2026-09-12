# Semantic split v4 audit

Audited directly against dataset CSVs without model/API calls.

Canonical IDs use underscore forms: `user_03`, `message_02`, `image_01`, and `event_253`.

## Root cause
v3 development records retained pre-normalization IDs such as `user03`, while source tables use `user_03`. Exact ownership joins therefore emitted `REJECT: user/message not found`. The review report described the earlier normalized candidate state and did not re-run against the stale v3 fields. Holdout `review_required` values were also stale pre-annotation placeholders.

## Repair
v4 canonicalizes IDs, validates every selected profile/message/image/event ownership relationship, preserves 14 development and 8 holdout cases, keeps user16 contaminated and development-only, replaces holdout placeholders with evidence-derived families, and retains unique normalized template IDs.

## Integrity
All IDs resolve; no duplicate cases; normalized template overlap is empty; source hashes match; holdout selection is model-independent; sample labels were not used; dataset files are unchanged; model calls are zero. Semantic annotations remain absent. The split is frozen only after these checks passed.

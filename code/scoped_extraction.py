"""Model-agnostic scoped extraction composition."""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from evidence import EvidenceBundle
from target_identity import validate_target_identity


def scope_case(case: dict, kind: str) -> dict:
    result = deepcopy(case)
    if kind == "text":
        result["evidence"]["images"] = []; result["image_paths"] = []
    elif kind == "image":
        result["evidence"]["messages"] = []
    return result


def compose_scoped(case: dict, text_result: dict, image_result: dict | None) -> dict:
    """Compose usable scoped bundles without semantic reinterpretation."""
    if not text_result.get("usable") or image_result is not None and not image_result.get("usable"):
        return {"usable": False, "bundle": None, "blocked": [{"reason": "scoped_output_unavailable"}]}
    facts = []
    for scope, result in (("text", text_result), ("image", image_result)):
        if result is None:
            continue
        for source in result["bundle"]["facts"]:
            fact = deepcopy(source)
            if scope == "image" and fact["fact_type"] != "image_financial_value":
                return {"usable": False, "bundle": None, "blocked": [{"reason": "non_image_fact_from_image_scope"}]}
            fact["fact_id"] = f"{scope}__{fact['fact_id']}"
            facts.append(fact)
    try:
        bundle = EvidenceBundle.model_validate({"facts": facts})
        idx = {row[key]: row for field, key in (("events", "event_id"), ("messages", "message_id"), ("images", "image_id"))
               for row in case["evidence"][field]}
        validate_target_identity(bundle.facts, case["evidence"]["events"], idx)
    except Exception as exc:
        return {"usable": False, "bundle": None, "blocked": [{"reason": "composition_validation", "detail": str(exc)}]}
    return {"usable": True, "bundle": bundle.model_dump(mode="json"), "blocked": []}


def extract_scoped(case: dict, text_extractor: Callable[[dict], dict],
                   image_extractor: Callable[[dict], dict]) -> dict:
    text = text_extractor(scope_case(case, "text"))
    image = image_extractor(scope_case(case, "image")) if case["image_paths"] else None
    result = compose_scoped(case, text, image)
    result["calls"] = len(text.get("attempts", [])) + len((image or {}).get("attempts", []))
    result["attempts"] = text.get("attempts", []) + (image or {}).get("attempts", [])
    return result

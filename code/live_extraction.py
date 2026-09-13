"""Accepted guarded semantic extraction adapter for submission execution."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import semantic_extractor as base
from scoped_extraction import compose_scoped, scope_case

ROOT = Path(__file__).resolve().parent
ACCEPTED_SUFFIX = (ROOT / "prompts/accepted_certainty_minimality_unknowns_v1.txt").read_text(encoding="utf-8").strip()
IMAGE_SUFFIX = (ROOT / "prompts/image_scoped_extraction_v1.txt").read_text(encoding="utf-8").strip()
PROVIDER = base.PROVIDER
MODEL = base.MODEL
SETTINGS = base.SETTINGS


def load_env() -> None:
    # Support both `python code/main.py` in the repository and an extracted
    # code.zip run from a directory that also contains dataset/.
    for path in (Path.cwd() / ".env", ROOT.parent / ".env", ROOT / ".env"):
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip().strip('"').strip("'")
        break


def _module(extra_prompt: str = ""):
    spec = importlib.util.spec_from_file_location("accepted_live_semantic_extractor", base.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SYSTEM_PROMPT += "\n" + ACCEPTED_SUFFIX
    if extra_prompt:
        module.SYSTEM_PROMPT += "\n" + extra_prompt
    return module


def _save_new(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _recorded_extract(module, case: dict, directory: Path) -> dict:
    original = module.call_model
    number = 0

    def recorded(runtime_case, correction=None):
        nonlocal number
        number += 1
        _save_new(directory / f"attempt_{number}_request.json", module.request_payload(runtime_case, correction))
        response, latency = original(runtime_case, correction)
        _save_new(directory / f"attempt_{number}_response.json", response)
        return response, latency

    module.call_model = recorded
    result = module.extract_once(case)
    _save_new(directory / "result.json", result)
    return result


def extract(case: dict, directory: Path) -> dict:
    """Run accepted text extraction and, when needed, an image-only call."""
    load_env()
    if not os.environ.get("FEATHERLESS_API_KEY"):
        raise RuntimeError("FEATHERLESS_API_KEY is not configured")
    cached = directory / "composed.json"
    if cached.is_file():
        return json.loads(cached.read_text(encoding="utf-8"))
    text = _recorded_extract(_module(), scope_case(case, "text"), directory / "text")
    image = (_recorded_extract(_module(IMAGE_SUFFIX), scope_case(case, "image"), directory / "image")
             if case["image_paths"] else None)
    composed = compose_scoped(case, text, image)
    composed["attempts"] = text.get("attempts", []) + (image or {}).get("attempts", [])
    composed["calls"] = len(composed["attempts"])
    _save_new(cached, composed)
    return composed

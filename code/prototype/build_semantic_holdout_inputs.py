"""Save byte-exact, offline extractor requests for the frozen holdout cases.

Selection is case-neutral: all same-user financial events plus only the frozen
split's message/image IDs. No profile, sample labels, reference, or model call.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prototype import extraction_experiment as extractor

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "code/prototype/extraction_artifacts/semantic_inventory_01"
SPLIT = BASE / "semantic_split_20260912_v5.json"
DEV_REFERENCE = BASE / "semantic_reference_annotations_dev_20260912_v4_frozen.json"
OUT = BASE / "holdout_runtime_inputs_v1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rows(filename: str) -> list[dict[str, str]]:
    with (ROOT / "dataset" / filename).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build() -> tuple[dict, dict[str, bytes]]:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    holdout = split["holdout"]
    if not split["frozen"] or len(holdout) != 8:
        raise ValueError("frozen holdout must contain exactly eight cases")
    events = rows("financial_events.csv")
    messages = rows("messages.csv")
    images = rows("images.csv")
    message_index = {row["message_id"]: row for row in messages}
    image_index = {row["image_id"]: row for row in images}
    entries, request_files = [], {}
    for case in holdout:
        case_id, user = case["case_id"], case["user_id"]
        if case["split"] != "holdout" or len(case["message_ids"]) != len(set(case["message_ids"])):
            raise ValueError(f"invalid frozen selection: {case_id}")
        if len(case["image_ids"]) != len(set(case["image_ids"])):
            raise ValueError(f"duplicate image selection: {case_id}")
        e = [row for row in events if row["user_id"] == user]
        m = [message_index[x] for x in case["message_ids"]]
        i = [image_index[x] for x in case["image_ids"]]
        if any(row["user_id"] != user for row in m + i):
            raise ValueError(f"cross-user evidence: {case_id}")
        if not set(case["linked_event_ids"]) <= {row["event_id"] for row in e}:
            raise ValueError(f"linked event absent from same-user events: {case_id}")
        paths = [ROOT / "dataset/media/images" / f"{row['image_id']}.png" for row in i]
        if any(not path.is_file() for path in paths):
            raise FileNotFoundError(f"selected image missing: {case_id}")
        runtime_case = {
            "case_id": case_id,
            "evidence": {"events": e, "messages": m, "images": i},
            "image_paths": [str(path) for path in paths],
        }
        body = {"model": extractor.MODEL, "messages": [
            {"role": "system", "content": extractor.SYSTEM_PROMPT},
            {"role": "user", "content": extractor.request_content(runtime_case)},
        ], **extractor.SETTINGS}
        encoded = json.dumps(body).encode("utf-8")
        filename = f"{case_id}.request.json"
        request_files[filename] = encoded
        entries.append({
            "case_id": case_id, "user_id": user, "request_file": filename,
            "included_evidence_ids": {
                "event_ids": [row["event_id"] for row in e],
                "message_ids": [row["message_id"] for row in m],
                "image_ids": [row["image_id"] for row in i],
            },
            "source_provenance": {
                "event_ids": {row["event_id"]: "dataset/financial_events.csv" for row in e},
                "message_ids": {row["message_id"]: "dataset/messages.csv" for row in m},
                "image_ids": {row["image_id"]: f"dataset/media/images/{row['image_id']}.png" for row in i},
            },
            "image_sha256": {row["image_id"]: sha(path.read_bytes()) for row, path in zip(i, paths)},
            "serialized_payload_sha256": sha(encoded),
            "serialized_payload_bytes": len(encoded),
        })
    manifest = {
        "version": "holdout-runtime-inputs-v1", "scope": "holdout_only",
        "split_sha256": sha(SPLIT.read_bytes()),
        "frozen_development_reference_sha256": sha(DEV_REFERENCE.read_bytes()),
        "schema_sha256": sha((ROOT / "code/evidence.py").read_bytes()),
        "extractor_sha256": sha((ROOT / "code/prototype/extraction_experiment.py").read_bytes()),
        "source_table_sha256": {name: sha((ROOT / "dataset" / name).read_bytes())
                                for name in ("financial_events.csv", "messages.csv", "images.csv")},
        "selection_policy": "all same-user financial events; only frozen split message/image IDs",
        "serialization": "json.dumps(body).encode('utf-8') as in extraction_experiment.call_model",
        "payload_format": "extraction_experiment.request_content with full PNG data URLs",
        "profile_included": False, "sample_labels_used": False, "model_calls": 0,
        "cases": entries,
    }
    return manifest, request_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest, requests = build()
    encoded = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    if args.check:
        if (OUT / "manifest.json").read_bytes() != encoded:
            raise ValueError("saved holdout manifest differs from source")
        for name, content in requests.items():
            if (OUT / name).read_bytes() != content:
                raise ValueError(f"saved request differs from source: {name}")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for name, content in requests.items():
            (OUT / name).write_bytes(content)
        (OUT / "manifest.json").write_bytes(encoded)
    print(f"{'verified' if args.check else 'built'} {len(requests)} offline holdout requests")


if __name__ == "__main__":
    main()

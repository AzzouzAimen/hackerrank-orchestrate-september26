"""Build the minimal submission archive from an explicit allowlist."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

FILES = (
    "README.md",
    "requirements.txt",
    "evidence.py",
    "evidence.schema.json",
    "finance.py",
    "input_preparation.py",
    "live_extraction.py",
    "main.py",
    "plans.py",
    "scoped_extraction.py",
    "semantic_extractor.py",
    "semantic_boundary.py",
    "submission_audit.py",
    "submission_preflight.py",
    "submission_runner.py",
    "target_identity.py",
    "evaluation/usage_report.md",
    "tests/__init__.py",
    "tests/test_boundary.py",
    "tests/test_finance_and_plans.py",
    "tests/test_scoped_pipeline.py",
    "tests/test_submission_preflight.py",
    "tests/test_submission_runner.py",
    "tests/test_target_identity.py",
    "prompts/accepted_certainty_minimality_unknowns_v1.txt",
    "prompts/image_scoped_extraction_v1.txt",
)


def main() -> None:
    output = ROOT / "code.zip"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing archive: {output}")
    missing = [name for name in FILES if not (HERE / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing package inputs: " + ", ".join(missing))
    manifest = {}
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in FILES:
            data = (HERE / name).read_bytes()
            archive.writestr(name.replace("\\", "/"), data)
            manifest[name.replace("\\", "/")] = hashlib.sha256(data).hexdigest()
        archive.writestr("MANIFEST.sha256.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"archive": str(output), "files": len(FILES) + 1,
                      "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                      "bytes": output.stat().st_size}, indent=2))


if __name__ == "__main__":
    main()

"""Score saved EvidenceBundle JSON against frozen semantic references.

The holdout split is accessed only through an explicit ``holdout`` command or
``case --split holdout``. This program performs no model inference.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from semantic_benchmark_scorer import human_report, score_case, score_set


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    one = commands.add_parser("case", help="Score one saved EvidenceBundle")
    one.add_argument("case_id")
    one.add_argument("output", type=Path, help="JSON file containing an EvidenceBundle")
    one.add_argument("--split", choices=("development", "holdout"), default="development")
    for name in ("development", "holdout"):
        batch = commands.add_parser(name, help=f"Score all frozen {name} cases")
        batch.add_argument("outputs_dir", type=Path,
                           help="Directory with <case_id>.json files; absent files score unavailable")
    cli.add_argument("--json-out", type=Path, help="Write complete structured results to this path")
    cli.add_argument("--report-out", type=Path, help="Write the concise text report to this path")
    return cli


def read_output(path: Path):
    return path.read_text(encoding="utf-8") if path.is_file() else None


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "case":
            result = score_case(args.split, args.case_id, read_output(args.output))
        else:
            from semantic_benchmark_scorer import load_references
            ids = [a["case_id"] for a in load_references(args.command)["annotations"]]
            outputs = {case_id: read_output(args.outputs_dir / f"{case_id}.json") for case_id in ids}
            result = score_set(args.command, outputs)
    except (ValueError, KeyError, OSError) as exc:
        print(f"Benchmark input error: {exc}", file=sys.stderr)
        return 2
    report = human_report(result)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(report, encoding="utf-8")
    print(report, file=sys.stderr if not args.report_out else sys.stdout, end="")
    return 0 if (result["semantic_pass"] if args.command == "case" else
                 result["summary"]["failed_cases"] == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())

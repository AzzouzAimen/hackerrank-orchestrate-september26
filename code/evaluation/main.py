"""Read-only entry point for saved shadow-evaluation results.

Future full-run evaluation and usage reporting will be added when authorized.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Buy or Wait? saved evaluation")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("saved-summary", help="Show recorded availability and usage; no model calls")
    args = parser.parse_args(argv)
    if args.command == "saved-summary":
        path = Path(__file__).resolve().parents[1] / "prototype/extraction_artifacts/audit_v2/operations.json"
        records = json.loads(path.read_text(encoding="utf-8"))["runs"]
        for record in records:
            print(f"{record['source']}: {record['all_usable']}/{record['logical_runs']} usable, "
                  f"{record['calls']} recorded calls, {record['total_tokens']} recorded tokens")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Buy or Wait command-line entry point."""
from __future__ import annotations

import argparse
from pathlib import Path


def project_root() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (Path.cwd(), here, here.parent):
        if (candidate / "dataset/requests.csv").is_file():
            return candidate
    raise RuntimeError("Cannot find dataset/requests.csv from the working directory or code location")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Buy or Wait? local entry point")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("preflight", help="Validate dataset joins and scope without model calls")
    run_parser = commands.add_parser("run", help="Generate output.csv with guarded live extraction")
    run_parser.add_argument("--artifact", type=Path, default=Path("run_artifacts/final"))
    run_parser.add_argument("--workers", type=int, default=4)
    audit_parser = commands.add_parser("audit", help="Audit an existing output and run artifact without model calls")
    audit_parser.add_argument("--artifact", type=Path, default=Path("run_artifacts/final"))
    audit_parser.add_argument("--output", type=Path, default=Path("output.csv"))
    args = parser.parse_args(argv)
    if args.command == "preflight":
        import json
        from submission_preflight import validate

        print(json.dumps(validate(project_root()), indent=2))
        return 0
    if args.command == "run":
        import json
        import os
        from live_extraction import extract, load_env
        from submission_preflight import validate
        from submission_runner import run

        root = project_root()
        load_env()
        if not os.environ.get("FEATHERLESS_API_KEY"):
            raise RuntimeError("FEATHERLESS_API_KEY is not configured")
        print(json.dumps({"preflight": validate(root)}, indent=2), flush=True)
        result = run(root, root / "dataset/requests.csv", root / "output.csv",
                     args.artifact.resolve(), extract, workers=args.workers)
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "audit":
        import json
        from submission_audit import audit

        root = project_root()
        result = audit(root, args.artifact.resolve(), args.output.resolve())
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

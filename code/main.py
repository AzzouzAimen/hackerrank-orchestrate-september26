"""Entry point for the currently implemented representative replay.

Full-dataset prediction is a separate later stage. This command never reads
evaluation requests or promotes model-generated facts to trusted evidence.
"""
from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Buy or Wait? local entry point")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("representative", help="Replay the five reviewed research cases")
    args = parser.parse_args(argv)
    if args.command == "representative":
        from prototype.run import main as replay

        replay()
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

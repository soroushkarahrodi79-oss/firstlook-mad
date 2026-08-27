"""Reproducible command line interface for the synthetic Phase 0C model."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from firstlook_mad.audit import run_audit_experiment
from firstlook_mad.synthetic import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="firstlook")
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate = subparsers.add_parser("simulate", help="run the Phase 0C synthetic model")
    simulate.add_argument("--config", type=Path, required=True)
    simulate.add_argument("--output", type=Path, required=True)

    validate = subparsers.add_parser("validate-config", help="validate without running")
    validate.add_argument("--config", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    if args.command == "validate-config":
        print(f"valid synthetic config: {config.scenario_id}")
        return 0
    result = run_audit_experiment(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"synthetic model complete: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

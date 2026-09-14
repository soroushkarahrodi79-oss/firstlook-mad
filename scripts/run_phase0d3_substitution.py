"""Run Phase 0D.3 staged reality substitution and write machine-readable outputs.

Outputs (deterministic, payload-free):
  - outputs/reports/phase0d3_substitution_manifest.json
  - outputs/reports/phase0d3_substitution_results.json

The manifest and results are regenerable byte-for-byte from tracked inputs
(the frozen 0C.1 config and the tracked canonical A-02 evidence). No network
access, no new dataset, no third-party record-level payload.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from firstlook_mad.reality_substitution import run_phase0d3

DEFAULT_MANIFEST = Path("outputs/reports/phase0d3_substitution_manifest.json")
DEFAULT_RESULTS = Path("outputs/reports/phase0d3_substitution_results.json")


def _write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_phase0d3_substitution")
    parser.add_argument("--config", type=Path, default=Path("configs/phase0c_synthetic.json"))
    parser.add_argument("--manifest-output", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results-output", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args(argv)

    result = run_phase0d3(config_path=args.config)
    manifest = cast(dict[str, object], result["manifest"])

    _write_json(args.manifest_output, manifest)
    _write_json(args.results_output, result)

    verdict = cast(dict[str, object], result["verdict"])
    entry = cast(dict[str, object], result["entry_decision"])
    print(f"entry_decision: {entry['decision']}")
    print(f"0D.3 verdict: {verdict['verdict']}")
    print(f"manifest: {args.manifest_output}")
    print(f"results: {args.results_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Phase 0D.2 real-data normalization and semantic-fitness gate runner.

Reads only local files -- the committed payload-free ledger
(``outputs/provenance/phase0d/``) and the gitignored raw evidence
(``data/raw/phase0d/``); it never touches the network. Writes the tracked
quality report and licence-cleared canonical A-02 output, plus gitignored
record-level derivatives under ``data/processed/phase0d2/``. The rules are
frozen in ``docs/PHASE_0D2_PREREGISTRATION.md``.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from firstlook_mad.normalization.pipeline import run_normalization, write_run


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-dir", type=Path, default=Path("outputs/provenance/phase0d"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/phase0d"))
    parser.add_argument("--output-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    run = run_normalization(ledger_dir=args.ledger_dir, raw_dir=args.raw_dir)
    for path in write_run(run, output_root=args.output_root):
        print(f"wrote: {path.as_posix()}")
    for item in run.report.assumptions:
        print(
            f"{item.assumption}: integrity={item.integrity} "
            f"structural={item.structural_validity} fitness={item.semantic_fitness} "
            f"completeness={item.completeness} eligibility={item.analytical_eligibility}"
        )
    print(f"0D.2 gate verdict: {run.report.gate.verdict}")
    print("STOP: this runner does not start Phase 0D.3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

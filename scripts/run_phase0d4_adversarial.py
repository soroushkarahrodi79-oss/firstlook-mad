"""Deterministically regenerate the Phase 0D.4 adversarial artifacts.

Writes:
- outputs/reports/phase0d4_adversarial_results.json
- outputs/reports/phase0d4_adversarial_manifest.json

Reuses the frozen Phase 0C.1 engine; acquires no new evidence; mutates no
historical 0C/0D output. Rerunning yields byte-identical files.
"""

from __future__ import annotations

import json
from pathlib import Path

from firstlook_mad.adversarial import build_manifest, build_results

RESULTS_PATH = Path("outputs/reports/phase0d4_adversarial_results.json")
MANIFEST_PATH = Path("outputs/reports/phase0d4_adversarial_manifest.json")


def _write(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    results = build_results()
    manifest = build_manifest(results)
    _write(RESULTS_PATH, results)
    _write(MANIFEST_PATH, manifest)
    verdict = results["formal_real_data_gate"]["aggregation"]["verdict"]  # type: ignore[index]
    print(f"Phase 0D.4 adversarial complete: formal gate = {verdict}")
    print(f"  results:  {RESULTS_PATH}")
    print(f"  manifest: {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

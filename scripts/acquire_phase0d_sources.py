"""Phase 0D bounded, reproducible acquisition attempts.

Each probe requests exactly one small, targeted endpoint identified in
``docs/PHASE_0D_PROTOCOL.md`` and ``data/phase0d_source_probes.json``. The
script never downloads a bulk dataset, never scrapes beyond the documented
endpoint, and never fabricates a fallback when a source is unreachable.

Every attempt is classified so that a network/tooling failure (this
execution environment blocks outbound access to the registered Madrid data
domains — see ``PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md`` §5) is never
confused with a real finding about data availability. Only a probe that
returns ``ACQUIRED`` produced bytes that may later be treated as ``REAL``
evidence; every other outcome is a blocker, not a result.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

Outcome = Literal[
    "ACQUIRED",
    "NETWORK_EGRESS_BLOCKED",
    "HTTP_ERROR",
    "OTHER_ERROR",
]

_BLOCKED_MARKERS = (
    "tunnel connection failed",
    "403 forbidden",
    "connect_rejected",
)


def _classify_error(message: str) -> Outcome:
    lowered = message.lower()
    if any(marker in lowered for marker in _BLOCKED_MARKERS):
        return "NETWORK_EGRESS_BLOCKED"
    if "http error" in lowered:
        return "HTTP_ERROR"
    return "OTHER_ERROR"


def attempt_probe(
    spec: dict[str, Any],
    *,
    timeout_seconds: float = 15.0,
    opener: Any = urllib.request.urlopen,
) -> dict[str, Any]:
    """Attempt one bounded acquisition and classify the outcome.

    Never raises: every failure mode is captured and classified so the
    acquisition log stays a complete, honest record of what was tried.
    """

    max_bytes = int(spec.get("max_bytes", 500_000))
    request = urllib.request.Request(
        spec["url"],
        headers={
            "Accept": spec.get("accept", "application/json"),
            "User-Agent": "FIRSTLOOK-MAD-Phase-0D/0.1 (+bounded research acquisition)",
        },
        method="GET",
    )
    attempted_at = datetime.now(UTC).isoformat()
    try:
        with opener(request, timeout=timeout_seconds) as response:
            body = response.read(max_bytes + 1)
            truncated = len(body) > max_bytes
            body = body[:max_bytes]
            return {
                "probe_id": spec["probe_id"],
                "priority_assumption": spec.get("priority_assumption"),
                "url": spec["url"],
                "attempted_at": attempted_at,
                "outcome": "ACQUIRED",
                "http_status": response.status,
                "bytes_read": len(body),
                "truncated": truncated,
                "nature_if_used": "REAL",
                "error": None,
            }
    except OSError as exc:
        message = f"{type(exc).__name__}: {exc}"
        return {
            "probe_id": spec["probe_id"],
            "priority_assumption": spec.get("priority_assumption"),
            "url": spec["url"],
            "attempted_at": attempted_at,
            "outcome": _classify_error(message),
            "http_status": None,
            "bytes_read": 0,
            "truncated": False,
            "nature_if_used": None,
            "error": message,
        }


def run_acquisition(config: dict[str, Any], *, sleep_between_s: float = 0.2) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for spec in config["probes"]:
        results.append(attempt_probe(spec))
        time.sleep(sleep_between_s)
    acquired = sum(1 for item in results if item["outcome"] == "ACQUIRED")
    blocked = sum(1 for item in results if item["outcome"] == "NETWORK_EGRESS_BLOCKED")
    return {
        "schema_version": "1.0",
        "phase": "0D",
        "generated_at": datetime.now(UTC).isoformat(),
        "config_consulted_at": config["consulted_at"],
        "purpose": config["purpose"],
        "summary": {
            "attempted": len(results),
            "acquired": acquired,
            "network_egress_blocked": blocked,
            "other_failures": len(results) - acquired - blocked,
        },
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("data/phase0d_source_probes.json"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/reports/phase0d_acquisition_log.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    log = run_acquisition(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = log["summary"]
    print(
        f"acquired: {summary['acquired']}/{summary['attempted']}; "
        f"network_egress_blocked: {summary['network_egress_blocked']}; "
        f"other_failures: {summary['other_failures']}"
    )
    print(f"wrote: {args.output}")
    if summary["acquired"] == 0:
        print(
            "NOTE: zero sources acquired. Do not treat this as evidence about "
            "data availability in Madrid — see the outcome classification "
            "of each probe before drawing any conclusion."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

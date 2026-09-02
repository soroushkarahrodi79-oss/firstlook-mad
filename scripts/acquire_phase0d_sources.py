"""Phase 0D bounded, reproducible acquisition attempts.

Each probe requests exactly one small, targeted endpoint identified in
``docs/PHASE_0D_PROTOCOL.md`` and ``data/phase0d_source_probes.json``. The
script never downloads a bulk dataset, never scrapes beyond the documented
endpoint, and never fabricates a fallback when a source is unreachable.

Every attempt is classified so that a network/tooling failure is never
confused with a real finding about data availability, and so that an
``HTTP 200`` response with an empty body is never confused with acquired
evidence either. Only a probe that returns ``ACQUIRED`` (a successful HTTP
response with a non-empty body) produced bytes that may be treated as
``REAL`` evidence; every other outcome is a blocker or a non-result, not a
finding about Madrid. See ``docs/PHASE_0D_PROTOCOL.md`` §7 for the dated
methodological deviation that introduced the ``EMPTY_RESPONSE`` and
``CREDENTIAL_REQUIRED`` outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

Outcome = Literal[
    "ACQUIRED",
    "EMPTY_RESPONSE",
    "CREDENTIAL_REQUIRED",
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


def _response_content_type(response: Any) -> str | None:
    headers = getattr(response, "headers", None)
    getter = getattr(headers, "get", None)
    if getter is None:
        return None
    value = getter("Content-Type")
    return str(value) if value is not None else None


def _raw_target_path(raw_dir: Path, probe_id: str, attempted_at: str) -> Path:
    """Deterministic, source-specific raw evidence path for a given day."""
    date_part = attempted_at[:10].replace("-", "")
    return raw_dir / probe_id / f"{date_part}.raw"


def _raw_fallback_path(raw_dir: Path, probe_id: str, attempted_at: str) -> Path:
    """Deterministic, run-specific fallback path used only on a same-day
    content mismatch, so existing raw evidence is never overwritten."""
    compact = attempted_at.replace("-", "").replace(":", "").split(".")[0].split("+")[0]
    return raw_dir / probe_id / f"{compact}Z.raw"


def persist_raw_response(
    raw_dir: Path,
    spec: dict[str, Any],
    body: bytes,
    *,
    attempted_at: str,
    http_status: int,
    content_type: str | None,
    truncated: bool,
    config_consulted_at: str,
) -> dict[str, Any]:
    """Persist a non-empty acquired response as immutable raw evidence.

    The primary target path is deterministic (probe id + acquisition date).
    If that path already holds *different* bytes from an earlier run, this
    falls back to a deterministic, run-specific path derived from this
    attempt's own timestamp -- raw evidence already on disk is never
    overwritten. If both the primary and fallback paths already hold
    different content (should not happen in normal operation), this raises
    rather than risk silently corrupting evidence.
    """

    probe_id = spec["probe_id"]
    source_dir = raw_dir / probe_id
    source_dir.mkdir(parents=True, exist_ok=True)

    target = _raw_target_path(raw_dir, probe_id, attempted_at)
    if target.exists() and target.read_bytes() != body:
        target = _raw_fallback_path(raw_dir, probe_id, attempted_at)
        if target.exists() and target.read_bytes() != body:
            raise FileExistsError(
                f"raw evidence target {target} already exists with different "
                f"content for probe '{probe_id}'; refusing to overwrite "
                "immutable evidence"
            )

    provenance_path = target.with_name(target.name + ".provenance.json")
    if target.exists():
        # Identical bytes already persisted (e.g. same-day rerun): the raw
        # file and its original provenance record stay untouched.
        existing: dict[str, Any] = json.loads(provenance_path.read_text(encoding="utf-8"))
        return existing

    target.write_bytes(body)
    provenance = {
        "probe_id": probe_id,
        "source_url": spec["url"],
        "acquired_at_utc": attempted_at,
        "http_status": http_status,
        "content_type": content_type,
        "byte_count": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "local_raw_path": target.as_posix(),
        "truncated": truncated,
        "evidence_nature": "REAL",
        "config_consulted_at": config_consulted_at,
    }
    provenance_path.write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return provenance


def attempt_probe(
    spec: dict[str, Any],
    *,
    timeout_seconds: float = 15.0,
    opener: Any = urllib.request.urlopen,
    raw_dir: Path | None = None,
    config_consulted_at: str = "",
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Attempt one bounded acquisition and classify the outcome.

    Never raises on a failed acquisition attempt: every failure mode is
    captured and classified so the acquisition log stays a complete, honest
    record of what was tried. (``persist_raw_response`` may still raise if it
    detects it would have to overwrite conflicting immutable evidence --
    that is a data-integrity guard, not a network-failure path.)

    A probe whose spec declares ``credential_env_var`` (e.g. AEMET) is never
    attempted over the network without that credential present in ``env``:
    it is classified ``CREDENTIAL_REQUIRED`` instead, so an unauthenticated
    response can never be mistaken for acquired evidence. When the
    credential is present it is sent as a request header only -- never as a
    URL query parameter -- and is never included in the returned result or
    in any persisted provenance.
    """

    env = env if env is not None else os.environ
    attempted_at = datetime.now(UTC).isoformat()
    base = {
        "probe_id": spec["probe_id"],
        "priority_assumption": spec.get("priority_assumption"),
        "url": spec["url"],
        "attempted_at": attempted_at,
    }
    empty_extras = {
        "content_type": None,
        "sha256": None,
        "raw_path": None,
        "nature_if_used": None,
    }

    credential_env_var = spec.get("credential_env_var")
    if credential_env_var and not env.get(credential_env_var):
        return {
            **base,
            "outcome": "CREDENTIAL_REQUIRED",
            "http_status": None,
            "bytes_read": 0,
            "truncated": False,
            "error": None,
            **empty_extras,
        }

    headers = {
        "Accept": spec.get("accept", "application/json"),
        "User-Agent": "FIRSTLOOK-MAD-Phase-0D/0.1 (+bounded research acquisition)",
    }
    if credential_env_var:
        headers[spec.get("credential_header", "api_key")] = env[credential_env_var]

    max_bytes = int(spec.get("max_bytes", 500_000))
    request = urllib.request.Request(spec["url"], headers=headers, method="GET")
    try:
        with opener(request, timeout=timeout_seconds) as response:
            body = response.read(max_bytes + 1)
            truncated = len(body) > max_bytes
            body = body[:max_bytes]
            content_type = _response_content_type(response)
            status = response.status

            if len(body) == 0:
                return {
                    **base,
                    "outcome": "EMPTY_RESPONSE",
                    "http_status": status,
                    "bytes_read": 0,
                    "truncated": False,
                    "error": None,
                    "content_type": content_type,
                    "sha256": None,
                    "raw_path": None,
                    "nature_if_used": None,
                }

            digest = hashlib.sha256(body).hexdigest()
            raw_path: str | None = None
            if raw_dir is not None:
                provenance = persist_raw_response(
                    raw_dir,
                    spec,
                    body,
                    attempted_at=attempted_at,
                    http_status=status,
                    content_type=content_type,
                    truncated=truncated,
                    config_consulted_at=config_consulted_at,
                )
                raw_path = provenance["local_raw_path"]

            return {
                **base,
                "outcome": "ACQUIRED",
                "http_status": status,
                "bytes_read": len(body),
                "truncated": truncated,
                "error": None,
                "content_type": content_type,
                "sha256": digest,
                "raw_path": raw_path,
                "nature_if_used": "REAL",
            }
    except OSError as exc:
        message = f"{type(exc).__name__}: {exc}"
        return {
            **base,
            "outcome": _classify_error(message),
            "http_status": None,
            "bytes_read": 0,
            "truncated": False,
            "error": message,
            **empty_extras,
        }


def run_acquisition(
    config: dict[str, Any],
    *,
    sleep_between_s: float = 0.2,
    raw_dir: Path | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for spec in config["probes"]:
        results.append(
            attempt_probe(
                spec,
                raw_dir=raw_dir,
                config_consulted_at=config["consulted_at"],
            )
        )
        time.sleep(sleep_between_s)

    counts = dict.fromkeys(
        [
            "ACQUIRED",
            "EMPTY_RESPONSE",
            "CREDENTIAL_REQUIRED",
            "NETWORK_EGRESS_BLOCKED",
            "HTTP_ERROR",
            "OTHER_ERROR",
        ],
        0,
    )
    for item in results:
        counts[item["outcome"]] += 1

    return {
        "schema_version": "1.1",
        "phase": "0D",
        "generated_at": datetime.now(UTC).isoformat(),
        "config_consulted_at": config["consulted_at"],
        "purpose": config["purpose"],
        "summary": {
            "attempted": len(results),
            "acquired": counts["ACQUIRED"],
            "empty_response": counts["EMPTY_RESPONSE"],
            "credential_required": counts["CREDENTIAL_REQUIRED"],
            "network_egress_blocked": counts["NETWORK_EGRESS_BLOCKED"],
            "http_error": counts["HTTP_ERROR"],
            "other_failures": counts["OTHER_ERROR"],
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
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw/phase0d"),
        help="Directory for immutable raw evidence persisted from ACQUIRED probes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    log = run_acquisition(config, raw_dir=args.raw_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = log["summary"]
    print(
        f"acquired: {summary['acquired']}/{summary['attempted']}; "
        f"empty_response: {summary['empty_response']}; "
        f"credential_required: {summary['credential_required']}; "
        f"network_egress_blocked: {summary['network_egress_blocked']}; "
        f"http_error: {summary['http_error']}; "
        f"other_failures: {summary['other_failures']}"
    )
    print(f"wrote: {args.output}")
    if summary["acquired"] > 0:
        print(f"raw evidence (if any new bytes): {args.raw_dir}")
    if summary["acquired"] == 0:
        print(
            "NOTE: zero sources acquired. Do not treat this as evidence about "
            "data availability in Madrid -- see the outcome classification "
            "of each probe before drawing any conclusion."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

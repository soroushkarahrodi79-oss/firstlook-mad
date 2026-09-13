"""Phase 0D.1C bounded, same-run AEMET two-hop acquisition.

AEMET's OpenData API returns a JSON *wrapper* containing a short-lived
``datos`` handle URL that must be followed almost immediately or it expires
(observed directly in Phase 0D.1B: a hop performed ~16 minutes after the
wrapper was acquired had already expired). This module performs both hops
in a single execution so the handle is followed as soon as it is resolved.

This is deliberately NOT a generic URL-follower. The hop-1 endpoint is a
fixed, hardcoded official AEMET OpenData URL, and the hop-2 request is only
made if the resolved ``datos`` URL's host is in :data:`ALLOWED_SECONDHOP_HOSTS`
-- the official AEMET OpenData storage domain. Any other host found in a
wrapper body is refused and reported as ``DISALLOWED_HOST`` rather than
followed.

Credential handling: the API key is read only from the ``AEMET_API_KEY``
environment variable, sent only as a request header (never a URL query
parameter), and never appears in a return value, log line, or persisted
provenance record. If the variable is unset, hop 1 is not attempted at all
(``CREDENTIAL_REQUIRED``) -- there is no fallback, unauthenticated request.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from scripts.acquire_phase0d_sources import (
    _classify_error,
    _response_content_type,
    attempt_probe,
    persist_raw_response,
)

AEMET_WRAPPER_PROBE_ID = "aemet_madrid_station_inventory"
AEMET_WRAPPER_URL = (
    "https://opendata.aemet.es/opendata/api/valores/climatologicos/"
    "inventarioestaciones/todasestaciones"
)
AEMET_SECONDHOP_PROBE_ID = "aemet_madrid_station_inventory_datos"
AEMET_CREDENTIAL_ENV_VAR = "AEMET_API_KEY"
AEMET_CREDENTIAL_HEADER = "api_key"

# Only this host is ever followed for a hop-2 request. AEMET's documented
# OpenData pattern always resolves `datos`/`metadatos` to this storage domain.
ALLOWED_SECONDHOP_HOSTS = frozenset({"opendata.aemet.es"})

SecondHopOutcome = Literal[
    "ACQUIRED",
    "NOT_ATTEMPTED",
    "MISSING_DATOS_FIELD",
    "DISALLOWED_HOST",
    "EMPTY_RESPONSE",
    "HTTP_ERROR",
    "NETWORK_EGRESS_BLOCKED",
    "OTHER_ERROR",
]

SecondHopClassification = Literal[
    "REAL_SOURCE_DATA",
    "NOT_USABLE_FOR_TARGET_TEST",
]


def _extract_datos_url(wrapper_body: bytes) -> str | None:
    try:
        payload = json.loads(wrapper_body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    datos = payload.get("datos")
    return datos if isinstance(datos, str) and datos else None


def _classify_secondhop_payload(body: bytes) -> SecondHopClassification:
    """Classify a resolved payload honestly -- REAL_SOURCE_DATA only if it
    actually looks like AEMET station-inventory records."""
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return "NOT_USABLE_FOR_TARGET_TEST"
    if (
        isinstance(payload, list)
        and payload
        and isinstance(payload[0], dict)
        and "indicativo" in payload[0]
    ):
        return "REAL_SOURCE_DATA"
    return "NOT_USABLE_FOR_TARGET_TEST"


def _station_summary(body: bytes) -> dict[str, Any]:
    """Only called once a payload is classified REAL_SOURCE_DATA."""
    stations: list[dict[str, Any]] = json.loads(body)
    madrid = [s for s in stations if str(s.get("provincia", "")).upper() == "MADRID"]
    return {
        "record_count": len(stations),
        "station_identifiers_sample": [s.get("indicativo") for s in stations[:5]],
        "province_field_present": all("provincia" in s for s in stations),
        "coordinate_fields_present": all("latitud" in s and "longitud" in s for s in stations),
        "madrid_station_count": len(madrid),
        "madrid_station_identifiers": [s.get("indicativo") for s in madrid],
    }


def run_aemet_secondhop(
    *,
    raw_dir: Path,
    config_consulted_at: str,
    env: Mapping[str, str],
    wrapper_opener: Any = urllib.request.urlopen,
    secondhop_opener: Any = urllib.request.urlopen,
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    """Run the bounded, same-execution AEMET wrapper + second-hop flow.

    Exactly one hop-1 request and, at most, one hop-2 request are made --
    there is no retry loop and no following of a URL found inside the
    hop-2 payload itself (AEMET's handle payloads do not contain further
    handles, and this function has no code path that would look for one).
    """
    hop1_spec = {
        "probe_id": AEMET_WRAPPER_PROBE_ID,
        "priority_assumption": "A-04",
        "url": AEMET_WRAPPER_URL,
        "accept": "application/json",
        "max_bytes": 500_000,
        "credential_env_var": AEMET_CREDENTIAL_ENV_VAR,
        "credential_header": AEMET_CREDENTIAL_HEADER,
    }
    hop1 = attempt_probe(
        hop1_spec,
        timeout_seconds=timeout_seconds,
        opener=wrapper_opener,
        raw_dir=raw_dir,
        config_consulted_at=config_consulted_at,
        env=env,
    )

    if hop1["outcome"] != "ACQUIRED":
        return {
            "hop1": hop1,
            "hop2": {
                "outcome": "NOT_ATTEMPTED",
                "reason": f"hop1 outcome was {hop1['outcome']}, not ACQUIRED",
                "resolved_url": None,
                "http_status": None,
                "sha256": None,
                "raw_path": None,
                "classification": None,
            },
        }

    raw_path = hop1["raw_path"]
    if raw_path is None:
        raise RuntimeError("hop1 outcome was ACQUIRED but returned no raw_path")
    parent_raw_path = Path(raw_path)
    wrapper_body = parent_raw_path.read_bytes()
    resolved_url = _extract_datos_url(wrapper_body)

    if resolved_url is None:
        return {
            "hop1": hop1,
            "hop2": {
                "outcome": "MISSING_DATOS_FIELD",
                "reason": "wrapper body has no non-empty 'datos' field",
                "resolved_url": None,
                "http_status": None,
                "sha256": None,
                "raw_path": None,
                "classification": None,
            },
        }

    host = urlparse(resolved_url).hostname
    if host not in ALLOWED_SECONDHOP_HOSTS:
        return {
            "hop1": hop1,
            "hop2": {
                "outcome": "DISALLOWED_HOST",
                "reason": f"resolved host {host!r} is not in {sorted(ALLOWED_SECONDHOP_HOSTS)}",
                "resolved_url": resolved_url,
                "http_status": None,
                "sha256": None,
                "raw_path": None,
                "classification": None,
            },
        }

    hop2 = _fetch_secondhop(
        resolved_url=resolved_url,
        parent_probe_id=AEMET_WRAPPER_PROBE_ID,
        parent_sha256=hop1["sha256"],
        parent_acquired_at_utc=hop1["attempted_at"],
        raw_dir=raw_dir,
        config_consulted_at=config_consulted_at,
        opener=secondhop_opener,
        timeout_seconds=timeout_seconds,
    )
    return {"hop1": hop1, "hop2": hop2}


def _fetch_secondhop(
    *,
    resolved_url: str,
    parent_probe_id: str,
    parent_sha256: str | None,
    parent_acquired_at_utc: str | None,
    raw_dir: Path,
    config_consulted_at: str,
    opener: Any,
    timeout_seconds: float,
) -> dict[str, Any]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "FIRSTLOOK-MAD-Phase-0D/0.1 (+bounded research acquisition)",
    }
    request = urllib.request.Request(resolved_url, headers=headers, method="GET")
    attempted_at = datetime.now(UTC).isoformat()
    max_bytes = 2_000_000

    try:
        with opener(request, timeout=timeout_seconds) as response:
            body = response.read(max_bytes + 1)
            truncated = len(body) > max_bytes
            body = body[:max_bytes]
            status = response.status
            content_type = _response_content_type(response)
    except OSError as exc:
        message = f"{type(exc).__name__}: {exc}"
        return {
            "outcome": _classify_error(message),
            "reason": message,
            "resolved_url": resolved_url,
            "http_status": None,
            "sha256": None,
            "raw_path": None,
            "classification": None,
        }

    if len(body) == 0:
        return {
            "outcome": "EMPTY_RESPONSE",
            "reason": "hop2 returned HTTP 200 with an empty body",
            "resolved_url": resolved_url,
            "http_status": status,
            "sha256": None,
            "raw_path": None,
            "classification": None,
        }

    spec = {"probe_id": AEMET_SECONDHOP_PROBE_ID, "url": resolved_url}
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
    provenance_path = Path(provenance["local_raw_path"] + ".provenance.json")
    on_disk: dict[str, Any] = json.loads(provenance_path.read_text(encoding="utf-8"))
    if "parent_probe_id" not in on_disk:
        on_disk["parent_probe_id"] = parent_probe_id
        on_disk["parent_raw_sha256"] = parent_sha256
        on_disk["parent_acquired_at_utc"] = parent_acquired_at_utc
        on_disk["resolved_url"] = resolved_url
        on_disk["hop"] = 2
        provenance_path.write_text(
            json.dumps(on_disk, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    classification = _classify_secondhop_payload(body)
    result: dict[str, Any] = {
        "outcome": "ACQUIRED",
        "resolved_url": resolved_url,
        "http_status": status,
        "sha256": provenance["sha256"],
        "raw_path": provenance["local_raw_path"],
        "classification": classification,
    }
    if classification == "REAL_SOURCE_DATA":
        result["station_summary"] = _station_summary(body)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/phase0d"))
    parser.add_argument("--config-consulted-at", default="2026-08-31T10:00:00+02:00")
    args = parser.parse_args()

    result = run_aemet_secondhop(
        raw_dir=args.raw_dir,
        config_consulted_at=args.config_consulted_at,
        env=os.environ,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

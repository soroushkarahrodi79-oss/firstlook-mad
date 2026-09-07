"""Phase 0D.1C bounded IGN/PNOA elevation (MDT05) service discovery.

The Phase 0D.1B IGN artifact (``/collections?f=json`` on
``api-features.idee.es``) turned out to be the wrong service family: an
INSPIRE vector-features API with zero terrain/elevation collections. This
module performs exactly two small, official, hardcoded metadata requests
against IGN's actual elevation service to confirm whether an MDT05-equivalent
product exists:

  1. ``GetCapabilities`` on the official WCS-INSPIRE MDT endpoint;
  2. ``DescribeCoverage`` for the resolved 5m-resolution peninsular coverage
     (a coverage description is grid/extent *metadata*, not raster bytes).

Neither request downloads a terrain tile or any raster pixel data --
``GetCoverage`` (the operation that would return actual elevation values) is
never called by this module.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.acquire_phase0d_sources import (
    _classify_error,
    _response_content_type,
    persist_raw_response,
)

WCS_BASE_URL = "https://servicios.idee.es/wcs-inspire/mdt"
CAPABILITIES_URL = f"{WCS_BASE_URL}?service=WCS&request=GetCapabilities"
FIVE_METER_PENINSULAR_COVERAGE_ID = "Elevacion25830_5"
DESCRIBE_COVERAGE_URL = (
    f"{WCS_BASE_URL}?service=WCS&version=2.0.1&request=DescribeCoverage"
    f"&coverageId={FIVE_METER_PENINSULAR_COVERAGE_ID}"
)
USER_AGENT = "FIRSTLOOK-MAD-Phase-0D/0.1 (+bounded research acquisition)"


def _fetch(url: str, *, opener: Any, timeout: float) -> tuple[str, int | None, bytes, str | None]:
    """GET one metadata URL. Never raises: failures are classified and
    returned rather than propagated."""
    request = urllib.request.Request(
        url, headers={"Accept": "application/xml", "User-Agent": USER_AGENT}, method="GET"
    )
    try:
        with opener(request, timeout=timeout) as response:
            body = response.read()
            outcome = "ACQUIRED" if body else "EMPTY_RESPONSE"
            return outcome, response.status, body, _response_content_type(response)
    except urllib.error.HTTPError as exc:
        return "HTTP_ERROR", exc.code, b"", None
    except OSError as exc:
        return _classify_error(str(exc)), None, b"", None


def _require_status(status: int | None) -> int:
    if status is None:
        raise RuntimeError("outcome was ACQUIRED but no HTTP status was captured")
    return status


def _persist(
    *,
    raw_dir: Path,
    probe_id: str,
    url: str,
    body: bytes,
    status: int,
    content_type: str | None,
    config_consulted_at: str,
) -> dict[str, Any]:
    attempted_at = datetime.now(UTC).isoformat()
    spec = {"probe_id": probe_id, "url": url}
    provenance = persist_raw_response(
        raw_dir,
        spec,
        body,
        attempted_at=attempted_at,
        http_status=status,
        content_type=content_type,
        truncated=False,
        config_consulted_at=config_consulted_at,
    )
    return {
        "outcome": "ACQUIRED",
        "raw_path": provenance["local_raw_path"],
        "sha256": provenance["sha256"],
        "http_status": status,
    }


def _extract_5m_coverage_ids(capabilities_xml: bytes) -> list[str]:
    text = capabilities_xml.decode("utf-8", errors="replace")
    ids = re.findall(r"<wcs:CoverageId>([^<]*)</wcs:CoverageId>", text)
    return [cid for cid in ids if cid.endswith("_5")]


def _extract_service_metadata(capabilities_xml: bytes) -> dict[str, str | None]:
    text = capabilities_xml.decode("utf-8", errors="replace")
    title = re.search(r"<ows:Title>([^<]*)</ows:Title>", text)
    abstract = re.search(r"<ows:Abstract>([^<]*)</ows:Abstract>", text)
    return {
        "title": title.group(1) if title else None,
        "abstract": abstract.group(1) if abstract else None,
    }


def _extract_extent_and_resolution(describe_xml: bytes) -> dict[str, Any]:
    text = describe_xml.decode("utf-8", errors="replace")
    envelope = re.search(
        r'<gml:Envelope srsName="([^"]*)"[^>]*>\s*'
        r"<gml:lowerCorner>([^<]*)</gml:lowerCorner>\s*"
        r"<gml:upperCorner>([^<]*)</gml:upperCorner>",
        text,
    )
    offsets = re.findall(r"<gml:offsetVector[^>]*>([^<]*)</gml:offsetVector>", text)
    return {
        "crs": envelope.group(1) if envelope else None,
        "lower_corner": envelope.group(2) if envelope else None,
        "upper_corner": envelope.group(3) if envelope else None,
        "grid_offset_vectors_m": offsets,
    }


def _run_capabilities_step(
    *, raw_dir: Path, config_consulted_at: str, opener: Any, timeout_seconds: float
) -> dict[str, Any]:
    outcome, status, body, content_type = _fetch(
        CAPABILITIES_URL, opener=opener, timeout=timeout_seconds
    )
    if outcome != "ACQUIRED":
        return {"outcome": outcome, "http_status": status}

    result = _persist(
        raw_dir=raw_dir,
        probe_id="ign_wcs_mdt_capabilities",
        url=CAPABILITIES_URL,
        body=body,
        status=_require_status(status),
        content_type=content_type,
        config_consulted_at=config_consulted_at,
    )
    five_meter_ids = _extract_5m_coverage_ids(body)
    result["classification"] = "REAL_METADATA"
    result["service_metadata"] = _extract_service_metadata(body)
    result["mdt05_equivalent_coverage_ids"] = five_meter_ids
    result["mdt05_available"] = len(five_meter_ids) > 0
    return result


def _run_describe_coverage_step(
    *, raw_dir: Path, config_consulted_at: str, opener: Any, timeout_seconds: float
) -> dict[str, Any]:
    outcome, status, body, content_type = _fetch(
        DESCRIBE_COVERAGE_URL, opener=opener, timeout=timeout_seconds
    )
    if outcome != "ACQUIRED":
        return {"outcome": outcome, "http_status": status}

    result = _persist(
        raw_dir=raw_dir,
        probe_id="ign_wcs_mdt_describe_5m",
        url=DESCRIBE_COVERAGE_URL,
        body=body,
        status=_require_status(status),
        content_type=content_type,
        config_consulted_at=config_consulted_at,
    )
    result["classification"] = "REAL_METADATA"
    result.update(_extract_extent_and_resolution(body))
    return result


def run_ign_mdt_discovery(
    *,
    raw_dir: Path,
    config_consulted_at: str,
    opener: Any = urllib.request.urlopen,
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    """Two-step, metadata-only IGN MDT05 discovery. Never downloads raster
    tiles -- only ``GetCapabilities`` and ``DescribeCoverage``."""
    capabilities = _run_capabilities_step(
        raw_dir=raw_dir,
        config_consulted_at=config_consulted_at,
        opener=opener,
        timeout_seconds=timeout_seconds,
    )
    coverage_ids = capabilities.get("mdt05_equivalent_coverage_ids") or []
    if FIVE_METER_PENINSULAR_COVERAGE_ID not in coverage_ids:
        return {"capabilities": capabilities, "describe_coverage": {"outcome": "NOT_ATTEMPTED"}}

    describe_coverage = _run_describe_coverage_step(
        raw_dir=raw_dir,
        config_consulted_at=config_consulted_at,
        opener=opener,
        timeout_seconds=timeout_seconds,
    )
    return {"capabilities": capabilities, "describe_coverage": describe_coverage}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/phase0d"))
    parser.add_argument("--config-consulted-at", default="2026-08-31T10:00:00+02:00")
    args = parser.parse_args()

    result = run_ign_mdt_discovery(
        raw_dir=args.raw_dir,
        config_consulted_at=args.config_consulted_at,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Phase 0D.1D bounded IGN/PNOA MDT05 elevation GetCoverage sample.

Phase 0D.1C (``scripts/acquire_phase0d_ign_mdt.py``) proved, metadata-only,
that IGN publishes an MDT05-equivalent 5 m coverage (``Elevacion25830_5``) on
its official WCS service and described its grid/extent. That module never
downloads a raster tile by design -- its docstring guarantees ``GetCoverage``
is never called.

This module performs exactly that missing step, once and bounded: a single
``GetCoverage`` request for a deliberately tiny Madrid-centre window, to prove
the chain

    metadata -> bounded real MDT05 terrain payload

is reproducible. It is NOT a bulk terrain download and NOT a tile crawler:

  * exactly one request is made -- there is no pagination and no tile loop;
  * the subset window is a fixed ~100 m x 100 m box (a 20 x 20 grid of 5 m
    posts), hardcoded below, well inside the coverage extent reported by the
    Phase 0D.1C ``DescribeCoverage`` metadata;
  * the coverage id, service base URL and CRS are the ones already verified in
    0D.1C -- this module discovers nothing new;
  * TLS certificate verification is left enabled (the default
    ``urllib``/``ssl`` behaviour); it is never disabled to force a response;
  * the exact bytes received are persisted immutably with SHA-256 provenance
    under ``data/raw/phase0d/`` (gitignored), and the payload is classified
    only after inspecting its actual content -- a GeoTIFF magic number yields
    ``REAL_SOURCE_DATA``; an XML ``ServiceException`` or any other body is
    classified honestly as not real terrain, never as a raster.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from scripts.acquire_phase0d_ign_mdt import (
    FIVE_METER_PENINSULAR_COVERAGE_ID,
    USER_AGENT,
    WCS_BASE_URL,
)
from scripts.acquire_phase0d_sources import (
    _classify_error,
    _response_content_type,
    persist_raw_response,
)

GETCOVERAGE_PROBE_ID = "ign_mdt05_getcoverage_madrid_sample"

# Deliberately tiny Madrid-centre window in the coverage's own CRS
# (EPSG:25830, easting/northing metres). ~100 m x 100 m -> a 20 x 20 grid of
# 5 m posts. Both corners sit well inside the Elevacion25830_5 extent reported
# by the Phase 0D.1C DescribeCoverage metadata
# (x in [-19452.5, 1140352.5], y in [3901197.5, 4865682.5]).
SUBSET_CRS = "EPSG:25830"
SUBSET_X_MIN = 440000
SUBSET_X_MAX = 440100
SUBSET_Y_MIN = 4474000
SUBSET_Y_MAX = 4474100
OUTPUT_FORMAT = "image/tiff"

GETCOVERAGE_URL = (
    f"{WCS_BASE_URL}?service=WCS&version=2.0.1&request=GetCoverage"
    f"&coverageId={FIVE_METER_PENINSULAR_COVERAGE_ID}"
    f"&subset=x({SUBSET_X_MIN},{SUBSET_X_MAX})"
    f"&subset=y({SUBSET_Y_MIN},{SUBSET_Y_MAX})"
    f"&format={OUTPUT_FORMAT}"
)

# Safety ceiling only. The bounded 20 x 20 window is a few kilobytes; this cap
# exists so a misbehaving service can never stream an unbounded body into
# immutable raw evidence. A truncated response is flagged, never silently
# treated as a complete raster.
MAX_BYTES = 4_000_000

CoverageOutcome = Literal[
    "ACQUIRED",
    "EMPTY_RESPONSE",
    "HTTP_ERROR",
    "NETWORK_EGRESS_BLOCKED",
    "OTHER_ERROR",
]

CoverageClassification = Literal[
    "REAL_SOURCE_DATA",
    "SERVICE_EXCEPTION",
    "UNRECOGNIZED_PAYLOAD",
]

# GeoTIFF is an ordinary TIFF; the WCS ``image/tiff`` output starts with a
# standard TIFF header: "II" + 42 (little-endian) or "MM" + 42 (big-endian),
# and the BigTIFF variants "II" + 43 / "MM" + 43.
_TIFF_MAGIC = (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")


def _looks_like_tiff(body: bytes) -> bool:
    return body[:4] in _TIFF_MAGIC


def _looks_like_service_exception(body: bytes) -> bool:
    head = body[:2048].lower()
    return b"exceptionreport" in head or b"serviceexception" in head


def _classify_coverage_payload(body: bytes) -> CoverageClassification:
    """Classify a GetCoverage body honestly, from its actual content.

    ``REAL_SOURCE_DATA`` only when the bytes are a real GeoTIFF raster; an XML
    service exception or any unrecognised body is never dressed up as terrain.
    """
    if _looks_like_tiff(body):
        return "REAL_SOURCE_DATA"
    if _looks_like_service_exception(body):
        return "SERVICE_EXCEPTION"
    return "UNRECOGNIZED_PAYLOAD"


def _fetch(
    url: str, *, opener: Any, timeout: float
) -> tuple[CoverageOutcome, int | None, bytes, str | None, bool]:
    """GET one URL. Never raises: failures are classified and returned.

    Reads at most ``MAX_BYTES`` (+1 to detect truncation). TLS verification is
    whatever ``opener`` provides; the default ``urllib.request.urlopen`` keeps
    certificate verification on and this module never turns it off.
    """
    request = urllib.request.Request(
        url,
        headers={"Accept": f"{OUTPUT_FORMAT}, application/xml", "User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with opener(request, timeout=timeout) as response:
            body = response.read(MAX_BYTES + 1)
            truncated = len(body) > MAX_BYTES
            body = body[:MAX_BYTES]
            outcome: CoverageOutcome = "ACQUIRED" if body else "EMPTY_RESPONSE"
            return outcome, response.status, body, _response_content_type(response), truncated
    except urllib.error.HTTPError as exc:
        return "HTTP_ERROR", exc.code, b"", None, False
    except OSError as exc:
        # _classify_error only ever returns NETWORK_EGRESS_BLOCKED / HTTP_ERROR
        # / OTHER_ERROR here, all valid CoverageOutcome members.
        classified = cast(CoverageOutcome, _classify_error(f"{type(exc).__name__}: {exc}"))
        return classified, None, b"", None, False


def run_ign_mdt_getcoverage_sample(
    *,
    raw_dir: Path,
    config_consulted_at: str,
    opener: Any = urllib.request.urlopen,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """Run the single bounded MDT05 GetCoverage request.

    Returns a JSON-serialisable summary. Only an ``ACQUIRED`` outcome persists
    raw bytes; every other outcome is a blocker or non-result, never treated as
    a raster. ``persist_raw_response`` may still raise if it would have to
    overwrite conflicting immutable evidence -- that is a data-integrity guard,
    not a network path.
    """
    outcome, status, body, content_type, truncated = _fetch(
        GETCOVERAGE_URL, opener=opener, timeout=timeout_seconds
    )

    base: dict[str, Any] = {
        "probe_id": GETCOVERAGE_PROBE_ID,
        "assumption": "A-03",
        "source_url": GETCOVERAGE_URL,
        "coverage_id": FIVE_METER_PENINSULAR_COVERAGE_ID,
        "subset_crs": SUBSET_CRS,
        "subset_bbox": {
            "x_min": SUBSET_X_MIN,
            "x_max": SUBSET_X_MAX,
            "y_min": SUBSET_Y_MIN,
            "y_max": SUBSET_Y_MAX,
        },
        "requested_format": OUTPUT_FORMAT,
        "outcome": outcome,
        "http_status": status,
    }

    if outcome != "ACQUIRED":
        base["classification"] = None
        base["raw_path"] = None
        base["sha256"] = None
        return base

    attempted_at = datetime.now(UTC).isoformat()
    spec = {"probe_id": GETCOVERAGE_PROBE_ID, "url": GETCOVERAGE_URL}
    provenance = persist_raw_response(
        raw_dir,
        spec,
        body,
        attempted_at=attempted_at,
        http_status=status if status is not None else 200,
        content_type=content_type,
        truncated=truncated,
        config_consulted_at=config_consulted_at,
    )

    classification = _classify_coverage_payload(body)
    base["classification"] = classification
    base["content_type"] = content_type
    base["byte_count"] = provenance["byte_count"]
    base["sha256"] = provenance["sha256"]
    base["raw_path"] = provenance["local_raw_path"]
    base["truncated"] = truncated
    base["is_geotiff"] = classification == "REAL_SOURCE_DATA"
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/phase0d"))
    parser.add_argument("--config-consulted-at", default="2026-08-31T10:00:00+02:00")
    args = parser.parse_args()

    result = run_ign_mdt_getcoverage_sample(
        raw_dir=args.raw_dir,
        config_consulted_at=args.config_consulted_at,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

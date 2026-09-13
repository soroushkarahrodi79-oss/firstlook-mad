"""Phase 0D.1C bounded EGIF (public forest-fire search) Madrid flow.

Performs the smallest sequence of official, hardcoded EGIF endpoints needed
to attempt a Madrid-filtered first result page in a single session:

  1. GET the public search landing page (fresh anti-forgery token + cookie);
  2. GET the official CCAA lookup helper, resolve "MADRID"'s id;
  3. GET the official province lookup helper for that CCAA id, resolve
     "MADRID" province's id;
  4. POST the search form (all fields taken from the landing page, with the
     CCAA/province ids and a narrow year window overridden);
  5. GET the first result page.

Every URL touched here is a hardcoded, official EGIF path -- never a URL
taken from response content -- so this is not a generic follower. No XML
incident chapters are downloaded, no pagination is crawled, and only one
narrow year window is tried.
"""

from __future__ import annotations

import argparse
import http.cookiejar
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

BASE_URL = "https://servicio.mapa.gob.es"
LANDING_PATH = "/incendios/Search/Publico"
CCAA_LOOKUP_PATH = "/incendios/ParteIncendioForestal/GetComunidadesAutonomasPublico"
PROVINCE_LOOKUP_PATH = "/incendios/ParteIncendioForestal/ProvinciasByCCAAIdPublico"
RESULTS_PATH = "/incendios/Search/PublicoPag"

FORM_FIELD_NAMES = (
    "__RequestVerificationToken",
    "c_bloque_maximoXml",
    "c_intervalo_c",
    "cbxNumPaginas",
    "egif_pin",
    "exportacinoTipo_R",
    "hdd_CCAA",
    "hdd_Causa",
    "hdd_Comarca",
    "hdd_EstadoPif",
    "hdd_FechasIncendio",
    "hdd_GrupoCausa",
    "hdd_ListEspProt",
    "hdd_MiscelaneaCausa",
    "hdd_Motivacion",
    "hdd_Municipio",
    "hdd_Prov",
    "hdd_SubGrupoCausa",
    "hdd_TipoMedios",
    "hdd_soypm",
    "txtNumAnioDesde",
    "txtNumAnioHasta",
    "viewport",
)

TARGET_REGION_NAME = "MADRID"
USER_AGENT = "FIRSTLOOK-MAD-Phase-0D/0.1 (+bounded research acquisition)"

TIMING_FIELD_PATTERNS = (
    "deteccion",
    "detección",
    "notificacion",
    "notificación",
    "aviso",
    "despacho",
    "salida",
    "llegada",
    "intervencion",
    "intervención",
    "extincion",
    "extinción",
    "control",
)


def _build_opener() -> tuple[urllib.request.OpenerDirector, http.cookiejar.CookieJar]:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    return opener, jar


def _fetch(
    opener: Any,
    url: str,
    *,
    timeout: float,
    data: bytes | None = None,
    content_type_header: str | None = None,
) -> tuple[str, int | None, bytes, str | None]:
    """GET (or POST, if ``data`` is given) one URL. Never raises: an HTTP
    error's body is still returned, so an error page can be scanned like any
    other response, but is never persisted as evidence by the caller."""
    headers = {"Accept": "*/*", "User-Agent": USER_AGENT}
    if content_type_header:
        headers["Content-Type"] = content_type_header
    method = "POST" if data is not None else "GET"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read()
            outcome = "ACQUIRED" if body else "EMPTY_RESPONSE"
            return outcome, response.status, body, _response_content_type(response)
    except urllib.error.HTTPError as exc:
        return "HTTP_ERROR", exc.code, exc.read(), None
    except OSError as exc:
        return _classify_error(str(exc)), None, b"", None


def _extract_field(html: str, name: str) -> str:
    for pattern in (
        rf'name="{re.escape(name)}"[^>]*value="([^"]*)"',
        rf'value="([^"]*)"[^>]*name="{re.escape(name)}"',
    ):
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return ""


def _resolve_region_id(options_json: bytes, target_name: str) -> str | None:
    try:
        options = json.loads(options_json)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(options, list):
        return None
    for option in options:
        if isinstance(option, dict) and str(option.get("Text", "")).upper() == target_name:
            value = option.get("Value")
            return str(value) if value is not None else None
    return None


def _encode_multipart(fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = "----FirstlookMadPhase0DBoundary"
    parts = []
    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n")
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n')
        parts.append(f"{value}\r\n")
    parts.append(f"--{boundary}--\r\n")
    body = "".join(parts).encode("utf-8")
    return body, f"multipart/form-data; boundary={boundary}"


def _persist_step(
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
        "probe_id": probe_id,
        "outcome": "ACQUIRED",
        "http_status": status,
        "raw_path": provenance["local_raw_path"],
        "sha256": provenance["sha256"],
    }


def _record_step(
    *,
    raw_dir: Path,
    probe_id: str,
    url: str,
    outcome: str,
    status: int | None,
    body: bytes,
    content_type: str | None,
    config_consulted_at: str,
) -> dict[str, Any]:
    """Persist only a genuinely ACQUIRED step; every other outcome is
    recorded honestly without writing raw evidence bytes for it."""
    if outcome == "ACQUIRED":
        if status is None:
            raise RuntimeError("outcome was ACQUIRED but no HTTP status was captured")
        return _persist_step(
            raw_dir=raw_dir,
            probe_id=probe_id,
            url=url,
            body=body,
            status=status,
            content_type=content_type,
            config_consulted_at=config_consulted_at,
        )
    return {
        "probe_id": probe_id,
        "outcome": outcome,
        "http_status": status,
        "raw_path": None,
        "sha256": None,
    }


def _lookup_region(
    *,
    opener: Any,
    raw_dir: Path,
    probe_id: str,
    url: str,
    config_consulted_at: str,
    timeout_seconds: float,
) -> tuple[dict[str, Any], str | None]:
    outcome, status, body, content_type = _fetch(opener, url, timeout=timeout_seconds)
    step = _record_step(
        raw_dir=raw_dir,
        probe_id=probe_id,
        url=url,
        outcome=outcome,
        status=status,
        body=body,
        content_type=content_type,
        config_consulted_at=config_consulted_at,
    )
    if outcome != "ACQUIRED":
        return step, None
    region_id = _resolve_region_id(body, TARGET_REGION_NAME)
    if region_id is None:
        step["resolution_error"] = f"{TARGET_REGION_NAME} not found in response list"
        return step, None
    return step, region_id


def _scan_timing_fields(html_or_text: str) -> dict[str, int]:
    lowered = html_or_text.lower()
    return {pattern: lowered.count(pattern) for pattern in TIMING_FIELD_PATTERNS}


def _finalize(steps: dict[str, Any], *, timing_body: bytes) -> dict[str, Any]:
    timing_fields = _scan_timing_fields(timing_body.decode("utf-8", errors="replace"))
    return {
        "steps": steps,
        "a01_timing_fields_observed": any(timing_fields.values()),
        "timing_field_occurrences": timing_fields,
    }


def run_egif_bounded_flow(
    *,
    raw_dir: Path,
    config_consulted_at: str,
    year_window: tuple[str, str] = ("2024", "2024"),
    timeout_seconds: float = 15.0,
    opener: urllib.request.OpenerDirector | None = None,
) -> dict[str, Any]:
    """Run the bounded, single-session Madrid EGIF search flow described in
    the module docstring. Never raises: every step's failure is classified
    and returned so the caller has an honest record of what happened.

    ``opener`` may be injected (e.g. in tests) to control every response
    without touching the network; it must be a real
    ``urllib.request.OpenerDirector`` (or a stand-in with a compatible
    ``.open()``) since this flow depends on cookie persistence across all
    five requests within a single session.
    """
    steps: dict[str, Any] = {}
    if opener is None:
        opener, _jar = _build_opener()

    landing_outcome, status, body, content_type = _fetch(
        opener, BASE_URL + LANDING_PATH, timeout=timeout_seconds
    )
    steps["landing"] = _record_step(
        raw_dir=raw_dir,
        probe_id="egif_search_landing_session",
        url=BASE_URL + LANDING_PATH,
        outcome=landing_outcome,
        status=status,
        body=body,
        content_type=content_type,
        config_consulted_at=config_consulted_at,
    )
    if landing_outcome != "ACQUIRED":
        return _finalize(steps, timing_body=b"")
    html = body.decode("utf-8", errors="replace")
    form_fields = {name: _extract_field(html, name) for name in FORM_FIELD_NAMES}

    steps["ccaa_lookup"], ccaa_id = _lookup_region(
        opener=opener,
        raw_dir=raw_dir,
        probe_id="egif_ccaa_lookup",
        url=BASE_URL + CCAA_LOOKUP_PATH,
        config_consulted_at=config_consulted_at,
        timeout_seconds=timeout_seconds,
    )
    if ccaa_id is None:
        return _finalize(steps, timing_body=b"")

    steps["province_lookup"], province_id = _lookup_region(
        opener=opener,
        raw_dir=raw_dir,
        probe_id="egif_provincia_lookup_madrid",
        url=f"{BASE_URL}{PROVINCE_LOOKUP_PATH}?id={ccaa_id}",
        config_consulted_at=config_consulted_at,
        timeout_seconds=timeout_seconds,
    )
    if province_id is None:
        return _finalize(steps, timing_body=b"")

    form_fields["hdd_CCAA"] = ccaa_id
    form_fields["hdd_Prov"] = province_id
    form_fields["txtNumAnioDesde"], form_fields["txtNumAnioHasta"] = year_window
    post_body, post_content_type = _encode_multipart(form_fields)

    post_outcome, status, body, content_type = _fetch(
        opener,
        BASE_URL + LANDING_PATH,
        timeout=timeout_seconds,
        data=post_body,
        content_type_header=post_content_type,
    )
    steps["search_post"] = _record_step(
        raw_dir=raw_dir,
        probe_id="egif_search_post_madrid",
        url=BASE_URL + LANDING_PATH,
        outcome=post_outcome,
        status=status,
        body=body,
        content_type=content_type,
        config_consulted_at=config_consulted_at,
    )
    if post_outcome != "ACQUIRED":
        return _finalize(steps, timing_body=b"")
    steps["search_post"]["madrid_echoed_in_response"] = (
        "madrid" in body.decode("utf-8", errors="replace").lower()
    )

    results_url = f"{BASE_URL}{RESULTS_PATH}?sortOrder=NumeroParte"
    results_outcome, status, body, content_type = _fetch(
        opener, results_url, timeout=timeout_seconds
    )
    steps["results_page"] = _record_step(
        raw_dir=raw_dir,
        probe_id="egif_results_page_madrid",
        url=results_url,
        outcome=results_outcome,
        status=status,
        body=body,
        content_type=content_type,
        config_consulted_at=config_consulted_at,
    )
    return _finalize(steps, timing_body=body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/phase0d"))
    parser.add_argument("--config-consulted-at", default="2026-08-31T10:00:00+02:00")
    args = parser.parse_args()

    result = run_egif_bounded_flow(
        raw_dir=args.raw_dir,
        config_consulted_at=args.config_consulted_at,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

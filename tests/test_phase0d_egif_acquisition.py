from __future__ import annotations

import io
import json
import tempfile
import unittest
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from scripts.acquire_phase0d_egif import FORM_FIELD_NAMES, run_egif_bounded_flow


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, headers: dict[str, str] | None = None):
        self._body = io.BytesIO(body)
        self.status = status
        self.headers = headers or {"Content-Type": "text/html; charset=utf-8"}

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _landing_html() -> bytes:
    inputs = "\n".join(
        f'<input type="hidden" name="{name}" value="" />' for name in FORM_FIELD_NAMES
    )
    return (
        f'<form id="formBusqueda">\n{inputs}\n'
        '<input name="__RequestVerificationToken" type="hidden" value="TOKEN123" />\n'
        "</form>"
    ).encode()


CCAA_JSON = json.dumps(
    [{"Text": "ANDALUCIA", "Value": "4"}, {"Text": "MADRID", "Value": "16"}]
).encode("utf-8")
PROVINCE_JSON = json.dumps([{"Text": "MADRID", "Value": "28"}]).encode("utf-8")
CCAA_JSON_NO_MADRID = json.dumps([{"Text": "ANDALUCIA", "Value": "4"}]).encode("utf-8")


class ScriptedOpener:
    """Routes requests to canned responses/exceptions by URL substring."""

    def __init__(self, routes: list[tuple[Callable[[urllib.request.Request], bool], object]]):
        self._routes = routes
        self.requested_urls: list[str] = []

    def open(self, request: urllib.request.Request, timeout: float | None = None) -> FakeResponse:
        self.requested_urls.append(request.full_url)
        for predicate, outcome in self._routes:
            if predicate(request):
                if isinstance(outcome, BaseException):
                    raise outcome
                assert isinstance(outcome, FakeResponse)
                return outcome
        raise AssertionError(f"no scripted response for {request.full_url} ({request.method})")


def _url_contains(fragment: str) -> Callable[[urllib.request.Request], bool]:
    return lambda request: fragment in request.full_url


def _is_post() -> Callable[[urllib.request.Request], bool]:
    return lambda request: request.method == "POST" or request.data is not None


class RunEgifBoundedFlowTests(unittest.TestCase):
    def test_happy_path_observes_timing_fields_and_persists_every_step(self) -> None:
        results_html = b"<td>Tiempos</td><td>Deteccion registrada</td>"
        opener = ScriptedOpener(
            [
                (_is_post(), FakeResponse(b"<html>madrid criteria echoed back</html>")),
                (_url_contains("GetComunidadesAutonomasPublico"), FakeResponse(CCAA_JSON)),
                (_url_contains("ProvinciasByCCAAIdPublico"), FakeResponse(PROVINCE_JSON)),
                (_url_contains("PublicoPag"), FakeResponse(results_html)),
                (_url_contains("Search/Publico"), FakeResponse(_landing_html())),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_egif_bounded_flow(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,  # type: ignore[arg-type]
            )

        self.assertTrue(result["a01_timing_fields_observed"])
        self.assertGreater(result["timing_field_occurrences"]["deteccion"], 0)
        for step in ("landing", "ccaa_lookup", "province_lookup", "search_post", "results_page"):
            self.assertEqual(result["steps"][step]["outcome"], "ACQUIRED")
            self.assertIsNotNone(result["steps"][step]["raw_path"])
        self.assertTrue(result["steps"]["search_post"]["madrid_echoed_in_response"])

    def test_madrid_not_found_in_ccaa_list_stops_before_province_lookup(self) -> None:
        opener = ScriptedOpener(
            [
                (
                    _url_contains("GetComunidadesAutonomasPublico"),
                    FakeResponse(CCAA_JSON_NO_MADRID),
                ),
                (_url_contains("Search/Publico"), FakeResponse(_landing_html())),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_egif_bounded_flow(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,  # type: ignore[arg-type]
            )
        self.assertIn("resolution_error", result["steps"]["ccaa_lookup"])
        self.assertNotIn("province_lookup", result["steps"])
        self.assertFalse(result["a01_timing_fields_observed"])

    def test_results_page_http_error_still_scans_returned_body(self) -> None:
        error_body = "Ordena por Tiempos (detección)".encode()
        http_error = urllib.error.HTTPError(
            "https://servicio.mapa.gob.es/incendios/Search/PublicoPag",
            500,
            "Internal Server Error",
            {},
            io.BytesIO(error_body),
        )
        opener = ScriptedOpener(
            [
                (_is_post(), FakeResponse(b"<html>no region mention</html>")),
                (_url_contains("GetComunidadesAutonomasPublico"), FakeResponse(CCAA_JSON)),
                (_url_contains("ProvinciasByCCAAIdPublico"), FakeResponse(PROVINCE_JSON)),
                (_url_contains("PublicoPag"), http_error),
                (_url_contains("Search/Publico"), FakeResponse(_landing_html())),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_egif_bounded_flow(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,  # type: ignore[arg-type]
            )
        self.assertEqual(result["steps"]["results_page"]["outcome"], "HTTP_ERROR")
        self.assertEqual(result["steps"]["results_page"]["http_status"], 500)
        self.assertTrue(result["a01_timing_fields_observed"])
        self.assertFalse(result["steps"]["search_post"]["madrid_echoed_in_response"])

    def test_no_timing_fields_observed_keeps_baseline_false(self) -> None:
        results_html = b"<td>NumeroParte</td><td>Superficie</td>"
        opener = ScriptedOpener(
            [
                (_is_post(), FakeResponse(b"<html></html>")),
                (_url_contains("GetComunidadesAutonomasPublico"), FakeResponse(CCAA_JSON)),
                (_url_contains("ProvinciasByCCAAIdPublico"), FakeResponse(PROVINCE_JSON)),
                (_url_contains("PublicoPag"), FakeResponse(results_html)),
                (_url_contains("Search/Publico"), FakeResponse(_landing_html())),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_egif_bounded_flow(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,  # type: ignore[arg-type]
            )
        self.assertFalse(result["a01_timing_fields_observed"])


if __name__ == "__main__":
    unittest.main()

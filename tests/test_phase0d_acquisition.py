from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock

from scripts.acquire_phase0d_sources import (
    _classify_error,
    _raw_target_path,
    attempt_probe,
    persist_raw_response,
    run_acquisition,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, headers: dict[str, str] | None = None):
        self._body = io.BytesIO(body)
        self.status = status
        self.headers = headers or {}

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class ClassificationTests(unittest.TestCase):
    def test_tunnel_403_is_classified_as_network_egress_blocked(self) -> None:
        message = "URLError: <urlopen error Tunnel connection failed: 403 Forbidden>"
        self.assertEqual(_classify_error(message), "NETWORK_EGRESS_BLOCKED")

    def test_generic_http_error_is_classified_as_http_error(self) -> None:
        message = "HTTPError: HTTP Error 404: Not Found"
        self.assertEqual(_classify_error(message), "HTTP_ERROR")

    def test_unknown_failure_is_other_error(self) -> None:
        self.assertEqual(_classify_error("TimeoutError: timed out"), "OTHER_ERROR")


class AttemptProbeTests(unittest.TestCase):
    def test_successful_probe_is_marked_real_if_used(self) -> None:
        opener = Mock(return_value=FakeResponse(b"{}"))
        spec = {"probe_id": "x", "url": "https://example.invalid", "max_bytes": 100}
        result = attempt_probe(spec, opener=opener)
        self.assertEqual(result["outcome"], "ACQUIRED")
        self.assertEqual(result["nature_if_used"], "REAL")
        self.assertIsNotNone(result["attempted_at"])
        self.assertEqual(result["sha256"], hashlib.sha256(b"{}").hexdigest())

    def test_http_200_empty_body_is_not_acquired(self) -> None:
        opener = Mock(return_value=FakeResponse(b"", status=200))
        spec = {"probe_id": "aemet_madrid_station_inventory", "url": "https://example.invalid"}
        result = attempt_probe(spec, opener=opener)
        self.assertEqual(result["outcome"], "EMPTY_RESPONSE")
        self.assertEqual(result["http_status"], 200)
        self.assertEqual(result["bytes_read"], 0)
        self.assertIsNone(result["nature_if_used"])
        self.assertIsNone(result["sha256"])
        self.assertIsNone(result["raw_path"])
        self.assertNotEqual(result["outcome"], "ACQUIRED")

    def test_blocked_probe_never_claims_real_nature(self) -> None:
        opener = Mock(side_effect=urllib.error.URLError("Tunnel connection failed: 403 Forbidden"))
        spec = {"probe_id": "x", "url": "https://example.invalid"}
        result = attempt_probe(spec, opener=opener)
        self.assertEqual(result["outcome"], "NETWORK_EGRESS_BLOCKED")
        self.assertIsNone(result["nature_if_used"])
        self.assertIsNone(result["http_status"])

    def test_http_error_remains_an_error_not_acquired(self) -> None:
        opener = Mock(
            side_effect=urllib.error.HTTPError(
                "https://example.invalid", 502, "Bad Gateway", {}, None
            )
        )
        spec = {"probe_id": "effis_current_fires_madrid_bbox", "url": "https://example.invalid"}
        result = attempt_probe(spec, opener=opener)
        self.assertEqual(result["outcome"], "HTTP_ERROR")
        self.assertIsNone(result["nature_if_used"])
        self.assertIsNone(result["raw_path"])

    def test_tls_certificate_failure_is_other_error_not_real(self) -> None:
        opener = Mock(
            side_effect=urllib.error.URLError(
                "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: "
                "certificate has expired"
            )
        )
        spec = {"probe_id": "osm_overpass_madrid_fire_stations", "url": "https://example.invalid"}
        result = attempt_probe(spec, opener=opener)
        self.assertEqual(result["outcome"], "OTHER_ERROR")
        self.assertIsNone(result["nature_if_used"])
        self.assertIsNone(result["raw_path"])

    def test_attempt_probe_never_raises_on_os_error(self) -> None:
        opener = Mock(side_effect=OSError("unexpected"))
        spec = {"probe_id": "x", "url": "https://example.invalid"}
        result = attempt_probe(spec, opener=opener)
        self.assertIn(
            result["outcome"],
            {"NETWORK_EGRESS_BLOCKED", "HTTP_ERROR", "OTHER_ERROR"},
        )

    def test_credential_required_when_env_var_missing(self) -> None:
        opener = Mock()
        spec = {
            "probe_id": "aemet_madrid_station_inventory",
            "url": "https://opendata.aemet.es/x",
            "credential_env_var": "AEMET_API_KEY",
        }
        result = attempt_probe(spec, opener=opener, env={})
        self.assertEqual(result["outcome"], "CREDENTIAL_REQUIRED")
        self.assertIsNone(result["nature_if_used"])
        self.assertIsNone(result["http_status"])
        opener.assert_not_called()

    def test_never_fabricates_aemet_data_absent_credential(self) -> None:
        opener = Mock(return_value=FakeResponse(b'{"fabricated": true}'))
        spec = {
            "probe_id": "aemet_madrid_station_inventory",
            "url": "https://opendata.aemet.es/x",
            "credential_env_var": "AEMET_API_KEY",
        }
        result = attempt_probe(spec, opener=opener, env={})
        self.assertEqual(result["outcome"], "CREDENTIAL_REQUIRED")
        opener.assert_not_called()

    def test_credential_used_as_header_and_never_leaked_into_result(self) -> None:
        captured_request: dict[str, object] = {}

        def opener(request: object, timeout: float) -> FakeResponse:
            captured_request["request"] = request
            return FakeResponse(b'{"ok": true}')

        spec = {
            "probe_id": "aemet_madrid_station_inventory",
            "url": "https://opendata.aemet.es/x",
            "credential_env_var": "AEMET_API_KEY",
            "credential_header": "api_key",
        }
        result = attempt_probe(spec, opener=opener, env={"AEMET_API_KEY": "TOP-SECRET-KEY"})
        self.assertEqual(result["outcome"], "ACQUIRED")

        request = captured_request["request"]
        # Request.get_header() does not normalize case itself (only
        # add_header() does, via str.capitalize() at storage time).
        self.assertEqual(request.get_header("Api_key"), "TOP-SECRET-KEY")  # type: ignore[attr-defined]

        serialized = json.dumps(result)
        self.assertNotIn("TOP-SECRET-KEY", serialized)
        self.assertNotIn("api_key", result["url"])


class RawPersistenceTests(unittest.TestCase):
    def test_persisted_bytes_match_received_bytes_and_sha256_is_correct(self) -> None:
        body = b'{"hello": "madrid"}'
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            opener = Mock(
                return_value=FakeResponse(body, headers={"Content-Type": "application/json"})
            )
            spec = {"probe_id": "ign_mdt05_madrid_capabilities", "url": "https://example.invalid"}
            result = attempt_probe(
                spec,
                opener=opener,
                raw_dir=raw_dir,
                config_consulted_at="2026-08-31T10:00:00+02:00",
            )
            self.assertEqual(result["outcome"], "ACQUIRED")
            raw_path = Path(result["raw_path"])
            self.assertTrue(raw_path.exists())
            self.assertEqual(raw_path.read_bytes(), body)
            self.assertEqual(result["sha256"], hashlib.sha256(body).hexdigest())

    def test_provenance_metadata_is_emitted(self) -> None:
        body = b"raw-evidence-bytes"
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            spec = {
                "probe_id": "madrid_city_open_data_fire_stations",
                "url": "https://example.invalid/x",
            }
            provenance = persist_raw_response(
                raw_dir,
                spec,
                body,
                attempted_at="2026-09-02T14:12:01.430614+00:00",
                http_status=200,
                content_type="application/json",
                truncated=False,
                config_consulted_at="2026-08-31T10:00:00+02:00",
            )
            for field in (
                "probe_id",
                "source_url",
                "acquired_at_utc",
                "http_status",
                "content_type",
                "byte_count",
                "sha256",
                "local_raw_path",
                "truncated",
                "evidence_nature",
                "config_consulted_at",
            ):
                self.assertIn(field, provenance)
            self.assertEqual(provenance["evidence_nature"], "REAL")
            self.assertEqual(provenance["byte_count"], len(body))
            self.assertEqual(provenance["sha256"], hashlib.sha256(body).hexdigest())
            self.assertEqual(provenance["source_url"], spec["url"])

            raw_path = Path(provenance["local_raw_path"])
            provenance_path = raw_path.with_name(raw_path.name + ".provenance.json")
            self.assertTrue(provenance_path.exists())
            on_disk = json.loads(provenance_path.read_text(encoding="utf-8"))
            self.assertEqual(on_disk, provenance)

    def test_raw_file_not_overwritten_silently_on_conflicting_content(self) -> None:
        spec = {"probe_id": "egif_public_search_madrid", "url": "https://example.invalid"}
        attempted_at = "2026-09-02T14:12:02.217958+00:00"
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            first = persist_raw_response(
                raw_dir,
                spec,
                b"first-run-bytes",
                attempted_at=attempted_at,
                http_status=200,
                content_type="text/html",
                truncated=False,
                config_consulted_at="2026-08-31T10:00:00+02:00",
            )
            target = _raw_target_path(raw_dir, spec["probe_id"], attempted_at)
            self.assertEqual(target.read_bytes(), b"first-run-bytes")

            second = persist_raw_response(
                raw_dir,
                spec,
                b"second-run-different-bytes",
                attempted_at=attempted_at,
                http_status=200,
                content_type="text/html",
                truncated=False,
                config_consulted_at="2026-08-31T10:00:00+02:00",
            )

            # The original target is untouched.
            self.assertEqual(target.read_bytes(), b"first-run-bytes")
            # The second attempt landed on a different, deterministic path.
            self.assertNotEqual(first["local_raw_path"], second["local_raw_path"])
            fallback_path = Path(second["local_raw_path"])
            self.assertEqual(fallback_path.read_bytes(), b"second-run-different-bytes")

    def test_idempotent_rerun_with_identical_bytes_does_not_rewrite(self) -> None:
        spec = {"probe_id": "enaire_uas_zones_madrid_bbox", "url": "https://example.invalid"}
        attempted_at = "2026-09-02T14:11:59.219853+00:00"
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            first = persist_raw_response(
                raw_dir,
                spec,
                b"identical-bytes",
                attempted_at=attempted_at,
                http_status=200,
                content_type="application/json",
                truncated=False,
                config_consulted_at="2026-08-31T10:00:00+02:00",
            )
            second = persist_raw_response(
                raw_dir,
                spec,
                b"identical-bytes",
                attempted_at=attempted_at,
                http_status=200,
                content_type="application/json",
                truncated=False,
                config_consulted_at="2026-08-31T10:00:00+02:00",
            )
            self.assertEqual(first, second)


class RunAcquisitionTests(unittest.TestCase):
    def test_summary_counts_match_results(self) -> None:
        config = {
            "consulted_at": "2026-08-31T10:00:00+02:00",
            "purpose": "test",
            "probes": [
                {"probe_id": "ok", "url": "https://example.invalid"},
                {"probe_id": "blocked", "url": "https://example.invalid"},
            ],
        }

        # Classification behaviour is covered directly by ClassificationTests
        # and AttemptProbeTests above; here we only assert the aggregate shape
        # of run_acquisition against real (offline-failing) network calls.
        log = run_acquisition(config, sleep_between_s=0.0)
        self.assertEqual(log["summary"]["attempted"], 2)
        self.assertEqual(
            log["summary"]["acquired"]
            + log["summary"]["empty_response"]
            + log["summary"]["credential_required"]
            + log["summary"]["network_egress_blocked"]
            + log["summary"]["http_error"]
            + log["summary"]["other_failures"],
            2,
        )
        self.assertEqual(log["phase"], "0D")

    def test_no_result_silently_treated_as_success(self) -> None:
        config = {
            "consulted_at": "2026-08-31T10:00:00+02:00",
            "purpose": "test",
            "probes": [{"probe_id": "unreachable", "url": "https://example.invalid"}],
        }
        log = run_acquisition(config, sleep_between_s=0.0)
        result = log["results"][0]
        if result["outcome"] != "ACQUIRED":
            self.assertIsNone(result["nature_if_used"])


class AcquisitionLogFixtureTests(unittest.TestCase):
    """Validate the committed Phase 0D acquisition logs, if present.

    ``phase0d_acquisition_log_local_2026-09-02.json`` is preserved evidence of
    the *pre-hardening* classification defect (docs/PHASE_0D_PROTOCOL.md §7.1)
    and is intentionally excluded here: it is expected to contain the very
    HTTP-200/0-byte-as-ACQUIRED defect this hardening fixes, and must not be
    rewritten or judged against the corrected invariant.
    """

    def test_committed_log_has_no_fabricated_real_data(self) -> None:
        log_path = ROOT / "outputs" / "reports" / "phase0d_acquisition_log.json"
        if not log_path.exists():
            self.skipTest("acquisition log not yet generated")
        log = json.loads(log_path.read_text(encoding="utf-8"))
        for result in log["results"]:
            if result["outcome"] != "ACQUIRED":
                self.assertIsNone(
                    result["nature_if_used"],
                    "a non-ACQUIRED probe must never be labelled REAL",
                )


if __name__ == "__main__":
    unittest.main()

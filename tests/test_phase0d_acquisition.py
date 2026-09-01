from __future__ import annotations

import io
import json
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock

from scripts.acquire_phase0d_sources import _classify_error, attempt_probe, run_acquisition

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = io.BytesIO(body)
        self.status = status

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

    def test_blocked_probe_never_claims_real_nature(self) -> None:
        opener = Mock(side_effect=urllib.error.URLError("Tunnel connection failed: 403 Forbidden"))
        spec = {"probe_id": "x", "url": "https://example.invalid"}
        result = attempt_probe(spec, opener=opener)
        self.assertEqual(result["outcome"], "NETWORK_EGRESS_BLOCKED")
        self.assertIsNone(result["nature_if_used"])
        self.assertIsNone(result["http_status"])

    def test_attempt_probe_never_raises_on_os_error(self) -> None:
        opener = Mock(side_effect=OSError("unexpected"))
        spec = {"probe_id": "x", "url": "https://example.invalid"}
        result = attempt_probe(spec, opener=opener)
        self.assertIn(result["outcome"], {"NETWORK_EGRESS_BLOCKED", "HTTP_ERROR", "OTHER_ERROR"})


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
            + log["summary"]["network_egress_blocked"]
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
    """Validate the committed Phase 0D acquisition log, if present."""

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

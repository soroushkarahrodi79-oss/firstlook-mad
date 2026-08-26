from __future__ import annotations

import copy
import io
import json
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock

from scripts.probe_sources import _summarise_body, fetch_probe, validate_manifest

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/json", status: int = 200):
        self._body = io.BytesIO(body)
        self.headers = {"Content-Type": content_type}
        self.status = status

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = (ROOT / "data" / "datasets_manifest.json").read_text(encoding="utf-8")
        cls.manifest = json.loads(text)

    def test_manifest_is_valid(self) -> None:
        self.assertEqual(validate_manifest(self.manifest), [])

    def test_duplicate_dataset_ids_are_rejected(self) -> None:
        document = copy.deepcopy(self.manifest)
        document["datasets"].append(copy.deepcopy(document["datasets"][0]))
        errors = validate_manifest(document)
        self.assertTrue(any("duplicate dataset_id" in error for error in errors))

    def test_invalid_feasibility_status_is_rejected(self) -> None:
        document = copy.deepcopy(self.manifest)
        document["datasets"][0]["feasibility_status"] = "HOPEFUL"
        errors = validate_manifest(document)
        self.assertTrue(any("feasibility_status is invalid" in error for error in errors))

    def test_missing_source_identifier_is_rejected(self) -> None:
        document = copy.deepcopy(self.manifest)
        document["datasets"][0]["source_url_or_id"] = ""
        self.assertTrue(any("source_url_or_id" in error for error in validate_manifest(document)))


class ProbeTests(unittest.TestCase):
    def test_json_schema_summary(self) -> None:
        document = {
            "layers": [{"id": 2, "name": "ZGUAS_Aero"}],
            "fields": [{"name": "id"}],
        }
        body = json.dumps(document).encode()
        summary = _summarise_body(body, "application/json")
        self.assertEqual(summary["layers"], [{"id": 2, "name": "ZGUAS_Aero"}])
        self.assertEqual(summary["fields"], ["id"])

    def test_probe_reads_bounded_response(self) -> None:
        opener = Mock(return_value=FakeResponse(b'{"layers": []}'))
        spec = {"probe_id": "x", "url": "https://example.invalid", "max_bytes": 100}
        result = fetch_probe(spec, opener=opener)
        self.assertTrue(result["ok"])
        self.assertFalse(result["truncated"])
        self.assertEqual(result["body_summary"]["layers"], [])

    def test_network_failure_is_graceful(self) -> None:
        opener = Mock(side_effect=urllib.error.URLError("offline"))
        spec = {"probe_id": "x", "url": "https://example.invalid"}
        result = fetch_probe(spec, retries=0, opener=opener)
        self.assertFalse(result["ok"])
        self.assertIn("URLError", result["error"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from scripts.acquire_phase0d_aemet import run_aemet_secondhop


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, headers: dict[str, str] | None = None):
        self._body = io.BytesIO(body)
        self.status = status
        self.headers = headers or {"Content-Type": "application/json"}

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


WRAPPER_BODY = json.dumps(
    {
        "descripcion": "exito",
        "estado": 200,
        "datos": "https://opendata.aemet.es/opendata/sh/deadbeef",
        "metadatos": "https://opendata.aemet.es/opendata/sh/cafef00d",
    }
).encode("utf-8")

EXPIRED_HANDLE_BODY = json.dumps({"descripcion": "datos expirados", "estado": 404}).encode("utf-8")

STATION_INVENTORY_BODY = json.dumps(
    [
        {
            "indicativo": "3195",
            "nombre": "MADRID, RETIRO",
            "provincia": "MADRID",
            "latitud": "402554N",
            "longitud": "003940W",
            "altitud": "667",
        },
        {
            "indicativo": "3129",
            "nombre": "MADRID AEROPUERTO",
            "provincia": "MADRID",
            "latitud": "402743N",
            "longitud": "003334W",
            "altitud": "609",
        },
        {
            "indicativo": "9434",
            "nombre": "ZARAGOZA AEROPUERTO",
            "provincia": "ZARAGOZA",
            "latitud": "413935N",
            "longitud": "010021W",
            "altitud": "247",
        },
    ]
).encode("utf-8")


class RunAemetSecondhopTests(unittest.TestCase):
    def test_credential_required_short_circuits_hop2(self) -> None:
        secondhop_opener = Mock()
        with tempfile.TemporaryDirectory() as tmp:
            result = run_aemet_secondhop(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                env={},
                secondhop_opener=secondhop_opener,
            )
        self.assertEqual(result["hop1"]["outcome"], "CREDENTIAL_REQUIRED")
        self.assertEqual(result["hop2"]["outcome"], "NOT_ATTEMPTED")
        secondhop_opener.assert_not_called()

    def test_missing_datos_field_stops_before_hop2(self) -> None:
        wrapper_opener = Mock(return_value=FakeResponse(b'{"descripcion": "exito", "estado": 200}'))
        secondhop_opener = Mock()
        with tempfile.TemporaryDirectory() as tmp:
            result = run_aemet_secondhop(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                env={"AEMET_API_KEY": "TOP-SECRET-KEY"},
                wrapper_opener=wrapper_opener,
                secondhop_opener=secondhop_opener,
            )
        self.assertEqual(result["hop1"]["outcome"], "ACQUIRED")
        self.assertEqual(result["hop2"]["outcome"], "MISSING_DATOS_FIELD")
        secondhop_opener.assert_not_called()

    def test_disallowed_host_is_refused_not_followed(self) -> None:
        malicious_wrapper = json.dumps(
            {"descripcion": "exito", "estado": 200, "datos": "https://evil.example/steal"}
        ).encode("utf-8")
        wrapper_opener = Mock(return_value=FakeResponse(malicious_wrapper))
        secondhop_opener = Mock()
        with tempfile.TemporaryDirectory() as tmp:
            result = run_aemet_secondhop(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                env={"AEMET_API_KEY": "TOP-SECRET-KEY"},
                wrapper_opener=wrapper_opener,
                secondhop_opener=secondhop_opener,
            )
        self.assertEqual(result["hop2"]["outcome"], "DISALLOWED_HOST")
        secondhop_opener.assert_not_called()

    def test_expired_handle_is_acquired_but_not_usable(self) -> None:
        wrapper_opener = Mock(return_value=FakeResponse(WRAPPER_BODY))
        secondhop_opener = Mock(return_value=FakeResponse(EXPIRED_HANDLE_BODY))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_aemet_secondhop(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                env={"AEMET_API_KEY": "TOP-SECRET-KEY"},
                wrapper_opener=wrapper_opener,
                secondhop_opener=secondhop_opener,
            )
        self.assertEqual(result["hop2"]["outcome"], "ACQUIRED")
        self.assertEqual(result["hop2"]["classification"], "NOT_USABLE_FOR_TARGET_TEST")
        self.assertNotIn("station_summary", result["hop2"])

    def test_successful_station_inventory_is_real_source_data(self) -> None:
        wrapper_opener = Mock(return_value=FakeResponse(WRAPPER_BODY))
        secondhop_opener = Mock(return_value=FakeResponse(STATION_INVENTORY_BODY))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_aemet_secondhop(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                env={"AEMET_API_KEY": "TOP-SECRET-KEY"},
                wrapper_opener=wrapper_opener,
                secondhop_opener=secondhop_opener,
            )
        hop2 = result["hop2"]
        self.assertEqual(hop2["outcome"], "ACQUIRED")
        self.assertEqual(hop2["classification"], "REAL_SOURCE_DATA")
        self.assertEqual(hop2["station_summary"]["record_count"], 3)
        self.assertEqual(hop2["station_summary"]["madrid_station_count"], 2)
        self.assertIn("3195", hop2["station_summary"]["madrid_station_identifiers"])
        self.assertTrue(hop2["station_summary"]["coordinate_fields_present"])

    def test_parent_child_provenance_linkage(self) -> None:
        wrapper_opener = Mock(return_value=FakeResponse(WRAPPER_BODY))
        secondhop_opener = Mock(return_value=FakeResponse(STATION_INVENTORY_BODY))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_aemet_secondhop(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                env={"AEMET_API_KEY": "TOP-SECRET-KEY"},
                wrapper_opener=wrapper_opener,
                secondhop_opener=secondhop_opener,
            )
            hop1_sha256 = result["hop1"]["sha256"]
            hop2_raw_path = Path(result["hop2"]["raw_path"])
            provenance = json.loads(
                (hop2_raw_path.parent / (hop2_raw_path.name + ".provenance.json")).read_text(
                    encoding="utf-8"
                )
            )
        self.assertEqual(provenance["parent_probe_id"], "aemet_madrid_station_inventory")
        self.assertEqual(provenance["parent_raw_sha256"], hop1_sha256)
        self.assertIsNotNone(provenance["parent_acquired_at_utc"])
        self.assertEqual(
            provenance["resolved_url"], "https://opendata.aemet.es/opendata/sh/deadbeef"
        )
        self.assertEqual(provenance["hop"], 2)

    def test_secrets_never_appear_in_result_or_provenance(self) -> None:
        wrapper_opener = Mock(return_value=FakeResponse(WRAPPER_BODY))
        secondhop_opener = Mock(return_value=FakeResponse(STATION_INVENTORY_BODY))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_aemet_secondhop(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                env={"AEMET_API_KEY": "TOP-SECRET-KEY"},
                wrapper_opener=wrapper_opener,
                secondhop_opener=secondhop_opener,
            )
            serialized_result = json.dumps(result)
            self.assertNotIn("TOP-SECRET-KEY", serialized_result)

            for provenance_file in Path(tmp).rglob("*.provenance.json"):
                self.assertNotIn("TOP-SECRET-KEY", provenance_file.read_text(encoding="utf-8"))
            for raw_file in Path(tmp).rglob("*.raw"):
                self.assertNotIn(b"TOP-SECRET-KEY", raw_file.read_bytes())

    def test_one_hop_maximum_secondhop_opener_called_once(self) -> None:
        wrapper_opener = Mock(return_value=FakeResponse(WRAPPER_BODY))
        secondhop_opener = Mock(return_value=FakeResponse(STATION_INVENTORY_BODY))
        with tempfile.TemporaryDirectory() as tmp:
            run_aemet_secondhop(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                env={"AEMET_API_KEY": "TOP-SECRET-KEY"},
                wrapper_opener=wrapper_opener,
                secondhop_opener=secondhop_opener,
            )
        self.assertEqual(wrapper_opener.call_count, 1)
        self.assertEqual(secondhop_opener.call_count, 1)


if __name__ == "__main__":
    unittest.main()

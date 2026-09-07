from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.provenance_ledger import (
    ARTIFACT_CLASSIFICATIONS,
    LedgerSecretGuardError,
    build_ledger_entry,
    build_ledger_from_raw_dir,
    write_ledger_entry,
)

BASE_SIDECAR = {
    "probe_id": "madrid_city_open_data_fire_stations",
    "source_url": "https://datos.madrid.es/egob/catalogo/211642-0-bomberos-parques.json",
    "acquired_at_utc": "2026-09-06T17:38:00.288687+00:00",
    "http_status": 200,
    "content_type": "application/json",
    "byte_count": 16273,
    "sha256": "5c3957873878d30c93556c75544b6d7740c648b84b0424682dfac655842f8eb6",
    "local_raw_path": "data/raw/phase0d/madrid_city_open_data_fire_stations/20260906.raw",
    "truncated": False,
    "evidence_nature": "REAL",
    "config_consulted_at": "2026-08-31T10:00:00+02:00",
}


class BuildLedgerEntryTests(unittest.TestCase):
    def test_only_allowlisted_fields_are_copied(self) -> None:
        sidecar = {**BASE_SIDECAR, "config_consulted_at": "2026-08-31T10:00:00+02:00"}
        entry = build_ledger_entry(sidecar, assumption="A-02", classification="REAL_SOURCE_DATA")
        self.assertNotIn("config_consulted_at", entry)
        self.assertEqual(entry["assumption"], "A-02")
        self.assertEqual(entry["evidence_classification"], "REAL_SOURCE_DATA")
        self.assertEqual(entry["sha256"], BASE_SIDECAR["sha256"])
        self.assertEqual(entry["schema_version"], "1.0")

    def test_parent_child_fields_pass_through_when_present(self) -> None:
        sidecar = {
            **BASE_SIDECAR,
            "probe_id": "aemet_madrid_station_inventory_datos",
            "parent_probe_id": "aemet_madrid_station_inventory",
            "parent_raw_sha256": "deadbeef",
            "parent_acquired_at_utc": "2026-09-06T17:37:58.062383+00:00",
            "resolved_url": "https://opendata.aemet.es/opendata/sh/3f1a111a",
            "hop": 2,
        }
        entry = build_ledger_entry(
            sidecar, assumption="A-04", classification="NOT_USABLE_FOR_TARGET_TEST"
        )
        self.assertEqual(entry["parent_probe_id"], "aemet_madrid_station_inventory")
        self.assertEqual(entry["parent_raw_sha256"], "deadbeef")
        self.assertEqual(entry["hop"], 2)

    def test_rejects_entry_containing_a_forbidden_marker(self) -> None:
        sidecar = {**BASE_SIDECAR, "sha256": "leaked-api_key-value"}
        with self.assertRaises(LedgerSecretGuardError):
            build_ledger_entry(sidecar, assumption="A-02", classification="REAL_SOURCE_DATA")

    def test_never_contains_raw_body_field(self) -> None:
        sidecar = {**BASE_SIDECAR, "raw_body": "this must never be copied"}
        entry = build_ledger_entry(sidecar, assumption="A-02", classification="REAL_SOURCE_DATA")
        self.assertNotIn("raw_body", entry)


class WriteLedgerEntryTests(unittest.TestCase):
    def test_writes_to_deterministic_path_mirroring_probe_and_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_dir = Path(tmp) / "ledger"
            out_path = write_ledger_entry(
                ledger_dir, BASE_SIDECAR, assumption="A-02", classification="REAL_SOURCE_DATA"
            )
            self.assertTrue(out_path.exists())
            self.assertEqual(
                out_path,
                ledger_dir / "madrid_city_open_data_fire_stations" / "20260906.provenance.json",
            )
            on_disk = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(on_disk["probe_id"], "madrid_city_open_data_fire_stations")


class BuildLedgerFromRawDirTests(unittest.TestCase):
    def test_builds_entries_for_classified_probes_and_skips_unclassified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            ledger_dir = Path(tmp) / "ledger"

            classified_dir = raw_dir / "madrid_city_open_data_fire_stations"
            classified_dir.mkdir(parents=True)
            (classified_dir / "20260906.raw.provenance.json").write_text(
                json.dumps(BASE_SIDECAR), encoding="utf-8"
            )

            unclassified_sidecar = {**BASE_SIDECAR, "probe_id": "some_new_unclassified_probe"}
            unclassified_dir = raw_dir / "some_new_unclassified_probe"
            unclassified_dir.mkdir(parents=True)
            (unclassified_dir / "20260906.raw.provenance.json").write_text(
                json.dumps(unclassified_sidecar), encoding="utf-8"
            )

            written = build_ledger_from_raw_dir(raw_dir, ledger_dir)

        self.assertEqual(len(written), 1)
        self.assertIn("madrid_city_open_data_fire_stations", str(written[0]))

    def test_sha256_override_beats_probe_default_for_shared_probe_id(self) -> None:
        """Two artifacts of one probe_id get different, content-pinned
        classifications: the verified AEMET real inventory (SHA override ->
        REAL_SOURCE_DATA) vs. the earlier expired body (probe default)."""
        verified_sha = next(iter(ARTIFACT_CLASSIFICATIONS))
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            ledger_dir = Path(tmp) / "ledger"
            probe_dir = raw_dir / "aemet_madrid_station_inventory_datos"
            probe_dir.mkdir(parents=True)

            expired = {
                **BASE_SIDECAR,
                "probe_id": "aemet_madrid_station_inventory_datos",
                "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                "local_raw_path": (
                    "data/raw/phase0d/aemet_madrid_station_inventory_datos/20260906.raw"
                ),
            }
            verified = {
                **BASE_SIDECAR,
                "probe_id": "aemet_madrid_station_inventory_datos",
                "sha256": verified_sha,
                "local_raw_path": (
                    "data/raw/phase0d/aemet_madrid_station_inventory_datos/20260906T191152Z.raw"
                ),
            }
            (probe_dir / "20260906.raw.provenance.json").write_text(
                json.dumps(expired), encoding="utf-8"
            )
            (probe_dir / "20260906T191152Z.raw.provenance.json").write_text(
                json.dumps(verified), encoding="utf-8"
            )

            build_ledger_from_raw_dir(raw_dir, ledger_dir)

            expired_entry = json.loads(
                (
                    ledger_dir / "aemet_madrid_station_inventory_datos" / "20260906.provenance.json"
                ).read_text(encoding="utf-8")
            )
            verified_entry = json.loads(
                (
                    ledger_dir
                    / "aemet_madrid_station_inventory_datos"
                    / "20260906T191152Z.provenance.json"
                ).read_text(encoding="utf-8")
            )
        self.assertEqual(expired_entry["evidence_classification"], "NOT_USABLE_FOR_TARGET_TEST")
        self.assertEqual(verified_entry["evidence_classification"], "REAL_SOURCE_DATA")

    def test_no_raw_bytes_or_secret_markers_anywhere_in_ledger_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            ledger_dir = Path(tmp) / "ledger"
            probe_dir = raw_dir / "madrid_city_open_data_fire_stations"
            probe_dir.mkdir(parents=True)
            (probe_dir / "20260906.raw").write_bytes(b'{"secret_lat_lon_payload": true}')
            (probe_dir / "20260906.raw.provenance.json").write_text(
                json.dumps(BASE_SIDECAR), encoding="utf-8"
            )

            build_ledger_from_raw_dir(raw_dir, ledger_dir)

            for ledger_file in ledger_dir.rglob("*.json"):
                content = ledger_file.read_text(encoding="utf-8")
                self.assertNotIn("secret_lat_lon_payload", content)
                for marker in ("api_key", "cookie", "token", "authorization", "password"):
                    self.assertNotIn(marker, content.lower())


if __name__ == "__main__":
    unittest.main()

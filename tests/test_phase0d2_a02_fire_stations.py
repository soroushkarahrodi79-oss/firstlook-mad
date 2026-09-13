from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from pyproj import Transformer

from firstlook_mad.normalization.a02_fire_stations import (
    FIRE_STATION_PROBE_ID,
    MADRID_CITY_FIRE_STATIONS,
    A02Normalization,
    DeclaredCoverage,
    RejectionReason,
    SourceDescriptor,
    a02_eligibility,
    normalize_fire_stations,
)
from firstlook_mad.normalization.crs import make_analytical_transformer, project_lon_lat
from firstlook_mad.normalization.evidence import LoadedArtifact, load_artifact
from firstlook_mad.normalization.models import (
    Completeness,
    Eligibility,
    Integrity,
    MalformedEvidenceError,
    StructuralValidity,
)
from firstlook_mad.normalization.serialization import canonical_json_bytes
from phase0d2_fixtures import (
    ACQUIRED_AT,
    FIRE_URL,
    PAYLOAD_SENTINEL,
    default_fire_station_records,
    fire_station_payload,
    fire_station_record,
    write_artifact,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
# 0C.1 reference synthetic extent in EPSG:25830 (configs/phase0c_synthetic.json).
MIN_EASTING_M, MAX_EASTING_M = 390_000.0, 500_000.0
MIN_NORTHING_M, MAX_NORTHING_M = 4_410_000.0, 4_520_000.0
MUNICIPAL = MADRID_CITY_FIRE_STATIONS
REGIONAL = SourceDescriptor(
    manifest_dataset_id="fixture_regional",
    declared_coverage=DeclaredCoverage.COMUNIDAD_DE_MADRID,
    license="CC-BY-4.0",
    attribution="fixture",
)


class FireStationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.transformer = make_analytical_transformer()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def load(self, payload: bytes, **kwargs: Any) -> LoadedArtifact:
        ledger_dir, raw_dir = write_artifact(
            self.root,
            probe_id=FIRE_STATION_PROBE_ID,
            payload=payload,
            assumption="A-02",
            classification="REAL_SOURCE_DATA",
            source_url=FIRE_URL,
            content_type="application/json",
            **kwargs,
        )
        return load_artifact(
            ledger_dir / FIRE_STATION_PROBE_ID / "20260906.provenance.json", raw_dir
        )

    def normalize(
        self, records: list[Any], descriptor: SourceDescriptor = MUNICIPAL
    ) -> A02Normalization:
        loaded = self.load(fire_station_payload(records))
        self.assertIsNotNone(loaded.verified_bytes)
        return normalize_fire_stations(
            loaded.verified_bytes or b"",
            source=loaded.evidence,
            transformer=self.transformer,
            descriptor=descriptor,
        )

    def rejection_reasons(self, result: A02Normalization, identifier: str) -> set[RejectionReason]:
        return {
            reason
            for record in result.checks.rejected_records
            if record.source_identifier == identifier
            for reason in record.reasons
        }


class CanonicalConversionTests(FireStationTestCase):
    def test_valid_records_become_sorted_canonical_stations(self) -> None:
        result = self.normalize(default_fire_station_records())
        records = result.dataset.records
        self.assertEqual([r.source_identifier for r in records], ["900001", "900002", "900003"])
        self.assertEqual(result.structural_validity, StructuralValidity.VALID)
        self.assertEqual(result.completeness, Completeness.COMPLETE_FOR_DECLARED_SCOPE)
        self.assertTrue(result.checks.reconciliation_ok)
        self.assertEqual(result.checks.inside_municipality_envelope_count, 3)
        first = records[0]
        self.assertEqual((first.source_latitude, first.source_longitude), (40.45, -3.69))
        for record in records:
            self.assertEqual(record.analytical_crs, "EPSG:25830")
            self.assertEqual(record.evidence_nature, "DERIVED")
            self.assertTrue(record.source_crs_interpretation.startswith("EPSG:4326 (interpreted"))
            self.assertTrue(MIN_EASTING_M <= record.easting_m <= MAX_EASTING_M)
            self.assertTrue(MIN_NORTHING_M <= record.northing_m <= MAX_NORTHING_M)

    def test_operational_properties_are_never_inferred(self) -> None:
        dataset = self.normalize(default_fire_station_records()).dataset
        self.assertEqual(set(dataset.not_inferred.values()), {"NOT_EVALUATED"})
        for key in ("docking_capability", "drone_suitability", "operational_readiness"):
            self.assertIn(key, dataset.not_inferred)

    def test_canonical_records_carry_only_source_derived_fields(self) -> None:
        dataset = self.normalize(default_fire_station_records()).dataset
        content = canonical_json_bytes(dataset)
        record_keys = set(json.loads(content)["records"][0])
        self.assertEqual(
            record_keys,
            {
                "analytical_crs",
                "easting_m",
                "evidence_nature",
                "northing_m",
                "source_crs_interpretation",
                "source_identifier",
                "source_latitude",
                "source_longitude",
                "source_probe_id",
                "source_record_uri",
                "source_sha256",
                "station_name",
            },
        )
        self.assertNotIn(PAYLOAD_SENTINEL.encode(), content)
        self.assertNotIn(b"api_key", content)


class CrsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transformer = make_analytical_transformer()

    def test_central_meridian_maps_to_the_utm_false_easting(self) -> None:
        easting, northing = project_lon_lat(self.transformer, -3.0, 40.0)
        self.assertAlmostEqual(easting, 500_000.0, places=3)
        self.assertLess(abs(northing - 4_427_757.2), 5.0)

    def test_round_trip_through_the_analytical_crs_is_stable(self) -> None:
        inverse = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)
        easting, northing = project_lon_lat(self.transformer, -3.7038, 40.4168)
        lon, lat = inverse.transform(easting, northing)
        self.assertAlmostEqual(lon, -3.7038, places=8)
        self.assertAlmostEqual(lat, 40.4168, places=8)

    def test_independent_transformers_agree_exactly(self) -> None:
        other = make_analytical_transformer()
        self.assertEqual(
            project_lon_lat(self.transformer, -3.69, 40.45), project_lon_lat(other, -3.69, 40.45)
        )


class InvalidCoordinateTests(FireStationTestCase):
    def test_invalid_coordinates_are_rejected_with_explicit_reasons(self) -> None:
        cases = {
            "out_of_range": ((91.0, -3.7), RejectionReason.COORDINATES_OUT_OF_RANGE),
            "string": (("40.4", -3.7), RejectionReason.NON_NUMERIC_COORDINATES),
            "boolean": ((True, -3.7), RejectionReason.NON_NUMERIC_COORDINATES),
            "non_finite": ((float("nan"), -3.7), RejectionReason.NON_FINITE_COORDINATES),
            "barcelona": ((41.38, 2.17), RejectionReason.OUTSIDE_MADRID_ENVELOPE),
            "swapped_axes": ((-3.70, 40.41), RejectionReason.OUTSIDE_MADRID_ENVELOPE),
        }
        for label, ((lat, lon), expected) in cases.items():
            with self.subTest(label):
                records = [
                    *default_fire_station_records(),
                    fire_station_record("999999", "X", lat, lon),
                ]
                result = self.normalize(records)
                self.assertEqual(self.rejection_reasons(result, "999999"), {expected})
                self.assertEqual(result.checks.canonical_record_count, 3)
                self.assertEqual(result.structural_validity, StructuralValidity.VALID_WITH_FLAGS)
                self.assertEqual(result.completeness, Completeness.INCOMPLETE_AFTER_REJECTIONS)
                self.assertEqual(
                    a02_eligibility(
                        Integrity.PASS, result.structural_validity, result.completeness
                    ),
                    Eligibility.NOT_ELIGIBLE,
                )

    def test_missing_location_is_rejected(self) -> None:
        record = fire_station_record("999999", "X", 40.4, -3.7)
        del record["location"]
        result = self.normalize([*default_fire_station_records(), record])
        self.assertEqual(
            self.rejection_reasons(result, "999999"), {RejectionReason.MISSING_COORDINATES}
        )


class DuplicateTests(FireStationTestCase):
    def test_duplicate_identifiers_reject_every_copy(self) -> None:
        records = [
            *default_fire_station_records(),
            fire_station_record("900001", "Fixture Park A bis", 40.42, -3.71),
        ]
        result = self.normalize(records)
        self.assertEqual(result.checks.duplicate_identifiers, ("900001",))
        self.assertEqual(
            [r.source_identifier for r in result.dataset.records], ["900002", "900003"]
        )
        duplicates = [r for r in result.checks.rejected_records if r.source_identifier == "900001"]
        self.assertEqual(len(duplicates), 2)
        for record in duplicates:
            self.assertIn(RejectionReason.DUPLICATE_IDENTIFIER, record.reasons)
        self.assertEqual(result.structural_validity, StructuralValidity.VALID_WITH_FLAGS)

    def test_duplicate_coordinates_are_flagged_and_kept(self) -> None:
        records = [
            *default_fire_station_records(),
            fire_station_record("900004", "Fixture Park D", 40.45, -3.69),
        ]
        result = self.normalize(records)
        self.assertEqual(result.checks.canonical_record_count, 4)
        self.assertEqual(result.checks.duplicate_coordinate_groups, (("900001", "900004"),))
        self.assertEqual(result.structural_validity, StructuralValidity.VALID_WITH_FLAGS)
        self.assertEqual(result.completeness, Completeness.UNKNOWN)
        self.assertEqual(
            a02_eligibility(Integrity.PASS, result.structural_validity, result.completeness),
            Eligibility.NOT_ELIGIBLE,
        )


class MissingFieldTests(FireStationTestCase):
    def test_blank_identifier_and_missing_name_are_rejected(self) -> None:
        blank_id = fire_station_record("   ", "Fixture Park Blank", 40.42, -3.70)
        nameless = fire_station_record("900010", None, 40.42, -3.70)
        result = self.normalize([*default_fire_station_records(), blank_id, nameless])
        reasons = {reason for r in result.checks.rejected_records for reason in r.reasons}
        self.assertEqual(
            reasons, {RejectionReason.INVALID_IDENTIFIER, RejectionReason.MISSING_NAME}
        )
        self.assertEqual(result.checks.source_record_count, 5)
        self.assertTrue(result.checks.reconciliation_ok)

    def test_non_object_record_is_rejected_on_every_required_field(self) -> None:
        result = self.normalize([*default_fire_station_records(), "not-a-record"])
        self.assertEqual(
            set(result.checks.rejected_records[0].reasons),
            {
                RejectionReason.INVALID_IDENTIFIER,
                RejectionReason.MISSING_NAME,
                RejectionReason.MISSING_COORDINATES,
            },
        )

    def test_empty_record_list_is_invalid_and_not_complete(self) -> None:
        result = self.normalize([])
        self.assertEqual(result.structural_validity, StructuralValidity.INVALID)
        self.assertEqual(result.completeness, Completeness.UNKNOWN)


class DeterminismTests(FireStationTestCase):
    def test_source_order_does_not_change_canonical_records(self) -> None:
        # Reordering the source changes its bytes and therefore (correctly) its SHA-256;
        # everything derived from the records themselves must be order-independent.
        forward = self.normalize(default_fire_station_records()).dataset.records
        reverse = self.normalize(list(reversed(default_fire_station_records()))).dataset.records
        excluded = {"source_sha256"}
        self.assertEqual(
            [record.model_dump(exclude=excluded) for record in forward],
            [record.model_dump(exclude=excluded) for record in reverse],
        )

    def test_repeated_runs_are_byte_identical(self) -> None:
        first = canonical_json_bytes(self.normalize(default_fire_station_records()))
        second = canonical_json_bytes(self.normalize(default_fire_station_records()))
        self.assertEqual(first, second)


class ProvenanceLinkageTests(FireStationTestCase):
    def test_every_record_links_to_the_verified_source(self) -> None:
        payload = fire_station_payload(default_fire_station_records())
        loaded = self.load(payload)
        dataset = normalize_fire_stations(
            loaded.verified_bytes or b"", source=loaded.evidence, transformer=self.transformer
        ).dataset
        expected_sha = hashlib.sha256(payload).hexdigest()
        self.assertEqual(loaded.evidence.sha256, expected_sha)
        self.assertEqual(dataset.source_sha256, expected_sha)
        self.assertEqual(dataset.source_url, FIRE_URL)
        self.assertEqual(dataset.source_acquired_at_utc, ACQUIRED_AT)
        self.assertEqual(dataset.source_evidence_classification, "REAL_SOURCE_DATA")
        self.assertEqual(
            (dataset.license, dataset.attribution), ("CC-BY-4.0", "Ayuntamiento de Madrid")
        )
        for record in dataset.records:
            self.assertEqual(record.source_sha256, expected_sha)
            self.assertEqual(record.source_probe_id, FIRE_STATION_PROBE_ID)


class MalformedInputTests(FireStationTestCase):
    def test_non_json_payload_fails_explicitly(self) -> None:
        loaded = self.load(b"<html>not json</html>")
        with self.assertRaises(MalformedEvidenceError):
            normalize_fire_stations(
                loaded.verified_bytes or b"", source=loaded.evidence, transformer=self.transformer
            )

    def test_json_without_record_graph_fails_explicitly(self) -> None:
        loaded = self.load(b'{"records": []}')
        with self.assertRaises(MalformedEvidenceError):
            normalize_fire_stations(
                loaded.verified_bytes or b"", source=loaded.evidence, transformer=self.transformer
            )


class IntegrityTests(FireStationTestCase):
    def payload(self) -> bytes:
        return fire_station_payload(default_fire_station_records())

    def test_ledger_digest_mismatch_is_integrity_fail(self) -> None:
        loaded = self.load(self.payload(), ledger_sha256="0" * 64)
        self.assertEqual(loaded.evidence.integrity, Integrity.FAIL)
        self.assertIsNone(loaded.verified_bytes)

    def test_missing_raw_bytes_stay_unavailable(self) -> None:
        loaded = self.load(self.payload(), write_raw=False)
        self.assertEqual(loaded.evidence.integrity, Integrity.RAW_UNAVAILABLE)
        self.assertIsNone(loaded.verified_bytes)

    def test_missing_sidecar_breaks_the_provenance_chain(self) -> None:
        loaded = self.load(self.payload(), write_sidecar=False)
        self.assertEqual(loaded.evidence.integrity, Integrity.FAIL)

    def test_truncated_response_is_integrity_fail(self) -> None:
        loaded = self.load(self.payload(), truncated=True)
        self.assertEqual(loaded.evidence.integrity, Integrity.FAIL)

    def test_ledger_entry_without_digest_fails_explicitly(self) -> None:
        self.load(self.payload())
        ledger_file = self.root / "ledger" / FIRE_STATION_PROBE_ID / "20260906.provenance.json"
        entry = json.loads(ledger_file.read_text(encoding="utf-8"))
        del entry["sha256"]
        ledger_file.write_text(json.dumps(entry), encoding="utf-8")
        with self.assertRaises(MalformedEvidenceError):
            load_artifact(ledger_file, self.root / "raw")


class SourceFactTests(FireStationTestCase):
    def test_descriptor_matches_the_committed_manifest(self) -> None:
        manifest = json.loads((REPO_ROOT / "data" / "datasets_manifest.json").read_text("utf-8"))
        entry = next(
            item
            for item in manifest["datasets"]
            if item["dataset_id"] == MUNICIPAL.manifest_dataset_id
        )
        self.assertEqual(entry["license"], MUNICIPAL.license)
        self.assertEqual(entry["spatial_coverage"], "Madrid municipality only")
        self.assertEqual(MUNICIPAL.declared_coverage, DeclaredCoverage.MADRID_MUNICIPALITY)

    def test_only_domain_wide_verified_valid_coverage_is_fully_eligible(self) -> None:
        result = self.normalize(default_fire_station_records(), descriptor=REGIONAL)
        self.assertEqual(result.completeness, Completeness.COMPLETE_FOR_ANALYTICAL_DOMAIN)
        self.assertEqual(
            a02_eligibility(Integrity.PASS, result.structural_validity, result.completeness),
            Eligibility.ELIGIBLE,
        )
        for integrity in (Integrity.FAIL, Integrity.RAW_UNAVAILABLE):
            self.assertEqual(
                a02_eligibility(integrity, result.structural_validity, result.completeness),
                Eligibility.NOT_ELIGIBLE,
            )
        self.assertEqual(
            a02_eligibility(
                Integrity.PASS,
                StructuralValidity.VALID_WITH_FLAGS,
                Completeness.COMPLETE_FOR_ANALYTICAL_DOMAIN,
            ),
            Eligibility.NOT_ELIGIBLE,
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from firstlook_mad.normalization.a01_ttfrp import (
    A01Observability,
    BaselineStatus,
    EgifArtifactEvidence,
    IncidentTimingRecord,
    a01_eligibility,
    derive_a01_observability,
)
from firstlook_mad.normalization.a04_weather import (
    A04Readiness,
    AemetContentType,
    CanonicalWeatherStationInventory,
    InventoryQuality,
    InventoryRejectionReason,
    WeatherArtifactEvidence,
    a04_eligibility,
    derive_a04_readiness,
    detect_aemet_content_type,
    normalize_station_inventory,
    parse_aemet_dms,
)
from firstlook_mad.normalization.crs import make_analytical_transformer
from firstlook_mad.normalization.evidence import load_artifact
from firstlook_mad.normalization.models import (
    Eligibility,
    Integrity,
    MalformedEvidenceError,
    StructuralValidity,
)
from phase0d2_fixtures import (
    AEMET_DATOS_URL,
    AEMET_WRAPPER,
    aemet_inventory_payload,
    aemet_station,
    default_aemet_stations,
    write_artifact,
)

FIRE_DAY = "2024-07-01"


def weather(
    content_type: AemetContentType | None,
    *,
    integrity: Integrity = Integrity.PASS,
    classification: str = "REAL_SOURCE_DATA",
    **fields: Any,
) -> WeatherArtifactEvidence:
    return WeatherArtifactEvidence(
        artifact_ref="fixture/20260906.raw",
        integrity=integrity,
        ledger_classification=classification,
        content_type=content_type,
        **fields,
    )


def series(
    *, dates: tuple[str, ...], variables: tuple[str, ...], **kwargs: Any
) -> WeatherArtifactEvidence:
    return weather(
        AemetContentType.OBSERVATION_SERIES,
        observed_dates=dates,
        observed_variables=variables,
        **kwargs,
    )


class AemetContentTypeTests(unittest.TestCase):
    def test_payload_shapes_are_distinguished(self) -> None:
        cases = {
            "wrapper": (AEMET_WRAPPER, AemetContentType.WRAPPER),
            "expired": (
                {"descripcion": "datos expirados", "estado": 404},
                AemetContentType.SERVICE_ERROR,
            ),
            "inventory": (default_aemet_stations(), AemetContentType.STATION_INVENTORY),
            "series": (
                [{"fecha": FIRE_DAY, "indicativo": "F001X"}],
                AemetContentType.OBSERVATION_SERIES,
            ),
            "strings": (["not", "records"], AemetContentType.UNRECOGNIZED),
            "empty": ([], AemetContentType.UNRECOGNIZED),
        }
        for label, (payload, expected) in cases.items():
            with self.subTest(label):
                self.assertEqual(detect_aemet_content_type(payload), expected)


class AemetDmsTests(unittest.TestCase):
    def test_valid_values_parse_to_signed_decimal_degrees(self) -> None:
        self.assertAlmostEqual(parse_aemet_dms("404736N", axis="latitude"), 40.793333333, places=8)
        self.assertAlmostEqual(parse_aemet_dms("040039W", axis="longitude"), -4.010833333, places=8)
        self.assertAlmostEqual(parse_aemet_dms("021000E", axis="longitude"), 2.166666667, places=8)

    def test_invalid_values_are_rejected_not_repaired(self) -> None:
        for value, axis in (
            ("4047N", "latitude"),
            ("406036N", "latitude"),
            ("404760N", "latitude"),
            ("404736W", "latitude"),
            ("040039N", "longitude"),
            ("", "latitude"),
        ):
            with self.subTest(value=value, axis=axis), self.assertRaises(ValueError):
                parse_aemet_dms(value, axis=axis)  # type: ignore[arg-type]


class A04ReadinessTests(unittest.TestCase):
    def test_station_inventory_does_not_imply_observations(self) -> None:
        readiness = derive_a04_readiness(
            [
                weather(AemetContentType.WRAPPER, classification="REAL_WRAPPER"),
                weather(
                    AemetContentType.SERVICE_ERROR, classification="NOT_USABLE_FOR_TARGET_TEST"
                ),
                weather(AemetContentType.STATION_INVENTORY, valid_madrid_record_count=23),
            ],
            fire_dates=frozenset(),
        )
        self.assertTrue(readiness.station_inventory_available)
        self.assertFalse(readiness.historical_observations_available)
        self.assertFalse(readiness.fire_day_observations_available)
        self.assertFalse(readiness.weather_falsification_ready)
        self.assertEqual(readiness.evidence_label, "WEATHER_EVIDENCE_NOT_OBSERVABLE")
        self.assertEqual(a04_eligibility(readiness), Eligibility.NOT_ELIGIBLE)

    def test_inventory_without_valid_madrid_records_is_not_available(self) -> None:
        readiness = derive_a04_readiness(
            [weather(AemetContentType.STATION_INVENTORY)], fire_dates=frozenset()
        )
        self.assertFalse(readiness.station_inventory_available)

    def test_observations_without_fire_dates_are_not_fire_day_ready(self) -> None:
        readiness = derive_a04_readiness(
            [series(dates=(FIRE_DAY,), variables=("wind", "visibility"))], fire_dates=frozenset()
        )
        self.assertTrue(readiness.historical_observations_available)
        self.assertFalse(readiness.fire_day_observations_available)
        self.assertFalse(readiness.weather_falsification_ready)

    def test_fire_day_coverage_without_visibility_is_not_ready(self) -> None:
        readiness = derive_a04_readiness(
            [series(dates=(FIRE_DAY,), variables=("wind",))], fire_dates=frozenset({FIRE_DAY})
        )
        self.assertTrue(readiness.fire_day_observations_available)
        self.assertFalse(readiness.weather_falsification_ready)
        self.assertEqual(a04_eligibility(readiness), Eligibility.NOT_ELIGIBLE)

    def test_complete_fire_day_evidence_is_the_only_path_to_ready(self) -> None:
        readiness = derive_a04_readiness(
            [series(dates=(FIRE_DAY,), variables=("wind", "visibility"))],
            fire_dates=frozenset({FIRE_DAY}),
        )
        self.assertTrue(readiness.weather_falsification_ready)
        self.assertEqual(readiness.evidence_label, "WEATHER_EVIDENCE_OBSERVABLE")
        self.assertEqual(a04_eligibility(readiness), Eligibility.ELIGIBLE)

    def test_unverified_or_non_source_observations_never_count(self) -> None:
        for kwargs in (
            {"integrity": Integrity.FAIL},
            {"integrity": Integrity.RAW_UNAVAILABLE},
            {"classification": "NOT_USABLE_FOR_TARGET_TEST"},
        ):
            with self.subTest(**kwargs):
                readiness = derive_a04_readiness(
                    [series(dates=(FIRE_DAY,), variables=("wind", "visibility"), **kwargs)],
                    fire_dates=frozenset({FIRE_DAY}),
                )
                self.assertFalse(readiness.historical_observations_available)
                self.assertFalse(readiness.weather_falsification_ready)

    def test_inventory_artifact_cannot_carry_observations(self) -> None:
        with self.assertRaises(ValueError):
            weather(AemetContentType.STATION_INVENTORY, observed_dates=(FIRE_DAY,))
        with self.assertRaises(ValueError):
            weather(AemetContentType.OBSERVATION_SERIES, valid_madrid_record_count=3)

    def test_readiness_chain_cannot_be_asserted_out_of_order(self) -> None:
        with self.assertRaises(ValueError):
            A04Readiness(
                station_inventory_available=True,
                historical_observations_available=False,
                fire_day_observations_available=True,
                weather_falsification_ready=False,
                evidence_label="WEATHER_EVIDENCE_NOT_OBSERVABLE",
            )
        with self.assertRaises(ValueError):
            A04Readiness(
                station_inventory_available=True,
                historical_observations_available=False,
                fire_day_observations_available=False,
                weather_falsification_ready=False,
                evidence_label="WEATHER_EVIDENCE_OBSERVABLE",
            )


class StationInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.transformer = make_analytical_transformer()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def normalize(
        self, payload: bytes
    ) -> tuple[CanonicalWeatherStationInventory, InventoryQuality]:
        probe = "aemet_madrid_station_inventory_datos"
        ledger_dir, raw_dir = write_artifact(
            self.root,
            probe_id=probe,
            payload=payload,
            assumption="A-04",
            classification="REAL_SOURCE_DATA",
            source_url=AEMET_DATOS_URL,
            content_type="text/plain;charset=ISO-8859-15",
        )
        loaded = load_artifact(ledger_dir / probe / "20260906.provenance.json", raw_dir)
        return normalize_station_inventory(
            loaded.verified_bytes or b"", source=loaded.evidence, transformer=self.transformer
        )

    def test_madrid_selection_uses_the_source_province_label(self) -> None:
        stations = [
            *default_aemet_stations(),
            aemet_station("F003X", "FIXTURE MIXED CASE", "Madrid"),
        ]
        inventory, quality = self.normalize(aemet_inventory_payload(stations))
        self.assertEqual(quality.source_record_count, 4)
        self.assertEqual(quality.madrid_province_record_count, 3)
        self.assertEqual(
            [r.station_identifier for r in inventory.records], ["F001X", "F002X", "F003X"]
        )
        self.assertEqual(quality.structural_validity, StructuralValidity.VALID)
        for record in inventory.records:
            self.assertEqual(record.record_kind, "STATION_INVENTORY_ENTRY_NOT_AN_OBSERVATION")
            self.assertEqual(record.analytical_crs, "EPSG:25830")
        self.assertIn("no weather observations", inventory.content_notice)

    def test_declared_iso_8859_15_charset_is_honoured(self) -> None:
        inventory, _ = self.normalize(aemet_inventory_payload(default_aemet_stations()))
        self.assertEqual(inventory.records[0].station_name, "FIXTURE ESTACIÓN NORTE")
        self.assertAlmostEqual(inventory.records[0].latitude, 40.793333333, places=8)

    def test_invalid_dms_rejects_the_record_without_repair(self) -> None:
        stations = [
            *default_aemet_stations(),
            aemet_station("F004X", "FIXTURE BAD", "MADRID", latitude="4024N"),
        ]
        inventory, quality = self.normalize(aemet_inventory_payload(stations))
        self.assertEqual(len(inventory.records), 2)
        self.assertEqual(
            quality.madrid_rejected_records[0].reasons, (InventoryRejectionReason.INVALID_LATITUDE,)
        )
        self.assertEqual(quality.structural_validity, StructuralValidity.VALID_WITH_FLAGS)

    def test_wrapper_payload_is_not_an_inventory(self) -> None:
        with self.assertRaises(MalformedEvidenceError):
            self.normalize(json.dumps(AEMET_WRAPPER).encode("iso-8859-15"))


class A01ObservabilityTests(unittest.TestCase):
    start = datetime(2024, 7, 1, 12, 0, tzinfo=UTC)

    def record(self, index: int, arrival_offset_s: float | None = 900.0) -> IncidentTimingRecord:
        return IncidentTimingRecord(
            incident_identifier=f"FIX-{index}",
            detection_at_utc=self.start,
            first_arrival_at_utc=(
                None
                if arrival_offset_s is None
                else self.start + timedelta(seconds=arrival_offset_s)
            ),
        )

    def source(self, records: list[IncidentTimingRecord], **kwargs: Any) -> EgifArtifactEvidence:
        values: dict[str, Any] = {
            "artifact_ref": "fixture/20260906.raw",
            "integrity": Integrity.PASS,
            "ledger_classification": "REAL_SOURCE_DATA",
            "incident_records": tuple(records),
        }
        values.update(kwargs)
        return EgifArtifactEvidence(**values)

    def test_interface_metadata_is_not_a_ttfrp_baseline(self) -> None:
        observability = derive_a01_observability(
            [
                EgifArtifactEvidence(
                    artifact_ref="egif_public_search_madrid/20260906.raw",
                    integrity=Integrity.PASS,
                    ledger_classification="REAL_METADATA",
                )
            ]
        )
        self.assertTrue(observability.public_interface_available)
        self.assertFalse(observability.incident_level_records_available)
        self.assertEqual(
            observability.ttfrp_baseline_status, BaselineStatus.BASELINE_NOT_OBSERVABLE
        )
        self.assertFalse(observability.proxy_ttfrp_generated)
        self.assertEqual(a01_eligibility(observability), Eligibility.NOT_ELIGIBLE)

    def test_metadata_artifact_cannot_carry_incident_records(self) -> None:
        with self.assertRaises(ValueError):
            self.source([self.record(0)], ledger_classification="REAL_METADATA")

    def test_ten_usable_records_are_the_pre_registered_minimum(self) -> None:
        nine = derive_a01_observability([self.source([self.record(i) for i in range(9)])])
        ten = derive_a01_observability([self.source([self.record(i) for i in range(10)])])
        self.assertEqual(nine.ttfrp_baseline_status, BaselineStatus.OBSERVABLE)
        self.assertEqual(a01_eligibility(nine), Eligibility.NOT_ELIGIBLE)
        self.assertEqual(a01_eligibility(ten), Eligibility.ELIGIBLE)

    def test_records_without_first_arrival_are_not_observable(self) -> None:
        observability = derive_a01_observability(
            [self.source([self.record(i, arrival_offset_s=None) for i in range(12)])]
        )
        self.assertTrue(observability.incident_level_records_available)
        self.assertEqual(observability.usable_timing_record_count, 0)
        self.assertEqual(
            observability.ttfrp_baseline_status, BaselineStatus.BASELINE_NOT_OBSERVABLE
        )

    def test_arrival_before_detection_is_not_usable(self) -> None:
        self.assertFalse(self.record(0, arrival_offset_s=-60.0).usable)

    def test_unverified_source_records_do_not_count(self) -> None:
        observability = derive_a01_observability(
            [self.source([self.record(i) for i in range(12)], integrity=Integrity.RAW_UNAVAILABLE)]
        )
        self.assertFalse(observability.public_interface_available)
        self.assertEqual(
            observability.ttfrp_baseline_status, BaselineStatus.BASELINE_NOT_OBSERVABLE
        )

    def test_naive_timestamps_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            IncidentTimingRecord(
                incident_identifier="FIX",
                detection_at_utc=datetime(2024, 7, 1, 12, 0),
                first_arrival_at_utc=None,
            )

    def test_status_and_proxy_flags_cannot_be_forced(self) -> None:
        with self.assertRaises(ValueError):
            A01Observability(
                public_interface_available=True,
                incident_level_records_available=False,
                usable_timing_record_count=0,
                ttfrp_baseline_status=BaselineStatus.OBSERVABLE,
            )
        with self.assertRaises(ValueError):
            A01Observability(
                public_interface_available=True,
                incident_level_records_available=False,
                usable_timing_record_count=0,
                ttfrp_baseline_status=BaselineStatus.BASELINE_NOT_OBSERVABLE,
                proxy_ttfrp_generated=True,  # type: ignore[arg-type]
            )

    def test_observability_record_has_no_invented_timestamp_fields(self) -> None:
        for field in A01Observability.model_fields:
            for word in ("dispatch", "detection", "response", "arrival_at", "seconds"):
                self.assertNotIn(word, field)


if __name__ == "__main__":
    unittest.main()

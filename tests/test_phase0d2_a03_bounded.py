from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from firstlook_mad.normalization.a03_bounded import (
    ENAIRE_PROBE_ID,
    MDT05_PROBE_ID,
    AirspaceSampleAssessment,
    BoundedEvidenceScope,
    CanonicalAirspaceSample,
    EvidenceScope,
    TerrainSampleAssessment,
    assess_terrain_sample,
    normalize_airspace_sample,
    rollup_a03_eligibility,
)
from firstlook_mad.normalization.crs import make_analytical_transformer
from firstlook_mad.normalization.evidence import load_artifact
from firstlook_mad.normalization.models import (
    Completeness,
    Eligibility,
    Envelope,
    MalformedEvidenceError,
    StructuralValidity,
    UnsupportedRasterLayoutError,
)
from phase0d2_fixtures import MDT05_URL, enaire_payload, enaire_url, geotiff_bytes, write_artifact

DOMAIN_COVERING_ENVELOPE = "-4.7,39.8,-3.0,41.2"
BOWTIE_OBJECT_ID = 100
BOWTIE_VERTEX_COUNT = 5
# 0C.1 reference synthetic extent in EPSG:25830 (configs/phase0c_synthetic.json).
MIN_EASTING_M, MAX_EASTING_M = 390_000.0, 500_000.0
MIN_NORTHING_M, MAX_NORTHING_M = 4_410_000.0, 4_520_000.0


class TempDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.transformer = make_analytical_transformer()

    def tearDown(self) -> None:
        self._tmp.cleanup()


class AirspaceSampleTests(TempDirTestCase):
    def normalize(
        self, payload: bytes, url: str | None = None
    ) -> tuple[AirspaceSampleAssessment, CanonicalAirspaceSample]:
        ledger_dir, raw_dir = write_artifact(
            self.root,
            probe_id=ENAIRE_PROBE_ID,
            payload=payload,
            assumption="A-03",
            classification="REAL_BOUNDED_SAMPLE",
            source_url=url or enaire_url(),
            content_type="application/geo+json; charset=UTF-8",
        )
        loaded = load_artifact(ledger_dir / ENAIRE_PROBE_ID / "20260906.provenance.json", raw_dir)
        return normalize_airspace_sample(
            loaded.verified_bytes or b"", source=loaded.evidence, transformer=self.transformer
        )

    def test_exceeded_transfer_limit_is_truncated_and_never_eligible(self) -> None:
        assessment, _ = self.normalize(enaire_payload(3, exceeded=True))
        scope = assessment.scope
        self.assertTrue(assessment.exceeded_transfer_limit)
        self.assertEqual(scope.completeness, Completeness.TRUNCATED_BY_SOURCE)
        self.assertEqual(scope.analytical_eligibility, Eligibility.NOT_ELIGIBLE)
        self.assertTrue(scope.bounded_sample)
        self.assertFalse(scope.eligible_for_full_madrid_analysis)
        self.assertEqual(scope.evidence_scope, EvidenceScope.REQUEST_ENVELOPE_SUBSET_OF_DOMAIN)

    def test_reaching_the_record_cap_is_truncation_even_without_the_flag(self) -> None:
        assessment, _ = self.normalize(enaire_payload(3), url=enaire_url(cap=3))
        self.assertFalse(assessment.exceeded_transfer_limit)
        self.assertEqual(assessment.scope.completeness, Completeness.TRUNCATED_BY_SOURCE)
        self.assertEqual(assessment.scope.analytical_eligibility, Eligibility.NOT_ELIGIBLE)

    def test_untruncated_bounded_sample_is_only_scope_eligible(self) -> None:
        assessment, _ = self.normalize(enaire_payload(3))
        scope = assessment.scope
        self.assertEqual(scope.completeness, Completeness.COMPLETE_FOR_DECLARED_SCOPE)
        self.assertEqual(scope.analytical_eligibility, Eligibility.ELIGIBLE_WITHIN_DECLARED_SCOPE)
        self.assertTrue(scope.bounded_sample)
        self.assertFalse(scope.eligible_for_full_madrid_analysis)
        self.assertEqual(
            scope.coverage_extent,
            Envelope(crs="EPSG:4326", min_x=-4.0, min_y=40.25, max_x=-3.4, max_y=40.65),
        )

    def test_only_a_domain_covering_untruncated_response_is_full_madrid_eligible(self) -> None:
        assessment, _ = self.normalize(
            enaire_payload(3), url=enaire_url(envelope=DOMAIN_COVERING_ENVELOPE)
        )
        self.assertFalse(assessment.scope.bounded_sample)
        self.assertTrue(assessment.scope.eligible_for_full_madrid_analysis)
        self.assertEqual(assessment.scope.analytical_eligibility, Eligibility.ELIGIBLE)

    def test_invalid_geometry_is_counted_and_never_repaired(self) -> None:
        assessment, sample = self.normalize(enaire_payload(3, invalid_first=True))
        self.assertEqual(assessment.invalid_geometry_count, 1)
        self.assertEqual(assessment.structural_validity, StructuralValidity.VALID_WITH_FLAGS)
        self.assertEqual(assessment.scope.analytical_eligibility, Eligibility.NOT_ELIGIBLE)
        bowtie = next(z for z in sample.zones if z.source_object_id == BOWTIE_OBJECT_ID)
        self.assertFalse(bowtie.geometry_valid)
        # Projected exactly as published: same vertices, no buffer(0)/make_valid rewrite.
        rings: Any = bowtie.geometry_coordinates_analytical
        self.assertEqual(len(rings), 1)
        self.assertEqual(len(rings[0]), BOWTIE_VERTEX_COUNT)
        self.assertEqual(rings[0][0], rings[0][-1])

    def test_crs_metadata_is_explicit_and_geometry_is_projected(self) -> None:
        assessment, sample = self.normalize(enaire_payload(3))
        self.assertEqual(assessment.scope.crs, "EPSG:4326")
        self.assertIn("RFC 7946", assessment.scope.crs_basis)
        self.assertEqual(sample.analytical_crs, "EPSG:25830")
        ring: Any = sample.zones[0].geometry_coordinates_analytical
        easting, northing = ring[0][0]
        self.assertTrue(MIN_EASTING_M <= easting <= MAX_EASTING_M)
        self.assertTrue(MIN_NORTHING_M <= northing <= MAX_NORTHING_M)

    def test_declared_crs_member_is_refused(self) -> None:
        payload = enaire_payload(3, extra={"crs": {"type": "name", "properties": {"name": "X"}}})
        with self.assertRaises(MalformedEvidenceError):
            self.normalize(payload)

    def test_request_url_without_envelope_fails_explicitly(self) -> None:
        with self.assertRaises(MalformedEvidenceError):
            self.normalize(enaire_payload(3), url="https://servais.enaire.es/query?f=geojson")

    def test_non_feature_collection_fails_explicitly(self) -> None:
        with self.assertRaises(MalformedEvidenceError):
            self.normalize(json.dumps({"type": "Feature"}).encode())


class BoundedScopeGuardTests(unittest.TestCase):
    def scope(self, **overrides: Any) -> BoundedEvidenceScope:
        values: dict[str, Any] = {
            "source_probe_id": "fixture",
            "source_sha256": "0" * 64,
            "acquisition_timestamp_utc": "2026-09-06T00:00:00+00:00",
            "evidence_scope": EvidenceScope.REQUEST_ENVELOPE_SUBSET_OF_DOMAIN,
            "coverage_extent": Envelope(crs="EPSG:4326", min_x=0, min_y=0, max_x=1, max_y=1),
            "crs": "EPSG:4326",
            "crs_basis": "fixture",
            "source_resolution": "fixture",
            "bounded_sample": True,
            "completeness": Completeness.COMPLETE_FOR_DECLARED_SCOPE,
            "eligible_for_full_madrid_analysis": False,
            "eligible_for_pipeline_verification": True,
            "analytical_eligibility": Eligibility.ELIGIBLE_WITHIN_DECLARED_SCOPE,
        }
        values.update(overrides)
        return BoundedEvidenceScope(**values)

    def test_consistent_bounded_scope_is_accepted(self) -> None:
        self.assertFalse(self.scope().eligible_for_full_madrid_analysis)

    def test_bounded_sample_cannot_be_full_madrid_eligible(self) -> None:
        with self.assertRaises(ValueError):
            self.scope(
                completeness=Completeness.COMPLETE_FOR_ANALYTICAL_DOMAIN,
                eligible_for_full_madrid_analysis=True,
                analytical_eligibility=Eligibility.ELIGIBLE,
            )

    def test_truncated_evidence_cannot_be_scope_eligible(self) -> None:
        with self.assertRaises(ValueError):
            self.scope(completeness=Completeness.TRUNCATED_BY_SOURCE)

    def test_eligible_requires_the_full_madrid_flag(self) -> None:
        with self.assertRaises(ValueError):
            self.scope(
                bounded_sample=False,
                completeness=Completeness.COMPLETE_FOR_ANALYTICAL_DOMAIN,
                analytical_eligibility=Eligibility.ELIGIBLE,
            )


class TerrainSampleTests(TempDirTestCase):
    def assess(self, payload: bytes, url: str = MDT05_URL) -> TerrainSampleAssessment:
        ledger_dir, raw_dir = write_artifact(
            self.root,
            probe_id=MDT05_PROBE_ID,
            payload=payload,
            assumption="A-03",
            classification="REAL_SOURCE_DATA",
            source_url=url,
            content_type="image/tiff",
        )
        loaded = load_artifact(ledger_dir / MDT05_PROBE_ID / "20260906.provenance.json", raw_dir)
        return assess_terrain_sample(loaded.verified_bytes or b"", source=loaded.evidence)

    def test_sample_window_is_parsed_with_its_declared_crs(self) -> None:
        assessment = self.assess(geotiff_bytes())
        raster = assessment.raster
        self.assertEqual((raster.width, raster.height), (20, 20))
        self.assertEqual(raster.projected_crs_epsg, 25830)
        self.assertEqual(raster.raster_type, "PIXEL_IS_AREA")
        self.assertEqual((raster.pixel_scale_x, raster.pixel_scale_y), (5.0, 5.0))
        self.assertTrue(assessment.extent_matches_request)
        self.assertEqual((raster.sample_window_min, raster.sample_window_max), (648.0, 654.0))
        self.assertEqual(raster.statistic_scope, "sample_window_only")
        self.assertEqual(assessment.structural_validity, StructuralValidity.VALID)

    def test_sample_is_bounded_and_never_substitution_eligible(self) -> None:
        scope = self.assess(geotiff_bytes()).scope
        self.assertEqual(scope.evidence_scope, EvidenceScope.FIXED_WINDOW_PIPELINE_SAMPLE)
        self.assertTrue(scope.bounded_sample)
        self.assertEqual(scope.completeness, Completeness.BOUNDED_SAMPLE)
        self.assertFalse(scope.eligible_for_full_madrid_analysis)
        self.assertEqual(scope.analytical_eligibility, Eligibility.NOT_ELIGIBLE)
        self.assertTrue(scope.eligible_for_pipeline_verification)
        self.assertEqual(scope.crs, "EPSG:25830")
        self.assertEqual(scope.source_resolution, "5 m x 5 m")

    def test_no_value_is_extrapolated_beyond_the_window(self) -> None:
        assessment = self.assess(geotiff_bytes())
        extent = assessment.scope.coverage_extent
        self.assertEqual((extent.max_x - extent.min_x, extent.max_y - extent.min_y), (100.0, 100.0))
        statistic_keys = {
            key
            for key in assessment.raster.model_dump()
            if any(word in key for word in ("min", "max", "mean", "value"))
        }
        self.assertEqual(
            statistic_keys,
            {"sample_window_min", "sample_window_max", "sample_window_value_count"},
        )

    def test_extent_mismatch_is_flagged_and_blocks_pipeline_verification(self) -> None:
        assessment = self.assess(geotiff_bytes(origin_x=440_005.0))
        self.assertFalse(assessment.extent_matches_request)
        self.assertEqual(assessment.structural_validity, StructuralValidity.VALID_WITH_FLAGS)
        self.assertFalse(assessment.scope.eligible_for_pipeline_verification)
        self.assertEqual(assessment.scope.analytical_eligibility, Eligibility.NOT_ELIGIBLE)

    def test_missing_projected_crs_geokey_is_flagged(self) -> None:
        assessment = self.assess(geotiff_bytes(epsg=None))
        self.assertIsNone(assessment.raster.projected_crs_epsg)
        self.assertEqual(assessment.scope.crs, "UNDECLARED")
        self.assertEqual(assessment.structural_validity, StructuralValidity.VALID_WITH_FLAGS)

    def test_nodata_is_excluded_from_sample_statistics(self) -> None:
        values = [-9999, *[650] * 399]
        raster = self.assess(geotiff_bytes(values=values, nodata="-9999")).raster
        self.assertEqual(raster.nodata, "-9999")
        self.assertEqual(raster.sample_window_value_count, 399)
        self.assertEqual(raster.sample_window_min, 650.0)

    def test_compressed_raster_is_not_decoded(self) -> None:
        with self.assertRaises(UnsupportedRasterLayoutError):
            self.assess(geotiff_bytes(compression=5))

    def test_service_exception_body_fails_explicitly(self) -> None:
        with self.assertRaises(MalformedEvidenceError):
            self.assess(b"<ows:ExceptionReport>fixture</ows:ExceptionReport>")

    def test_truncated_tiff_fails_explicitly(self) -> None:
        with self.assertRaises(MalformedEvidenceError):
            self.assess(geotiff_bytes()[:100])


class RollupTests(unittest.TestCase):
    def test_a03_rollup_never_upgrades_missing_or_partial_components(self) -> None:
        e = Eligibility
        cases = [
            ((e.NOT_ELIGIBLE, e.NOT_ELIGIBLE), e.NOT_ELIGIBLE),
            ((e.ELIGIBLE, e.ELIGIBLE), e.ELIGIBLE),
            ((e.ELIGIBLE, e.NOT_ELIGIBLE), e.ELIGIBLE_WITHIN_DECLARED_SCOPE),
            ((e.ELIGIBLE_WITHIN_DECLARED_SCOPE, e.NOT_ELIGIBLE), e.ELIGIBLE_WITHIN_DECLARED_SCOPE),
            ((e.ELIGIBLE, None), e.ELIGIBLE_WITHIN_DECLARED_SCOPE),
            ((None, None), e.NOT_ELIGIBLE),
        ]
        for (airspace, terrain), expected in cases:
            with self.subTest(airspace=airspace, terrain=terrain):
                self.assertEqual(rollup_a03_eligibility(airspace, terrain), expected)


if __name__ == "__main__":
    unittest.main()

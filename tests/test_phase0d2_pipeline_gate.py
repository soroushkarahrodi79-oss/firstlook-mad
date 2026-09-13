from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.normalize_phase0d2 import main

from firstlook_mad.normalization.a02_fire_stations import FIRE_STATION_PROBE_ID
from firstlook_mad.normalization.gate import evaluate_gate
from firstlook_mad.normalization.models import (
    Completeness,
    Eligibility,
    GateVerdict,
    Integrity,
    MalformedEvidenceError,
    NormalizationOutcome,
    SemanticFitness,
    StructuralValidity,
)
from firstlook_mad.normalization.pipeline import (
    A02_CANONICAL_PATH,
    REPORT_PATH,
    A01Details,
    A03Details,
    A04Details,
    AssumptionAssessment,
    NormalizationRun,
    run_normalization,
    write_run,
)
from firstlook_mad.normalization.serialization import (
    SECRET_MARKERS,
    TrackedOutputLeakError,
    assert_no_secret_markers,
)
from phase0d2_fixtures import (
    FIRE_URL,
    PAYLOAD_SENTINEL,
    build_evidence_tree,
    write_artifact,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
E = Eligibility


class GateRuleTests(unittest.TestCase):
    def gate(self, a01: E, a02: E, a03: E, a04: E, failures: tuple[str, ...] = ()) -> GateVerdict:
        eligibility = {"A-01": a01, "A-02": a02, "A-03": a03, "A-04": a04}
        return evaluate_gate(eligibility, integrity_failures=failures).verdict

    def test_all_four_eligible_without_integrity_failures_is_ready(self) -> None:
        self.assertEqual(
            self.gate(E.ELIGIBLE, E.ELIGIBLE, E.ELIGIBLE, E.ELIGIBLE),
            GateVerdict.NORMALIZATION_READY,
        )

    def test_integrity_failure_blocks_ready(self) -> None:
        self.assertEqual(
            self.gate(E.ELIGIBLE, E.ELIGIBLE, E.ELIGIBLE, E.ELIGIBLE, ("x/1.raw",)),
            GateVerdict.PARTIAL_NORMALIZATION,
        )

    def test_scope_restricted_eligibility_is_never_ready(self) -> None:
        decision = evaluate_gate(
            {
                "A-01": E.ELIGIBLE,
                "A-02": E.ELIGIBLE_WITHIN_DECLARED_SCOPE,
                "A-03": E.ELIGIBLE,
                "A-04": E.ELIGIBLE,
            }
        )
        self.assertEqual(decision.verdict, GateVerdict.PARTIAL_NORMALIZATION)
        self.assertTrue(decision.scope_restricted_includes_a02)

    def test_single_scoped_assumption_is_partial(self) -> None:
        self.assertEqual(
            self.gate(
                E.NOT_ELIGIBLE, E.ELIGIBLE_WITHIN_DECLARED_SCOPE, E.NOT_ELIGIBLE, E.NOT_ELIGIBLE
            ),
            GateVerdict.PARTIAL_NORMALIZATION,
        )

    def test_all_not_eligible_is_semantically_insufficient(self) -> None:
        self.assertEqual(
            self.gate(E.NOT_ELIGIBLE, E.NOT_ELIGIBLE, E.NOT_ELIGIBLE, E.NOT_ELIGIBLE),
            GateVerdict.SEMANTICALLY_INSUFFICIENT,
        )

    def test_missing_or_unknown_assumptions_are_errors_not_defaults(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_gate({"A-01": E.ELIGIBLE, "A-02": E.ELIGIBLE, "A-03": E.ELIGIBLE})
        with self.assertRaises(ValueError):
            evaluate_gate(
                {
                    "A-01": E.ELIGIBLE,
                    "A-02": E.ELIGIBLE,
                    "A-03": E.ELIGIBLE,
                    "A-04": E.ELIGIBLE,
                    "A-05": E.ELIGIBLE,
                }
            )


class PipelineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ledger_dir, self.raw_dir = build_evidence_tree(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_pipeline(self) -> NormalizationRun:
        return run_normalization(ledger_dir=self.ledger_dir, raw_dir=self.raw_dir)

    def assessment(self, run: NormalizationRun, assumption: str) -> AssumptionAssessment:
        return next(a for a in run.report.assumptions if a.assumption == assumption)


class PipelineReportTests(PipelineTestCase):
    def test_fixture_tree_yields_partial_normalization(self) -> None:
        gate = self.run_pipeline().report.gate
        self.assertEqual(gate.verdict, GateVerdict.PARTIAL_NORMALIZATION)
        self.assertEqual(
            gate.eligibility_by_assumption,
            {
                "A-01": E.NOT_ELIGIBLE,
                "A-02": E.ELIGIBLE_WITHIN_DECLARED_SCOPE,
                "A-03": E.NOT_ELIGIBLE,
                "A-04": E.NOT_ELIGIBLE,
            },
        )
        self.assertTrue(gate.scope_restricted_includes_a02)
        self.assertEqual(gate.integrity_failures, ())

    def test_quality_dimensions_stay_separate_with_no_composite_score(self) -> None:
        report = json.loads(self.run_pipeline().report_bytes())
        self.assertEqual(
            [a["assumption"] for a in report["assumptions"]], ["A-01", "A-02", "A-03", "A-04"]
        )
        for item in report["assumptions"]:
            for dimension in (
                "evidence_acquired",
                "normalized_successfully",
                "integrity",
                "structural_validity",
                "semantic_fitness",
                "completeness",
                "analytical_eligibility",
                "eligible_for_downstream_substitution",
                "blockers",
                "reason",
            ):
                self.assertIn(dimension, item)
        self.assertNotIn("score", json.dumps(report).lower())

    def test_a01_stays_baseline_not_observable(self) -> None:
        a01 = self.assessment(self.run_pipeline(), "A-01")
        self.assertIsInstance(a01.details, A01Details)
        assert isinstance(a01.details, A01Details)
        self.assertEqual(
            a01.details.observability.ttfrp_baseline_status.value, "BASELINE_NOT_OBSERVABLE"
        )
        self.assertTrue(a01.details.observability.public_interface_available)
        self.assertEqual(a01.normalization_outcome, NormalizationOutcome.OBSERVABILITY_RECORD_ONLY)
        self.assertFalse(a01.normalized_successfully)
        self.assertEqual(a01.completeness, Completeness.NOT_OBSERVED)

    def test_a03_bounded_components_are_never_full_madrid_eligible(self) -> None:
        a03 = self.assessment(self.run_pipeline(), "A-03")
        assert isinstance(a03.details, A03Details)
        self.assertIsNotNone(a03.details.airspace)
        self.assertIsNotNone(a03.details.terrain)
        for component in (a03.details.airspace, a03.details.terrain):
            assert component is not None
            self.assertTrue(component.scope.bounded_sample)
            self.assertFalse(component.scope.eligible_for_full_madrid_analysis)
        self.assertEqual(a03.completeness, Completeness.TRUNCATED_BY_SOURCE)
        self.assertEqual(a03.analytical_eligibility, E.NOT_ELIGIBLE)
        self.assertEqual(len(a03.details.metadata_only_artifacts), 1)

    def test_a04_inventory_only_readiness(self) -> None:
        a04 = self.assessment(self.run_pipeline(), "A-04")
        assert isinstance(a04.details, A04Details)
        readiness = a04.details.readiness
        self.assertEqual(
            (
                readiness.station_inventory_available,
                readiness.historical_observations_available,
                readiness.fire_day_observations_available,
                readiness.weather_falsification_ready,
            ),
            (True, False, False, False),
        )
        self.assertEqual(a04.normalization_outcome, NormalizationOutcome.CANONICAL_INVENTORY_ONLY)
        self.assertFalse(a04.eligible_for_downstream_substitution)
        self.assertEqual(a04.semantic_fitness, SemanticFitness.NOT_FIT_FOR_TARGET_ROLE)

    def test_report_generation_is_deterministic(self) -> None:
        first, second = self.run_pipeline(), self.run_pipeline()
        self.assertEqual(first.report_bytes(), second.report_bytes())
        self.assertEqual([o.content for o in first.outputs], [o.content for o in second.outputs])
        out_a, out_b = self.root / "out_a", self.root / "out_b"
        paths_a = write_run(first, output_root=out_a)
        write_run(second, output_root=out_b)
        for path in paths_a:
            relative = path.relative_to(out_a)
            self.assertEqual(path.read_bytes(), (out_b / relative).read_bytes())

    def test_tracked_outputs_carry_no_payload_or_secret_markers(self) -> None:
        run = self.run_pipeline()
        report = run.report_bytes().decode("utf-8")
        for forbidden in (PAYLOAD_SENTINEL, "Fixture Park", "Fixture zone", "FIXTURE ESTACI"):
            self.assertNotIn(forbidden, report)
        for marker in SECRET_MARKERS:
            self.assertNotIn(marker, report.lower())
        tracked = [o for o in run.outputs if o.record.tracked_in_git]
        self.assertEqual([o.record.relative_path for o in tracked], [A02_CANONICAL_PATH])
        tracked_text = tracked[0].content.decode("utf-8")
        self.assertNotIn(PAYLOAD_SENTINEL, tracked_text)
        for marker in SECRET_MARKERS:
            self.assertNotIn(marker, tracked_text.lower())
        for output in run.outputs:
            if not output.record.tracked_in_git:
                self.assertTrue(output.record.relative_path.startswith("data/processed/phase0d2/"))

    def test_secret_guard_refuses_marked_output(self) -> None:
        with self.assertRaises(TrackedOutputLeakError):
            assert_no_secret_markers(b'{"Cookie": "x"}', where="fixture")


class UnknownAndMalformedEvidenceTests(PipelineTestCase):
    def fire_raw(self) -> Path:
        return self.raw_dir / FIRE_STATION_PROBE_ID / "20260906.raw"

    def test_missing_raw_evidence_stays_unknown_and_never_eligible(self) -> None:
        self.fire_raw().unlink()
        run = self.run_pipeline()
        a02 = self.assessment(run, "A-02")
        self.assertEqual(a02.integrity, Integrity.RAW_UNAVAILABLE)
        self.assertEqual(a02.structural_validity, StructuralValidity.NOT_NORMALIZED)
        self.assertEqual(a02.semantic_fitness, SemanticFitness.UNKNOWN)
        self.assertEqual(a02.completeness, Completeness.UNKNOWN)
        self.assertEqual(a02.analytical_eligibility, E.NOT_ELIGIBLE)
        self.assertEqual(a02.normalization_outcome, NormalizationOutcome.NOT_ATTEMPTED)
        self.assertEqual(run.report.gate.verdict, GateVerdict.SEMANTICALLY_INSUFFICIENT)
        self.assertNotIn(A02_CANONICAL_PATH, [o.record.relative_path for o in run.outputs])

    def test_tampered_raw_evidence_is_recorded_as_integrity_failure(self) -> None:
        self.fire_raw().write_bytes(b'{"@graph": []}')
        run = self.run_pipeline()
        a02 = self.assessment(run, "A-02")
        self.assertEqual(a02.integrity, Integrity.FAIL)
        self.assertEqual(a02.analytical_eligibility, E.NOT_ELIGIBLE)
        self.assertIn(f"{FIRE_STATION_PROBE_ID}/20260906.raw", run.report.gate.integrity_failures)

    def test_malformed_source_payload_is_recorded_as_failed(self) -> None:
        write_artifact(
            self.root,
            probe_id=FIRE_STATION_PROBE_ID,
            payload=b"not json at all",
            assumption="A-02",
            classification="REAL_SOURCE_DATA",
            source_url=FIRE_URL,
            content_type="application/json",
        )
        a02 = self.assessment(self.run_pipeline(), "A-02")
        self.assertEqual(a02.normalization_outcome, NormalizationOutcome.FAILED)
        self.assertEqual(a02.structural_validity, StructuralValidity.INVALID)
        self.assertTrue(any("not valid JSON" in blocker for blocker in a02.blockers))

    def test_malformed_ledger_entry_aborts_explicitly(self) -> None:
        broken = self.ledger_dir / "broken_probe"
        broken.mkdir()
        (broken / "20260906.provenance.json").write_text('{"probe_id": "broken_probe"}', "utf-8")
        with self.assertRaises(MalformedEvidenceError):
            self.run_pipeline()

    def test_missing_ledger_directory_fails_explicitly(self) -> None:
        with self.assertRaises(MalformedEvidenceError):
            run_normalization(ledger_dir=self.root / "absent", raw_dir=self.raw_dir)


class RunnerTests(PipelineTestCase):
    def test_runner_writes_report_and_canonical_outputs(self) -> None:
        output_root = self.root / "out"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(
                [
                    "--ledger-dir",
                    str(self.ledger_dir),
                    "--raw-dir",
                    str(self.raw_dir),
                    "--output-root",
                    str(output_root),
                ]
            )
        self.assertEqual(exit_code, 0)
        self.assertTrue((output_root / REPORT_PATH).is_file())
        self.assertTrue((output_root / A02_CANONICAL_PATH).is_file())
        self.assertIn("0D.2 gate verdict: PARTIAL_NORMALIZATION", stdout.getvalue())


LOCAL_RAW = REPO_ROOT / "data" / "raw" / "phase0d" / FIRE_STATION_PROBE_ID


@unittest.skipUnless(
    LOCAL_RAW.is_dir() and (REPO_ROOT / REPORT_PATH).is_file(),
    "local gitignored Phase 0D.1 raw evidence or committed 0D.2 report not present",
)
class RealEvidenceRegenerationTests(unittest.TestCase):
    def test_committed_outputs_regenerate_byte_for_byte(self) -> None:
        kwargs = {
            "ledger_dir": REPO_ROOT / "outputs" / "provenance" / "phase0d",
            "raw_dir": REPO_ROOT / "data" / "raw" / "phase0d",
        }
        first, second = run_normalization(**kwargs), run_normalization(**kwargs)
        self.assertEqual(first.report_bytes(), second.report_bytes())
        committed = (REPO_ROOT / REPORT_PATH).read_text(encoding="utf-8")
        self.assertEqual(committed, first.report_bytes().decode("utf-8"))
        for output in first.outputs:
            if output.record.tracked_in_git:
                on_disk = (REPO_ROOT / output.record.relative_path).read_text(encoding="utf-8")
                self.assertEqual(on_disk, output.content.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()

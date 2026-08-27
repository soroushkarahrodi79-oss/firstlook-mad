from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from firstlook_mad.audit import (
    a01_sensitivity,
    f_aware_site_order,
    f_factor_ablation,
    fair_comparator,
    multi_seed_audit,
    run_audit_experiment,
    sample_size_audit,
)
from firstlook_mad.cli import main
from firstlook_mad.domain import (
    CandidateSite,
    CoverageModel,
    EvidenceNature,
    GateOutcome,
    GatePolicy,
    Incident,
    ProjectedPoint,
    TTFRPAssumptions,
    UASPerformanceProfile,
    WeatherScenario,
    ZoneState,
)
from firstlook_mad.geo import euclidean_distance_m
from firstlook_mad.safety import assess_gate
from firstlook_mad.simulation import evaluate_pair
from firstlook_mad.synthetic import generate_inputs, load_config
from firstlook_mad.validation import greedy_site_order, run_experiment

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "phase0c_synthetic.json"


def point(easting_m: float = 450_000.0, northing_m: float = 4_470_000.0) -> ProjectedPoint:
    return ProjectedPoint(easting_m=easting_m, northing_m=northing_m)


def incident(
    *,
    easting_m: float = 450_000.0,
    airspace: ZoneState = ZoneState.POTENTIALLY_ALLOWED,
    terrain_multiplier: float = 1.0,
) -> Incident:
    return Incident(
        incident_id="incident",
        point=point(easting_m),
        risk_weight=1.0,
        terrain_multiplier=terrain_multiplier,
        airspace=airspace,
        temporary_restriction=False,
        manned_aircraft_conflict=False,
        incident_confidence=1.0,
        data_age_minutes=1.0,
    )


def site(*, easting_m: float = 451_000.0, available: bool | None = True) -> CandidateSite:
    return CandidateSite(
        site_id="site",
        point=point(easting_m),
        assumed_available=available,
        uas_available=True,
        communications_available=True,
        camera_available=True,
        camera_communications_available=True,
    )


def profile(*, max_sortie_distance_m: float = 10_000.0) -> UASPerformanceProfile:
    return UASPerformanceProfile(
        profile_id="assumed",
        cruise_speed_mps=10.0,
        max_sortie_distance_m=max_sortie_distance_m,
        reserve_fraction=0.25,
        max_wind_mps=12.0,
        max_precipitation_mm_h=2.0,
        min_visibility_m=3_000.0,
        min_temperature_c=-5.0,
        max_temperature_c=45.0,
        minimum_battery_fraction=0.8,
    )


def ttfrp() -> TTFRPAssumptions:
    return TTFRPAssumptions(
        scenario_id="assumed",
        alert_processing_s=10.0,
        verification_s=20.0,
        preflight_gate_s=30.0,
        launch_s=40.0,
        scene_acquisition_s=50.0,
        first_analysis_s=60.0,
    )


def weather(*, wind_mps: float | None = 5.0) -> WeatherScenario:
    return WeatherScenario(
        scenario_id="assumed",
        wind_mps=wind_mps,
        precipitation_mm_h=0.0,
        visibility_m=10_000.0,
        temperature_c=25.0,
    )


class GeometryTests(unittest.TestCase):
    def test_metric_distance_uses_projected_coordinates(self) -> None:
        left = point(450_000.0, 4_470_000.0)
        right = point(453_000.0, 4_474_000.0)
        self.assertEqual(euclidean_distance_m(left, right), 5_000.0)

    def test_degree_crs_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ProjectedPoint(crs="EPSG:4326", easting_m=450_000.0, northing_m=4_470_000.0)

    def test_degree_like_or_swapped_coordinates_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ProjectedPoint(easting_m=-3.7, northing_m=40.4)
        with self.assertRaises(ValidationError):
            ProjectedPoint(easting_m=4_470_000.0, northing_m=450_000.0)


class GateTests(unittest.TestCase):
    def test_first_failure_is_primary_and_blocks_simulation(self) -> None:
        result = assess_gate(
            incident=incident(airspace=ZoneState.RESTRICTED),
            site=site(available=False),
            profile=profile(),
            weather=weather(wind_mps=20.0),
            effective_distance_m=1_000.0,
            battery_fraction=1.0,
            max_data_age_minutes=60.0,
            minimum_incident_confidence=0.75,
            policy=GatePolicy(),
        )
        self.assertEqual(result.outcome, GateOutcome.NO_GO)
        self.assertEqual(result.primary_reason, "site_available")
        self.assertGreater(sum(check.state.value != "PASS" for check in result.checks), 1)

    def test_unknown_and_authorization_never_produce_go(self) -> None:
        outcomes = {}
        for zone in (ZoneState.UNKNOWN, ZoneState.REQUIRES_AUTHORIZATION):
            result = assess_gate(
                incident=incident(airspace=zone),
                site=site(),
                profile=profile(),
                weather=weather(),
                effective_distance_m=1_000.0,
                battery_fraction=1.0,
                max_data_age_minutes=60.0,
                minimum_incident_confidence=0.75,
                policy=GatePolicy(
                    reserve=False,
                    site_availability=False,
                    uas_availability=False,
                    battery=False,
                    communications=False,
                    incident_confidence=False,
                    data_freshness=False,
                    temporary_restriction=False,
                    manned_aircraft_conflict=False,
                    weather=False,
                ),
            )
            outcomes[zone] = result.outcome
        self.assertEqual(outcomes[ZoneState.UNKNOWN], GateOutcome.UNKNOWN)
        self.assertEqual(
            outcomes[ZoneState.REQUIRES_AUTHORIZATION],
            GateOutcome.REQUIRES_HUMAN_REVIEW,
        )
        self.assertNotIn("SAFE_TO_FLY", {outcome.value for outcome in GateOutcome})


class ProgressiveModelTests(unittest.TestCase):
    def evaluate(
        self,
        model: CoverageModel,
        *,
        test_incident: Incident | None = None,
        test_weather: WeatherScenario | None = None,
        test_profile: UASPerformanceProfile | None = None,
    ) -> object:
        return evaluate_pair(
            incident=test_incident or incident(),
            site=site(),
            profile=test_profile or profile(),
            ttfrp=ttfrp(),
            weather=test_weather or weather(),
            model=model,
            battery_fraction=1.0,
            max_data_age_minutes=60.0,
            minimum_incident_confidence=0.75,
        )

    def test_models_add_time_and_relief_progressively(self) -> None:
        distance_only = self.evaluate(CoverageModel.A_DISTANCE)
        travel = self.evaluate(CoverageModel.B_TRAVEL_TIME)
        relief = self.evaluate(
            CoverageModel.C_RELIEF,
            test_incident=incident(terrain_multiplier=1.5),
        )
        self.assertIsNone(distance_only.ttfrp_seconds)
        self.assertEqual(travel.travel_seconds, 100.0)
        self.assertEqual(travel.ttfrp_seconds, 310.0)
        self.assertEqual(relief.travel_seconds, 150.0)

    def test_airspace_weather_and_reserve_can_each_exclude(self) -> None:
        airspace = self.evaluate(
            CoverageModel.D_AIRSPACE,
            test_incident=incident(airspace=ZoneState.RESTRICTED),
        )
        wind = self.evaluate(
            CoverageModel.E_WEATHER,
            test_weather=weather(wind_mps=20.0),
        )
        reserve = self.evaluate(
            CoverageModel.F_ENERGY,
            test_incident=incident(easting_m=450_000.0),
            test_profile=profile(max_sortie_distance_m=2_500.0),
        )
        self.assertEqual(airspace.gate.primary_reason, "airspace")
        self.assertEqual(wind.gate.primary_reason, "wind")
        self.assertEqual(reserve.gate.primary_reason, "range")
        self.assertFalse(airspace.feasible or wind.feasible or reserve.feasible)


class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config(CONFIG_PATH)

    def test_generation_and_site_selection_are_deterministic(self) -> None:
        first_incidents, first_sites = generate_inputs(self.config)
        second_incidents, second_sites = generate_inputs(self.config)
        self.assertEqual(first_incidents, second_incidents)
        self.assertEqual(first_sites, second_sites)
        first_order = greedy_site_order(
            first_incidents,
            first_sites,
            self.config.reference_profile.max_sortie_distance_m / 2.0,
        )
        second_order = greedy_site_order(
            second_incidents,
            second_sites,
            self.config.reference_profile.max_sortie_distance_m / 2.0,
        )
        self.assertEqual(first_order, second_order)

    def test_results_preserve_evidence_interpretation_decision(self) -> None:
        result = run_experiment(self.config)
        self.assertEqual(set(result), {"metadata", "evidence", "interpretation", "decision"})
        self.assertEqual(result["metadata"]["nature"], EvidenceNature.SYNTHETIC.value)
        self.assertEqual(
            result["interpretation"]["A_01_travel_materiality"],
            "CONDITION_DEPENDENT",
        )
        weather_rows = result["evidence"]["weather_erosion"]
        self.assertEqual(weather_rows[1]["risk_weighted_coverage"], 0.0)
        self.assertEqual(weather_rows[2]["risk_weighted_coverage"], 0.0)
        profile_rows = result["evidence"]["profile_sensitivity"]
        profile_coverage = [row["risk_weighted_coverage"] for row in profile_rows]
        self.assertEqual(profile_coverage, sorted(profile_coverage))

    def test_cli_writes_reproducible_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            self.assertEqual(
                main(["simulate", "--config", str(CONFIG_PATH), "--output", str(first)]),
                0,
            )
            self.assertEqual(
                main(["simulate", "--config", str(CONFIG_PATH), "--output", str(second)]),
                0,
            )
            self.assertEqual(first.read_bytes(), second.read_bytes())
            document = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(document["metadata"]["seed"], self.config.seed)
            self.assertEqual(document["metadata"]["schema_version"], "1.1")
            audit = document["evidence"]["robustness_audit"]
            self.assertEqual(
                set(audit),
                {
                    "ablation",
                    "fair_comparator",
                    "multi_seed",
                    "a01_sensitivity",
                    "site_selection_comparison",
                    "sample_size_sensitivity",
                    "randomness_invariants",
                },
            )

    def test_ablation_never_loses_a_full_f_survivor(self) -> None:
        incidents, sites = generate_inputs(self.config)
        result = f_factor_ablation(
            incidents=incidents,
            sites=sites,
            config=self.config,
            ttfrp=self.config.ttfrp_scenarios[0],
            weather=self.config.weather_scenarios[0],
        )
        self.assertTrue(all(row["removal_never_reduces_survivors"] for row in result["rows"]))
        range_row = next(row for row in result["rows"] if row["factor_removed"] == "range")
        self.assertGreater(range_row["covered_incidents_delta"], 0)
        self.assertGreater(range_row["delta_pp"], 0.0)

    def test_camera_unknown_los_is_declared_incomparable(self) -> None:
        incidents, sites = generate_inputs(self.config)
        result = fair_comparator(
            incidents=incidents,
            sites=sites,
            config=self.config,
            ttfrp=self.config.ttfrp_scenarios[0],
            weather=self.config.weather_scenarios[0],
        )
        self.assertEqual(result["comparison_status"], "INCOMPARABLE")
        self.assertEqual(
            result["camera_visibility_treatment"]["unknown_visibility_policy"],
            "DO_NOT_SCORE_AS_ZERO; DECLARE_INCOMPARABLE",
        )

    def test_shared_and_specific_comparator_gates_do_not_leak(self) -> None:
        low_confidence = incident().model_copy(update={"incident_confidence": 0.0})
        test_site = site()
        common = fair_comparator(
            incidents=[low_confidence],
            sites=[test_site],
            config=self.config,
            ttfrp=self.config.ttfrp_scenarios[0],
            weather=self.config.weather_scenarios[0],
        )
        self.assertEqual(common["stage_1_raw_physical_proxy"]["uas"]["covered_incidents"], 1)
        self.assertEqual(common["stage_1_raw_physical_proxy"]["camera"]["covered_incidents"], 1)
        self.assertEqual(
            common["stage_2_after_shared_incident_gates"]["uas"]["covered_incidents"], 0
        )
        self.assertEqual(
            common["stage_2_after_shared_incident_gates"]["camera"]["covered_incidents"], 0
        )

        camera_down = test_site.model_copy(update={"camera_available": False})
        camera_specific = fair_comparator(
            incidents=[incident()],
            sites=[camera_down],
            config=self.config,
            ttfrp=self.config.ttfrp_scenarios[0],
            weather=self.config.weather_scenarios[0],
        )["stage_3_after_architecture_specific_gates"]
        self.assertEqual(camera_specific["dock_only"]["covered_incidents"], 1)
        self.assertEqual(camera_specific["camera_optimistic_upper_bound"]["covered_incidents"], 0)

        uas_down = test_site.model_copy(update={"assumed_available": False})
        uas_specific = fair_comparator(
            incidents=[incident()],
            sites=[uas_down],
            config=self.config,
            ttfrp=self.config.ttfrp_scenarios[0],
            weather=self.config.weather_scenarios[0],
        )["stage_3_after_architecture_specific_gates"]
        self.assertEqual(uas_specific["dock_only"]["covered_incidents"], 0)
        self.assertEqual(uas_specific["camera_optimistic_upper_bound"]["covered_incidents"], 1)

    def test_site_stream_is_invariant_to_incident_sample_size(self) -> None:
        result = sample_size_audit(self.config)
        self.assertTrue(result["all_sites_unchanged"])

    def test_audit_verdict_uses_only_allowed_taxonomy(self) -> None:
        result = run_audit_experiment(self.config)
        self.assertIn(
            result["decision"]["status"],
            {
                "CONDITION_DEPENDENT_STRONG",
                "CONDITION_DEPENDENT_WEAK",
                "NEGATIVE_RESULT_NOT_ROBUST",
                "INCONCLUSIVE",
            },
        )

    def test_multi_seed_aggregate_is_deterministic_order_invariant_and_varies(self) -> None:
        compact = self.config.model_copy(
            update={"incident_count": 30, "robustness_seeds": (260803, 260804, 260805)}
        )
        forward = multi_seed_audit(compact)
        repeat = multi_seed_audit(compact)
        reversed_config = compact.model_copy(update={"robustness_seeds": (260805, 260804, 260803)})
        reversed_result = multi_seed_audit(reversed_config)
        self.assertEqual(forward, repeat)
        self.assertEqual(forward, reversed_result)
        self.assertGreater(len({row["a_coverage"] for row in forward["runs"]}), 1)

    def test_a01_sweep_is_monotone_and_reports_a_discrete_crossover(self) -> None:
        incidents, sites = generate_inputs(self.config)
        result = a01_sensitivity(
            incidents=incidents,
            sites=sites,
            config=self.config,
            ttfrp=self.config.ttfrp_scenarios[0],
            weather=self.config.weather_scenarios[0],
        )
        dominance = [row["travel_dominates_fraction"] for row in result["sweep"]]
        self.assertEqual(dominance, sorted(dominance, reverse=True))
        crossover = result["crossover_interval"]
        self.assertEqual(crossover["status"], "BRACKETED")
        self.assertEqual(
            crossover["upper_seconds"] - crossover["lower_seconds"],
            self.config.a01_sweep_step_seconds,
        )

    def test_f_aware_selection_is_deterministic(self) -> None:
        incidents, sites = generate_inputs(self.config)
        arguments = {
            "incidents": incidents,
            "sites": sites,
            "config": self.config,
            "ttfrp": self.config.ttfrp_scenarios[0],
            "weather": self.config.weather_scenarios[0],
        }
        self.assertEqual(f_aware_site_order(**arguments), f_aware_site_order(**arguments))


if __name__ == "__main__":
    unittest.main()

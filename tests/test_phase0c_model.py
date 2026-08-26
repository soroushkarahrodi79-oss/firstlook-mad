from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from firstlook_mad.cli import main
from firstlook_mad.domain import (
    CandidateSite,
    CoverageModel,
    EvidenceNature,
    GateOutcome,
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
        communications_available=True,
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
            include_airspace=True,
            include_weather=True,
            include_full_operations=True,
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
                include_airspace=True,
                include_weather=False,
                include_full_operations=False,
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


if __name__ == "__main__":
    unittest.main()

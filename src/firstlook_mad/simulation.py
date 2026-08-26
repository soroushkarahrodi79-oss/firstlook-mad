"""Progressive A-F coverage and TTFRP calculations."""

from __future__ import annotations

from firstlook_mad.domain import (
    CandidateSite,
    CoverageModel,
    FactorCheck,
    FactorState,
    GateOutcome,
    GateResult,
    Incident,
    PairEvaluation,
    TTFRPAssumptions,
    UASPerformanceProfile,
    WeatherScenario,
)
from firstlook_mad.geo import euclidean_distance_m
from firstlook_mad.safety import assess_gate


def _optimistic_gate(distance_m: float, max_one_way_m: float) -> GateResult:
    passed = distance_m <= max_one_way_m
    check = FactorCheck(
        factor="range",
        state=FactorState.PASS if passed else FactorState.FAIL,
        detail=f"distance={distance_m:.1f}; max_one_way={max_one_way_m:.1f}",
    )
    return GateResult(
        outcome=GateOutcome.GO_SIMULATION if passed else GateOutcome.NO_GO,
        primary_reason=None if passed else "range",
        checks=(check,),
    )


def evaluate_pair(
    *,
    incident: Incident,
    site: CandidateSite,
    profile: UASPerformanceProfile,
    ttfrp: TTFRPAssumptions,
    weather: WeatherScenario,
    model: CoverageModel,
    battery_fraction: float,
    max_data_age_minutes: float,
    minimum_incident_confidence: float,
) -> PairEvaluation:
    """Evaluate one synthetic incident/site pair with progressive constraints."""

    distance_m = euclidean_distance_m(incident.point, site.point)
    effective_distance_m = (
        distance_m * incident.terrain_multiplier
        if model
        in {
            CoverageModel.C_RELIEF,
            CoverageModel.D_AIRSPACE,
            CoverageModel.E_WEATHER,
            CoverageModel.F_ENERGY,
        }
        else distance_m
    )

    if model in {CoverageModel.A_DISTANCE, CoverageModel.B_TRAVEL_TIME, CoverageModel.C_RELIEF}:
        gate = _optimistic_gate(
            effective_distance_m,
            profile.max_sortie_distance_m / 2.0,
        )
    else:
        gate = assess_gate(
            incident=incident,
            site=site,
            profile=profile,
            weather=weather,
            effective_distance_m=effective_distance_m,
            battery_fraction=battery_fraction,
            max_data_age_minutes=max_data_age_minutes,
            minimum_incident_confidence=minimum_incident_confidence,
            include_airspace=True,
            include_weather=model in {CoverageModel.E_WEATHER, CoverageModel.F_ENERGY},
            include_full_operations=model is CoverageModel.F_ENERGY,
        )

    feasible = gate.outcome is GateOutcome.GO_SIMULATION
    if model is CoverageModel.A_DISTANCE or not feasible:
        travel_seconds = None
        total_seconds = None
    else:
        travel_seconds = effective_distance_m / profile.cruise_speed_mps
        total_seconds = ttfrp.non_travel_seconds + travel_seconds

    return PairEvaluation(
        incident_id=incident.incident_id,
        site_id=site.site_id,
        model=model,
        feasible=feasible,
        distance_m=distance_m,
        effective_distance_m=effective_distance_m,
        travel_seconds=travel_seconds,
        ttfrp_seconds=total_seconds,
        gate=gate,
    )

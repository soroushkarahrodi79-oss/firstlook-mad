"""Synthetic falsification experiments and transparent metrics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import median

from firstlook_mad.domain import (
    CandidateSite,
    CoverageModel,
    GatePolicy,
    Incident,
    PairEvaluation,
    SyntheticConfig,
    TTFRPAssumptions,
    UASPerformanceProfile,
    WeatherScenario,
)
from firstlook_mad.geo import euclidean_distance_m
from firstlook_mad.simulation import evaluate_pair
from firstlook_mad.synthetic import generate_inputs


@dataclass(frozen=True)
class NetworkOutcome:
    metrics: dict[str, object]
    best_by_incident: dict[str, PairEvaluation]


def _percentile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * probability)
    return ordered[index]


def greedy_site_order(
    incidents: list[Incident],
    sites: list[CandidateSite],
    max_one_way_m: float,
) -> list[CandidateSite]:
    """Greedy risk-weighted geometric coverage, deterministic under ties."""

    uncovered = {incident.incident_id for incident in incidents}
    remaining = list(sites)
    selected: list[CandidateSite] = []
    incident_by_id = {incident.incident_id: incident for incident in incidents}
    while remaining:
        ranked: list[tuple[float, str, CandidateSite, set[str]]] = []
        for site in remaining:
            covered = {
                incident_id
                for incident_id in uncovered
                if euclidean_distance_m(incident_by_id[incident_id].point, site.point)
                <= max_one_way_m
            }
            gain = sum(incident_by_id[item].risk_weight for item in covered)
            ranked.append((-gain, site.site_id, site, covered))
        _, _, winner, newly_covered = min(ranked, key=lambda item: (item[0], item[1]))
        selected.append(winner)
        remaining.remove(winner)
        uncovered -= newly_covered
    return selected


def evaluate_network(
    *,
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    model: CoverageModel,
    ttfrp: TTFRPAssumptions,
    weather: WeatherScenario,
    profile: UASPerformanceProfile | None = None,
    gate_policy: GatePolicy | None = None,
) -> NetworkOutcome:
    selected_profile = profile or config.reference_profile
    best_by_incident: dict[str, PairEvaluation] = {}
    pair_exclusions: Counter[str] = Counter()
    total_risk = sum(incident.risk_weight for incident in incidents)
    covered_risk = 0.0
    travel_seconds: list[float] = []
    ttfrp_seconds: list[float] = []

    for incident in incidents:
        evaluations = [
            evaluate_pair(
                incident=incident,
                site=site,
                profile=selected_profile,
                ttfrp=ttfrp,
                weather=weather,
                model=model,
                battery_fraction=config.battery_fraction,
                max_data_age_minutes=config.max_data_age_minutes,
                minimum_incident_confidence=config.minimum_incident_confidence,
                gate_policy=gate_policy,
            )
            for site in sites
        ]
        feasible = [item for item in evaluations if item.feasible]
        if feasible:
            if model is CoverageModel.A_DISTANCE:
                best = min(feasible, key=lambda item: (item.distance_m, item.site_id))
            else:
                best = min(
                    feasible,
                    key=lambda item: (
                        item.ttfrp_seconds if item.ttfrp_seconds is not None else float("inf"),
                        item.site_id,
                    ),
                )
            best_by_incident[incident.incident_id] = best
            covered_risk += incident.risk_weight
            if best.travel_seconds is not None:
                travel_seconds.append(best.travel_seconds)
            if best.ttfrp_seconds is not None:
                ttfrp_seconds.append(best.ttfrp_seconds)
        else:
            pair_exclusions.update(
                item.gate.primary_reason or "unclassified" for item in evaluations
            )

    metrics: dict[str, object] = {
        "model": model.value,
        "site_count": len(sites),
        "incident_count": len(incidents),
        "covered_incidents": len(best_by_incident),
        "risk_weighted_coverage": covered_risk / total_risk,
        "median_travel_seconds": median(travel_seconds) if travel_seconds else None,
        "median_ttfrp_seconds": median(ttfrp_seconds) if ttfrp_seconds else None,
        "p90_ttfrp_seconds": _percentile(ttfrp_seconds, 0.90),
        "pair_exclusions": dict(sorted(pair_exclusions.items())),
    }
    return NetworkOutcome(metrics=metrics, best_by_incident=best_by_incident)


def _camera_times(
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    ttfrp: TTFRPAssumptions,
) -> dict[str, float]:
    times: dict[str, float] = {}
    for incident in incidents:
        visible = any(
            site.assumed_available is True
            and euclidean_distance_m(incident.point, site.point) <= config.camera.radius_m
            for site in sites
        )
        if visible:
            times[incident.incident_id] = ttfrp.alert_processing_s + config.camera.picture_latency_s
    return times


def _alternative_metrics(
    *,
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    ttfrp: TTFRPAssumptions,
    weather: WeatherScenario,
) -> dict[str, object]:
    dock = evaluate_network(
        incidents=incidents,
        sites=sites,
        config=config,
        model=CoverageModel.F_ENERGY,
        ttfrp=ttfrp,
        weather=weather,
    )
    camera_times = _camera_times(incidents, sites, config, ttfrp)
    risk_by_id = {incident.incident_id: incident.risk_weight for incident in incidents}
    total_risk = sum(risk_by_id.values())
    dock_times = {
        incident_id: result.ttfrp_seconds
        for incident_id, result in dock.best_by_incident.items()
        if result.ttfrp_seconds is not None
    }
    hybrid_times: dict[str, float] = {}
    for incident_id in set(camera_times) | set(dock_times):
        candidates = [
            value
            for value in (camera_times.get(incident_id), dock_times.get(incident_id))
            if value is not None
        ]
        hybrid_times[incident_id] = min(candidates)

    def summarize(times: dict[str, float]) -> dict[str, object]:
        values = list(times.values())
        covered_risk = sum(risk_by_id[item] for item in times)
        return {
            "covered_incidents": len(times),
            "risk_weighted_coverage": covered_risk / total_risk,
            "median_ttfrp_seconds": median(values) if values else None,
            "p90_ttfrp_seconds": _percentile(values, 0.90),
        }

    return {
        "dock_only": summarize(dock_times),
        "camera_only": summarize(camera_times),
        "best_available_observation_proxy": summarize(hybrid_times),
        "warning": (
            "Camera radius/latency and picture equivalence are ASSUMED; "
            "this is not a cost or operational comparison."
        ),
    }


def run_experiment(config: SyntheticConfig) -> dict[str, object]:
    incidents, sites = generate_inputs(config)
    ordered_sites = greedy_site_order(
        incidents,
        sites,
        config.reference_profile.max_sortie_distance_m / 2.0,
    )
    central_ttfrp = config.ttfrp_scenarios[0]
    calm_weather = config.weather_scenarios[0]

    progressive: list[dict[str, object]] = []
    diminishing: list[dict[str, object]] = []
    for size in config.network_sizes:
        chosen = ordered_sites[:size]
        for model in CoverageModel:
            outcome = evaluate_network(
                incidents=incidents,
                sites=chosen,
                config=config,
                model=model,
                ttfrp=central_ttfrp,
                weather=calm_weather,
            )
            progressive.append(outcome.metrics)
        full = next(
            item
            for item in progressive
            if item["site_count"] == size and item["model"] == CoverageModel.F_ENERGY.value
        )
        diminishing.append(
            {
                "site_count": size,
                "risk_weighted_coverage": full["risk_weighted_coverage"],
            }
        )

    weather_erosion: list[dict[str, object]] = []
    largest_network = ordered_sites[: config.network_sizes[-1]]
    for weather in config.weather_scenarios:
        outcome = evaluate_network(
            incidents=incidents,
            sites=largest_network,
            config=config,
            model=CoverageModel.F_ENERGY,
            ttfrp=central_ttfrp,
            weather=weather,
        )
        weather_erosion.append({"weather_scenario": weather.scenario_id, **outcome.metrics})

    bottleneck: list[dict[str, object]] = []
    for ttfrp in config.ttfrp_scenarios:
        outcome = evaluate_network(
            incidents=incidents,
            sites=largest_network,
            config=config,
            model=CoverageModel.F_ENERGY,
            ttfrp=ttfrp,
            weather=calm_weather,
        )
        travel_values = [
            result.travel_seconds
            for result in outcome.best_by_incident.values()
            if result.travel_seconds is not None
        ]
        shares = [value / (value + ttfrp.non_travel_seconds) for value in travel_values]
        dominates = [value > ttfrp.non_travel_seconds for value in travel_values]
        bottleneck.append(
            {
                "ttfrp_scenario": ttfrp.scenario_id,
                "non_travel_seconds": ttfrp.non_travel_seconds,
                "feasible_incidents": len(travel_values),
                "median_travel_share": median(shares) if shares else None,
                "travel_dominates_fraction": (
                    sum(dominates) / len(dominates) if dominates else None
                ),
            }
        )

    profile_sensitivity: list[dict[str, object]] = []
    for profile in config.profiles:
        outcome = evaluate_network(
            incidents=incidents,
            sites=largest_network,
            config=config,
            model=CoverageModel.F_ENERGY,
            ttfrp=central_ttfrp,
            weather=calm_weather,
            profile=profile,
        )
        profile_sensitivity.append({"profile_id": profile.profile_id, **outcome.metrics})

    dominance_values = [item["travel_dominates_fraction"] for item in bottleneck]
    a01_interpretation = (
        "CONDITION_DEPENDENT"
        if any(isinstance(value, float) and value > 0.0 for value in dominance_values)
        else "WEAKENED_IN_TESTED_GRID"
    )
    alternatives = _alternative_metrics(
        incidents=incidents,
        sites=largest_network,
        config=config,
        ttfrp=central_ttfrp,
        weather=calm_weather,
    )

    return {
        "metadata": {
            "schema_version": "1.0",
            "phase": "0C",
            "scenario_id": config.scenario_id,
            "seed": config.seed,
            "crs": config.crs,
            "nature": config.nature.value,
            "assumptions_note": config.assumptions_note,
        },
        "evidence": {
            "incident_count": len(incidents),
            "candidate_site_count": len(sites),
            "selected_site_order": [site.site_id for site in ordered_sites],
            "progressive_models": progressive,
            "diminishing_returns": diminishing,
            "weather_erosion": weather_erosion,
            "bottleneck_test": bottleneck,
            "profile_sensitivity": profile_sensitivity,
            "alternative_comparison": alternatives,
        },
        "interpretation": {
            "A_01_travel_materiality": a01_interpretation,
            "limitations": [
                "All incidents, sites, timings and performance values are synthetic/assumed.",
                "No numerical threshold is used to declare material operational improvement.",
                "A gate pass means GO_SIMULATION, never authorization or safety to fly.",
                "The camera alternative ignores cost, line of sight, smoke and image equivalence.",
            ],
        },
        "decision": {
            "gate": "SYNTHETIC MODEL",
            "status": "MODEL_RUN_COMPLETE_NOT_OPERATIONAL_VALIDATION",
            "allowed_claim": "The deterministic falsification harness executed.",
            "prohibited_claim": "The results predict Madrid response or authorize operations.",
        },
    }

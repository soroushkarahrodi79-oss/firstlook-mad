"""Phase 0C.1 robustness and fair-comparator audit."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Any, cast

from firstlook_mad.domain import (
    CandidateSite,
    CoverageModel,
    GatePolicy,
    Incident,
    SyntheticConfig,
    TTFRPAssumptions,
    WeatherScenario,
)
from firstlook_mad.geo import euclidean_distance_m
from firstlook_mad.synthetic import generate_inputs
from firstlook_mad.validation import (
    NetworkOutcome,
    evaluate_network,
    greedy_site_order,
    run_experiment,
)

FACTOR_GROUPS = {
    "common_incident_factors": (
        "alert_processing",
        "incident_confidence",
        "data_freshness",
        "incident_existence_NOT_MODELED",
        "location_uncertainty_NOT_MODELED",
    ),
    "uas_specific_factors": (
        "range",
        "reserve",
        "site_availability",
        "uas_availability",
        "battery",
        "communications",
        "airspace",
        "temporary_restriction",
        "manned_aircraft_conflict",
        "weather",
    ),
    "camera_specific_factors": (
        "camera_radius",
        "camera_availability",
        "camera_communications",
        "line_of_sight_NOT_MODELED",
        "smoke_occlusion_NOT_MODELED",
        "observation_equivalence_NOT_ESTABLISHED",
    ),
}

ABLATION_FACTORS = tuple(GatePolicy.model_fields)
MAJORITY_THRESHOLD = 0.5
STRONG_CROSSOVER_SPAN_STEPS = 2


@dataclass(frozen=True)
class CoverageSet:
    incident_ids: frozenset[str]
    risk_weighted_coverage: float


def _percentile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * probability)]


def _robust_stats(values: list[float]) -> dict[str, float | None]:
    return {
        "median": median(values) if values else None,
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
        "p10": _percentile(values, 0.10),
        "p90": _percentile(values, 0.90),
    }


def _network_coverage(outcome: NetworkOutcome) -> float:
    value = outcome.metrics["risk_weighted_coverage"]
    if not isinstance(value, (int, float)):
        raise TypeError("risk_weighted_coverage must be numeric")
    return float(value)


def _coverage_set(incidents: list[Incident], incident_ids: set[str]) -> CoverageSet:
    total = sum(incident.risk_weight for incident in incidents)
    covered = sum(
        incident.risk_weight for incident in incidents if incident.incident_id in incident_ids
    )
    return CoverageSet(frozenset(incident_ids), covered / total)


def _coverage_document(incidents: list[Incident], incident_ids: set[str]) -> dict[str, object]:
    coverage = _coverage_set(incidents, incident_ids)
    return {
        "covered_incidents": len(coverage.incident_ids),
        "risk_weighted_coverage": coverage.risk_weighted_coverage,
    }


def _geometric_ids(
    incidents: list[Incident], sites: list[CandidateSite], radius_m: float
) -> set[str]:
    return {
        incident.incident_id
        for incident in incidents
        if any(euclidean_distance_m(incident.point, site.point) <= radius_m for site in sites)
    }


def _common_incident_passes(incident: Incident, config: SyntheticConfig) -> bool:
    return (
        incident.incident_confidence is not None
        and incident.incident_confidence >= config.minimum_incident_confidence
        and incident.data_age_minutes is not None
        and incident.data_age_minutes <= config.max_data_age_minutes
    )


def _summary_from_times(incidents: list[Incident], times: dict[str, float]) -> dict[str, object]:
    coverage = _coverage_set(incidents, set(times))
    values = list(times.values())
    return {
        "covered_incidents": len(times),
        "risk_weighted_coverage": coverage.risk_weighted_coverage,
        "median_latency_seconds": median(values) if values else None,
        "p90_latency_seconds": _percentile(values, 0.90),
    }


def fair_comparator(
    *,
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    ttfrp: TTFRPAssumptions,
    weather: WeatherScenario,
) -> dict[str, object]:
    """Compare aligned stages and state where the evidence cannot support ranking."""

    uas_raw_ids = _geometric_ids(
        incidents, sites, config.reference_profile.max_sortie_distance_m / 2.0
    )
    camera_raw_ids = _geometric_ids(incidents, sites, config.camera.radius_m)
    common_ids = {
        incident.incident_id for incident in incidents if _common_incident_passes(incident, config)
    }
    uas_shared = uas_raw_ids & common_ids
    camera_shared = camera_raw_ids & common_ids

    dock = evaluate_network(
        incidents=incidents,
        sites=sites,
        config=config,
        model=CoverageModel.F_ENERGY,
        ttfrp=ttfrp,
        weather=weather,
    )
    shared_latency = ttfrp.alert_processing_s + ttfrp.verification_s + ttfrp.first_analysis_s
    dock_times = {
        incident_id: shared_latency
        + ttfrp.preflight_gate_s
        + ttfrp.launch_s
        + ttfrp.scene_acquisition_s
        + (evaluation.travel_seconds or 0.0)
        for incident_id, evaluation in dock.best_by_incident.items()
    }
    camera_times: dict[str, float] = {}
    for incident in incidents:
        if incident.incident_id not in common_ids:
            continue
        available = any(
            site.camera_available is True
            and site.camera_communications_available is True
            and euclidean_distance_m(incident.point, site.point) <= config.camera.radius_m
            for site in sites
        )
        if available:
            camera_times[incident.incident_id] = (
                shared_latency
                + config.camera.architecture_specific_latency_s
                + config.camera.picture_latency_s
            )

    best_available = {
        incident_id: min(
            value
            for value in (dock_times.get(incident_id), camera_times.get(incident_id))
            if value is not None
        )
        for incident_id in set(dock_times) | set(camera_times)
    }
    return {
        "factor_contract": FACTOR_GROUPS,
        "latency_contract": {
            "shared": ("alert_processing_s", "verification_s", "first_analysis_s"),
            "uas_specific": (
                "preflight_gate_s",
                "launch_s",
                "travel_seconds",
                "scene_acquisition_s",
            ),
            "camera_specific": (
                "architecture_specific_latency_s",
                "picture_latency_s",
            ),
            "warning": "Latency components are ASSUMED and not empirically equivalent.",
        },
        "stage_1_raw_physical_proxy": {
            "uas": _coverage_document(incidents, uas_raw_ids),
            "camera": _coverage_document(incidents, camera_raw_ids),
            "status": "PHYSICAL_PROXY_ONLY",
        },
        "stage_2_after_shared_incident_gates": {
            "uas": _coverage_document(incidents, uas_shared),
            "camera": _coverage_document(incidents, camera_shared),
        },
        "stage_3_after_architecture_specific_gates": {
            "dock_only": _summary_from_times(incidents, dock_times),
            "camera_optimistic_upper_bound": _summary_from_times(incidents, camera_times),
            "best_available_observation_proxy": _summary_from_times(incidents, best_available),
        },
        "camera_visibility_treatment": {
            "CAMERA_OPTIMISTIC_NO_LOS_PENALTY": "reported as an upper bound",
            "CAMERA_UNKNOWN_LOS": "NOT_COMPARABLE_UNDER_MISSING_LOS_EVIDENCE",
            "unknown_visibility_policy": "DO_NOT_SCORE_AS_ZERO; DECLARE_INCOMPARABLE",
        },
        "comparison_status": "INCOMPARABLE",
        "prohibited_inference": (
            "No economic, operational-equivalence, or architecture-dominance claim is supported."
        ),
    }


def f_factor_ablation(
    *,
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    ttfrp: TTFRPAssumptions,
    weather: WeatherScenario,
) -> dict[str, object]:
    full = evaluate_network(
        incidents=incidents,
        sites=sites,
        config=config,
        model=CoverageModel.F_ENERGY,
        ttfrp=ttfrp,
        weather=weather,
    )
    rows: list[dict[str, object]] = []
    for factor in ABLATION_FACTORS:
        policy = GatePolicy().model_copy(update={factor: False})
        without = evaluate_network(
            incidents=incidents,
            sites=sites,
            config=config,
            model=CoverageModel.F_ENERGY,
            ttfrp=ttfrp,
            weather=weather,
            gate_policy=policy,
        )
        full_ids = set(full.best_by_incident)
        without_ids = set(without.best_by_incident)
        rows.append(
            {
                "factor_removed": factor,
                "coverage_with_all_factors": full.metrics["risk_weighted_coverage"],
                "coverage_with_factor": full.metrics["risk_weighted_coverage"],
                "coverage_without_factor": without.metrics["risk_weighted_coverage"],
                "delta_pp": 100.0 * (_network_coverage(without) - _network_coverage(full)),
                "marginal_effect_percentage_points": 100.0
                * (_network_coverage(without) - _network_coverage(full)),
                "additional_incidents_when_removed": len(without_ids - full_ids),
                "covered_incidents_delta": len(without_ids) - len(full_ids),
                "removal_never_reduces_survivors": full_ids <= without_ids,
                "notes": "marginal synthetic effect under this configuration",
            }
        )
    return {
        "method": "leave-one-factor-out from full F on a fixed incident/site cohort",
        "full_f": full.metrics,
        "rows": rows,
        "interaction_warning": (
            "Marginal effects overlap and do not sum to A→F erosion; this is not "
            "first-failure attribution or a causal decomposition."
        ),
    }


def f_aware_site_order(
    *,
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    ttfrp: TTFRPAssumptions,
    weather: WeatherScenario,
) -> list[CandidateSite]:
    selected: list[CandidateSite] = []
    remaining = list(sites)
    while remaining:
        ranked: list[tuple[float, str, CandidateSite]] = []
        for candidate in remaining:
            outcome = evaluate_network(
                incidents=incidents,
                sites=[*selected, candidate],
                config=config,
                model=CoverageModel.F_ENERGY,
                ttfrp=ttfrp,
                weather=weather,
            )
            ranked.append((-_network_coverage(outcome), candidate.site_id, candidate))
        _, _, winner = min(ranked, key=lambda item: (item[0], item[1]))
        selected.append(winner)
        remaining.remove(winner)
    return selected


def site_selection_comparison(
    *,
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    ttfrp: TTFRPAssumptions,
    weather: WeatherScenario,
) -> dict[str, object]:
    a_order = greedy_site_order(
        incidents, sites, config.reference_profile.max_sortie_distance_m / 2.0
    )
    f_order = f_aware_site_order(
        incidents=incidents,
        sites=sites,
        config=config,
        ttfrp=ttfrp,
        weather=weather,
    )
    rows: list[dict[str, object]] = []
    for size in config.network_sizes:
        a_outcome = evaluate_network(
            incidents=incidents,
            sites=a_order[:size],
            config=config,
            model=CoverageModel.F_ENERGY,
            ttfrp=ttfrp,
            weather=weather,
        )
        f_outcome = evaluate_network(
            incidents=incidents,
            sites=f_order[:size],
            config=config,
            model=CoverageModel.F_ENERGY,
            ttfrp=ttfrp,
            weather=weather,
        )
        a_ids = set(a_outcome.best_by_incident)
        f_ids = set(f_outcome.best_by_incident)
        union = a_ids | f_ids
        rows.append(
            {
                "site_count": size,
                "a_selected_sites": [site.site_id for site in a_order[:size]],
                "f_aware_selected_sites": [site.site_id for site in f_order[:size]],
                "a_selected_f_coverage": a_outcome.metrics["risk_weighted_coverage"],
                "f_aware_f_coverage": f_outcome.metrics["risk_weighted_coverage"],
                "coverage_gain_percentage_points": 100.0
                * (_network_coverage(f_outcome) - _network_coverage(a_outcome)),
                "survivor_jaccard": len(a_ids & f_ids) / len(union) if union else 1.0,
            }
        )
    return {
        "a_order": [site.site_id for site in a_order],
        "f_aware_order": [site.site_id for site in f_order],
        "rows": rows,
        "warning": "Both optimizers use synthetic incidents and candidate sites.",
    }


def a01_sensitivity(
    *,
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    ttfrp: TTFRPAssumptions,
    weather: WeatherScenario,
) -> dict[str, object]:
    outcome = evaluate_network(
        incidents=incidents,
        sites=sites,
        config=config,
        model=CoverageModel.F_ENERGY,
        ttfrp=ttfrp,
        weather=weather,
    )
    travel = sorted(
        evaluation.travel_seconds
        for evaluation in outcome.best_by_incident.values()
        if evaluation.travel_seconds is not None
    )
    sweep: list[dict[str, object]] = []
    majority: list[int] = []
    non_majority: list[int] = []
    for non_travel in range(0, config.a01_sweep_max_seconds + 1, config.a01_sweep_step_seconds):
        shares = [value / (value + non_travel) for value in travel]
        dominates_fraction = (
            sum(value > non_travel for value in travel) / len(travel) if travel else None
        )
        sweep.append(
            {
                "non_travel_seconds": non_travel,
                "fixed_f_survivors": len(travel),
                "feasible_incidents": len(travel),
                "median_travel_share": median(shares) if shares else None,
                "travel_dominates_fraction": dominates_fraction,
                "median_ttfrp_seconds": (
                    median(value + non_travel for value in travel) if travel else None
                ),
                "p90_ttfrp_seconds": (
                    _percentile([value + non_travel for value in travel], 0.90) if travel else None
                ),
            }
        )
        if dominates_fraction is not None and dominates_fraction > MAJORITY_THRESHOLD:
            majority.append(non_travel)
        elif dominates_fraction is not None:
            non_majority.append(non_travel)
    if majority and non_majority:
        crossover: dict[str, object] = {
            "status": "BRACKETED",
            "lower_seconds": max(value for value in majority if value < min(non_majority)),
            "upper_seconds": min(non_majority),
        }
    elif majority:
        crossover = {"status": "ABOVE_SWEEP", "lower_seconds": max(majority)}
    else:
        crossover = {"status": "AT_OR_BELOW_ZERO"}
    return {
        "cohort": "fixed full-F survivors; membership is not recomputed during latency sweep",
        "survivor_bias_warning": (
            "Results characterize only synthetic incidents already surviving every F gate."
        ),
        "sweep": sweep,
        "crossover_interval": crossover,
    }


def _seed_run(config: SyntheticConfig, seed: int) -> dict[str, object]:
    seeded = config.model_copy(update={"seed": seed})
    incidents, sites = generate_inputs(seeded)
    ttfrp = seeded.ttfrp_scenarios[0]
    weather = seeded.weather_scenarios[0]
    a_order = greedy_site_order(
        incidents, sites, seeded.reference_profile.max_sortie_distance_m / 2.0
    )
    selected = a_order[: seeded.network_sizes[-1]]
    a_outcome = evaluate_network(
        incidents=incidents,
        sites=selected,
        config=seeded,
        model=CoverageModel.A_DISTANCE,
        ttfrp=ttfrp,
        weather=weather,
    )
    f_outcome = evaluate_network(
        incidents=incidents,
        sites=selected,
        config=seeded,
        model=CoverageModel.F_ENERGY,
        ttfrp=ttfrp,
        weather=weather,
    )
    comparator = fair_comparator(
        incidents=incidents,
        sites=selected,
        config=seeded,
        ttfrp=ttfrp,
        weather=weather,
    )
    sensitivity = a01_sensitivity(
        incidents=incidents,
        sites=selected,
        config=seeded,
        ttfrp=ttfrp,
        weather=weather,
    )
    camera = cast(
        dict[str, dict[str, object]],
        comparator["stage_3_after_architecture_specific_gates"],
    )
    crossover = cast(dict[str, object], sensitivity["crossover_interval"])
    return {
        "seed": seed,
        "a_coverage": a_outcome.metrics["risk_weighted_coverage"],
        "f_coverage": f_outcome.metrics["risk_weighted_coverage"],
        "a_to_f_erosion_percentage_points": 100.0
        * (_network_coverage(a_outcome) - _network_coverage(f_outcome)),
        "camera_optimistic_coverage": camera["camera_optimistic_upper_bound"][
            "risk_weighted_coverage"
        ],
        "a01_crossover_lower_seconds": crossover.get("lower_seconds"),
        "a01_crossover_upper_seconds": crossover.get("upper_seconds"),
        "comparison_status": comparator["comparison_status"],
    }


def multi_seed_audit(config: SyntheticConfig) -> dict[str, object]:
    rows = [_seed_run(config, seed) for seed in sorted(set(config.robustness_seeds))]
    metric_names = (
        "a_coverage",
        "f_coverage",
        "a_to_f_erosion_percentage_points",
        "camera_optimistic_coverage",
        "a01_crossover_lower_seconds",
        "a01_crossover_upper_seconds",
    )
    summaries: dict[str, dict[str, float | None]] = {}
    for metric in metric_names:
        values: list[float] = []
        for row in rows:
            value = row[metric]
            if isinstance(value, (int, float)):
                values.append(float(value))
        summaries[metric] = _robust_stats(values)
    return {
        "seed_count": len(rows),
        "seeds": [row["seed"] for row in rows],
        "runs": rows,
        "summary": summaries,
        "all_comparisons_incomparable": all(
            row["comparison_status"] == "INCOMPARABLE" for row in rows
        ),
    }


def sample_size_audit(config: SyntheticConfig) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    reference_sites: list[CandidateSite] | None = None
    for sample_size in config.sample_sizes:
        sized = config.model_copy(update={"incident_count": sample_size})
        incidents, sites = generate_inputs(sized)
        if reference_sites is None:
            reference_sites = sites
        ordered = greedy_site_order(
            incidents, sites, sized.reference_profile.max_sortie_distance_m / 2.0
        )
        selected = ordered[: sized.network_sizes[-1]]
        a_outcome = evaluate_network(
            incidents=incidents,
            sites=selected,
            config=sized,
            model=CoverageModel.A_DISTANCE,
            ttfrp=sized.ttfrp_scenarios[0],
            weather=sized.weather_scenarios[0],
        )
        f_outcome = evaluate_network(
            incidents=incidents,
            sites=selected,
            config=sized,
            model=CoverageModel.F_ENERGY,
            ttfrp=sized.ttfrp_scenarios[0],
            weather=sized.weather_scenarios[0],
        )
        rows.append(
            {
                "incident_count": sample_size,
                "sites_unchanged": sites == reference_sites,
                "a_coverage": a_outcome.metrics["risk_weighted_coverage"],
                "f_coverage": f_outcome.metrics["risk_weighted_coverage"],
            }
        )
    return {"rows": rows, "all_sites_unchanged": all(row["sites_unchanged"] for row in rows)}


def run_audit_experiment(config: SyntheticConfig) -> dict[str, object]:
    original = cast(dict[str, Any], run_experiment(config))
    incidents, sites = generate_inputs(config)
    ttfrp = config.ttfrp_scenarios[0]
    weather = config.weather_scenarios[0]
    a_order = greedy_site_order(
        incidents, sites, config.reference_profile.max_sortie_distance_m / 2.0
    )
    selected = a_order[: config.network_sizes[-1]]
    ablation = f_factor_ablation(
        incidents=incidents,
        sites=selected,
        config=config,
        ttfrp=ttfrp,
        weather=weather,
    )
    comparator = fair_comparator(
        incidents=incidents,
        sites=selected,
        config=config,
        ttfrp=ttfrp,
        weather=weather,
    )
    multi_seed = multi_seed_audit(config)
    a01 = a01_sensitivity(
        incidents=incidents,
        sites=selected,
        config=config,
        ttfrp=ttfrp,
        weather=weather,
    )
    selection = site_selection_comparison(
        incidents=incidents,
        sites=sites,
        config=config,
        ttfrp=ttfrp,
        weather=weather,
    )
    multi_seed_document = cast(dict[str, Any], multi_seed)
    crossover_summary = multi_seed_document["summary"]["a01_crossover_lower_seconds"]
    crossover_range = float(crossover_summary["maximum"]) - float(crossover_summary["minimum"])
    a01_status = (
        "STRONGLY_CONDITION_DEPENDENT"
        if crossover_range >= config.a01_sweep_step_seconds * STRONG_CROSSOVER_SPAN_STEPS
        else "CONDITION_DEPENDENT"
    )
    erosion = multi_seed_document["summary"]["a_to_f_erosion_percentage_points"]
    verdict = (
        "CONDITION_DEPENDENT_STRONG"
        if float(erosion["minimum"]) > 0.0 and multi_seed_document["all_comparisons_incomparable"]
        else "CONDITION_DEPENDENT_WEAK"
    )
    robustness = {
        "ablation": ablation,
        "fair_comparator": comparator,
        "multi_seed": multi_seed,
        "a01_sensitivity": a01,
        "site_selection_comparison": selection,
        "sample_size_sensitivity": sample_size_audit(config),
        "randomness_invariants": {
            "site_stream_independent_of_incident_count": True,
            "deterministic_tie_breaking": "lexicographic site_id",
            "seed_ordering": "sorted unique integers",
        },
    }
    original["metadata"].update(
        {
            "schema_version": "1.1",
            "phase": "0C.1",
            "audit": "ROBUSTNESS_AND_FAIR_COMPARATOR",
            "robustness_seed_count": len(set(config.robustness_seeds)),
        }
    )
    original["evidence"]["robustness_audit"] = robustness
    original["interpretation"] = {
        "phase_0c_human_gate": "PASS WITH CONDITIONS — ROBUSTNESS AUDIT REQUIRED",
        "robustness_verdict": verdict,
        "A_01_status": a01_status,
        "biggest_correction": (
            "The original camera-versus-dock result is not a fair architecture ranking; "
            "under unknown line of sight it is an optimistic camera upper bound and the "
            "architectures remain incomparable."
        ),
        "limitations": [
            "Every UAS profile, latency, camera property, incident and site is ASSUMED/SYNTHETIC.",
            "Leave-one-out effects overlap and are not causal or additive.",
            "The A-01 sweep uses a fixed F-survivor cohort and is subject to survivor bias.",
            "No result represents real Madrid coverage, cost, authorization, or safety.",
        ],
    }
    original["decision"] = {
        "gate": "SYNTHETIC MODEL ROBUSTNESS AUDIT",
        "status": verdict,
        "A_01_status": a01_status,
        "allowed_claim": (
            "The negative reposition signal and travel-time crossover are condition-dependent "
            "within the declared synthetic experiment."
        ),
        "prohibited_claim": (
            "NO SUPPORT FOR BUILD; no architecture winner or Madrid operational coverage claim."
        ),
        "phase_0d": "STOP_PENDING_REVIEW_OF_DRAFT_PR_2",
    }
    return original

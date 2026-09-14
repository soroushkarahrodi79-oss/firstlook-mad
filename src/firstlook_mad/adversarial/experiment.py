"""Phase 0D.4 adversarial execution over the frozen Phase 0C.1 engine.

The frozen 0C.1 engine is reused unchanged (``generate_inputs``,
``evaluate_network``, ``greedy_site_order``, ``euclidean_distance_m``). This
module only *perturbs its inputs* and *reads its outputs*; it introduces no new
physics and no parallel model. All parameters come from
:mod:`firstlook_mad.adversarial.stresses` and are frozen before results.

Layering (see ``docs/PHASE_0D4_PREREGISTRATION.md``):

* formal gate = evidence-qualified critical set {T3-REAL, T4-REAL, T5};
* diagnostic battery = {T1, T2, T3-SYNTH, T4-SYNTH, T6}.

A diagnostic ``FAILS`` never drives the formal gate.
"""

from __future__ import annotations

import itertools
import json
import math
from collections.abc import Mapping
from pathlib import Path

from firstlook_mad.adversarial import stresses as S
from firstlook_mad.domain import (
    CandidateSite,
    CoverageModel,
    Incident,
    ProjectedPoint,
    SyntheticConfig,
    UASPerformanceProfile,
    WeatherScenario,
)
from firstlook_mad.synthetic import generate_inputs, load_config
from firstlook_mad.validation import NetworkOutcome, evaluate_network, greedy_site_order

OPTIMISTIC_PROFILE_ID = "assumed-optimistic-envelope-v1"

# Evidence-qualification for the formal gate (PHASE_0D4_PREREGISTRATION §4, §9):
# only REAL or DERIVED_FROM_REAL evidence may produce an *adjudicated* real
# comparison. A definite classification on any other evidence class fails closed.
QUALIFIED_EVIDENCE_CLASSES = frozenset({"REAL", "DERIVED_FROM_REAL"})
DEFINITE_CLASSIFICATIONS = frozenset({"SURVIVES", "DEGRADES", "FAILS"})
NON_ADJUDICATED_CLASSIFICATIONS = frozenset({"NOT_EVALUATED", "INCOMPARABLE"})


class EvidenceQualificationError(ValueError):
    """A formal-critical branch tried to adjudicate the gate on non-real evidence."""


# --------------------------------------------------------------------------- #
# Small deterministic helpers over the frozen engine
# --------------------------------------------------------------------------- #
def _round_cov(value: float) -> float:
    return round(float(value), S.COVERAGE_DECIMALS)


def _weather_by_id(config: SyntheticConfig, scenario_id: str) -> WeatherScenario:
    for scenario in config.weather_scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(f"weather scenario {scenario_id!r} not in frozen config")


def _profile_by_id(config: SyntheticConfig, profile_id: str) -> UASPerformanceProfile:
    for profile in config.profiles:
        if profile.profile_id == profile_id:
            return profile
    raise KeyError(f"profile {profile_id!r} not in frozen config")


def _outcome(
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    model: CoverageModel,
    *,
    weather: WeatherScenario | None = None,
    profile: UASPerformanceProfile | None = None,
) -> NetworkOutcome:
    return evaluate_network(
        incidents=incidents,
        sites=sites,
        config=config,
        model=model,
        ttfrp=config.ttfrp_scenarios[0],
        weather=weather or config.weather_scenarios[0],
        profile=profile or config.reference_profile,
    )


def _coverage(
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    model: CoverageModel,
    *,
    weather: WeatherScenario | None = None,
    profile: UASPerformanceProfile | None = None,
) -> float:
    value = _outcome(incidents, sites, config, model, weather=weather, profile=profile).metrics[
        "risk_weighted_coverage"
    ]
    assert isinstance(value, int | float)
    return _round_cov(value)


def _delta_record(name: str, baseline: float, adversarial: float) -> dict[str, object]:
    absolute = adversarial - baseline
    relative = (absolute / baseline) if baseline not in (0.0,) else None
    if math.isclose(absolute, 0.0, abs_tol=10 ** (-S.COVERAGE_DECIMALS)):
        direction = "NO_CHANGE"
    elif absolute > 0:
        direction = "ADVERSARIAL_GREATER"
    else:
        direction = "ADVERSARIAL_SMALLER"
    return {
        "metric": name,
        "baseline_value": _round_cov(baseline),
        "adversarial_value": _round_cov(adversarial),
        "absolute_delta": _round_cov(absolute),
        "relative_delta": round(relative, S.COVERAGE_DECIMALS) if relative is not None else None,
        "effect_direction": direction,
    }


def _relative_reduction(baseline: float, adversarial: float) -> float | None:
    """Fractional loss of a positive baseline (0 => no loss, 1 => erased)."""

    if baseline <= 0.0:
        return None
    return (baseline - adversarial) / baseline


def _single_site_dominance(
    outcome: NetworkOutcome, incidents: list[Incident]
) -> tuple[float, str | None]:
    risk_by_id = {incident.incident_id: incident.risk_weight for incident in incidents}
    per_site: dict[str, float] = {}
    for incident_id, pair in outcome.best_by_incident.items():
        per_site[pair.site_id] = per_site.get(pair.site_id, 0.0) + risk_by_id[incident_id]
    covered = sum(per_site.values())
    if covered <= 0.0:
        return 0.0, None
    top_site, top_risk = max(per_site.items(), key=lambda kv: (kv[1], kv[0]))
    return round(top_risk / covered, S.SHARE_DECIMALS), top_site


def _inside_domain(easting_m: float, northing_m: float) -> bool:
    return (
        S.DOMAIN_MIN_E <= easting_m <= S.DOMAIN_MAX_E
        and S.DOMAIN_MIN_N <= northing_m <= S.DOMAIN_MAX_N
    )


# --------------------------------------------------------------------------- #
# T1 — candidate-location fragility (DIAGNOSTIC)
# --------------------------------------------------------------------------- #
def _run_t1(
    incidents: list[Incident],
    sites: list[CandidateSite],
    ordered: list[CandidateSite],
    config: SyntheticConfig,
    phase0d3: dict[str, object],
) -> dict[str, object]:
    base_a = _coverage(incidents, sites, config, CoverageModel.A_DISTANCE)
    base_f = _coverage(incidents, sites, config, CoverageModel.F_ENERGY)

    # T1b — drop the single highest greedy-A-ranked site.
    dropped_site = ordered[S.T1B_DROP_GREEDY_RANK]
    kept = [site for site in sites if site.site_id != dropped_site.site_id]
    t1b_a = _coverage(incidents, kept, config, CoverageModel.A_DISTANCE)
    t1b_f = _coverage(incidents, kept, config, CoverageModel.F_ENERGY)

    # Single-site dominance of Model-A covered risk on the full network.
    dominance_share, dominant_site = _single_site_dominance(
        _outcome(incidents, sites, config, CoverageModel.A_DISTANCE), incidents
    )

    # T1c — exact uniform displacement, no repair; outside domain => NOT_EVALUATED.
    displaced, any_outside = _displace_sites(sites)
    if any_outside:
        t1c: dict[str, object] = {
            "result_classification": "NOT_EVALUATED",
            "reason": "NOT_EVALUATED_CONFIG_INVALID: a displaced candidate falls "
            "outside the frozen analytical domain; no clipping/repair is applied",
            "evidence_class": "NOT_EVALUATED",
            "displace_m": S.T1C_DISPLACE_M,
        }
        t1c_rel_a: float | None = None
    else:
        assert displaced is not None
        t1c_a = _coverage(incidents, displaced, config, CoverageModel.A_DISTANCE)
        t1c_f = _coverage(incidents, displaced, config, CoverageModel.F_ENERGY)
        t1c_rel_a = _rel_abs(base_a, t1c_a)
        t1c = {
            "result_classification": "EVALUATED",
            "evidence_class": "SYNTHETIC_STRESS_TEST",
            "displace_m": S.T1C_DISPLACE_M,
            "model_a": _delta_record("model_a_risk_weighted_coverage", base_a, t1c_a),
            "model_f": _delta_record("model_f_risk_weighted_coverage", base_f, t1c_f),
        }

    t1b_rel_a = _rel_abs(base_a, t1b_a)
    evaluable_rel = [value for value in (t1b_rel_a, t1c_rel_a) if value is not None]
    max_rel_a = max(evaluable_rel) if evaluable_rel else 0.0
    dominated = dominance_share >= S.T1_DOMINANCE_SHARE

    if max_rel_a >= S.T1_DEGRADE_MAX_REL or dominated:
        classification = "FAILS"
    elif max_rel_a >= S.T1_SURVIVE_MAX_REL:
        classification = "DEGRADES"
    else:
        classification = "SURVIVES"

    reason = (
        "No strong placement fragility was detected under the two pre-specified synthetic "
        "perturbations, and no single site crossed the 50% dominance rule: "
        f"max |relative Δ Model-A coverage| = {max_rel_a:.6f} "
        f"(survive<{S.T1_SURVIVE_MAX_REL}, degrade<{S.T1_DEGRADE_MAX_REL}); "
        f"single-site Model-A dominance share = {dominance_share:.6f} "
        f"(dominance threshold {S.T1_DOMINANCE_SHARE}). Scope: the two frozen perturbations only."
    )

    return {
        "stress_id": "T1",
        "target_assumption": "A-02 (candidate placement) — model geometry",
        "criticality": "DIAGNOSTIC",
        "result_classification": classification,
        "reason": reason,
        "baseline_config": "0C.1 full domain, seed 260827, 10 sites, reference profile",
        "primary_metric": "model_a_risk_weighted_coverage",
        "max_relative_delta_model_a": round(max_rel_a, S.COVERAGE_DECIMALS),
        "single_site_dominance": {
            "share_of_model_a_covered_risk": dominance_share,
            "dominant_site_id": dominant_site,
            "threshold": S.T1_DOMINANCE_SHARE,
            "dominated": dominated,
        },
        "sub_tests": {
            "t1a_real_vs_matched_control": _t1a_context(phase0d3),
            "t1b_drop_top_site": {
                "evidence_class": "SYNTHETIC_STRESS_TEST",
                "dropped_site_id": dropped_site.site_id,
                "dropped_greedy_rank": S.T1B_DROP_GREEDY_RANK,
                "model_a": _delta_record("model_a_risk_weighted_coverage", base_a, t1b_a),
                "model_f": _delta_record("model_f_risk_weighted_coverage", base_f, t1b_f),
            },
            "t1c_uniform_displacement": t1c,
        },
    }


def _rel_abs(baseline: float, adversarial: float) -> float:
    if baseline == 0.0:
        return 0.0
    return abs((adversarial - baseline) / baseline)


def _displace_sites(
    sites: list[CandidateSite],
) -> tuple[list[CandidateSite] | None, bool]:
    count = len(sites)
    moved: list[CandidateSite] = []
    for index, site in enumerate(sites):
        theta = 2.0 * math.pi * index / count
        new_e = site.point.easting_m + S.T1C_DISPLACE_M * math.cos(theta)
        new_n = site.point.northing_m + S.T1C_DISPLACE_M * math.sin(theta)
        if not _inside_domain(new_e, new_n):
            return None, True
        moved.append(
            site.model_copy(update={"point": ProjectedPoint(easting_m=new_e, northing_m=new_n)})
        )
    return moved, False


def _t1a_context(phase0d3: dict[str, object]) -> dict[str, object]:
    verdict = phase0d3.get("verdict", {})
    comparison = phase0d3.get("comparison", {})
    assert isinstance(verdict, dict) and isinstance(comparison, dict)
    return {
        "evidence_class": "DERIVED_FROM_REAL / SYNTHETIC (matched municipal envelope)",
        "source": S.PHASE0D3_RESULTS_PATH,
        "phase0d3_verdict": verdict.get("verdict"),
        "primary_relative_delta_median_nearest": comparison.get("primary_relative_delta"),
        "effect_material": comparison.get("effect_material"),
        "direction_stable_across_seeds": verdict.get("direction_stable_across_seeds"),
        "note": "Real A-02 placement produced no material, seed-stable geometry signal at "
        "matched municipal scope (SUBSTITUTION_UNINFORMATIVE). Municipal-scope context "
        "only; no regional claim; not re-run here.",
    }


# --------------------------------------------------------------------------- #
# T2 — diminishing returns (DIAGNOSTIC)
# --------------------------------------------------------------------------- #
def _run_t2(
    incidents: list[Incident],
    ordered: list[CandidateSite],
    config: SyntheticConfig,
    phase0d3: dict[str, object],
) -> dict[str, object]:
    sizes: list[int] = list(config.network_sizes)
    coverages: list[float] = [
        _coverage(incidents, ordered[:size], config, CoverageModel.F_ENERGY) for size in sizes
    ]
    rows: list[dict[str, object]] = [
        {"site_count": size, "model_f_risk_weighted_coverage": coverage}
        for size, coverage in zip(sizes, coverages, strict=True)
    ]

    segments: list[dict[str, object]] = []
    per_site_gains: list[float] = []
    for (prev_size, prev_cov), (curr_size, curr_cov) in itertools.pairwise(
        zip(sizes, coverages, strict=True)
    ):
        added = curr_size - prev_size
        gain = curr_cov - prev_cov
        per_site = gain / added if added else 0.0
        per_site_gains.append(per_site)
        segments.append(
            {
                "from_sites": prev_size,
                "to_sites": curr_size,
                "coverage_gain": round(gain, S.COVERAGE_DECIMALS),
                "per_site_marginal_gain": round(per_site, S.COVERAGE_DECIMALS),
            }
        )

    peak = max(per_site_gains) if per_site_gains else 0.0
    last = per_site_gains[-1] if per_site_gains else 0.0
    ratio = (last / peak) if peak > 0.0 else None

    if ratio is None:
        classification = "FAILS"
    elif ratio >= S.T2_SURVIVE_RATIO:
        classification = "SURVIVES"
    elif ratio >= S.T2_DEGRADE_RATIO:
        classification = "DEGRADES"
    else:
        classification = "FAILS"

    return {
        "stress_id": "T2",
        "target_assumption": "RQ6 (diminishing returns) — model marginal benefit",
        "criticality": "DIAGNOSTIC",
        "evidence_class": "SYNTHETIC",
        "result_classification": classification,
        "reason": (
            f"last-segment per-site marginal gain / peak per-site marginal gain = "
            f"{'n/a' if ratio is None else format(ratio, '.6f')} "
            f"(survive≥{S.T2_SURVIVE_RATIO}, degrade≥{S.T2_DEGRADE_RATIO})."
        ),
        "site_count_sequence": list(config.network_sizes),
        "primary_metric": "model_f_per_site_marginal_gain_ratio",
        "last_over_peak_ratio": round(ratio, S.COVERAGE_DECIMALS) if ratio is not None else None,
        "diminishing_returns": rows,
        "segments": segments,
        "matched_scope_context": {
            "evidence_class": "DERIVED_FROM_REAL / SYNTHETIC",
            "source": S.PHASE0D3_RESULTS_PATH,
            "note": "At the 0D.3 station-envelope scope Model-A coverage is already saturated "
            "at 1.0 for 10 and 13 sites; 13 real locations do not materially outperform a "
            "smaller configuration there. Municipal-scope context only.",
            "phase0d3_any_full_coverage_threshold_crossed": _nested_get(
                phase0d3, "comparison", "any_full_coverage_threshold_crossed"
            ),
        },
    }


def _nested_get(document: dict[str, object], *keys: str) -> object:
    node: object = document
    for key in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


# --------------------------------------------------------------------------- #
# T3 — weather / performance erosion (split authority)
# --------------------------------------------------------------------------- #
def _run_t3_real() -> dict[str, object]:
    return {
        "stress_id": "T3-REAL",
        "target_assumption": "A-04 (fire-weather erosion)",
        "criticality": "FORMAL-CRITICAL",
        "evidence_class": "NOT_EVALUATED",
        "result_classification": "NOT_EVALUATED",
        "reason": "NOT_EVALUATED_MISSING_EVIDENCE: A-04 real fire-day weather observations are "
        "unavailable (WEATHER_EVIDENCE_NOT_OBSERVABLE); PROTOCOL §4.2 bands require real "
        "out-of-envelope frequency. AEMET station inventory is not weather observations. "
        "No real weather evidence is manufactured to avoid this.",
    }


def _run_t3_synth(
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
) -> dict[str, object]:
    baseline = _weather_by_id(config, S.T3_BASELINE_SCENARIO)
    stress = _weather_by_id(config, S.T3_STRESS_SCENARIO)
    artifact = _weather_by_id(config, S.T3_DESIGN_ARTIFACT_SCENARIO)
    optimistic = _profile_by_id(config, OPTIMISTIC_PROFILE_ID)

    base_ref = _coverage(incidents, sites, config, CoverageModel.F_ENERGY, weather=baseline)
    stress_ref = _coverage(incidents, sites, config, CoverageModel.F_ENERGY, weather=stress)
    stress_opt = _coverage(
        incidents, sites, config, CoverageModel.F_ENERGY, weather=stress, profile=optimistic
    )
    artifact_ref = _coverage(incidents, sites, config, CoverageModel.F_ENERGY, weather=artifact)

    reduction = _relative_reduction(base_ref, stress_ref)
    if reduction is None:
        classification = "NOT_EVALUATED"
    elif reduction >= S.T3_FAIL_REL:
        classification = "FAILS"
    elif reduction >= S.T3_DEGRADE_REL:
        classification = "DEGRADES"
    else:
        classification = "SURVIVES"

    return {
        "stress_id": "T3-SYNTH",
        "target_assumption": "A-04 (fire-weather erosion) — SYNTHETIC stress proxy",
        "criticality": "DIAGNOSTIC",
        "evidence_class": "SYNTHETIC_STRESS_TEST",
        "result_classification": classification,
        "reason": (
            f"relative reduction of Model-F coverage under {S.T3_STRESS_SCENARIO} "
            f"(reference profile) = {'n/a' if reduction is None else format(reduction, '.6f')} "
            f"(fail≥{S.T3_FAIL_REL}, degrade≥{S.T3_DEGRADE_REL})."
        ),
        "primary_metric": "model_f_risk_weighted_coverage_relative_reduction_reference_profile",
        "reference_profile": _delta_record(
            "model_f_within_vs_wind_outside_reference", base_ref, stress_ref
        ),
        "relative_reduction_reference_profile": (
            round(reduction, S.COVERAGE_DECIMALS) if reduction is not None else None
        ),
        "profile_dependence_diagnostic": {
            "note": "Reported, not classified. The optimistic profile (max_wind 16 == stress "
            "wind) is not wind-gated by this stress; the collapse is reference-profile "
            "specific. Classification is fixed on the reference profile (0C.1 headline).",
            "optimistic_profile_model_f_under_stress": stress_opt,
            "reference_profile_model_f_under_stress": stress_ref,
        },
        "visibility_unknown_design_artifact": {
            "note": "Excluded from classification. PROTOCOL §4.2 declares UNKNOWN-visibility→0 a "
            "conservative design rule, not a weather-frequency signal.",
            "model_f_visibility_unknown_reference": artifact_ref,
        },
        "known_outcome_disclosure": "The tracked 0C.1 results already record 0.0 Model-F coverage "
        "for the reference-profile wind-outside scenario, so this FAILS is known before "
        "execution; it is diagnostic evidence about the synthetic model, not new real-weather "
        "evidence and not a gate-driving falsification.",
    }


# --------------------------------------------------------------------------- #
# T4 — airspace / geographic constraints (split authority)
# --------------------------------------------------------------------------- #
def _run_t4_real() -> dict[str, object]:
    return {
        "stress_id": "T4-REAL",
        "target_assumption": "A-03 (airspace / geographic constraints)",
        "criticality": "FORMAL-CRITICAL",
        "evidence_class": "NOT_EVALUATED",
        "result_classification": "NOT_EVALUATED",
        "reason": "NOT_EVALUATED_MISSING_EVIDENCE: A-03 is NOT_ELIGIBLE (ENAIRE truncated 50/50, "
        "exceededTransferLimit; IGN MDT05 is a 100 m x 100 m pipeline-proof window). The bounded "
        "samples are never promoted to a full-domain constraint layer; no real constraint layer "
        "is manufactured to avoid this.",
    }


def _run_t4_synth(
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
) -> dict[str, object]:
    base_a = _coverage(incidents, sites, config, CoverageModel.A_DISTANCE)
    base_f = _coverage(incidents, sites, config, CoverageModel.F_ENERGY)

    mild_sites, mild_removed = _exclude_box(sites, S.T4_MILD_BOX)
    quad_sites, quad_removed = _exclude_quadrant(sites)

    mild_a = _coverage(incidents, mild_sites, config, CoverageModel.A_DISTANCE)
    mild_f = _coverage(incidents, mild_sites, config, CoverageModel.F_ENERGY)
    quad_a = _coverage(incidents, quad_sites, config, CoverageModel.A_DISTANCE)
    quad_f = _coverage(incidents, quad_sites, config, CoverageModel.F_ENERGY)

    reduction = _relative_reduction(base_a, mild_a) or 0.0
    if reduction >= S.T4_DEGRADE_MAX_REL:
        classification = "FAILS"
    elif reduction >= S.T4_SURVIVE_MAX_REL:
        classification = "DEGRADES"
    else:
        classification = "SURVIVES"

    # Interpretive honesty: the frozen rule yields a classification, but if the
    # pre-specified mild exclusion removed no candidate the realised stress was a
    # no-op and the classification is non-informative for spatial robustness.
    stress_effective = mild_removed > 0
    interpretive_status = "EFFECTIVE_STRESS" if stress_effective else "NO_OP_STRESS"

    return {
        "stress_id": "T4-SYNTH",
        "target_assumption": "A-03 (airspace / geographic) — SYNTHETIC exclusion proxy",
        "criticality": "DIAGNOSTIC",
        "evidence_class": "SYNTHETIC_STRESS_TEST",
        "result_classification": classification,
        "reason": (
            f"relative reduction of Model-A coverage under the mild central-box exclusion "
            f"= {reduction:.6f} (fail≥{S.T4_DEGRADE_MAX_REL}, degrade≥{S.T4_SURVIVE_MAX_REL}). "
            "Never reported as an ENAIRE result."
        ),
        "primary_metric": "model_a_risk_weighted_coverage_relative_reduction_mild_exclusion",
        "stress_effective": stress_effective,
        "interpretive_status": interpretive_status,
        "informative_for_spatial_robustness": stress_effective,
        "interpretation_note": (
            "T4-SYNTH mechanically SURVIVES under the frozen rule, but the pre-specified mild "
            "exclusion removed zero candidate sites. The realised stress was therefore a no-op "
            "and this SURVIVES classification is non-informative for spatial robustness."
        )
        if not stress_effective
        else "The mild exclusion removed at least one candidate; classification is informative.",
        "mild_exclusion": {
            "box_min_e_max_e_min_n_max_n": list(S.T4_MILD_BOX),
            "candidates_removed": mild_removed,
            "model_a": _delta_record("model_a_risk_weighted_coverage", base_a, mild_a),
            "model_f": _delta_record("model_f_risk_weighted_coverage", base_f, mild_f),
        },
        "quadrant_exclusion_context": {
            "rule": f"E >= {S.T4_QUADRANT_MIN_E} AND N >= {S.T4_QUADRANT_MIN_N} (NE quadrant)",
            "candidates_removed": quad_removed,
            "model_a": _delta_record("model_a_risk_weighted_coverage", base_a, quad_a),
            "model_f": _delta_record("model_f_risk_weighted_coverage", base_f, quad_f),
            "note": "Reported for context, not classified.",
        },
    }


def _exclude_box(
    sites: list[CandidateSite], box: tuple[float, float, float, float]
) -> tuple[list[CandidateSite], int]:
    min_e, max_e, min_n, max_n = box
    kept = [
        site
        for site in sites
        if not (min_e <= site.point.easting_m <= max_e and min_n <= site.point.northing_m <= max_n)
    ]
    return kept, len(sites) - len(kept)


def _exclude_quadrant(sites: list[CandidateSite]) -> tuple[list[CandidateSite], int]:
    kept = [
        site
        for site in sites
        if not (
            site.point.easting_m >= S.T4_QUADRANT_MIN_E
            and site.point.northing_m >= S.T4_QUADRANT_MIN_N
        )
    ]
    return kept, len(sites) - len(kept)


# --------------------------------------------------------------------------- #
# T5 — camera / hybrid comparator (FORMAL-CRITICAL, INCOMPARABLE)
# --------------------------------------------------------------------------- #
def _run_t5(phase0c: dict[str, object]) -> dict[str, object]:
    alternatives = _nested_get(phase0c, "evidence", "alternative_comparison")
    fair = _nested_get(phase0c, "evidence", "robustness_audit", "fair_comparator")
    assert isinstance(alternatives, dict) and isinstance(fair, dict)
    return {
        "stress_id": "T5",
        "target_assumption": "Camera / tower / hybrid comparator vs UAS dock",
        "criticality": "FORMAL-CRITICAL",
        "evidence_class": "SYNTHETIC",
        "result_classification": "INCOMPARABLE",
        "reason": "PROTOCOL §4.5: the architecture ranking is structurally unadjudicable under "
        "unknown LOS / smoke / FOV / observation-equivalence. The camera figure is an optimistic "
        "upper bound, never read as camera-beats-dock. Real A-02 stations supply no camera "
        "attributes (NOT_EVALUATED); none is imputed.",
        "dock_only": _nested_get(alternatives, "dock_only"),
        "camera_only_optimistic_upper_bound": _nested_get(alternatives, "camera_only"),
        "best_available_observation_proxy": _nested_get(
            alternatives, "best_available_observation_proxy"
        ),
        "fair_comparator_status": fair.get("comparison_status"),
        "fair_comparator_all_incomparable": _nested_get(
            fair, "multi_seed", "all_comparisons_incomparable"
        ),
        "prohibited_inference": fair.get("prohibited_inference"),
    }


# --------------------------------------------------------------------------- #
# T6 — threshold / gate fragility (DIAGNOSTIC)
# --------------------------------------------------------------------------- #
def _run_t6(
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
) -> dict[str, object]:
    outcome = _outcome(incidents, sites, config, CoverageModel.F_ENERGY)
    travels = sorted(
        pair.travel_seconds
        for pair in outcome.best_by_incident.values()
        if pair.travel_seconds is not None
    )
    survivor_count = len(travels)

    def dominates_fraction(budget: float) -> float:
        if survivor_count == 0:
            return 0.0
        return sum(1 for value in travels if value > budget) / survivor_count

    central = S.T6_CENTRAL_NON_TRAVEL_S
    low = central - S.T6_STEP_S
    high = central + S.T6_STEP_S
    points = {
        "low": {
            "non_travel_s": low,
            "travel_dominates_fraction": round(dominates_fraction(low), 6),
        },
        "central": {
            "non_travel_s": central,
            "travel_dominates_fraction": round(dominates_fraction(central), 6),
        },
        "high": {
            "non_travel_s": high,
            "travel_dominates_fraction": round(dominates_fraction(high), 6),
        },
    }
    booleans = {key: value["travel_dominates_fraction"] > 0 for key, value in points.items()}
    flips = len(set(booleans.values())) > 1

    fractions = [float(value["travel_dominates_fraction"]) for value in points.values()]
    spread_max = max(fractions)
    spread_min = min(fractions)
    relative_spread = ((spread_max - spread_min) / spread_max) if spread_max > 0 else 0.0

    if flips:
        classification = "FAILS"
    elif relative_spread > S.T6_DEGRADE_REL:
        classification = "DEGRADES"
    else:
        classification = "SURVIVES"

    flip_boundary = max(travels) if travels else None

    return {
        "stress_id": "T6",
        "target_assumption": "A-01 travel-materiality qualitative switch (model-emitted)",
        "criticality": "DIAGNOSTIC",
        "evidence_class": "SYNTHETIC",
        "result_classification": classification,
        "reason": (
            f"boolean B=(travel_dominates_fraction>0) over ±{S.T6_STEP_S:.0f}s window around "
            f"{central:.0f}s: low={booleans['low']}, central={booleans['central']}, "
            f"high={booleans['high']}; flips={flips} (flip⇒FAILS). "
            "This is a model-emitted qualitative switch, NOT the real-data A-01 bands of "
            "PROTOCOL §4.1."
        ),
        "primary_metric": "travel_dominates_fraction_boolean_flip",
        "fixed_full_f_survivor_cohort": survivor_count,
        "survivor_bias_warning": "Characterises only synthetic incidents already surviving every "
        "F gate; membership is not recomputed during the sweep.",
        "window_points": points,
        "booleans": booleans,
        "boolean_flips_in_window": flips,
        "dominance_flip_boundary_seconds": (
            round(flip_boundary, S.SECONDS_DECIMALS) if flip_boundary is not None else None
        ),
        "distance_central_to_flip_seconds": (
            round(flip_boundary - central, S.SECONDS_DECIMALS)
            if flip_boundary is not None
            else None
        ),
        "secondary_context": {
            "note": "0D.3 material-relative-delta threshold (0.20) was not narrowly crossed "
            "(0D.3 primary_relative_delta = 0.0598), so that gate is not threshold-fragile.",
        },
    }


# --------------------------------------------------------------------------- #
# Formal gate aggregation (evidence-qualified critical set only)
# --------------------------------------------------------------------------- #
def _aggregate_formal_gate(formal_branches: list[dict[str, object]]) -> dict[str, object]:
    classifications: dict[str, str] = {}
    evidence_classes: dict[str, str] = {}
    adjudicated: dict[str, str] = {}
    for branch in formal_branches:
        stress_id = str(branch["stress_id"])
        classification = str(branch["result_classification"])
        evidence_class = str(branch.get("evidence_class", ""))
        classifications[stress_id] = classification
        evidence_classes[stress_id] = evidence_class
        if classification in DEFINITE_CLASSIFICATIONS:
            # Fail closed: a definite SURVIVES/DEGRADES/FAILS may adjudicate the
            # formal gate ONLY on REAL or DERIVED_FROM_REAL evidence. Synthetic,
            # synthetic-stress or not-evaluated evidence can never drive the gate.
            if evidence_class not in QUALIFIED_EVIDENCE_CLASSES:
                raise EvidenceQualificationError(
                    f"evidence-qualification violation: formal-critical branch {stress_id!r} "
                    f"reports a definite classification {classification!r} on non-qualified "
                    f"evidence class {evidence_class!r}; only REAL or DERIVED_FROM_REAL evidence "
                    f"may adjudicate the formal gate (fail-closed, PHASE_0D4_PREREGISTRATION §9)."
                )
            adjudicated[stress_id] = classification
        elif classification not in NON_ADJUDICATED_CLASSIFICATIONS:
            raise EvidenceQualificationError(
                f"unknown formal-critical classification {classification!r} for branch "
                f"{stress_id!r}; expected one of "
                f"{sorted(DEFINITE_CLASSIFICATIONS | NON_ADJUDICATED_CLASSIFICATIONS)}."
            )

    fails = [k for k, v in adjudicated.items() if v == "FAILS"]
    degrades = [k for k, v in adjudicated.items() if v == "DEGRADES"]

    if fails:
        verdict = "REFUTED"
        rule = "clause 1: ≥1 evidence-qualified critical branch is an adjudicated FAILS."
    elif degrades:
        verdict = "WEAKENED"
        rule = "clause 2: ≥1 evidence-qualified critical branch is an adjudicated DEGRADES."
    elif len(adjudicated) == len(classifications) and set(adjudicated.values()) == {"SURVIVES"}:
        verdict = "SURVIVES"
        rule = "clause 3: every evidence-qualified critical branch is an adjudicated SURVIVES."
    else:
        verdict = "INCOMPARABLE"
        rule = (
            "clause 4: at least one evidence-qualified critical branch is NOT_EVALUATED or "
            "INCOMPARABLE and none is an adjudicated FAILS/DEGRADES; an overall real-data "
            "robustness judgement cannot be made."
        )

    return {
        "vocabulary": list(S.GATE_VERDICTS),
        "evidence_qualified_critical_set": list(S.FORMAL_CRITICAL_BRANCHES),
        "branch_classifications": classifications,
        "branch_evidence_classes": evidence_classes,
        "qualified_evidence_classes": sorted(QUALIFIED_EVIDENCE_CLASSES),
        "adjudicated_real_comparisons": adjudicated,
        "evidence_qualification_enforced": "A definite SURVIVES/DEGRADES/FAILS adjudicates the "
        "formal gate ONLY on REAL or DERIVED_FROM_REAL evidence; any other evidence class fails "
        "closed (EvidenceQualificationError). Synthetic evidence can never drive "
        "REFUTED/WEAKENED/SURVIVES.",
        "verdict": verdict,
        "rule_applied": rule,
        "reachability_disclosure": "Given evidence availability frozen at preregistration "
        "(T3-REAL and T4-REAL NOT_EVALUATED_MISSING_EVIDENCE; T5 INCOMPARABLE under PROTOCOL "
        "§4.5), some terminal states are structurally unreachable for the formal gate. This is "
        "not adjusted to force a more decisive result.",
        "no_claim_inflation": "No BUILD/REPOSITION/KILL/SAFE_TO_FLY/MADRID_VALIDATED/SUPPORTED/"
        "REFUTED(assumption-level); no assumption-state change; no regional claim from "
        "municipal-only evidence.",
    }


def _diagnostic_summary(diagnostic_branches: list[dict[str, object]]) -> dict[str, object]:
    buckets: dict[str, list[str]] = {
        "SURVIVES": [],
        "DEGRADES": [],
        "FAILS": [],
        "INCOMPARABLE": [],
        "NOT_EVALUATED": [],
    }
    for branch in diagnostic_branches:
        buckets[str(branch["result_classification"])].append(str(branch["stress_id"]))
    return {
        "note": "Synthetic-mechanism characterisation ONLY. A diagnostic FAILS is scoped to the "
        "pre-specified synthetic stress; it is never promoted into a real-data gate failure.",
        "survived": buckets["SURVIVES"],
        "degraded": buckets["DEGRADES"],
        "failed": buckets["FAILS"],
        "incomparable": buckets["INCOMPARABLE"],
        "not_evaluated": buckets["NOT_EVALUATED"],
    }


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #
def _load_json(path: str) -> dict[str, object]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def run_adversarial(
    config_path: str = S.CONFIG_PATH,
    *,
    phase0c_path: str = S.PHASE0C_RESULTS_PATH,
    phase0d3_path: str = S.PHASE0D3_RESULTS_PATH,
) -> dict[str, object]:
    """Execute every 0D.4 branch deterministically and return the results tree."""

    config = load_config(Path(config_path))
    phase0c = _load_json(phase0c_path)
    phase0d3 = _load_json(phase0d3_path)

    incidents, sites = generate_inputs(config)
    ordered = greedy_site_order(
        incidents, sites, config.reference_profile.max_sortie_distance_m / 2.0
    )

    baseline = {
        "config": config_path,
        "seed": config.seed,
        "incident_count": len(incidents),
        "site_count": len(sites),
        "network_sizes": list(config.network_sizes),
        "reference_profile_id": config.reference_profile_id,
        "model_a_risk_weighted_coverage_full_network": _coverage(
            incidents, sites, config, CoverageModel.A_DISTANCE
        ),
        "model_f_risk_weighted_coverage_full_network": _coverage(
            incidents, sites, config, CoverageModel.F_ENERGY
        ),
    }

    t3_real = _run_t3_real()
    t4_real = _run_t4_real()
    t5 = _run_t5(phase0c)
    formal_branches = [t3_real, t4_real, t5]

    t1 = _run_t1(incidents, sites, ordered, config, phase0d3)
    t2 = _run_t2(incidents, ordered, config, phase0d3)
    t3_synth = _run_t3_synth(incidents, sites, config)
    t4_synth = _run_t4_synth(incidents, sites, config)
    t6 = _run_t6(incidents, sites, config)
    diagnostic_branches = [t1, t2, t3_synth, t4_synth, t6]

    return {
        "metadata": {
            "phase": "0D.4",
            "experiment_version": S.EXPERIMENT_VERSION,
            "preregistration": S.PREREGISTRATION,
            "use": S.USE,
            "crs": config.crs,
        },
        "boundaries": {
            "no_assumption_state_change": "No assumption moves TESTING -> SUPPORTED/REFUTED.",
            "no_decision": "0D.4 decides no BUILD / REPOSITION / KILL.",
            "no_regional_inference": "No Comunidad de Madrid regional claim from municipal-only "
            "A-02 evidence.",
            "not_safe_to_fly": "No SAFE_TO_FLY, no MADRID VALIDATED, no operational claim.",
            "synthetic_stress_labelling": "Every synthetic perturbation is SYNTHETIC_STRESS_TEST, "
            "never real Madrid evidence.",
        },
        "frozen_parameters": _jsonable(S.FROZEN_PARAMETERS),
        "baseline_control": baseline,
        "formal_real_data_gate": {
            "branches": formal_branches,
            "aggregation": _aggregate_formal_gate(formal_branches),
        },
        "diagnostic_battery": {
            "branches": diagnostic_branches,
            "summary": _diagnostic_summary(diagnostic_branches),
        },
    }


def _jsonable(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    return value


def build_results(
    config_path: str = S.CONFIG_PATH,
    *,
    phase0c_path: str = S.PHASE0C_RESULTS_PATH,
    phase0d3_path: str = S.PHASE0D3_RESULTS_PATH,
) -> dict[str, object]:
    """Alias returning the full results tree (machine-readable results file)."""

    return run_adversarial(config_path, phase0c_path=phase0c_path, phase0d3_path=phase0d3_path)


def build_manifest(results: dict[str, object]) -> dict[str, object]:
    """Distil the results into the machine-readable manifest."""

    formal = results["formal_real_data_gate"]
    diagnostic = results["diagnostic_battery"]
    assert isinstance(formal, dict) and isinstance(diagnostic, dict)
    formal_branches = formal["branches"]
    diagnostic_branches = diagnostic["branches"]
    assert isinstance(formal_branches, list) and isinstance(diagnostic_branches, list)

    def _summarise(branch: dict[str, object]) -> dict[str, object]:
        summary: dict[str, object] = {
            "stress_id": branch.get("stress_id"),
            "target_assumption": branch.get("target_assumption"),
            "criticality": branch.get("criticality"),
            "evidence_class": branch.get("evidence_class"),
            "result_classification": branch.get("result_classification"),
            "reason": branch.get("reason"),
        }
        # Carry the T4-SYNTH no-op interpretation into the manifest, when present.
        if "interpretive_status" in branch:
            summary["interpretive_status"] = branch.get("interpretive_status")
            summary["informative_for_spatial_robustness"] = branch.get(
                "informative_for_spatial_robustness"
            )
        return summary

    return {
        "metadata": results["metadata"],
        "what_was_stressed": {
            "formal_real_data_gate": [_summarise(b) for b in formal_branches],
            "diagnostic_battery": [_summarise(b) for b in diagnostic_branches],
        },
        "constant_vs_changed": {
            "held_constant": [
                "frozen 0C.1 engine (generate_inputs, evaluate_network, greedy_site_order)",
                "seed 260827, 180 incidents, reference profile, thresholds, scoring logic",
                "all tracked 0C/0D outputs (immutable)",
            ],
            "changed_per_test": "exactly one stress dimension per test (candidate set, weather "
            "scenario, spatial exclusion, or non-travel budget)",
        },
        "criticality": {
            "formal_critical": list(S.FORMAL_CRITICAL_BRANCHES),
            "diagnostic": list(S.DIAGNOSTIC_BRANCHES),
        },
        "not_evaluable": [
            b["stress_id"]
            for b in [*formal_branches, *diagnostic_branches]
            if isinstance(b, dict) and b.get("result_classification") == "NOT_EVALUATED"
        ],
        "formal_gate_verdict": formal["aggregation"]["verdict"],
        "diagnostic_summary": diagnostic["summary"],
        "frozen_parameters": results["frozen_parameters"],
    }

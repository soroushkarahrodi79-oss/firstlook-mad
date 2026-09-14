"""Phase 0D.3 — staged reality substitution over a matched geographic support.

This module *orchestrates a controlled substitution*; it does not build a second
model. It reuses the frozen Phase 0C.1 engine (``generate_inputs``,
``evaluate_network``, ``euclidean_distance_m``) unchanged. The single variable
that differs between the CONTROL and REAL arms is the candidate-site locations.

All comparisons are confined to geometry-only metrics that do not read any
candidate operational attribute (pre-registration §6, §7). Model-F feasibility,
TTFRP-as-baseline, weather erosion and the camera comparator are NOT_EVALUATED
because the real evidence does not establish the operational properties they
require.
"""

from __future__ import annotations

import math
from statistics import median
from typing import cast

from firstlook_mad.domain import (
    CandidateSite,
    CoverageModel,
    Incident,
    SyntheticBounds,
    SyntheticConfig,
    UASPerformanceProfile,
)
from firstlook_mad.geo import euclidean_distance_m
from firstlook_mad.reality_substitution.evidence import CanonicalA02Evidence
from firstlook_mad.synthetic import generate_inputs
from firstlook_mad.validation import evaluate_network

EXPERIMENT_VERSION = "0D.3-1.0.0"
NORMALIZATION_VERSION = "0D.2-1.0.0"
MATCHED_COUNT_POLICY = "match_real_candidate_count"
SCOPE_MATCH_METHOD = "station_bounding_box_epsg25830"
# Pre-registered materiality threshold (relative change in median nearest
# distance). Fixed before any result is seen (pre-registration §8).
MATERIAL_RELATIVE_DELTA = 0.20
DISTANCE_DECIMALS = 3
COVERAGE_DECIMALS = 6

# Non-A-02 assumptions may never enter substitution (Phase 0D.2 eligibility).
INELIGIBLE_ASSUMPTIONS = ("A-01", "A-03", "A-04")

# Metrics that require candidate operational attributes; NOT_EVALUATED here
# because the real evidence marks those properties NOT_EVALUATED.
NOT_EVALUATED_METRICS = (
    "model_f_feasible_coverage",
    "ttfrp_seconds_baseline",
    "weather_erosion",
    "camera_or_hybrid_comparison",
    "scenario_survival",
    "operational_gate_outcome",
)


class ScopeMatchError(ValueError):
    """The matched geographic support could not be defined defensibly."""


def derive_support(evidence: CanonicalA02Evidence) -> SyntheticBounds:
    """Axis-aligned bounding box of the real A-02 stations in EPSG:25830.

    This is the exact geographic support of the real evidence (pre-registration
    §5.1). It is computed from the canonical records, never padded or invented.
    """

    eastings = [site.point.easting_m for site in evidence.sites]
    northings = [site.point.northing_m for site in evidence.sites]
    if not eastings or not northings:
        raise ScopeMatchError("no A-02 stations to define a matched support")
    min_e, max_e = min(eastings), max(eastings)
    min_n, max_n = min(northings), max(northings)
    if min_e >= max_e or min_n >= max_n:
        raise ScopeMatchError("A-02 stations are collinear or coincident; no 2-D support")
    return SyntheticBounds(
        min_easting_m=min_e, max_easting_m=max_e, min_northing_m=min_n, max_northing_m=max_n
    )


def build_scope_config(
    base_config: SyntheticConfig,
    support: SyntheticBounds,
    *,
    site_count: int,
    seed: int | None = None,
) -> SyntheticConfig:
    """0C.1 config with ONLY bounds and site_count changed (pre-registration §5.2)."""

    update: dict[str, object] = {"bounds": support, "site_count": site_count}
    if seed is not None:
        update["seed"] = seed
    return base_config.model_copy(update=update)


def real_sites_in_support(
    evidence: CanonicalA02Evidence, support: SyntheticBounds
) -> list[CandidateSite]:
    """Return the real sites, asserting every one lies within the matched support."""

    sites = list(evidence.sites)
    for site in sites:
        inside = (
            support.min_easting_m <= site.point.easting_m <= support.max_easting_m
            and support.min_northing_m <= site.point.northing_m <= support.max_northing_m
        )
        if not inside:
            raise ScopeMatchError(f"real site {site.site_id} lies outside its own support box")
    return sites


def _nearest_distances(incidents: list[Incident], sites: list[CandidateSite]) -> list[float]:
    return [
        min(euclidean_distance_m(incident.point, site.point) for site in sites)
        for incident in incidents
    ]


def _percentile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * probability)]


def _distance_stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"median": None, "p90": None, "max": None, "min": None, "mean": None}
    return {
        "median": round(median(values), DISTANCE_DECIMALS),
        "p90": round(_percentile(values, 0.90) or 0.0, DISTANCE_DECIMALS),
        "max": round(max(values), DISTANCE_DECIMALS),
        "min": round(min(values), DISTANCE_DECIMALS),
        "mean": round(sum(values) / len(values), DISTANCE_DECIMALS),
    }


def _candidate_dispersion(sites: list[CandidateSite]) -> dict[str, object]:
    eastings = [site.point.easting_m for site in sites]
    northings = [site.point.northing_m for site in sites]
    bbox_area = (max(eastings) - min(eastings)) * (max(northings) - min(northings))
    nn: list[float] = []
    for i, site in enumerate(sites):
        others = [
            euclidean_distance_m(site.point, other.point) for j, other in enumerate(sites) if j != i
        ]
        if others:
            nn.append(min(others))
    return {
        "candidate_bbox_area_m2": round(bbox_area, DISTANCE_DECIMALS),
        "mean_nearest_neighbour_m": round(sum(nn) / len(nn), DISTANCE_DECIMALS) if nn else None,
        "centroid_easting_m": round(sum(eastings) / len(eastings), DISTANCE_DECIMALS),
        "centroid_northing_m": round(sum(northings) / len(northings), DISTANCE_DECIMALS),
    }


def _model_a_coverage(
    incidents: list[Incident],
    sites: list[CandidateSite],
    config: SyntheticConfig,
    profile: UASPerformanceProfile,
) -> float:
    outcome = evaluate_network(
        incidents=incidents,
        sites=sites,
        config=config,
        model=CoverageModel.A_DISTANCE,
        ttfrp=config.ttfrp_scenarios[0],
        weather=config.weather_scenarios[0],
        profile=profile,
    )
    value = outcome.metrics["risk_weighted_coverage"]
    assert isinstance(value, int | float)
    return round(float(value), COVERAGE_DECIMALS)


def run_arm(
    incidents: list[Incident], sites: list[CandidateSite], config: SyntheticConfig
) -> dict[str, object]:
    """Geometry-only metrics for one arm (pre-registration §7)."""

    nearest = _nearest_distances(incidents, sites)
    coverage = {
        f"one_way_{int(profile.max_sortie_distance_m / 2.0)}m": _model_a_coverage(
            incidents, sites, config, profile
        )
        for profile in config.profiles
    }
    return {
        "candidate_count": len(sites),
        "incident_count": len(incidents),
        "nearest_distance_m": _distance_stats(nearest),
        "model_a_risk_weighted_coverage_by_one_way_range": coverage,
        "candidate_dispersion": _candidate_dispersion(sites),
    }


def _delta_record(name: str, control: float | None, real: float | None) -> dict[str, object]:
    if control is None or real is None:
        return {
            "metric": name,
            "control": control,
            "real": real,
            "delta_real_minus_control": None,
            "relative_delta": None,
            "effect_direction": "NOT_EVALUATED",
        }
    delta = real - control
    relative = (delta / control) if control != 0 else None
    if math.isclose(delta, 0.0, abs_tol=10 ** (-DISTANCE_DECIMALS)):
        direction = "NO_CHANGE"
    elif delta > 0:
        direction = "REAL_GREATER"
    else:
        direction = "REAL_SMALLER"
    return {
        "metric": name,
        "control": round(control, DISTANCE_DECIMALS),
        "real": round(real, DISTANCE_DECIMALS),
        "delta_real_minus_control": round(delta, DISTANCE_DECIMALS),
        "relative_delta": round(relative, COVERAGE_DECIMALS) if relative is not None else None,
        "effect_direction": direction,
    }


def compare_arms(control: dict[str, object], real: dict[str, object]) -> dict[str, object]:
    """Per-metric CONTROL / REAL / DELTA / direction / threshold-crossing records."""

    c_near = control["nearest_distance_m"]
    r_near = real["nearest_distance_m"]
    assert isinstance(c_near, dict) and isinstance(r_near, dict)
    nearest_records = [
        _delta_record(f"nearest_distance_m.{stat}", c_near[stat], r_near[stat])
        for stat in ("median", "p90", "max", "min", "mean")
    ]

    c_cov = control["model_a_risk_weighted_coverage_by_one_way_range"]
    r_cov = real["model_a_risk_weighted_coverage_by_one_way_range"]
    assert isinstance(c_cov, dict) and isinstance(r_cov, dict)
    coverage_records = []
    threshold_crossed_any = False
    for key in sorted(c_cov):
        control_value = float(c_cov[key])
        real_value = float(r_cov[key])
        control_full = math.isclose(control_value, 1.0)
        real_full = math.isclose(real_value, 1.0)
        crossed = control_full != real_full
        threshold_crossed_any = threshold_crossed_any or crossed
        coverage_records.append(
            {
                "metric": f"model_a_risk_weighted_coverage.{key}",
                "control": control_value,
                "real": real_value,
                "delta_real_minus_control": round(real_value - control_value, COVERAGE_DECIMALS),
                "full_coverage_threshold_crossed": crossed,
                "effect_direction": (
                    "NO_CHANGE"
                    if math.isclose(real_value, control_value)
                    else ("REAL_GREATER" if real_value > control_value else "REAL_SMALLER")
                ),
            }
        )

    median_record = next(r for r in nearest_records if r["metric"] == "nearest_distance_m.median")
    relative_obj = median_record["relative_delta"]
    relative = float(relative_obj) if isinstance(relative_obj, int | float) else None
    material = relative is not None and abs(relative) >= MATERIAL_RELATIVE_DELTA

    control_count = int(cast(int, control["candidate_count"]))
    real_count = int(cast(int, real["candidate_count"]))

    return {
        "candidate_count": {
            "control": control_count,
            "real": real_count,
            "delta_real_minus_control": real_count - control_count,
        },
        "nearest_distance_records": nearest_records,
        "coverage_records": coverage_records,
        "primary_metric": "nearest_distance_m.median",
        "primary_relative_delta": relative,
        "material_threshold": MATERIAL_RELATIVE_DELTA,
        "effect_material": material,
        "any_full_coverage_threshold_crossed": threshold_crossed_any,
        "not_evaluated_metrics": list(NOT_EVALUATED_METRICS),
    }


def run_robustness(
    base_config: SyntheticConfig,
    support: SyntheticBounds,
    real_sites: list[CandidateSite],
    seeds: tuple[int, ...],
) -> dict[str, object]:
    """Direction stability of the median-nearest-distance effect across seeds.

    REAL sites are seed-independent; only incidents and control sites are
    regenerated per seed (pre-registration §8).
    """

    rows: list[dict[str, object]] = []
    directions: set[str] = set()
    for seed in sorted(set(seeds)):
        scope_config = build_scope_config(
            base_config, support, site_count=len(real_sites), seed=seed
        )
        incidents, control_sites = generate_inputs(scope_config)
        control_median = median(_nearest_distances(incidents, control_sites))
        real_median = median(_nearest_distances(incidents, real_sites))
        delta = real_median - control_median
        if math.isclose(delta, 0.0, abs_tol=10 ** (-DISTANCE_DECIMALS)):
            direction = "NO_CHANGE"
        else:
            direction = "REAL_GREATER" if delta > 0 else "REAL_SMALLER"
        directions.add(direction)
        rows.append(
            {
                "seed": seed,
                "control_median_nearest_m": round(control_median, DISTANCE_DECIMALS),
                "real_median_nearest_m": round(real_median, DISTANCE_DECIMALS),
                "delta_real_minus_control_m": round(delta, DISTANCE_DECIMALS),
                "direction": direction,
            }
        )
    non_trivial = directions - {"NO_CHANGE"}
    stable = len(non_trivial) <= 1
    return {
        "seed_count": len(rows),
        "seeds": [row["seed"] for row in rows],
        "rows": rows,
        "distinct_directions": sorted(directions),
        "direction_stable": stable,
    }

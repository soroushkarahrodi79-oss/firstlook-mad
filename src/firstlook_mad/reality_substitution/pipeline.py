"""Phase 0D.3 orchestration: entry decision, arms, comparison, verdict, manifest.

The verdict vocabulary and the material / threshold / stability rules are frozen
in ``docs/PHASE_0D3_PREREGISTRATION.md`` (§8, §9). This module only applies them;
it never redefines a threshold after seeing a result.
"""

from __future__ import annotations

from pathlib import Path

from firstlook_mad.domain import CandidateSite, SyntheticBounds, SyntheticConfig
from firstlook_mad.reality_substitution.evidence import (
    NOT_EVALUATED_OPERATIONAL_PROPERTIES,
    CanonicalA02Evidence,
    load_canonical_a02,
)
from firstlook_mad.reality_substitution.experiment import (
    EXPERIMENT_VERSION,
    INELIGIBLE_ASSUMPTIONS,
    MATCHED_COUNT_POLICY,
    NORMALIZATION_VERSION,
    SCOPE_MATCH_METHOD,
    build_scope_config,
    compare_arms,
    derive_support,
    real_sites_in_support,
    run_arm,
    run_robustness,
)
from firstlook_mad.synthetic import generate_inputs, load_config

# 0C.1 reference synthetic extent (analytical domain), from configs/phase0c_synthetic.json.
ANALYTICAL_DOMAIN_AREA_M2 = (500000.0 - 390000.0) * (4520000.0 - 4410000.0)

ENTRY_PROCEED = "PROCEED"
ENTRY_LIMITED_PROCEED = "LIMITED_PROCEED"
ENTRY_STOP = "STOP"

VERDICT_INFORMATIVE = "SUBSTITUTION_INFORMATIVE"
VERDICT_WEAK_SIGNAL = "SUBSTITUTION_WEAK_SIGNAL"
VERDICT_UNINFORMATIVE = "SUBSTITUTION_UNINFORMATIVE"
VERDICT_INVALID = "SUBSTITUTION_INVALID"

VERDICT_VOCABULARY = (
    VERDICT_INFORMATIVE,
    VERDICT_WEAK_SIGNAL,
    VERDICT_UNINFORMATIVE,
    VERDICT_INVALID,
)

# Only A-02 survived Phase 0D.2 as eligible; the others may never enter.
ELIGIBLE_ASSUMPTION = "A-02"

REQUIRED_MANIFEST_KEYS = (
    "synthetic_variable_replaced",
    "real_evidence_source",
    "source_sha256",
    "canonical_output_sha256",
    "declared_scope",
    "analytical_scope",
    "scope_match_method",
    "assumptions_held_constant",
    "assumptions_not_substituted",
    "random_seed_policy",
    "normalization_version",
    "experiment_version",
)


class IneligibleAssumptionError(ValueError):
    """An assumption Phase 0D.2 ruled NOT_ELIGIBLE was asked to enter substitution."""


class MalformedManifestError(ValueError):
    """A substitution manifest is missing a required field."""


def permit_entry(assumption_id: str) -> None:
    """Allow only A-02 to enter 0D.3 substitution (pre-registration §2)."""

    if assumption_id != ELIGIBLE_ASSUMPTION:
        raise IneligibleAssumptionError(
            f"{assumption_id} is NOT_ELIGIBLE at Phase 0D.2 and cannot enter 0D.3 substitution"
        )


def validate_manifest(manifest: dict[str, object]) -> None:
    """Reject a manifest missing any required key (mission: malformed manifests fail)."""

    missing = [key for key in REQUIRED_MANIFEST_KEYS if key not in manifest]
    if missing:
        raise MalformedManifestError(f"substitution manifest missing keys: {sorted(missing)}")


class MultiAssumptionSubstitutionError(ValueError):
    """More than the A-02 candidate locations differ between the arms."""


def assert_single_substitution(
    control_sites: list[CandidateSite], real_sites: list[CandidateSite]
) -> None:
    """Guard: only candidate locations may differ (pre-registration §5, §10).

    The two arms share one ``scope_config`` and one ``incidents`` list by
    construction, so demand/seed/scenarios/thresholds are identical. Here we also
    require matched candidate count, so the manipulated variable is location
    (and, for real sites, the honest NOT_EVALUATED operational properties).
    """

    if len(control_sites) != len(real_sites):
        raise MultiAssumptionSubstitutionError(
            f"candidate count differs ({len(control_sites)} vs {len(real_sites)}); "
            "the primary arm must match count so only location varies"
        )
    for site in real_sites:
        for prop in NOT_EVALUATED_OPERATIONAL_PROPERTIES:
            if getattr(site, prop) is not None:
                raise MultiAssumptionSubstitutionError(
                    f"real site {site.site_id} has an invented operational property '{prop}'"
                )


def entry_decision(evidence: CanonicalA02Evidence) -> dict[str, object]:
    """LIMITED_PROCEED: A-02 is scope-restricted but a matched-scope test is valid."""

    return {
        "decision": ENTRY_LIMITED_PROCEED,
        "justification": (
            "A-02 real evidence is ELIGIBLE_WITHIN_DECLARED_SCOPE (Madrid municipality "
            "only), so it cannot validly replace the synthetic candidate layer across "
            "the full analytical domain (rules out PROCEED). A scientifically valid "
            "matched-scope comparison can nonetheless be constructed by restricting both "
            "arms to the exact geographic support of the real evidence (the station "
            "bounding box). No STOP condition holds: 0C.1 reproduces from tracked inputs, "
            "the matched scope is definable from tracked 0D.2 outputs, the scope-matched "
            "synthetic control is generable, exactly one assumption is substituted, and "
            "confining the comparison to geometry-only metrics keeps it non-misleading."
        ),
        "eligible_entrant": "A-02",
        "excluded_ineligible": list(INELIGIBLE_ASSUMPTIONS),
        "excluded_reason": "NOT_ELIGIBLE at Phase 0D.2; cannot enter substitution",
    }


def decide_verdict(
    comparison: dict[str, object], robustness: dict[str, object]
) -> dict[str, object]:
    """Apply the frozen §9 verdict rule. INFORMATIVE is structurally unreachable."""

    material = bool(comparison["effect_material"])
    threshold_crossed = bool(comparison["any_full_coverage_threshold_crossed"])
    stable = bool(robustness["direction_stable"])

    if not material and not threshold_crossed:
        verdict = VERDICT_UNINFORMATIVE
        rationale = (
            "The effect is not material (|relative delta of median nearest distance| "
            f"< {comparison['material_threshold']}) and no pre-existing coverage threshold "
            "is crossed under any profile: at matched scope the real evidence has too "
            "little geometric leverage to test the model."
        )
    else:
        verdict = VERDICT_WEAK_SIGNAL
        reasons = []
        if material:
            reasons.append("the primary metric is material")
        if threshold_crossed:
            reasons.append("a pre-existing coverage threshold is crossed")
        scope_note = (
            "the effect is confined to the municipal support (~1.9% of the analytical "
            "domain) against synthetic demand, and INFORMATIVE is unreachable by "
            "pre-registration (§9 structural cap)"
        )
        if not stable:
            scope_note += "; the effect direction is not stable across all robustness seeds"
        rationale = f"Valid, reproducible comparison; {' and '.join(reasons)}, but {scope_note}."

    return {
        "verdict": verdict,
        "rationale": rationale,
        "effect_material": material,
        "any_full_coverage_threshold_crossed": threshold_crossed,
        "direction_stable_across_seeds": stable,
        "informative_structurally_unreachable": True,
        "informative_cap_reason": (
            "A-02 covers ~1.9% of the analytical domain and demand is synthetic "
            "(A-01 BASELINE_NOT_OBSERVABLE); no effect measured here is relevant to the "
            "tested mechanism across the analytical domain."
        ),
    }


def build_manifest(
    evidence: CanonicalA02Evidence,
    support: SyntheticBounds,
    base_config: SyntheticConfig,
    real_site_count: int,
) -> dict[str, object]:
    """Machine-readable substitution manifest (mission 'SUBSTITUTION MANIFEST')."""

    support_dict = {
        "min_easting_m": round(support.min_easting_m, 3),
        "max_easting_m": round(support.max_easting_m, 3),
        "min_northing_m": round(support.min_northing_m, 3),
        "max_northing_m": round(support.max_northing_m, 3),
        "crs": "EPSG:25830",
    }
    support_area = (support.max_easting_m - support.min_easting_m) * (
        support.max_northing_m - support.min_northing_m
    )
    return {
        "experiment_version": EXPERIMENT_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "synthetic_variable_replaced": (
            "A-02 candidate-site locations (existence and location only)"
        ),
        "real_evidence_source": {
            "canonical_path": "outputs/canonical/phase0d2/a02_madrid_city_fire_stations.json",
            "source_url": evidence.source_url,
            "source_evidence_classification": evidence.source_evidence_classification,
            "record_count": evidence.record_count,
        },
        "source_sha256": evidence.source_sha256,
        "canonical_output_sha256": evidence.canonical_output_sha256,
        "declared_scope": evidence.declared_coverage,
        "analytical_scope": "COMUNIDAD_DE_MADRID (0C.1 synthetic extent 110 km x 110 km)",
        "matched_support_epsg25830": support_dict,
        "matched_support_area_m2": round(support_area, 3),
        "analytical_domain_area_m2": ANALYTICAL_DOMAIN_AREA_M2,
        "matched_support_fraction_of_domain": round(support_area / ANALYTICAL_DOMAIN_AREA_M2, 6),
        "scope_match_method": SCOPE_MATCH_METHOD,
        "candidate_count_policy": MATCHED_COUNT_POLICY,
        "real_candidate_count": real_site_count,
        "native_synthetic_candidate_count": base_config.site_count,
        "assumptions_held_constant": [
            "incidents / demand (synthetic, identical)",
            "random seed (260827 primary; 25 robustness seeds)",
            "UAS performance profiles",
            "TTFRP scenarios",
            "weather scenarios",
            "travel model",
            "thresholds and constraints",
            "scoring / coverage logic",
            "geographic support (matched to real evidence, identical in both arms)",
        ],
        "assumptions_not_substituted": list(INELIGIBLE_ASSUMPTIONS),
        "operational_properties_not_evaluated": {
            prop: "NOT_EVALUATED" for prop in NOT_EVALUATED_OPERATIONAL_PROPERTIES
        },
        "not_inferred_from_source": evidence.not_inferred,
        "random_seed_policy": (
            "primary seed 260827 from configs/phase0c_synthetic.json; robustness over the "
            "25 pre-declared robustness_seeds; REAL sites are seed-independent; both arms "
            "share one incidents list per seed"
        ),
    }


def run_phase0d3(
    config_path: Path = Path("configs/phase0c_synthetic.json"),
    canonical_path: Path | None = None,
) -> dict[str, object]:
    """Execute the full Phase 0D.3 staged substitution and return a result dict."""

    permit_entry(ELIGIBLE_ASSUMPTION)  # only A-02 may enter
    base_config = load_config(config_path)
    evidence = (
        load_canonical_a02() if canonical_path is None else load_canonical_a02(canonical_path)
    )
    entry = entry_decision(evidence)

    support = derive_support(evidence)
    real_sites = real_sites_in_support(evidence, support)

    # Primary comparison: matched count so only location varies.
    scope_config = build_scope_config(base_config, support, site_count=len(real_sites))
    incidents, control_sites = generate_inputs(scope_config)
    assert_single_substitution(control_sites, real_sites)

    control_metrics = run_arm(incidents, control_sites, scope_config)
    real_metrics = run_arm(incidents, real_sites, scope_config)
    comparison = compare_arms(control_metrics, real_metrics)

    robustness = run_robustness(base_config, support, real_sites, base_config.robustness_seeds)
    verdict = decide_verdict(comparison, robustness)

    # Secondary, native-count control (transparency only; not the verdict basis).
    native_config = build_scope_config(base_config, support, site_count=base_config.site_count)
    native_incidents, native_control_sites = generate_inputs(native_config)
    native_control_metrics = run_arm(native_incidents, native_control_sites, native_config)

    manifest = build_manifest(evidence, support, base_config, len(real_sites))
    validate_manifest(manifest)

    return {
        "metadata": {
            "phase": "0D.3",
            "experiment_version": EXPERIMENT_VERSION,
            "crs": "EPSG:25830",
            "use": "RESEARCH / SIMULATION PROTOTYPE ONLY",
            "preregistration": "docs/PHASE_0D3_PREREGISTRATION.md",
        },
        "entry_decision": entry,
        "manifest": manifest,
        "control": control_metrics,
        "real_substitution": real_metrics,
        "comparison": comparison,
        "robustness": robustness,
        "secondary_native_count_control": {
            "note": (
                "Synthetic control at native 0C.1 count (10) over the same matched support; "
                "shown so candidate count (10 vs 13) is transparent. Not the primary "
                "comparison and not used for the verdict."
            ),
            "control": native_control_metrics,
        },
        "verdict": verdict,
        "boundaries": {
            "no_regional_inference": (
                "This is a municipal-only experiment; no Comunidad de Madrid inference is emitted."
            ),
            "no_assumption_state_change": "No assumption moves TESTING -> SUPPORTED/REFUTED.",
            "no_decision": "Phase 0D.3 does not decide BUILD / REPOSITION / KILL.",
            "not_safe_to_fly": "No SAFE_TO_FLY, no MADRID VALIDATED, no operational claim.",
        },
    }

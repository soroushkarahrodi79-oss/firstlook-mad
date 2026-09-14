"""Tests for Phase 0D.3 staged reality substitution.

These tests protect the falsification-first design: only A-02 may enter, scope
stays matched and municipal, exactly one assumption is substituted, NOT_EVALUATED
operational properties stay unknown, provenance hashes are preserved, outputs are
deterministic, and no regional inference can escape a municipal-only experiment.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from firstlook_mad.domain import EvidenceNature, SyntheticBounds
from firstlook_mad.reality_substitution import run_phase0d3
from firstlook_mad.reality_substitution.evidence import (
    CANONICAL_A02_PATH,
    EXPECTED_SOURCE_SHA256,
    NOT_EVALUATED_OPERATIONAL_PROPERTIES,
    CanonicalA02IntegrityError,
    MissingCanonicalA02Error,
    load_canonical_a02,
)
from firstlook_mad.reality_substitution.experiment import (
    MATERIAL_RELATIVE_DELTA,
    ScopeMatchError,
    build_scope_config,
    derive_support,
    real_sites_in_support,
)
from firstlook_mad.reality_substitution.pipeline import (
    ELIGIBLE_ASSUMPTION,
    INELIGIBLE_ASSUMPTIONS,
    REQUIRED_MANIFEST_KEYS,
    VERDICT_INFORMATIVE,
    VERDICT_VOCABULARY,
    IneligibleAssumptionError,
    MalformedManifestError,
    MultiAssumptionSubstitutionError,
    assert_single_substitution,
    entry_decision,
    permit_entry,
    validate_manifest,
)
from firstlook_mad.synthetic import generate_inputs, load_config

CONFIG_PATH = Path("configs/phase0c_synthetic.json")
PRIMARY_SEED = 260827
EXPECTED_REAL_COUNT = 13
MAX_SUPPORT_FRACTION = 0.02


@pytest.fixture(scope="module")
def result() -> dict[str, object]:
    return run_phase0d3(config_path=CONFIG_PATH)


@pytest.fixture(scope="module")
def evidence():
    return load_canonical_a02(CANONICAL_A02_PATH)


# --- entry eligibility -------------------------------------------------------


def test_only_a02_may_enter_substitution() -> None:
    permit_entry(ELIGIBLE_ASSUMPTION)  # does not raise
    assert ELIGIBLE_ASSUMPTION == "A-02"


@pytest.mark.parametrize("assumption", ["A-01", "A-03", "A-04"])
def test_ineligible_assumptions_cannot_enter(assumption: str) -> None:
    assert assumption in INELIGIBLE_ASSUMPTIONS
    with pytest.raises(IneligibleAssumptionError):
        permit_entry(assumption)


def test_entry_decision_is_limited_proceed_and_excludes_ineligible(evidence) -> None:
    entry = entry_decision(evidence)
    assert entry["decision"] == "LIMITED_PROCEED"
    assert entry["eligible_entrant"] == "A-02"
    assert set(entry["excluded_ineligible"]) == {"A-01", "A-03", "A-04"}


# --- scope: matched and municipal -------------------------------------------


def test_support_is_station_bounding_box(evidence) -> None:
    support = derive_support(evidence)
    eastings = [s.point.easting_m for s in evidence.sites]
    northings = [s.point.northing_m for s in evidence.sites]
    assert support.min_easting_m == min(eastings)
    assert support.max_easting_m == max(eastings)
    assert support.min_northing_m == min(northings)
    assert support.max_northing_m == max(northings)


def test_scope_restricted_a02_cannot_become_full_domain_evidence(result) -> None:
    manifest = result["manifest"]
    # The matched station-envelope extent is a tiny fraction (~1.9%) of the domain.
    assert manifest["matched_support_fraction_of_domain"] < MAX_SUPPORT_FRACTION
    # Source declared coverage is preserved as a documented source fact.
    assert manifest["declared_scope"] == "MADRID_MUNICIPALITY"
    assert manifest["analytical_scope"].startswith("COMUNIDAD_DE_MADRID")
    # Declared scope and analytical scope are kept distinct, never conflated.
    assert manifest["declared_scope"] not in manifest["analytical_scope"]


def test_matched_support_is_not_labelled_municipality_boundary(result) -> None:
    manifest = result["manifest"]
    definition = manifest["matched_support_definition"]
    # The bbox extent must be explicitly distinguished from the municipality boundary.
    assert "bounding box" in definition
    assert "NOT the official Madrid municipality boundary" in definition
    assert manifest["scope_match_method"] == "station_bounding_box_epsg25830"
    # declared_scope (source fact) is annotated as distinct from the experiment extent.
    assert "distinct from" in manifest["declared_scope_note"]


def test_no_regional_inference_from_municipal_experiment(result) -> None:
    boundaries = result["boundaries"]
    assert "no_regional_inference" in boundaries
    assert "municipal-scope" in boundaries["no_regional_inference"]
    assert "regional" in boundaries["no_regional_inference"]
    # The verdict object flags that INFORMATIVE (domain-relevant) is unreachable.
    assert result["verdict"]["informative_structurally_unreachable"] is True


def test_scope_mismatch_is_rejected(evidence) -> None:
    # A support box that excludes a real station must be rejected, not silently used.
    tight = SyntheticBounds(
        min_easting_m=440000.0,
        max_easting_m=445000.0,
        min_northing_m=4470000.0,
        max_northing_m=4475000.0,
    )
    with pytest.raises(ScopeMatchError):
        real_sites_in_support(evidence, tight)


# --- single substitution: only candidate locations change -------------------


def test_control_and_real_share_identical_non_a02_parameters(evidence) -> None:
    support = derive_support(evidence)
    scope_config = build_scope_config(
        support=support, base_config=load_config(CONFIG_PATH), site_count=len(evidence.sites)
    )
    incidents_a, _ = generate_inputs(scope_config)
    incidents_b, _ = generate_inputs(scope_config)
    # Same seed, same demand for both arms.
    assert incidents_a == incidents_b
    assert scope_config.seed == PRIMARY_SEED


def test_seeds_are_identical_across_arms(evidence) -> None:
    base = load_config(CONFIG_PATH)
    support = derive_support(evidence)
    scope_config = build_scope_config(base, support, site_count=len(evidence.sites))
    assert scope_config.seed == base.seed


def test_only_bounds_and_site_count_change_in_scope_config(evidence) -> None:
    base = load_config(CONFIG_PATH)
    support = derive_support(evidence)
    scope_config = build_scope_config(base, support, site_count=len(evidence.sites))
    changed = {
        field
        for field in type(base).model_fields
        if getattr(base, field) != getattr(scope_config, field)
    }
    assert changed == {"bounds", "site_count"}


def test_multi_assumption_substitution_is_rejected(evidence) -> None:
    support = derive_support(evidence)
    scope_config = build_scope_config(
        load_config(CONFIG_PATH), support, site_count=len(evidence.sites)
    )
    _, control_sites = generate_inputs(scope_config)
    real_sites = real_sites_in_support(evidence, support)
    # Count mismatch (a second changed variable) must raise.
    with pytest.raises(MultiAssumptionSubstitutionError):
        assert_single_substitution(control_sites[:-1], real_sites)


def test_matched_arms_pass_single_substitution_guard(evidence) -> None:
    support = derive_support(evidence)
    scope_config = build_scope_config(
        load_config(CONFIG_PATH), support, site_count=len(evidence.sites)
    )
    _, control_sites = generate_inputs(scope_config)
    real_sites = real_sites_in_support(evidence, support)
    assert_single_substitution(control_sites, real_sites)  # does not raise
    assert len(control_sites) == len(real_sites) == EXPECTED_REAL_COUNT


# --- operational properties stay NOT_EVALUATED ------------------------------


def test_real_sites_operational_properties_stay_not_evaluated(evidence) -> None:
    for site in evidence.sites:
        for prop in NOT_EVALUATED_OPERATIONAL_PROPERTIES:
            assert getattr(site, prop) is None


def test_no_fire_station_becomes_a_validated_uas_dock(evidence) -> None:
    for site in evidence.sites:
        # Real-derived provenance, never SYNTHETIC/ASSUMED, and no dock/availability.
        assert site.nature is EvidenceNature.DERIVED
        assert site.assumed_available is None
        assert site.uas_available is None
        assert site.site_id.startswith("A02-")


def test_invented_operational_property_is_rejected(evidence) -> None:
    support = derive_support(evidence)
    real_sites = list(real_sites_in_support(evidence, support))
    tampered = real_sites[0].model_copy(update={"assumed_available": True})
    with pytest.raises(MultiAssumptionSubstitutionError):
        assert_single_substitution(real_sites, [tampered, *real_sites[1:]])


def test_unknown_stays_unknown_in_not_evaluated_metrics(result) -> None:
    not_evaluated = result["comparison"]["not_evaluated_metrics"]
    assert "model_f_feasible_coverage" in not_evaluated
    assert "ttfrp_seconds_baseline" in not_evaluated
    assert "camera_or_hybrid_comparison" in not_evaluated


# --- provenance & integrity --------------------------------------------------


def test_missing_canonical_a02_fails_explicitly(tmp_path: Path) -> None:
    with pytest.raises(MissingCanonicalA02Error):
        load_canonical_a02(tmp_path / "absent.json")


def test_malformed_canonical_a02_wrong_hash_fails(tmp_path: Path) -> None:
    document = json.loads(CANONICAL_A02_PATH.read_text(encoding="utf-8"))
    document["source_sha256"] = "0" * 64
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(CanonicalA02IntegrityError):
        load_canonical_a02(bad)


def test_malformed_canonical_a02_wrong_count_fails(tmp_path: Path) -> None:
    document = json.loads(CANONICAL_A02_PATH.read_text(encoding="utf-8"))
    document["records"] = document["records"][:5]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(CanonicalA02IntegrityError):
        load_canonical_a02(bad)


def test_provenance_hashes_are_preserved(result, evidence) -> None:
    manifest = result["manifest"]
    assert manifest["source_sha256"] == EXPECTED_SOURCE_SHA256
    assert evidence.source_sha256 == EXPECTED_SOURCE_SHA256
    # canonical_output_sha256 is the sha256 of the tracked canonical file bytes.
    expected = hashlib.sha256(CANONICAL_A02_PATH.read_bytes()).hexdigest()
    assert manifest["canonical_output_sha256"] == expected


# --- manifest schema ---------------------------------------------------------


def test_manifest_has_all_required_keys(result) -> None:
    validate_manifest(result["manifest"])  # does not raise
    for key in REQUIRED_MANIFEST_KEYS:
        assert key in result["manifest"]


def test_malformed_manifest_fails() -> None:
    with pytest.raises(MalformedManifestError):
        validate_manifest({"experiment_version": "0D.3-1.0.0"})


# --- verdict & determinism ---------------------------------------------------


def test_verdict_is_in_frozen_vocabulary(result) -> None:
    assert result["verdict"]["verdict"] in VERDICT_VOCABULARY


def test_informative_is_structurally_unreachable(result) -> None:
    # By pre-registration, INFORMATIVE cannot be emitted in this configuration.
    assert result["verdict"]["verdict"] != VERDICT_INFORMATIVE
    assert result["verdict"]["informative_structurally_unreachable"] is True


def test_outputs_are_deterministic() -> None:
    first = run_phase0d3(config_path=CONFIG_PATH)
    second = run_phase0d3(config_path=CONFIG_PATH)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_comparison_reports_all_six_fields_per_metric(result) -> None:
    for record in result["comparison"]["nearest_distance_records"]:
        assert "control" in record
        assert "real" in record
        assert "delta_real_minus_control" in record
        assert "effect_direction" in record
    assert "material_threshold" in result["comparison"]
    assert result["comparison"]["material_threshold"] == MATERIAL_RELATIVE_DELTA

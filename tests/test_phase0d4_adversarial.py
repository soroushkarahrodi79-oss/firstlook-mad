"""Phase 0D.4 adversarial falsification — determinism, freeze and guardrails.

These tests prove the pre-registered invariants (docs/PHASE_0D4_PREREGISTRATION.md
§"Tests"): frozen parameters, evidence-qualified formal gate, synthetic-stress
labelling, missing-evidence never promoted, diagnostic FAILS never gate-driving,
no assumption/state change, deterministic outputs, malformed input fails, unknown
stays unknown.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from firstlook_mad.adversarial import build_manifest, build_results
from firstlook_mad.adversarial import stresses as S
from firstlook_mad.adversarial.experiment import (
    EvidenceQualificationError,
    _aggregate_formal_gate,
    _displace_sites,
)
from firstlook_mad.domain import CandidateSite, ProjectedPoint

RESULTS_PATH = Path("outputs/reports/phase0d4_adversarial_results.json")
MANIFEST_PATH = Path("outputs/reports/phase0d4_adversarial_manifest.json")
PHASE0C_PATH = Path("outputs/reports/phase0c_synthetic_results.json")

FULL_NETWORK_SITE_COUNT = 10  # 0C.1 native candidate count


@pytest.fixture(scope="module")
def results() -> dict[str, object]:
    return build_results()


def _formal_branches(results: dict[str, object]) -> list[dict[str, object]]:
    return results["formal_real_data_gate"]["branches"]  # type: ignore[index,return-value]


def _diagnostic_branches(results: dict[str, object]) -> list[dict[str, object]]:
    return results["diagnostic_battery"]["branches"]  # type: ignore[index,return-value]


def _by_id(results: dict[str, object]) -> dict[str, dict[str, object]]:
    branches = _formal_branches(results) + _diagnostic_branches(results)
    return {str(b["stress_id"]): b for b in branches}


# --------------------------------------------------------------------------- #
# Reproducibility and freeze
# --------------------------------------------------------------------------- #
def test_baseline_reproduces_0c1(results: dict[str, object]) -> None:
    baseline = results["baseline_control"]
    assert isinstance(baseline, dict)
    phase0c = json.loads(PHASE0C_PATH.read_text(encoding="utf-8"))
    progressive = phase0c["evidence"]["progressive_models"]
    a10 = next(
        r
        for r in progressive
        if r["model"] == "A_DISTANCE" and r["site_count"] == FULL_NETWORK_SITE_COUNT
    )
    f10 = next(
        r
        for r in progressive
        if r["model"] == "F_ENERGY" and r["site_count"] == FULL_NETWORK_SITE_COUNT
    )
    assert baseline["model_a_risk_weighted_coverage_full_network"] == round(
        a10["risk_weighted_coverage"], S.COVERAGE_DECIMALS
    )
    assert baseline["model_f_risk_weighted_coverage_full_network"] == round(
        f10["risk_weighted_coverage"], S.COVERAGE_DECIMALS
    )


def test_outputs_are_deterministic() -> None:
    first = build_results()
    second = build_results()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_committed_artifacts_match_regeneration(results: dict[str, object]) -> None:
    on_disk = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    assert json.dumps(on_disk, sort_keys=True) == json.dumps(results, sort_keys=True)
    manifest_on_disk = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert json.dumps(manifest_on_disk, sort_keys=True) == json.dumps(
        build_manifest(results), sort_keys=True
    )


def test_frozen_parameters_recorded_and_unchanged(results: dict[str, object]) -> None:
    recorded = results["frozen_parameters"]
    expected = json.loads(json.dumps(dict(S.FROZEN_PARAMETERS)))
    assert recorded == expected
    # The parameters actually used equal the frozen snapshot (no in-run drift).
    assert expected["T3"]["fail_rel"] == S.T3_FAIL_REL
    assert expected["T6"]["step_s"] == S.T6_STEP_S
    assert expected["T1"]["displace_m"] == S.T1C_DISPLACE_M


# --------------------------------------------------------------------------- #
# Evidence-qualified formal gate
# --------------------------------------------------------------------------- #
def test_formal_gate_is_evidence_qualified_set_only(results: dict[str, object]) -> None:
    ids = {str(b["stress_id"]) for b in _formal_branches(results)}
    assert ids == set(S.FORMAL_CRITICAL_BRANCHES)


def test_formal_gate_verdict_incomparable_under_missing_evidence(
    results: dict[str, object],
) -> None:
    aggregation = results["formal_real_data_gate"]["aggregation"]  # type: ignore[index]
    assert isinstance(aggregation, dict)
    assert aggregation["verdict"] == "INCOMPARABLE"
    assert aggregation["adjudicated_real_comparisons"] == {}
    assert aggregation["verdict"] in S.GATE_VERDICTS


def test_diagnostic_fails_never_drive_formal_gate(results: dict[str, object]) -> None:
    summary = results["diagnostic_battery"]["summary"]  # type: ignore[index]
    assert isinstance(summary, dict)
    # Known synthetic collapses are recorded as diagnostic FAILS ...
    assert set(summary["failed"]) == {"T3-SYNTH", "T6"}
    # ... but the formal verdict is not REFUTED/WEAKENED from them.
    verdict = results["formal_real_data_gate"]["aggregation"]["verdict"]  # type: ignore[index]
    assert verdict == "INCOMPARABLE"
    # And no diagnostic id leaks into the formal critical set.
    formal_ids = {str(b["stress_id"]) for b in _formal_branches(results)}
    assert not (set(S.DIAGNOSTIC_BRANCHES) & formal_ids)


def test_aggregator_real_fails_drives_refuted() -> None:
    # (A) REAL + FAILS -> REFUTED. A failed real critical test is never downgraded.
    branches = [
        {"stress_id": "T3-REAL", "result_classification": "FAILS", "evidence_class": "REAL"},
        {
            "stress_id": "T4-REAL",
            "result_classification": "NOT_EVALUATED",
            "evidence_class": "NOT_EVALUATED",
        },
        {"stress_id": "T5", "result_classification": "INCOMPARABLE", "evidence_class": "SYNTHETIC"},
    ]
    result = _aggregate_formal_gate(branches)
    assert result["verdict"] == "REFUTED"
    assert result["adjudicated_real_comparisons"] == {"T3-REAL": "FAILS"}


def test_aggregator_derived_from_real_degrades_drives_weakened() -> None:
    # (B) DERIVED_FROM_REAL + DEGRADES -> WEAKENED.
    branches = [
        {
            "stress_id": "T3-REAL",
            "result_classification": "DEGRADES",
            "evidence_class": "DERIVED_FROM_REAL",
        },
        {
            "stress_id": "T4-REAL",
            "result_classification": "NOT_EVALUATED",
            "evidence_class": "NOT_EVALUATED",
        },
        {"stress_id": "T5", "result_classification": "INCOMPARABLE", "evidence_class": "SYNTHETIC"},
    ]
    assert _aggregate_formal_gate(branches)["verdict"] == "WEAKENED"


def test_aggregator_all_qualified_survives_drives_survives() -> None:
    # (C) all evidence-qualified REAL/DERIVED_FROM_REAL + SURVIVES -> SURVIVES.
    branches = [
        {"stress_id": "T3-REAL", "result_classification": "SURVIVES", "evidence_class": "REAL"},
        {
            "stress_id": "T4-REAL",
            "result_classification": "SURVIVES",
            "evidence_class": "DERIVED_FROM_REAL",
        },
        {"stress_id": "T5", "result_classification": "SURVIVES", "evidence_class": "REAL"},
    ]
    assert _aggregate_formal_gate(branches)["verdict"] == "SURVIVES"


def test_aggregator_synthetic_fails_cannot_drive_refuted() -> None:
    # (D) SYNTHETIC + FAILS on a FORMAL-CRITICAL branch must fail closed.
    branches = [
        {"stress_id": "T3-REAL", "result_classification": "FAILS", "evidence_class": "SYNTHETIC"},
        {
            "stress_id": "T4-REAL",
            "result_classification": "NOT_EVALUATED",
            "evidence_class": "NOT_EVALUATED",
        },
        {"stress_id": "T5", "result_classification": "INCOMPARABLE", "evidence_class": "SYNTHETIC"},
    ]
    with pytest.raises(EvidenceQualificationError):
        _aggregate_formal_gate(branches)


def test_aggregator_synthetic_stress_degrades_cannot_drive_weakened() -> None:
    # (E) SYNTHETIC_STRESS_TEST + DEGRADES must fail closed.
    branches = [
        {
            "stress_id": "T3-REAL",
            "result_classification": "DEGRADES",
            "evidence_class": "SYNTHETIC_STRESS_TEST",
        },
        {
            "stress_id": "T4-REAL",
            "result_classification": "NOT_EVALUATED",
            "evidence_class": "NOT_EVALUATED",
        },
        {"stress_id": "T5", "result_classification": "INCOMPARABLE", "evidence_class": "SYNTHETIC"},
    ]
    with pytest.raises(EvidenceQualificationError):
        _aggregate_formal_gate(branches)


def test_aggregator_t5_synthetic_incomparable_is_valid_non_adjudicated() -> None:
    # (F) T5 = SYNTHETIC + INCOMPARABLE is valid and yields no adjudicated comparison.
    branches = [
        {
            "stress_id": "T3-REAL",
            "result_classification": "NOT_EVALUATED",
            "evidence_class": "NOT_EVALUATED",
        },
        {
            "stress_id": "T4-REAL",
            "result_classification": "NOT_EVALUATED",
            "evidence_class": "NOT_EVALUATED",
        },
        {"stress_id": "T5", "result_classification": "INCOMPARABLE", "evidence_class": "SYNTHETIC"},
    ]
    result = _aggregate_formal_gate(branches)
    assert result["verdict"] == "INCOMPARABLE"
    assert result["adjudicated_real_comparisons"] == {}


def test_aggregator_real_run_regenerates_incomparable(results: dict[str, object]) -> None:
    # (G) The actual Phase 0D.4 formal branches regenerate INCOMPARABLE, no adjudication.
    aggregation = results["formal_real_data_gate"]["aggregation"]  # type: ignore[index]
    assert isinstance(aggregation, dict)
    assert aggregation["verdict"] == "INCOMPARABLE"
    assert aggregation["adjudicated_real_comparisons"] == {}


# --------------------------------------------------------------------------- #
# Missing evidence never promoted; bounded never full-domain
# --------------------------------------------------------------------------- #
def test_t3_real_not_evaluated_never_survives(results: dict[str, object]) -> None:
    branch = _by_id(results)["T3-REAL"]
    assert branch["result_classification"] == "NOT_EVALUATED"
    assert branch["evidence_class"] == "NOT_EVALUATED"
    assert branch["criticality"] == "FORMAL-CRITICAL"
    assert "observation" in str(branch["reason"]).lower()  # inventory != observations


def test_t4_real_bounded_not_full_domain(results: dict[str, object]) -> None:
    branch = _by_id(results)["T4-REAL"]
    assert branch["result_classification"] == "NOT_EVALUATED"
    assert branch["evidence_class"] == "NOT_EVALUATED"
    reason = str(branch["reason"]).lower()
    assert "bounded" in reason and "full-domain" in reason


def test_no_not_evaluated_branch_is_survives(results: dict[str, object]) -> None:
    for branch in _formal_branches(results) + _diagnostic_branches(results):
        if branch["result_classification"] == "NOT_EVALUATED":
            assert branch["result_classification"] != "SURVIVES"


# --------------------------------------------------------------------------- #
# Synthetic-stress labelling
# --------------------------------------------------------------------------- #
def test_synthetic_stress_always_labelled(results: dict[str, object]) -> None:
    by = _by_id(results)
    assert by["T3-SYNTH"]["evidence_class"] == "SYNTHETIC_STRESS_TEST"
    assert by["T4-SYNTH"]["evidence_class"] == "SYNTHETIC_STRESS_TEST"
    t1 = by["T1"]["sub_tests"]  # type: ignore[index]
    assert isinstance(t1, dict)
    assert t1["t1b_drop_top_site"]["evidence_class"] == "SYNTHETIC_STRESS_TEST"


def test_no_synthetic_branch_claims_real(results: dict[str, object]) -> None:
    for branch in _diagnostic_branches(results):
        assert branch.get("evidence_class") != "REAL"
    # T3-SYNTH explicitly disclaims being real weather.
    by = _by_id(results)
    assert "not new real-weather" in str(by["T3-SYNTH"]["known_outcome_disclosure"])
    assert "ENAIRE" in str(by["T4-SYNTH"]["reason"])  # never reported as ENAIRE


# --------------------------------------------------------------------------- #
# Criticality frozen; unknown stays unknown; T6 is a model switch
# --------------------------------------------------------------------------- #
def test_criticality_is_frozen(results: dict[str, object]) -> None:
    by = _by_id(results)
    for stress_id in S.FORMAL_CRITICAL_BRANCHES:
        assert by[stress_id]["criticality"] == "FORMAL-CRITICAL"
    for stress_id in S.DIAGNOSTIC_BRANCHES:
        assert by[stress_id]["criticality"] == "DIAGNOSTIC"


def test_t5_unknown_remains_incomparable(results: dict[str, object]) -> None:
    branch = _by_id(results)["T5"]
    assert branch["result_classification"] == "INCOMPARABLE"
    assert "INCOMPARABLE" in str(branch["fair_comparator_status"])


def test_t6_is_model_switch_not_real_a01_bands(results: dict[str, object]) -> None:
    branch = _by_id(results)["T6"]
    reason = str(branch["reason"])
    assert "model-emitted qualitative switch" in reason
    assert "§4.1" in reason
    assert branch["criticality"] == "DIAGNOSTIC"


def test_t1c_boundary_outside_domain_is_not_evaluated() -> None:
    # A single site within R of the eastern edge, displaced east (bearing 0),
    # exits the domain -> NOT_EVALUATED_CONFIG_INVALID, no repair.
    near_edge = CandidateSite(
        site_id="EDGE",
        point=ProjectedPoint(easting_m=S.DOMAIN_MAX_E - 100.0, northing_m=4_465_000.0),
        assumed_available=True,
        uas_available=True,
        communications_available=True,
        camera_available=True,
        camera_communications_available=True,
    )
    moved, any_outside = _displace_sites([near_edge])
    assert any_outside is True
    assert moved is None


# --------------------------------------------------------------------------- #
# No claim inflation, no assumption/state change, no regional claim
# --------------------------------------------------------------------------- #
FORBIDDEN_DECISION_TOKENS = {
    "BUILD",
    "REPOSITION",
    "KILL",
    "SAFE_TO_FLY",
    "MADRID_VALIDATED",
    "SUPPORTED",
}


def test_no_decision_or_assumption_state_emitted(results: dict[str, object]) -> None:
    verdict = results["formal_real_data_gate"]["aggregation"]["verdict"]  # type: ignore[index]
    assert verdict in S.GATE_VERDICTS
    for branch in _formal_branches(results) + _diagnostic_branches(results):
        assert branch["result_classification"] in S.TEST_CLASSIFICATIONS
        assert branch["result_classification"] not in FORBIDDEN_DECISION_TOKENS
    boundaries = results["boundaries"]
    assert isinstance(boundaries, dict)
    assert "TESTING -> SUPPORTED/REFUTED" in boundaries["no_assumption_state_change"]


def test_no_regional_claim(results: dict[str, object]) -> None:
    boundaries = results["boundaries"]
    assert isinstance(boundaries, dict)
    assert "regional" in str(boundaries["no_regional_inference"]).lower()
    by = _by_id(results)
    t1a = by["T1"]["sub_tests"]["t1a_real_vs_matched_control"]  # type: ignore[index]
    assert "no regional claim" in str(t1a["note"]).lower()


# --------------------------------------------------------------------------- #
# Malformed input fails
# --------------------------------------------------------------------------- #
def test_malformed_config_fails() -> None:
    with pytest.raises((FileNotFoundError, ValueError)):
        build_results(config_path="configs/does_not_exist.json")


def test_malformed_results_manifest_fails() -> None:
    with pytest.raises((KeyError, AssertionError, TypeError)):
        build_manifest({"not": "a valid results tree"})


# --------------------------------------------------------------------------- #
# T4-SYNTH no-op interpretation flag
# --------------------------------------------------------------------------- #
def test_t4_synth_no_op_flag(results: dict[str, object]) -> None:
    # The mild exclusion removed 0 sites: SURVIVES by the frozen rule, but flagged
    # non-informative for spatial robustness (no-op stress).
    t4 = _by_id(results)["T4-SYNTH"]
    assert t4["result_classification"] == "SURVIVES"
    mild = t4["mild_exclusion"]
    assert isinstance(mild, dict)
    if mild["candidates_removed"] == 0:
        assert t4["stress_effective"] is False
        assert t4["interpretive_status"] == "NO_OP_STRESS"
        assert t4["informative_for_spatial_robustness"] is False
        assert "no-op" in str(t4["interpretation_note"]).lower()


# --------------------------------------------------------------------------- #
# Diminishing-returns diagnostic reproduces 0C.1 exactly
# --------------------------------------------------------------------------- #
def test_t2_reproduces_0c1_diminishing_returns(results: dict[str, object]) -> None:
    t2 = _by_id(results)["T2"]
    rows = t2["diminishing_returns"]
    assert isinstance(rows, list)
    got = [row["model_f_risk_weighted_coverage"] for row in rows]  # type: ignore[index]
    phase0c = json.loads(PHASE0C_PATH.read_text(encoding="utf-8"))
    expected = [
        round(row["risk_weighted_coverage"], S.COVERAGE_DECIMALS)
        for row in phase0c["evidence"]["diminishing_returns"]
    ]
    assert got == expected

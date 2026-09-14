"""Frozen Phase 0D.4 adversarial stress parameters.

Every value here is fixed by ``docs/PHASE_0D4_PREREGISTRATION.md`` (§3-§9, as
amended 2026-09-14) **before** any adversarial result was executed. Nothing in
this module may change after a 0D.4 result exists without a dated deviation in
the preregistration. :data:`FROZEN_PARAMETERS` is the machine-readable snapshot
that the experiment records and the tests pin, so a silent post-freeze edit is
detectable.
"""

from __future__ import annotations

from types import MappingProxyType

EXPERIMENT_VERSION = "0D.4-1.0.0"
PREREGISTRATION = "docs/PHASE_0D4_PREREGISTRATION.md"
USE = "RESEARCH / SIMULATION PROTOTYPE ONLY"

# Tracked inputs (never mutated by 0D.4).
CONFIG_PATH = "configs/phase0c_synthetic.json"
PHASE0C_RESULTS_PATH = "outputs/reports/phase0c_synthetic_results.json"
PHASE0D3_RESULTS_PATH = "outputs/reports/phase0d3_substitution_results.json"

# Frozen analytical domain (full 0C.1 synthetic extent, EPSG:25830).
DOMAIN_MIN_E = 390_000.0
DOMAIN_MAX_E = 500_000.0
DOMAIN_MIN_N = 4_410_000.0
DOMAIN_MAX_N = 4_520_000.0

COVERAGE_DECIMALS = 6
SHARE_DECIMALS = 6
SECONDS_DECIMALS = 3

# --- T1 candidate-location fragility (DIAGNOSTIC) --------------------------
T1B_DROP_GREEDY_RANK = 0  # remove the single highest-ranked greedy-A site
T1C_DISPLACE_M = 2500.0  # exact uniform displacement magnitude, no repair
T1_SURVIVE_MAX_REL = 0.20
T1_DEGRADE_MAX_REL = 0.50
T1_DOMINANCE_SHARE = 0.50

# --- T2 diminishing returns (DIAGNOSTIC) ----------------------------------
# Site-count sequence is the config's own network_sizes; not restated here.
T2_SURVIVE_RATIO = 0.20  # last-segment per-site gain / peak per-site gain
T2_DEGRADE_RATIO = 0.05

# --- T3 weather / performance erosion -------------------------------------
T3_BASELINE_SCENARIO = "within-assumed-envelope"
T3_STRESS_SCENARIO = "wind-outside-assumed-envelope"  # 16 m/s, the genuine stress
T3_DESIGN_ARTIFACT_SCENARIO = "visibility-unknown"  # design rule, excluded
T3_DEGRADE_REL = 0.50
T3_FAIL_REL = 0.95

# --- T4 airspace / geographic exclusion (SYNTHETIC branch, DIAGNOSTIC) -----
# Geometry-defined, no result peeking. (min_e, max_e, min_n, max_n)
T4_MILD_BOX = (435_000.0, 455_000.0, 4_455_000.0, 4_475_000.0)  # ~3.3% of domain
T4_QUADRANT_MIN_E = 445_000.0  # NE quadrant = E >= mid AND N >= mid (25% of domain)
T4_QUADRANT_MIN_N = 4_465_000.0
T4_SURVIVE_MAX_REL = 0.20
T4_DEGRADE_MAX_REL = 0.50

# --- T6 threshold / gate fragility (DIAGNOSTIC) ---------------------------
T6_CENTRAL_NON_TRAVEL_S = 900.0  # balanced-central TTFRP non-travel budget
T6_STEP_S = 120.0  # == config a01_sweep_step_seconds; the ±1-step window
T6_DEGRADE_REL = 0.50

# Machine-readable frozen snapshot (pinned by tests; recorded in outputs).
FROZEN_PARAMETERS: MappingProxyType[str, object] = MappingProxyType(
    {
        "experiment_version": EXPERIMENT_VERSION,
        "domain_epsg25830": {
            "min_easting_m": DOMAIN_MIN_E,
            "max_easting_m": DOMAIN_MAX_E,
            "min_northing_m": DOMAIN_MIN_N,
            "max_northing_m": DOMAIN_MAX_N,
        },
        "T1": {
            "drop_greedy_rank": T1B_DROP_GREEDY_RANK,
            "displace_m": T1C_DISPLACE_M,
            "survive_max_rel": T1_SURVIVE_MAX_REL,
            "degrade_max_rel": T1_DEGRADE_MAX_REL,
            "dominance_share": T1_DOMINANCE_SHARE,
        },
        "T2": {
            "survive_ratio": T2_SURVIVE_RATIO,
            "degrade_ratio": T2_DEGRADE_RATIO,
        },
        "T3": {
            "baseline_scenario": T3_BASELINE_SCENARIO,
            "stress_scenario": T3_STRESS_SCENARIO,
            "design_artifact_scenario": T3_DESIGN_ARTIFACT_SCENARIO,
            "degrade_rel": T3_DEGRADE_REL,
            "fail_rel": T3_FAIL_REL,
        },
        "T4": {
            "mild_box": list(T4_MILD_BOX),
            "quadrant_min_easting_m": T4_QUADRANT_MIN_E,
            "quadrant_min_northing_m": T4_QUADRANT_MIN_N,
            "survive_max_rel": T4_SURVIVE_MAX_REL,
            "degrade_max_rel": T4_DEGRADE_MAX_REL,
        },
        "T6": {
            "central_non_travel_s": T6_CENTRAL_NON_TRAVEL_S,
            "step_s": T6_STEP_S,
            "degrade_rel": T6_DEGRADE_REL,
        },
    }
)

# Frozen criticality (amended 2026-09-14). Formal gate = evidence-qualified set.
FORMAL_CRITICAL_BRANCHES = ("T3-REAL", "T4-REAL", "T5")
DIAGNOSTIC_BRANCHES = ("T1", "T2", "T3-SYNTH", "T4-SYNTH", "T6")

# Formal-gate verdict vocabulary (repository governance: PHASE_0D_ROADMAP §0D.4).
GATE_VERDICTS = ("SURVIVES", "WEAKENED", "REFUTED", "INCOMPARABLE")
# Per-test classification vocabulary.
TEST_CLASSIFICATIONS = (
    "SURVIVES",
    "DEGRADES",
    "FAILS",
    "INCOMPARABLE",
    "NOT_EVALUATED",
)

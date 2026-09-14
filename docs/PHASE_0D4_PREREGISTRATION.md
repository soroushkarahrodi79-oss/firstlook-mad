# PHASE 0D.4 — PRE-REGISTERED ADVERSARIAL FALSIFICATION

> **Status:** pre-specified **2026-09-14**, on branch
> `claude/phase0d4-adversarial-falsification-20q34p` at base `c97426f`
> (PR #15 / Phase 0D.3 merged into `main`).
>
> **Session branch-name note.** The Phase 0D.4 mission brief suggested the branch
> `research/phase0d4-adversarial-falsification`. This cloud session imposed the
> branch name `claude/phase0d4-adversarial-falsification-20q34p`. The work is on
> the session-imposed branch; the difference is recorded here and in the PR, as
> the brief requires. No other divergence from the brief is implied.
>
> **This preregistration is committed and pushed ALONE, before any adversarial
> result is executed, at the project owner's explicit instruction (2026-09-14).**
> A separate later commit will add the implementation, the machine-readable
> outputs and the gate report. This two-commit ordering is a deliberate integrity
> control: the frozen rules below exist in Git history **before** the result
> artifacts do, and the owner reviews these rules before results are produced.
>
> **This is NOT a blinded pre-registration.** The Phase 0C.1 synthetic results
> (`outputs/reports/phase0c_synthetic_results.json`) and the Phase 0D.3
> substitution results are already tracked and known. The 0C/0D evidence is in
> hand. What is frozen here is the **adversarial experiment** — the stresses,
> parameters, metrics, thresholds, criticality, aggregation and verdict rules —
> **not ignorance of the inputs**. The thresholds below are chosen for
> defensibility (the config's own step sizes, the config's designated reference
> profile, natural collapse/flip criteria), **not** to obtain any particular
> verdict. No threshold may be changed after 0D.4 results are observed without a
> dated deviation (§12) that preserves the original result.
>
> **Use:** `RESEARCH / SIMULATION PROTOTYPE ONLY`. This document does not, and
> cannot, authorize `BUILD`, `REPOSITION`, `KILL`, `SAFE_TO_FLY`,
> `MADRID VALIDATED`, `SUPPORTED`, `REFUTED` (assumption-level), Phase 0D.5, or
> Phase 0E. It measures **fragility of the model mechanism**, nothing else.
>
> **Companion documents (authoritative, not duplicated):**
> `docs/PHASE_0D_ROADMAP.md` (§0D.4 gate vocabulary and lines of attack),
> `docs/PHASE_0D_PROTOCOL.md` (§4 per-test decision logic and frozen thresholds,
> §5 missing-data rule), `configs/phase0c_synthetic.json` (the frozen 0C.1 model),
> `outputs/reports/phase0c_synthetic_results.json` (the frozen 0C.1 results),
> `outputs/reports/phase0d3_substitution_results.json` (the frozen 0D.3 results),
> `docs/PHASE_0D3_PREREGISTRATION.md` (matched-scope conventions),
> `docs/ASSUMPTIONS.md` (assumption states), `docs/LIMITATIONS.md`,
> `docs/PRODUCT_CONTRACT.md`.

---

## 0. What 0D.4 tries to break, and what "usefulness" means here

The hypothesis that survived Phase 0C.1 is **negative / strongly
condition-dependent**, not positive. The 0C.1 robustness verdict is
`CONDITION_DEPENDENT_STRONG` with **no support for `BUILD`**; A-01 is
`STRONGLY_CONDITION_DEPENDENT`; the camera-vs-UAS comparison is `INCOMPARABLE`;
Phase 0D.3 was `SUBSTITUTION_UNINFORMATIVE`. **0D.4 does not test whether the
UAS/dock concept works.** It tests the **fragility of the surviving model
mechanism** — the deterministic falsification harness and the interpretable
signals it produces.

Concretely, the "usefulness / differentiation" placed under adversarial stress
is the mechanism's capacity to:

- produce a **positive coverage signal at all** (Model-A/F risk-weighted
  coverage materially above zero), and
- produce **stable, non-arbitrary, interpretable** qualitative signals (the
  A-01 travel-materiality label; the diminishing-returns shape; the
  architecture comparison).

An adversarial test **FAILS** when a pre-specified stress **erases** that signal
(coverage → 0) or **reverses/flips** a qualitative conclusion. A negative or
inconclusive 0D.4 result is a **successful** scientific outcome if it is true.
The mechanism is not rescued.

`EVIDENCE → STRESS CONDITION → MODEL RESPONSE → INTERPRETATION → DECISION` stay
strictly separate throughout.

---

## 1. Governance: this prompt does NOT replace repository governance

Per the mission brief's own instruction ("FIRST use any existing
repository-defined 0D.4 gate … Do not replace repository governance with this
prompt"), the following repository definitions are used **verbatim** and
**override** the brief's fallback structures:

- **Gate verdict vocabulary (from `docs/PHASE_0D_ROADMAP.md` §0D.4, line 57 and
  240):** `SURVIVES` / `WEAKENED` / `REFUTED` / `INCOMPARABLE`. The brief's
  fallback `ADVERSARIAL_ROBUST` / `ADVERSARIAL_CONDITION_DEPENDENT` /
  `ADVERSARIAL_FRAGILE` / `ADVERSARIAL_INCONCLUSIVE` is **NOT used**; it is only
  cited to explain semantic intent.
- **Lines of attack (roadmap §0D.4):** transit-time materiality (A-01); fire
  weather erasing benefit (A-04); airspace/geographic constraints collapsing
  eligibility (A-03); strongly diminishing returns (RQ6); simpler
  camera/tower/hybrid comparability; incomplete LOS/image-equivalence forcing
  `INCOMPARABLE`.
- **Frozen per-test thresholds (`docs/PHASE_0D_PROTOCOL.md` §4):** the A-01
  materiality bands (≥40% strengthens / <20% weakens), the A-03 erosion anchor
  (0C.1 A→F erosion 45.20–72.75 pp), the A-04 out-of-envelope bands, and the
  `INCOMPARABLE`-unless-LOS-evidence rule for the camera comparator, are reused
  where a test invokes them.
- **Missing-data rule (`docs/PHASE_0D_PROTOCOL.md` §5, roadmap global stop rule
  2):** absence of real evidence never becomes implicit support; a bounded
  sample is never promoted to a complete layer; `REAL` / `DERIVED` / `ASSUMED` /
  `SYNTHETIC` are kept distinct.

The brief's per-test fragility labels (`SURVIVES` / `DEGRADES` / `FAILS` /
`NOT_EVALUATED`) are used at the **per-test** level only (the repository defines
no per-test vocabulary), extended with `INCOMPARABLE` for the comparator test.
The **gate** uses the repository vocabulary above.

---

## 2. Entry preconditions (verified in code/tests before any result)

All must hold; failure of any one that blocks the whole gate → `STOP` with
`PRECONDITION_FAILED`. Failure that blocks only one test → that test is
`NOT_EVALUATED` and the gate proceeds.

1. **0C.1 reproduces byte-for-byte** from `configs/phase0c_synthetic.json` + the
   tracked engine. *(Verified 2026-09-14: `firstlook simulate` output is
   byte-identical to `outputs/reports/phase0c_synthetic_results.json`.)*
2. **Canonical A-02 present and integrity-linked:**
   `outputs/canonical/phase0d2/a02_madrid_city_fire_stations.json` is **tracked**
   (not gitignored), parses, holds 13 records, and its `source_sha256`
   (`5c3957…f8eb6`) matches the pre-registered value. *(Verified 2026-09-14.)*
3. **Assumption states unchanged:** A-01…A-09 remain as in `docs/ASSUMPTIONS.md`
   (A-01…A-04 all `TESTING`). 0D.4 changes none of them.
4. **No new external evidence** is acquired; no network dependency is introduced;
   `data/raw/**` and all historical 0C/0D outputs are immutable.

---

## 3. Frozen control (baseline)

The single frozen control is the **full-domain Phase 0C.1 synthetic model**, not
the Phase 0D.3 station-envelope experiment (0D.3 had a deliberately narrow
municipal scope; its ≈1.9%-of-domain extent is **not** the universal baseline).

- **Config:** `configs/phase0c_synthetic.json`, `seed = 260827`,
  `incident_count = 180`, `site_count = 10`, `network_sizes = [1,2,3,5,10]`,
  full analytical domain `EPSG:25830` E [390000, 500000], N [4410000, 4520000]
  (110 km × 110 km).
- **Reference profile:** `assumed-reference-envelope-v1` (the config's
  `reference_profile_id`) unless a test explicitly sweeps profiles.
- **Baseline metric values** (from the tracked, byte-reproduced 0C.1 results;
  quoted here so any post-result drift is detectable):
  - Model-A risk-weighted coverage @ 10 sites (reference): **0.553475**.
  - Model-F risk-weighted coverage @ 10 sites (reference, within-envelope):
    **0.101496**.
  - A→F erosion @ seed 260827: **45.20 pp**; across the 25 robustness seeds
    median **54.06 pp** (min 45.20, max 72.75).
  - Diminishing-returns (Model-F) by network size [1,2,3,5,10]:
    [0.023708, 0.023708, 0.030453, 0.054093, 0.101496].
  - Weather erosion (Model-F @ 10, reference): within-envelope **0.101496**,
    wind-outside-envelope **0.0**, visibility-unknown **0.0**.
  - A-01 bottleneck `travel_dominates_fraction`: balanced (900 s) **0.176**,
    low (300 s) **0.882**, high (2400 s) **0.0**; sweep dominance crosses to
    0 between 840 s (**0.294**) and 960 s (**0.0**); median-travel-share
    crossover bracketed **600–720 s**.
  - Architecture comparison: `comparison_status = INCOMPARABLE`
    (`all_comparisons_incomparable = true`).

Every adversarial value is compared against **this** control, on the **same**
incidents/seed/profile, changing exactly one stress dimension per test.

---

## 4. Evidence classes (frozen, per the protocol §5 taxonomy)

Every reported adversarial comparison is tagged with exactly one class:

- `REAL` — direct real observation.
- `DERIVED_FROM_REAL` — reproducibly computed from `REAL` (e.g. the canonical
  A-02 station locations).
- `SYNTHETIC` — the frozen 0C.1 synthetic model values.
- `SYNTHETIC_STRESS_TEST` — a synthetic perturbation introduced **only** for
  falsification, with values frozen in this document before results. **Never
  reported as real Madrid evidence.**
- `NOT_EVALUATED` — model structure or evidence insufficient for a valid test.

Binding: a `SYNTHETIC` or `SYNTHETIC_STRESS_TEST` value combined with `REAL`
values in one pipeline does **not** become `REAL`. Missing real evidence is
**never** classified `SURVIVES` (mission rule; §9).

---

## 5. Adversarial test families (frozen)

Six families. Each family's **criticality is frozen here** (§8) and may not be
changed after results. Where 0C.1 already computes a quantity, 0D.4 **reads the
frozen 0C.1 output** rather than recomputing a parallel model.

### T1 — Candidate-location fragility · DIAGNOSTIC

Question: is the model's coverage strongly dependent on favourable candidate
placement; does one site dominate; is the result a lucky spatial draw?

- **T1a — real-vs-matched-control (`DERIVED_FROM_REAL` / `SYNTHETIC`).** Reuse
  the frozen Phase 0D.3 matched-scope comparison **verbatim** (13 real A-02
  stations vs 13 synthetic control sites over the station-envelope support). No
  re-run needed; cite `outputs/reports/phase0d3_substitution_results.json`. This
  already showed the real placement produces **no material, seed-stable
  geometry signal** at matched scope (`SUBSTITUTION_UNINFORMATIVE`). Reported as
  diagnostic context; it is a **municipal-scope** result and emits **no regional
  claim**.
- **T1b — drop-top-site (`SYNTHETIC_STRESS_TEST`).** Remove the single
  highest-ranked candidate in the frozen 0C.1 greedy A-order
  (`selected_site_order[0]` = `SYN-SITE-003`) from the full network; recompute
  Model-A and Model-F risk-weighted coverage over all 180 incidents.
- **T1c — uniform displacement (`SYNTHETIC_STRESS_TEST`).** Displace **every**
  synthetic candidate site by a fixed magnitude **R = 2500 m** at a
  deterministic per-site bearing `θ_i = 2π · i / site_count` (i = site index; no
  RNG; fully deterministic). Sites are re-projected within the domain bounds;
  recompute Model-A and Model-F risk-weighted coverage.

**Primary metric:** Model-A risk-weighted coverage @ full network (placement is
a pure-geometry effect; Model-F reported as secondary because it also reads
synthetic operational booleans).
**Classification (frozen):**
- `SURVIVES`: `max` over {T1b, T1c} of `|relative Δ Model-A coverage|` **< 0.20**
  **and** no single site accounts for **≥ 50 %** of Model-A covered risk.
- `DEGRADES`: that `max |relative Δ|` in **[0.20, 0.50)** and no single-site
  ≥50% dominance.
- `FAILS`: that `max |relative Δ|` **≥ 0.50**, **or** one site accounts for
  ≥ 50 % of Model-A covered risk (result is a lucky/dominant single draw).

### T2 — Diminishing returns · DIAGNOSTIC

Question (RQ6): do added candidate sites keep producing meaningful benefit, or
do returns collapse after a few sites?

- Site-count sequence is the config's **own frozen** `network_sizes = [1,2,3,5,10]`
  (no search for a flattering count). Read Model-F `diminishing_returns` from the
  frozen 0C.1 output (`SYNTHETIC`).
- Matched-scope context (`DERIVED_FROM_REAL` / `SYNTHETIC`): from 0D.3, Model-A
  coverage is already **saturated at 1.0** for 10 and 13 sites over the
  station-envelope support — reported as diagnostic context on whether 13 real
  locations materially outperform a smaller configuration (they do not, at
  matched scope).

**Primary metric:** marginal Model-F risk-weighted-coverage gain **per added
site** across the sequence; ratio of the last-segment (5→10) per-site marginal
gain to the peak per-site marginal gain.
**Classification (frozen):**
- `SURVIVES`: last-segment per-site marginal gain **≥ 20 %** of the peak
  per-site marginal gain (returns not strongly diminishing).
- `DEGRADES`: last-segment per-site gain in **[5 %, 20 %)** of peak.
- `FAILS`: last-segment per-site gain **< 5 %** of peak, **or** the sequence
  saturates such that added sites contribute ~0 (RQ6 "strongly diminishing"
  confirmed).

### T3 — Weather / performance erosion · **CRITICAL**

A-04 weather observations are `NOT_ELIGIBLE`
(`WEATHER_EVIDENCE_NOT_OBSERVABLE`). Therefore this family is split:

- **T3-REAL — `NOT_EVALUATED` (`NOT_EVALUATED_MISSING_EVIDENCE`).** No real
  fire-day weather frequency test is possible (PROTOCOL §4.2 bands require real
  out-of-envelope frequency). A-04 inventory ≠ weather observations. This is
  **not** classified `SURVIVES`.
- **T3-SYNTH — `SYNTHETIC_STRESS_TEST`.** Use the three **existing** frozen 0C
  weather scenarios. Read Model-F risk-weighted coverage @ 10 sites, **reference
  profile** (the 0C.1 headline profile): within-envelope (baseline),
  wind-outside-envelope (the genuine meteorological stress), visibility-unknown.
  - **visibility-unknown is reported as a `DESIGN_ARTIFACT`, excluded from the
    classification** — PROTOCOL §4.2 declares UNKNOWN-visibility→0 a conservative
    **design rule**, not a weather-frequency signal.
  - The classification uses the **wind-outside-envelope** scenario only.

**Primary metric:** relative reduction of Model-F coverage under
wind-outside-envelope vs within-envelope, reference profile.
**Classification (frozen):**
- `SURVIVES`: relative reduction **< 0.50** (benefit materially retained under
  the adverse-wind envelope).
- `DEGRADES`: relative reduction in **[0.50, 0.95)**.
- `FAILS`: relative reduction **≥ 0.95** (benefit **erased** under the
  pre-specified adverse-weather envelope).

Profile dependence (the optimistic profile's `max_wind = 16` equals the stress
wind) is **reported as a diagnostic**, but the classification is fixed on the
reference profile to match the 0C.1 headline. **This synthetic stress is never
called "real Madrid weather."**

### T4 — Airspace / geographic constraints · DIAGNOSTIC

A-03 is `NOT_ELIGIBLE` (ENAIRE truncated 50/50; MDT05 is a 100 m × 100 m
window). Split:

- **T4-REAL — `NOT_EVALUATED` (`NOT_EVALUATED_MISSING_EVIDENCE`).** The bounded
  ENAIRE/IGN samples are **not** promoted to a full-domain constraint layer
  (enforced by test). Not classified `SURVIVES`.
- **T4-SYNTH — `SYNTHETIC_STRESS_TEST`.** Pre-specified rectangular exclusion of
  a candidate sub-region of the synthetic domain, defined **purely by domain
  geometry** (no result peeking). Domain midpoint = E 445000, N 4465000.
  - **T4-SYNTH-a (mild):** exclude the central box E [435000, 455000],
    N [4455000, 4475000] (20 km × 20 km ≈ 400 km², ≈ 3.3 % of domain).
  - **T4-SYNTH-b (quadrant):** exclude the north-east quadrant E ≥ 445000 **and**
    N ≥ 4465000 (25 % of domain by geometry).
  Any candidate site inside the excluded region is removed; incidents are
  unchanged (demand is not moved). Recompute Model-A and Model-F risk-weighted
  coverage over all 180 incidents.

**Primary metric:** relative reduction of Model-A coverage under the **mild**
(T4-SYNTH-a) exclusion. **Classification (frozen):**
- `SURVIVES`: relative reduction **< 0.20** under the mild exclusion.
- `DEGRADES`: relative reduction in **[0.20, 0.50)**.
- `FAILS`: relative reduction **≥ 0.50** (network collapses under modest spatial
  exclusion). The quadrant exclusion is reported for context, not classified.

**Never reported as an ENAIRE result.**

### T5 — Camera / hybrid comparator · **CRITICAL**

Recover the **existing** comparator from the frozen 0C.1 output
(`alternative_comparison` and the staged `fair_comparator`). Report `dock_only`,
`camera_only`, and `best_available_observation_proxy` (hybrid) risk-weighted
coverage and latency, plus the three fair-comparator stages.

- The real A-02 stations supply **no** `camera_available` attribute
  (`NOT_EVALUATED`); it is **never imputed**. The comparator therefore runs on
  the `SYNTHETIC` configuration only, stated as a limitation.
- Per PROTOCOL §4.5 and the tracked `fair_comparator`
  (`comparison_status = INCOMPARABLE`): under **unknown LOS / smoke / FOV /
  observation-equivalence**, the camera figure is an **optimistic upper bound**,
  not a ranking.

**Classification (frozen): `INCOMPARABLE`.** The architecture-ranking question is
**structurally unadjudicable** from available evidence. The raw numbers (e.g.
`camera_only` risk-weighted coverage ≈ 0.313 vs `dock_only` ≈ 0.101) are
reported **only** as an optimistic camera upper bound and explicitly **not**
read as camera-beats-dock. Any evidence that would make it comparable (defensible
LOS/smoke/FOV/equivalence) does not exist in the repository and is not acquired.

### T6 — Threshold / gate fragility · **CRITICAL**

Question: does a scientific conclusion depend on **narrowly** crossing an
existing threshold; does a small perturbation flip a gate?

- **Target:** the A-01 travel-materiality qualitative label, the one
  threshold-sensitive label 0C.1 emits (`A_01_travel_materiality`:
  `CONDITION_DEPENDENT` iff any `travel_dominates_fraction > 0`, else
  `WEAKENED_IN_TESTED_GRID`).
- **Perturbation (frozen):** ± **one** `a01_sweep_step_seconds` (= **120 s**, the
  config's own step) around the balanced-central TTFRP non-travel budget
  (**900 s**), i.e. non-travel ∈ {780, 900, 1020} s, evaluated on the **fixed
  full-F-survivor cohort** exactly as 0C.1's `a01_sensitivity` does (same
  survivor-bias caveat).
- **Conclusion under test (frozen):** boolean `B = (travel_dominates_fraction >
  0)` at the central 900 s.

**Classification (frozen):**
- `FAILS`: `B` **flips** (true↔false) anywhere within the ±120 s window — a
  one-step perturbation flips the qualitative A-01 gate.
- `DEGRADES`: `B` holds across the window but `travel_dominates_fraction`
  changes by **> 50 %** relative across the window.
- `SURVIVES`: `B` holds and `travel_dominates_fraction` changes by **≤ 50 %**
  relative across the window.

Also **reported** (not classified): the distance from 900 s to the observed
dominance-flip interval (840–960 s from the frozen sweep); and, as secondary
context, that the 0D.3 material-relative-delta threshold (0.20) was **not**
narrowly crossed (0D.3 `primary_relative_delta` = 0.0598, far below 0.20).

### No optional seventh test

0D.4 is bounded to T1–T6. No additional adversarial test is added; 0D.4 is not
turned into an unbounded sensitivity study.

---

## 6. Per-test reporting schema (frozen)

For every adversarial comparison the machine-readable output records:

1. `baseline_value`; 2. `adversarial_value`; 3. `absolute_delta`;
4. `relative_delta` (where meaningful); 5. `threshold_crossing` (which frozen
threshold, and whether crossed); 6. `effect_direction`; 7. `interpretability`
note; 8. `evidence_class` (§4); plus `stress_id`, `target_assumption`,
`baseline_config`, `stress_config`, `parameters_frozen_before_execution` (a
copy of the frozen params from this document), `criticality`,
`result_classification`, and `reason`.

---

## 7. Per-test classification vocabulary (frozen)

`SURVIVES` / `DEGRADES` / `FAILS` / `INCOMPARABLE` / `NOT_EVALUATED`.

- `SURVIVES`: mechanism materially similar; no failure threshold crossed.
- `DEGRADES`: performance materially worsens but the test's criterion is not
  failed.
- `FAILS`: the stress erases or reverses the meaningful result / crosses the
  failure threshold.
- `INCOMPARABLE`: the comparison the test requires is structurally unadjudicable
  from available evidence (reserved for T5).
- `NOT_EVALUATED`: evidence or model structure insufficient for a valid test
  (e.g. T3-REAL, T4-REAL). **Missing evidence is never `SURVIVES`.**

---

## 8. Criticality (frozen BEFORE results — may not be downgraded after)

- **CRITICAL:** **T3** (weather / performance erosion), **T5** (camera / hybrid
  comparator), **T6** (threshold / gate fragility).
- **DIAGNOSTIC:** **T1** (candidate-location fragility), **T2** (diminishing
  returns), **T4** (airspace / geographic constraints).

Rationale (fixed here, before results): T3, T5, T6 operate on the frozen
full-domain 0C.1 mechanism against **existing** thresholds and comparators and
directly target the roadmap's core lines of attack (weather erasing benefit,
architecture comparability, threshold fragility). T1, T2, T4 are, at their
evaluable scopes, either structurally low-leverage (T1/T2 at the saturated
matched scope; T1 full-domain placement perturbation) or synthetic-only spatial
stress (T4-SYNTH); they **inform** robustness but must not, by themselves, drive
the gate. **A failed CRITICAL test is never re-labelled DIAGNOSTIC after
results** (mission rule).

---

## 9. Gate aggregation (frozen BEFORE results)

The final gate uses the **repository** vocabulary
`SURVIVES` / `WEAKENED` / `REFUTED` / `INCOMPARABLE`, decided over the **CRITICAL
set only** (DIAGNOSTIC tests inform but cannot move the gate), in this
**precedence** (first matching rule wins):

1. **`REFUTED`** iff **either** (a) a CRITICAL test's `FAILS` is **unconditional**
   — the benefit is erased/reversed even at the **mildest** pre-specified stress
   setting of that test — **or** (b) **≥ 2 of the 3** CRITICAL tests are `FAILS`.
   *(A single, purely conditional collapse is not `REFUTED`.)*
2. else **`WEAKENED`** iff **≥ 1** CRITICAL test is `FAILS` (a conditional
   collapse under a specific pre-specified condition) **or** `DEGRADES`.
3. else **`INCOMPARABLE`** iff **fewer than 2** CRITICAL tests reached a definite
   `{SURVIVES, DEGRADES, FAILS}` adjudication (too many CRITICAL tests
   `NOT_EVALUATED`, and/or the only remaining decisive comparator is
   `INCOMPARABLE`, so an overall robustness judgement cannot be made).
4. else **`SURVIVES`** (≥ 2 CRITICAL tests adjudicated, all `SURVIVES`, none
   `FAILS`/`DEGRADES`).

Notes bound before results:
- `T5` is expected to be `INCOMPARABLE` by construction (no LOS evidence). Under
  the precedence above, `T5`'s `INCOMPARABLE` **does not dominate** the gate as
  long as **≥ 2** CRITICAL tests (i.e. T3 and T6) are adjudicated; it is reported
  as a standing per-test finding regardless of the gate.
- All four gate verdicts are reachable under these rules; **none is
  pre-determined**. The verdict is **not** asserted in this preregistration
  commit; it is produced in the later result commit by applying these rules.

**No-claim-inflation (binding).** Whatever the gate verdict, 0D.4 emits **no**
`BUILD` / `REPOSITION` / `KILL` / `SAFE_TO_FLY` / `MADRID_VALIDATED` /
`SUPPORTED` / `REFUTED` (assumption-level); it changes **no** assumption state;
it emits **no** regional claim from municipal-only evidence. A gate `REFUTED` or
`WEAKENED` is scoped explicitly to *"under the pre-specified adversarial stress,
the model mechanism …"*, never to Madrid reality.

---

## 10. Missing-evidence handling (frozen)

- T3-REAL and T4-REAL are `NOT_EVALUATED` (`NOT_EVALUATED_MISSING_EVIDENCE`);
  they are **never** promoted to `SURVIVES`, and their synthetic counterparts
  (T3-SYNTH, T4-SYNTH) carry the `SYNTHETIC_STRESS_TEST` class and are never
  reported as real Madrid evidence.
- If a CRITICAL test cannot be evaluated at all, it counts toward clause 9.3
  (`INCOMPARABLE`), never toward `SURVIVES`.
- If an entry precondition in §2 that blocks the **whole** gate fails, the run
  stops with `PRECONDITION_FAILED` and no gate verdict is emitted.

---

## 11. Stop rules and boundaries

- No stress parameter in §5 changes after §5 is committed, within one run
  (enforced by test: a frozen-parameters snapshot is compared to the executed
  parameters).
- No operational property of the real A-02 stations is invented; where a test
  would need one, that test is `NOT_EVALUATED`.
- No new external dataset; no network dependency; `data/raw/**` and all 0C/0D
  outputs immutable.
- No assumption changes `TESTING → SUPPORTED/REFUTED`. 0D.4 decides no
  `BUILD/REPOSITION/KILL`.
- After packaging 0D.4: **HARD STOP.** Phase 0D.5 is not started.

---

## 12. Deviations

Any change to §3–§9 after 0D.4 results exist is recorded here with date, reason
and authorizer, and the verdict under these original rules is reported alongside.

- **Initial state:** no deviations.

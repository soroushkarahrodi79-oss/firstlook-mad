# PHASE 0D.3 — PRE-REGISTERED STAGED REALITY SUBSTITUTION

> **Status:** pre-registered **2026-09-14**, on branch
> `research/phase0d3-reality-substitution` at base `abdd260` (PR #14 merged into
> `main`). The Phase 0D.3 experiment design below was **frozen before any 0D.3
> result output was generated**.
>
> **This is NOT a blinded pre-registration.** Phase 0D.1 (acquisition) and Phase
> 0D.2 (normalization and semantic fitness) evidence is already known: A-02 is
> `ELIGIBLE_WITHIN_DECLARED_SCOPE` (13 Madrid-municipality fire stations), and
> A-01, A-03, A-04 are `NOT_ELIGIBLE`. The design is frozen with that knowledge
> in hand. What is frozen here is the **experiment**, not ignorance of the
> inputs.
>
> **Use:** `RESEARCH / SIMULATION PROTOTYPE ONLY`. This document does not, and
> cannot, authorize `BUILD`, `SAFE_TO_FLY`, `MADRID VALIDATED`, Phase 0D.4, or
> Phase 0E.
>
> **Companion documents (authoritative, not duplicated):**
> `docs/PHASE_0D_ROADMAP.md` (§0D.3), `docs/PHASE_0D2_PREREGISTRATION.md`
> (analytical domain, A-02 rules, non-claims), `docs/PRODUCT_CONTRACT.md`
> (analytical domain, hypothesis), `configs/phase0c_synthetic.json` (the frozen
> 0C.1 model), `outputs/canonical/phase0d2/a02_madrid_city_fire_stations.json`
> (the real A-02 evidence).
>
> These rules are frozen. Any change made after 0D.3 results exist is a **dated
> deviation** recorded in §11, and the verdict under the original rules is
> reported alongside. No threshold may be altered after seeing 0D.3 results
> without preserving the original verdict.

---

## 1. Question

When exactly one synthetic assumption of the frozen Phase 0C.1 model — the
**candidate-site locations** (A-02's target role, `PHASE_0D2_PREREGISTRATION.md`
§3) — is replaced by the real, integrity-verified A-02 fire-station locations
that survived Phase 0D.2, **and the comparison is confined to a matched
geographic support so that scope is held constant**, is the resulting change in
the model's *geometry-only* outputs a scientifically interpretable effect?

This is **not** a test of whether the UAS thesis is true, **not** Madrid
validation, **not** a `BUILD` signal, and **not** an operational or TTFRP claim.
`EVIDENCE → INTERPRETATION → DECISION` stay separate.

## 2. What must be true before any result is generated (entry preconditions)

All of the following are verified in code/tests before results are produced;
failure of any one forces `STOP` / `SUBSTITUTION_INVALID` (§9):

1. **0C.1 reproducible from tracked inputs.** `configs/phase0c_synthetic.json`
   + the tracked engine regenerate `outputs/reports/phase0c_synthetic_results.json`
   byte-for-byte. (Verified 2026-09-14.)
2. **Canonical A-02 present and integrity-linked.** The tracked file
   `outputs/canonical/phase0d2/a02_madrid_city_fire_stations.json` parses, holds
   13 records, and its recorded `source_sha256`
   (`5c3957873878d30c93556c75544b6d7740c648b84b0424682dfac655842f8eb6`) is
   preserved in the substitution manifest. A missing or altered file → explicit
   failure (never a reconstructed or fabricated substitute).
3. **A-02 is the only assumption eligible to enter.** Per Phase 0D.2, only A-02
   is `ELIGIBLE_WITHIN_DECLARED_SCOPE`. A-01, A-03, A-04 are `NOT_ELIGIBLE` and
   **cannot** enter substitution. This is enforced by test.

## 3. Analytical domain vs declared scope (the mandatory distinction)

- **Analytical domain (0C.1 / Product Contract):** Comunidad de Madrid,
  represented in the 0C.1 model by the synthetic extent `EPSG:25830`
  E 390,000–500,000 m, N 4,410,000–4,520,000 m (110 km × 110 km = **12,100
  km²**).
- **Declared scope of the real A-02 evidence:** Madrid **municipality** only
  (`declared_coverage = MADRID_MUNICIPALITY`). Its geographic support is the
  axis-aligned bounding box of the 13 canonical stations in `EPSG:25830`,
  E [435063.001, 449956.520], N [4465720.117, 4481279.118]
  (≈14.89 km × 15.56 km ≈ **231.7 km²**, ≈ **1.9 %** of the analytical domain;
  values from the Phase 0D.2 quality report `easting_range_m` /
  `northing_range_m`).

**Binding rule.** Replacing a region-wide synthetic candidate layer with 13
municipal stations and reading the result as a *regional* real-vs-synthetic test
would confound **reality substitution** with **geographic scope reduction**.
This experiment therefore holds scope constant by construction: **both** arms
operate on the **same** municipal support (§5). No regional inference may be
emitted from this municipal-only experiment (enforced by test).

## 4. Entry decision vocabulary (frozen)

Exactly one of `PROCEED` / `LIMITED_PROCEED` / `STOP`, with the mission's
semantics:

- `PROCEED` — real evidence can validly replace the synthetic assumption across
  the **full analytical domain**.
- `LIMITED_PROCEED` — real evidence is **scope-restricted**, but a scientifically
  valid **matched-scope** comparison can be constructed.
- `STOP` — any of: no eligible real evidence; matched scope not definable
  defensibly; 0C.1 not reproducible; scope-matched synthetic control not
  generable; substitution changes >1 assumption; the comparison would be
  scientifically misleading; required tracked inputs unavailable in this
  environment.

`LIMITED_PROCEED` is **not** to be forced. The entry decision is recorded in the
gate report with its justification against every `STOP` condition.

## 5. Experiment design (frozen)

Two arms over an **identical** matched geographic support and **identical**
non-A-02 parameters. The single manipulated variable is the candidate-site
locations.

### 5.1 Matched geographic support

`SUPPORT` = the axis-aligned bounding box of the 13 canonical A-02 station
coordinates in `EPSG:25830` (computed deterministically from the canonical file;
not hardcoded, not padded, not invented). This is the **exact geographic support
of the real evidence**, already documented in Phase 0D.2. Prefer-an-authoritative-
municipality-polygon was considered: none is tracked in the repository (only
axis-aligned sanity envelopes in `normalization/models.py`); acquiring a new
boundary dataset is prohibited (§0D.3 mission rule) and manually drawing a
polygon is prohibited. The station bounding box is the defensible spatial rule
already in the repository, so it is used for **both** arms.

### 5.2 Scope-restricted 0C.1 configuration

`scope_config` = `configs/phase0c_synthetic.json` with **only** two fields
changed: `bounds` ← `SUPPORT`, and `site_count` ← 13 (to match the real
candidate count, isolating the location effect; see §5.5). Everything else is
**identical**: `seed = 260827`, `incident_count = 180`, all three UAS profiles,
all TTFRP scenarios, all weather scenarios, camera assumptions, thresholds,
`robustness_seeds`, CRS. The scope restriction is applied **identically to both
arms**; it is the matched support, not a second substituted variable.

### 5.3 CONTROL arm

`incidents, control_sites = generate_inputs(scope_config)` using the **original,
unmodified** synthetic candidate-location mechanism (uniform draw over
`SUPPORT`). Control sites carry their synthetic operational attributes exactly as
0C.1 generates them.

### 5.4 REAL-substitution arm

The **same** `incidents` (byte-identical demand), the **same** seed, scenarios,
weather, travel model, thresholds and constraints — but the candidate sites are
the 13 real canonical fire stations, mapped to `CandidateSite` with:

- `site_id = "A02-" + source_identifier`, `point = (easting_m, northing_m)`;
- `nature = DERIVED` (real-derived provenance; a `DERIVED` value is added to
  `EvidenceNature` for this purpose, additively);
- **all operational attributes = `None`** (`assumed_available`, `uas_available`,
  `communications_available`, `camera_available`,
  `camera_communications_available`). These are the properties Phase 0D.2 marks
  `NOT_EVALUATED`. They are **never invented** (§6).

### 5.5 Candidate count

The primary comparison matches count (13 synthetic vs 13 real) so that the only
difference between arms is **location**. Candidate count is nonetheless reported
as a delta against the native 0C.1 count (10). A secondary, native-count control
(`site_count = 10`) is reported for transparency; it is **not** the primary
comparison and does not affect the verdict.

## 6. A-02 non-claims (binding)

The 13 real stations are **real public-asset locations only**. They are **not**
drone docks, launch sites, UAS bases, operational/authorised/available/
dispatch-capable/safe-to-fly/permitted facilities. Every operational property
stays `NOT_EVALUATED`. Consequently:

- Only **geometry-only** metrics (§7) that do **not** read any candidate
  operational attribute are compared. In the 0C.1 engine these are coverage
  models **A/B/C/D/E** and pure nearest-distance geometry; model **F** and the
  camera comparator read candidate operational booleans and are therefore
  **`NOT_EVALUATED`** for the REAL arm (holding them constant would require
  inventing the real stations' availability). Marking them `NOT_EVALUATED` is the
  honest outcome, not a failure to compute.
- No model-derived time is called a real TTFRP baseline. A-01 stays
  `BASELINE_NOT_OBSERVABLE`.

## 7. Metrics (frozen before execution)

For each arm, computed identically. **Primary metric in bold.**

1. `candidate_count`.
2. **`nearest_distance_m` — median** incident-to-nearest-candidate Euclidean
   distance (also p90, max, min, mean), over all 180 incidents, nearest by pure
   geometry (`euclidean_distance_m`), no feasibility gate, no operational filter.
3. `model_a_risk_weighted_coverage` at each of the three **pre-existing** profile
   one-way ranges (`max_sortie_distance_m / 2` = 15,000 / 20,000 / 25,000 m),
   reusing `evaluate_network(model=A_DISTANCE)`. No new radius is invented.
4. `candidate_dispersion`: candidate bounding-box area (m²), mean
   nearest-neighbour distance among candidates, centroid (E, N) — the minimal
   dispersion diagnostics needed to interpret a nearest-distance change.

Explicitly `NOT_EVALUATED` (operational properties not established by real
evidence): model-F feasibility/coverage, TTFRP seconds as any baseline, weather
erosion, camera / hybrid comparison, scenario survival, gate outcomes.

For each reported metric the results record: (1) CONTROL absolute, (2) REAL
absolute, (3) DELTA (REAL − CONTROL), (4) effect direction, (5) whether any
pre-existing threshold is crossed, (6) whether the change is scientifically
interpretable.

## 8. "Material" and threshold-crossing (frozen before the real result)

- **Material effect (primary):** the relative change in **median**
  `nearest_distance_m`, `|DELTA| / CONTROL`, is **≥ 0.20 (20 %)**. Twenty percent
  is a pre-set, non-tuned magnitude chosen before any result is seen; it is not
  adjusted afterwards.
- **Threshold crossing:** under any of the three pre-existing profile ranges, one
  arm's `model_a_risk_weighted_coverage` reaches full coverage (`= 1.0`) while
  the other does not — i.e. the substitution changes whether every synthetic
  incident is within one-way range of some candidate.
- **Direction stability (robustness):** §5's comparison is re-run over the 25
  pre-declared 0C.1 `robustness_seeds`. For each seed, `incidents` and
  `control_sites` are regenerated (REAL sites are seed-independent). Direction is
  **stable** iff `sign(median_nearest(REAL) − median_nearest(CONTROL))` is the
  same on **all 25** seeds and equals the primary-seed sign. This is the only
  robustness check; no broad sensitivity phase is started.

## 9. Verdict vocabulary and rule (frozen)

Exactly one of `SUBSTITUTION_INFORMATIVE` / `SUBSTITUTION_WEAK_SIGNAL` /
`SUBSTITUTION_UNINFORMATIVE` / `SUBSTITUTION_INVALID`, evaluated in this
precedence:

1. **`SUBSTITUTION_INVALID`** if any hold: canonical A-02 missing / hash mismatch;
   `SUPPORT` not definable; >1 assumption differs between arms; outputs
   non-deterministic across two runs; A-01/A-03/A-04 attempted entry; a metric
   used in the comparison requires an operational property real evidence does not
   establish. (A defensible matched comparison cannot be completed.)
2. Otherwise the comparison is valid and reproducible; then:
   - **`SUBSTITUTION_UNINFORMATIVE`** if the effect is **not** material **and**
     **no** threshold is crossed under any profile — the real evidence has too
     little geometric leverage at matched scope to test the model.
   - **`SUBSTITUTION_WEAK_SIGNAL`** if the effect **is** material on the primary
     metric **or** a threshold is crossed, but the effect is small, unstable
     (direction not stable across all 25 seeds), profile-dependent, and/or
     **strongly scope-limited** (municipal support ≈1.9 % of the analytical
     domain, demand synthetic).
   - **`SUBSTITUTION_INFORMATIVE`** — reserved for a valid, reproducible,
     material, seed-stable effect **relevant to the tested mechanism across the
     analytical domain**.

**Pre-registered structural cap.** Two facts known before running — A-02 covers
≈1.9 % of the analytical domain, and the demand field is synthetic because A-01
is `BASELINE_NOT_OBSERVABLE` — mean that no effect measured here can be
"relevant to the tested mechanism across the analytical domain."
**`SUBSTITUTION_INFORMATIVE` is therefore unreachable in this configuration by
pre-registration; the maximum attainable verdict is `SUBSTITUTION_WEAK_SIGNAL`.**
This cap is a structural design decision fixed before results exist, not a
post-hoc downgrade.

`SUBSTITUTION_INFORMATIVE` does **not** mean the hypothesis is supported, under
any circumstances.

## 10. Stop rules and boundaries

- One assumption only. If the design ever changes more than candidate locations
  between arms → `SUBSTITUTION_INVALID`.
- No operational property is invented; if a needed metric requires one, that
  metric is `NOT_EVALUATED`, not estimated.
- No new external dataset is acquired; no network dependency is introduced.
- No assumption changes `TESTING → SUPPORTED/REFUTED`; Phase 0D.3 does not decide
  `BUILD/REPOSITION/KILL`.
- After packaging 0D.3: **HARD STOP.** Phase 0D.4 is not started.

## 11. Deviations

A change to §3–§9 after 0D.3 results exist is recorded here with date, reason and
authorizer, and the verdict under these original rules is reported alongside.
**Initial state: no deviations.**

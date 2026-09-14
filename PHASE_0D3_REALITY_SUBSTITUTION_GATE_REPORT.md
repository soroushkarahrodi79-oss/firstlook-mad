# PHASE 0D.3 — STAGED REALITY SUBSTITUTION GATE REPORT

> **Use:** `RESEARCH / SIMULATION PROTOTYPE ONLY`. **Date:** 2026-09-14.
> **Branch:** `research/phase0d3-reality-substitution` (base `abdd260`, PR #14
> merged). **Pre-registration:** `docs/PHASE_0D3_PREREGISTRATION.md`. The design
> was pre-specified within the execution session before the experiment was run
> per the recorded workflow; **however, the preregistration, implementation and
> result outputs were committed together, so that ordering is not independently
> verifiable from Git history.** Not blinded — 0D.1/0D.2 evidence was already
> known. No threshold was changed after the results were observed.
>
> **Entry decision:** `LIMITED_PROCEED` · **Verdict:** `SUBSTITUTION_UNINFORMATIVE`.
>
> This report does **not** authorize `BUILD`, `SAFE_TO_FLY`, `MADRID VALIDATED`,
> Phase 0D.4 or Phase 0E, and changes **no** assumption state.

Machine-readable companions:
`outputs/reports/phase0d3_substitution_manifest.json` (what changed) and
`outputs/reports/phase0d3_substitution_results.json` (per-metric deltas). Both
regenerate byte-for-byte via `uv run python scripts/run_phase0d3_substitution.py`.

---

## Evidence

- **Real evidence substituted (A-02).** The 13 canonical Madrid-municipality
  fire stations from Phase 0D.2,
  `outputs/canonical/phase0d2/a02_madrid_city_fire_stations.json`
  (`source_sha256 5c39578738…f8eb6`, classification `REAL_SOURCE_DATA`,
  `declared_coverage = MADRID_MUNICIPALITY`, CRS `EPSG:25830`). Existence and
  **location only**; every operational property is `NOT_EVALUATED`.
- **Synthetic reference (0C.1).** `configs/phase0c_synthetic.json`, verified to
  regenerate `outputs/reports/phase0c_synthetic_results.json` byte-for-byte
  (reproducibility precondition met, 2026-09-14).
- **Eligibility (Phase 0D.2).** Only A-02 is `ELIGIBLE_WITHIN_DECLARED_SCOPE`.
  A-01, A-03, A-04 are `NOT_ELIGIBLE` and are excluded from entry by test.

## Experimental design

A single, attribution-preserving substitution over a **matched station-envelope
extent**, comparing **geometry-only** metrics. The Phase 0C.1 engine
(`generate_inputs`, `evaluate_network`, `euclidean_distance_m`) is reused
unchanged; no second model is built.

- **Matched extent** = the axis-aligned **bounding box of the 13 real station
  locations** in `EPSG:25830`: E [435063.001, 449956.520],
  N [4465720.117, 4481279.118] (≈14.89 × 15.56 km ≈ **231.7 km²** = **1.9 %** of
  the 12,100 km² 0C.1 analytical domain). Derived from the canonical file (0D.2
  `easting_range_m`/`northing_range_m`); not padded, not invented, no new dataset
  acquired. **This is a station-envelope extent, NOT the official Madrid
  municipality boundary and NOT the source dataset's legal/administrative
  support** — a conservative, repository-derived extent used only to hold
  geographic support constant between arms. (The source's declared coverage
  remains `MADRID_MUNICIPALITY`, a separate source fact.)
- **Both arms** use one scope-restricted config (only `bounds` and `site_count`
  changed vs 0C.1), one seed (`260827`), one identical incidents list, matched
  candidate count (13 vs 13). The single manipulated variable is candidate
  **location**.
- **Metrics (frozen §7):** incident-to-nearest-candidate distance
  (median/p90/max/min/mean; **primary = median**), Model-A risk-weighted coverage
  at the three pre-existing profile one-way ranges (15/20/25 km), and candidate
  dispersion diagnostics.
- **Material rule (frozen §8):** |relative Δ of median nearest distance| ≥ 0.20.
  **Threshold crossing:** one arm reaches full Model-A coverage (=1.0) and the
  other does not. **Robustness:** direction stability of the median effect across
  the 25 pre-declared 0C.1 seeds.

## Entry decision

**`LIMITED_PROCEED`.** A-02 is scope-restricted to the Madrid municipality, so it
cannot validly replace the synthetic candidate layer across the full analytical
domain (rules out `PROCEED`). No `STOP` condition holds: 0C.1 reproduces from
tracked inputs; the matched station-envelope extent is definable from tracked 0D.2 outputs; the
scope-matched synthetic control is generable; exactly one assumption is
substituted; confining the comparison to geometry-only metrics keeps it
non-misleading; and all required inputs are tracked and available in this
environment. `LIMITED_PROCEED` was not forced — it is the honest classification.

## Control

Synthetic 0C.1 candidate mechanism (uniform draw) over the matched station-envelope extent, 13
sites, seed 260827, against the 180 synthetic incidents. Candidate sites keep
their synthetic operational attributes.

- median nearest distance **2067.102 m**; p90 4141.199 m; max 5340.280 m;
  mean 2174.801 m.
- Model-A risk-weighted coverage: **1.0** at 15 km, 20 km and 25 km one-way.
- dispersion: candidate bbox 152.3 M m²; mean nearest-neighbour 2120.935 m.

## Reality substitution

Identical incidents/seed/scenarios/thresholds; candidate sites = the 13 real
fire stations (operational properties `None` = `NOT_EVALUATED`, provenance
`DERIVED`).

- median nearest distance **2190.772 m**; p90 4236.809 m; max 6002.968 m;
  mean 2381.925 m.
- Model-A risk-weighted coverage: **1.0** at 15 km, 20 km and 25 km one-way.
- dispersion: candidate bbox 231.7 M m²; mean nearest-neighbour 2945.079 m.

## Comparison

| Metric | CONTROL | REAL | Δ (REAL−CTRL) | rel. Δ | Direction | Threshold crossed? | Interpretable? |
|---|---|---|---|---|---|---|---|
| **nearest median (m)** | 2067.102 | 2190.772 | +123.670 | **+5.98 %** | REAL greater | — | yes, not material |
| nearest p90 (m) | 4141.199 | 4236.809 | +95.610 | +2.31 % | REAL greater | — | yes |
| nearest max (m) | 5340.280 | 6002.968 | +662.688 | +12.41 % | REAL greater | — | yes |
| nearest mean (m) | 2174.801 | 2381.925 | +207.124 | +9.52 % | REAL greater | — | yes |
| Model-A cov. @15 km | 1.0 | 1.0 | 0 | 0 | none | **no** | saturated |
| Model-A cov. @20 km | 1.0 | 1.0 | 0 | 0 | none | **no** | saturated |
| Model-A cov. @25 km | 1.0 | 1.0 | 0 | 0 | none | **no** | saturated |

- **Primary metric not material:** +5.98 % < the 20 % pre-registered bar.
- **No threshold crossing:** the 15–25 km ranges dwarf the ~15 km support, so
  Model-A coverage saturates at 1.0 in **both** arms and cannot discriminate.
- **Direction unstable:** across the 25 pre-declared seeds the median effect is a
  near-coin-flip — REAL greater on 13 seeds, REAL smaller on 12
  (`direction_stable = false`). The primary-seed sign is not robust.
- **Secondary (native-count) control, transparency only:** at the native 0C.1
  count (10 synthetic vs 13 real) the real set's median nearest distance is
  *lower* (2190.8 m vs 2547.1 m) — but that mixes a count change with the
  location change and is not the verdict basis.

## What changed

- The candidate-site **locations** (uniform-synthetic → 13 real fire stations)
  and, as a reported side effect, candidate count vs the native 0C.1 value
  (10 → 13). The real stations fill the support box more widely (larger mean
  nearest-neighbour, 2945 vs 2121 m) and cluster centre-north, shifting the
  centroid ~2.0 km west and ~1.0 km south of the synthetic centroid.
- Median incident-to-nearest-candidate distance rose ~6 % under the primary seed.

## What did not change

- Incidents/demand, seed, UAS profiles, TTFRP scenarios, weather scenarios,
  travel model, thresholds, scoring logic, CRS and the geographic support — all
  identical across arms.
- Model-A coverage (saturated in both arms).
- Assumption states: A-01/A-02/A-03/A-04 remain exactly as Phase 0D.2 left them.
  No `TESTING → SUPPORTED/REFUTED`. A-01 stays `BASELINE_NOT_OBSERVABLE`.
- Operational properties of the real stations stay `NOT_EVALUATED`; no station
  became a dock, launch site, or safe-to-fly/available/permitted facility.

## Limitations

- **Scope (dominant).** The support is ~1.9 % of the analytical domain; nothing
  here generalizes to the Comunidad de Madrid.
- **Synthetic demand.** Incidents are synthetic-uniform (A-01
  `BASELINE_NOT_OBSERVABLE`); the metric measures how each candidate set blankets
  a uniform field, not real Madrid incidents.
- **Operational blindness.** Model-F feasibility, TTFRP-as-baseline, weather
  erosion and the camera/hybrid comparison are `NOT_EVALUATED` because the real
  evidence establishes no operational properties. Only geometry was compared.
- **Coverage saturation.** The pre-existing profile ranges (15–25 km) exceed the
  support diameter, so Model-A coverage cannot discriminate the arms.
- **Count confound in the secondary control** (10 vs 13), explicitly excluded
  from the verdict.
- Determinism verified on this environment (uv, Python 3.12, pyproj 3.7.2);
  1 mm rounding mitigates but does not prove cross-platform bit-identity.

## Missing evidence

- Real incident-level demand for Madrid (A-01) — none; `BASELINE_NOT_OBSERVABLE`.
- Regional/INFOMA candidate assets beyond the municipality (A-02 regional layer).
- Real airspace/terrain layers (A-03) and fire-day weather observations (A-04).
- Any operational property (availability, dispatch, docking, permission) of the
  real stations — all `NOT_EVALUATED`.

## Risks

- **Scope-reduction confound** — mitigated by the matched-support design; both
  arms share the identical station bounding box, so scope is constant, not a
  second variable.
- **Reading a municipal result as regional** — blocked by pre-registration and by
  test (`no regional inference`); the verdict is capped below
  `SUBSTITUTION_INFORMATIVE` by construction.
- **Over-reading a ~6 % shift** — the effect is below the material bar and its
  direction is not seed-stable; it must not be reported as "real data performs
  better/worse."
- **Evidence inflation** — none: outputs are payload-free (hashes, counts,
  aggregate stats, derived bbox, provenance URL already published in 0D.2).

## Verdict

**`SUBSTITUTION_UNINFORMATIVE`.** The matched-scope, single-substitution
comparison is methodologically valid and reproducible, but at the matched
station-envelope extent the real A-02 evidence has too little geometric leverage to test the
model: the primary metric moves only +5.98 % (below the 20 % pre-registered
materiality bar), no pre-existing coverage threshold is crossed (Model-A
saturates identically in both arms), and the median-effect direction is not
stable across the 25 seeds. Per the pre-registered §9 rule this is
`SUBSTITUTION_UNINFORMATIVE`. `SUBSTITUTION_INFORMATIVE` was unreachable by
pre-registration in any case (scope ≈1.9 %, synthetic demand).

This is a **completed, valid experiment with a negative (uninformative) result**,
not a failure: it says the available real evidence, at its true scope, cannot yet
move the model's geometry meaningfully — which is the honest, falsification-first
outcome.

## Stop statement

Phase 0D.3 is packaged and stops here. This result does **not** prove the UAS
thesis, does **not** support `BUILD`, does **not** claim `SAFE_TO_FLY` or
`MADRID VALIDATED`, and changes **no** assumption to `SUPPORTED`/`REFUTED`. No
A-01/A-03/A-04 data was acquired. **Phase 0D.4 has NOT started.**

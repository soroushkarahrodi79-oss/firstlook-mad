# PHASE 0D.4 — ADVERSARIAL FALSIFICATION GATE REPORT

> **Phase:** 0D.4 · **Date:** 2026-09-14 · **Branch:**
> `claude/phase0d4-adversarial-falsification-20q34p` · **Use:**
> `RESEARCH / SIMULATION PROTOTYPE ONLY`
>
> **Formal gate verdict (repository vocabulary `SURVIVES / WEAKENED / REFUTED /
> INCOMPARABLE`, `PHASE_0D_ROADMAP.md` §0D.4):** **`INCOMPARABLE`**.
>
> This phase measures **fragility of the synthetic model mechanism**. It is
> **not** Madrid validation, **not** `BUILD`/`REPOSITION`/`KILL`, **not**
> `SAFE_TO_FLY`, and changes **no** assumption state. A negative or inconclusive
> result is a successful scientific outcome when it is true.
>
> **Authoritative companions:** `docs/PHASE_0D4_PREREGISTRATION.md` (frozen rules,
> commits `3a64b1d` → `470517b` → `4512090`, amended before results),
> `outputs/reports/phase0d4_adversarial_results.json`,
> `outputs/reports/phase0d4_adversarial_manifest.json`.

---

## Evidence

Everything reproduces deterministically from tracked inputs only; no evidence was
acquired.

- **Frozen 0C.1 engine** (`configs/phase0c_synthetic.json` + the tracked engine).
  0C.1 reproduces `outputs/reports/phase0c_synthetic_results.json` **byte-for-byte**
  (verified 2026-09-14). The 0D.4 module reuses `generate_inputs`,
  `evaluate_network`, `greedy_site_order`, `euclidean_distance_m` **unchanged** —
  no parallel model, no new physics.
- **Canonical A-02** (`outputs/canonical/phase0d2/a02_madrid_city_fire_stations.json`,
  tracked, 13 records, `source_sha256` `5c3957…f8eb6`) — used only for the T1a
  matched-scope context (cited from the frozen 0D.3 results), never for
  operational attributes.
- **Frozen 0D.3 results** (`…/phase0d3_substitution_results.json`) — cited for
  T1a / T2 matched-scope context.

Evidence classes are kept distinct throughout: `REAL` / `DERIVED_FROM_REAL` /
`SYNTHETIC` / `SYNTHETIC_STRESS_TEST` / `NOT_EVALUATED`. A `SYNTHETIC` or
`SYNTHETIC_STRESS_TEST` value combined with real values never becomes `REAL`.

## Pre-specification

The design was frozen **before any result** in `docs/PHASE_0D4_PREREGISTRATION.md`,
across three prereg-only commits (initial `3a64b1d`; a pre-result amendment
`470517b` splitting gate authority and demoting synthetic branches; a wording-only
`4512090`). Not blinded — the 0C/0D evidence is known; ordering is enforced by the
multi-commit split plus owner review, not claimed from Git alone. Thresholds use
the config's own step sizes / reference profile / natural collapse-and-flip
criteria. No threshold was changed after results (§Deviations, none).

**Two reporting layers, kept separate (frozen):**

- **Formal real-data gate** — driven **only** by the evidence-qualified critical
  set **{T3-REAL, T4-REAL, T5}** (the real-data adversarial questions).
- **Diagnostic battery** — **{T1, T2, T3-SYNTH, T4-SYNTH, T6}** — characterises
  the *synthetic* mechanism's fragility and **never** drives the formal gate. A
  diagnostic `FAILS` stays diagnostic.

## Baseline (frozen control)

Full-domain 0C.1 synthetic model (seed 260827, 180 incidents, 10 sites, reference
profile `assumed-reference-envelope-v1`), **not** the narrow 0D.3 station-envelope
experiment.

| Baseline metric | Value |
|---|---|
| Model-A risk-weighted coverage (10 sites) | **0.553475** |
| Model-F risk-weighted coverage (10 sites, within-envelope) | **0.101496** |

Both match the tracked 0C.1 output exactly (pinned by test).

## Adversarial test matrix

| Test | Layer | Criticality | Evidence class | Result |
|---|---|---|---|---|
| T1 candidate-location fragility | diagnostic | DIAGNOSTIC | SYNTHETIC_STRESS_TEST | **SURVIVES** |
| T2 diminishing returns | diagnostic | DIAGNOSTIC | SYNTHETIC | **SURVIVES** |
| T3-REAL weather erosion | formal | FORMAL-CRITICAL | NOT_EVALUATED | **NOT_EVALUATED** |
| T3-SYNTH weather erosion | diagnostic | DIAGNOSTIC | SYNTHETIC_STRESS_TEST | **FAILS** |
| T4-REAL airspace/geographic | formal | FORMAL-CRITICAL | NOT_EVALUATED | **NOT_EVALUATED** |
| T4-SYNTH airspace/geographic | diagnostic | DIAGNOSTIC | SYNTHETIC_STRESS_TEST | **SURVIVES** |
| T5 camera / hybrid comparator | formal | FORMAL-CRITICAL | SYNTHETIC | **INCOMPARABLE** |
| T6 threshold / gate fragility | diagnostic | DIAGNOSTIC | SYNTHETIC | **FAILS** |

### T1 — Candidate-location fragility · DIAGNOSTIC · SURVIVES

- **T1a (matched-scope real context, `DERIVED_FROM_REAL`/`SYNTHETIC`):** the 0D.3
  real-A-02-vs-synthetic comparison was `SUBSTITUTION_UNINFORMATIVE` — no material,
  seed-stable geometry signal at the ~1.9%-of-domain municipal envelope. Municipal
  context only; no regional claim.
- **T1b drop-top-site (`SYNTHETIC_STRESS_TEST`):** removing the single
  highest-greedy-ranked site (`SYN-SITE-003`) moves Model-A coverage
  0.553475 → 0.515692 (**−6.83 %**).
- **T1c uniform displacement 2500 m (`SYNTHETIC_STRESS_TEST`):** every site
  displaced 2500 m at a deterministic per-site bearing; all stayed inside the
  frozen domain (evaluated). Model-A coverage 0.553475 → 0.550157 (**−0.60 %**).
- **Single-site dominance:** the most-covering site holds **20.4 %** of Model-A
  covered risk (`SYN-SITE-006`), below the 50 % dominance threshold.

`max |relative Δ Model-A| = 0.068 < 0.20` and no single-site dominance ⇒
**SURVIVES**. The model's coverage is not a lucky spatial draw and is not
dominated by one site.

### T2 — Diminishing returns · DIAGNOSTIC · SURVIVES

Model-F risk-weighted coverage across the config's own `network_sizes`
[1, 2, 3, 5, 10] = [0.023708, 0.023708, 0.030453, 0.054093, 0.101496] (reproduces
0C.1 exactly). Per-site marginal gains: 0 (1→2), 0.006745 (2→3), 0.011820 (3→5),
0.009481 (5→10). Last-segment / peak ratio = **0.802 ≥ 0.20** ⇒ **SURVIVES**: on
the full domain returns are **not** strongly diminishing within the tested range.
(Matched-scope context: at the 0D.3 envelope Model-A is already saturated at 1.0,
so 13 real locations do not materially outperform a smaller set there.)

### T3 — Weather / performance erosion · split gate authority

- **T3-REAL (FORMAL-CRITICAL) → `NOT_EVALUATED_MISSING_EVIDENCE`.** A-04 real
  fire-day weather observations are unavailable (`WEATHER_EVIDENCE_NOT_OBSERVABLE`);
  PROTOCOL §4.2 bands require real out-of-envelope frequency. AEMET station
  **inventory is not weather observations**. Never `SURVIVES`; never synthesised.
- **T3-SYNTH (DIAGNOSTIC, `SYNTHETIC_STRESS_TEST`) → FAILS.** Model-F coverage
  (reference profile): within-envelope 0.101496 → wind-outside-envelope (16 m/s)
  **0.0** (**−100 %**, ≥ 0.95 ⇒ FAILS). **Profile-dependent:** the optimistic
  profile (`max_wind = 16`) retains **0.134804** under the same 16 m/s stress —
  the collapse is reference-profile-specific. `visibility-unknown` → 0.0 is
  reported as a **design-rule artifact** (PROTOCOL §4.2), excluded from
  classification. **Known before execution** (the tracked 0C.1 output already
  records 0.0): this is diagnostic evidence about the synthetic model, **not**
  real-weather evidence and **not** a gate-driving falsification.

### T4 — Airspace / geographic constraints · split gate authority

- **T4-REAL (FORMAL-CRITICAL) → `NOT_EVALUATED_MISSING_EVIDENCE`.** A-03 is
  `NOT_ELIGIBLE` (ENAIRE truncated 50/50, `exceededTransferLimit`; IGN MDT05 is a
  100 m x 100 m window). Bounded samples are **never** promoted to a full-domain
  constraint layer; never `SURVIVES`; never synthesised.
- **T4-SYNTH (DIAGNOSTIC, `SYNTHETIC_STRESS_TEST`) → SURVIVES.** Geometry-defined
  exclusion (no result peeking). The **mild** central box (E [435000, 455000],
  N [4455000, 4475000], ≈3.3 % of domain) contains **0** candidate sites ⇒ Model-A
  reduction **0 %** ⇒ SURVIVES. Context: the NE **quadrant** exclusion (25 % of
  domain) removes 4 sites and reduces Model-A coverage 0.553475 → 0.403994
  (**−27.0 %**). Never reported as an ENAIRE result.

### T5 — Camera / hybrid comparator · FORMAL-CRITICAL · INCOMPARABLE

From the frozen 0C.1 fair comparator (`comparison_status = INCOMPARABLE`,
`all_comparisons_incomparable = true`): dock-only risk-weighted coverage 0.101496;
camera-only 0.312742 reported **only** as an *optimistic upper bound* under unknown
LOS/smoke/FOV/observation-equivalence, **never** read as camera-beats-dock
(PROTOCOL §4.5). Real A-02 stations supply no camera attributes (`NOT_EVALUATED`);
none is imputed. The architecture ranking is **structurally unadjudicable** ⇒
**INCOMPARABLE**.

### T6 — Threshold / gate fragility · DIAGNOSTIC · FAILS

Target: the A-01 travel-materiality qualitative switch
`B = (travel_dominates_fraction > 0)` on the fixed 17-incident full-F-survivor
cohort. Over the ±120 s window (the config's own `a01_sweep_step_seconds`) around
the balanced-central 900 s budget: low (780 s) dominance 0.412 → **B true**;
central (900 s) 0.176 → **B true**; high (1020 s) 0.0 → **B false**. **B flips
within the window ⇒ FAILS.** The dominance-flip boundary is **911.672 s** — only
**+11.7 s** above the central assumption: the qualitative "travel dominates for
some incidents" label is threshold-fragile within seconds of the central budget.
**This is a model-emitted qualitative switch, not the real-data A-01 bands of
PROTOCOL §4.1**, and it is diagnostic (survivor-biased cohort).

## What survived

- **T1 (SURVIVES):** coverage is not placement-fragile (≤6.8 % under a dropped top
  site, 0.6 % under 2500 m displacement) and not single-site-dominated (20.4 %).
- **T2 (SURVIVES):** returns are not strongly diminishing on the full domain
  (last/peak per-site ratio 0.80).
- **T4-SYNTH (SURVIVES):** the mild synthetic spatial exclusion removes no
  candidate and does not collapse coverage.

These are **synthetic-mechanism** survivals only.

## What failed

- **T3-SYNTH (diagnostic FAILS):** reference-profile UAS coverage is **erased**
  (→0) under a single plausible synthetic adverse-wind envelope — though the
  optimistic profile survives, so the collapse is profile-specific.
- **T6 (diagnostic FAILS):** the A-01 travel-materiality label flips **~12 s** from
  the central assumption — the qualitative conclusion is threshold-fragile.

**Both are DIAGNOSTIC and known from 0C.1; neither drives the formal gate.** They
sharpen, but do not extend, the existing `CONDITION_DEPENDENT_STRONG` reading.

## What could not be evaluated

- **T3-REAL** and **T4-REAL** (both FORMAL-CRITICAL) are
  `NOT_EVALUATED_MISSING_EVIDENCE`: no real fire-day weather (A-04) and no
  full-domain airspace/terrain layer (A-03) exist in the repository, and none was
  manufactured.
- **T5** (FORMAL-CRITICAL) is `INCOMPARABLE`: the camera/UAS ranking is
  unadjudicable without LOS/smoke/FOV/observation-equivalence evidence.

## Missing evidence

The real-data adversarial questions cannot be mounted because the enabling real
evidence does not exist within scope: A-04 weather observations
(`WEATHER_EVIDENCE_NOT_OBSERVABLE`), a full-domain A-03 constraint layer (only
bounded ENAIRE/IGN samples), and camera observation-equivalence evidence
(`unknown LOS`). This is the substantive finding of the formal gate, and it is not
engineered around.

## Risks

- **Over-reading the synthetic diagnostics.** T3-SYNTH and T6 `FAILS` are about the
  *model*, on known 0C.1 behaviour and (T6) a survivor-biased cohort — not Madrid
  reality. Guarded by the two-layer split.
- **Profile sensitivity.** T3-SYNTH's collapse is reference-profile-specific;
  reporting only the reference figure could overstate weather fragility. Mitigated
  by reporting the optimistic-profile survival explicitly.
- **Structural INCOMPARABLE.** The formal verdict is INCOMPARABLE by evidence
  availability; it must not be read as "robust" or as "refuted" — only as "not
  adjudicable with current real evidence."

## Interpretation

The **synthetic mechanism** is internally robust to candidate placement (T1),
delivers non-collapsing marginal returns over the tested range (T2), and is
insensitive to a modest synthetic spatial exclusion (T4-SYNTH). It remains
fragile, as 0C.1 already showed, to adverse weather on the reference profile
(T3-SYNTH) and to a knife-edge threshold in the A-01 travel-materiality label
(T6) — both diagnostic and both known.

The **real-data adversarial falsification cannot be performed**: its three
evidence-qualified critical branches are all unevaluable (T3-REAL, T4-REAL) or
structurally incomparable (T5). The honest formal reading is therefore
**`INCOMPARABLE`** — the concept was neither strengthened nor refuted by real
adversarial evidence, because none exists. This is consistent with, and does not
upgrade, the standing `CONDITION_DEPENDENT_STRONG` / no-`BUILD`-support scientific
state.

## Final verdict

**Formal 0D.4 gate: `INCOMPARABLE`** (rule: no evidence-qualified critical branch
produced an adjudicated real comparison; T3-REAL and T4-REAL
`NOT_EVALUATED_MISSING_EVIDENCE`, T5 `INCOMPARABLE`).

**Diagnostic battery:** survived {T1, T2, T4-SYNTH}; failed {T3-SYNTH, T6}; none
NOT_EVALUATED. Diagnostic `FAILS` are scoped to synthetic stress and are never
promoted into a real-data gate failure.

**No assumption state changed** (A-01…A-09 unchanged). **No** `BUILD` /
`REPOSITION` / `KILL` / `SAFE_TO_FLY` / `MADRID_VALIDATED` / `SUPPORTED` /
`REFUTED` (assumption-level). **No** regional claim from municipal-only evidence.

## Stop statement

Phase 0D.4 is packaged for human review as a draft PR. The agent does not merge.
**Phase 0D.5 has NOT started.** No new A-01/A-03/A-04 evidence was acquired; no
operational feasibility is claimed.

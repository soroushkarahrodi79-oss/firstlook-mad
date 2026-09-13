# PHASE 0D ROADMAP — MADRID REAL-DATA FALSIFICATION

> **Status of this document:** execution roadmap and gate ledger for Phase 0D
> (real-data falsification) through Phase 0F (strategic decision). It is a
> **plan**, not a results record. It **claims no future outcome**. Every gate
> below pre-registers its allowed verdict vocabulary *before* the work runs, so
> that no threshold is changed after seeing results.
>
> **Companion documents (authoritative, not duplicated here):**
> - `docs/PHASE_0D_PROTOCOL.md` — pre-registered 0D per-test decision logic,
>   missing-data rule, stop rules, methodological deviations.
> - `docs/VALIDATION_PLAN.md` — BUILD/REPOSITION/KILL framework and the
>   (provisional) validation thresholds.
> - `docs/ASSUMPTIONS.md` — assumption ledger (A-01 … A-09) and their states.
> - `PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` — dated evidence/gate ledger.
>
> **Non-negotiable research principle.** FIRSTLOOK-MAD is falsification-first.
> We are trying to discover whether the concept survives evidence, not to prove
> it works. The three layers are kept permanently separate:
>
> ```
> EVIDENCE  →  INTERPRETATION  →  DECISION
> ```
>
> Insufficient evidence is a legitimate result. Any of
> `INSUFFICIENT_EVIDENCE` / `PARTIAL` / `NO_BASELINE` / `REPOSITION` / `KILL`
> can be the scientifically correct outcome, and none of the acquisition or
> normalization gates below implies `BUILD`, `SAFE_TO_FLY`, `SUPPORTED`, or
> `MADRID VALIDATED`.

---

## Global stop rules (apply to every sub-phase)

1. **No threshold changes after seeing results.** A post-hoc change is recorded
   as a deviation in an ADR and in `docs/PHASE_0D_PROTOCOL.md` §7.
2. **No evidence upgrade by convenience.** Metadata is not observation; a
   bounded sample is not a complete layer; interface availability is not a
   dataset; acquisition success is not scientific validation.
3. **No assumption state change** (`SUPPORTED`/`REFUTED`) without the
   pre-registered protocol authorizing that transition.
4. **First-failure-wins gates.** On `FAIL`/`BLOCKED`, stop and record; do not
   proceed to the next sub-phase.
5. **Human gate.** Each sub-phase closes as a PR for human review. The agent
   does not merge, and does not begin the next sub-phase's implementation until
   the owner authorizes it.

---

## Gate & verdict overview

| Sub-phase | Gate | Pre-registered verdict vocabulary |
|---|---|---|
| 0D.1 | REAL INPUT AVAILABILITY | `REAL INPUT AVAILABLE` / `PARTIAL REAL INPUT` / `NO REAL INPUT` |
| 0D.2 | NORMALIZATION & SEMANTIC FITNESS | `NORMALIZATION_READY` / `PARTIAL_NORMALIZATION` / `SEMANTICALLY_INSUFFICIENT` |
| 0D.3 | INCREMENTAL SUBSTITUTION | `SUBSTITUTION_INFORMATIVE` / `SUBSTITUTION_PARTIAL` / `SUBSTITUTION_UNINFORMATIVE` |
| 0D.4 | ADVERSARIAL FALSIFICATION | `SURVIVES` / `WEAKENED` / `REFUTED` / `INCOMPARABLE` |
| 0D.5 | ROBUSTNESS & UNCERTAINTY | `ROBUST` / `CONDITION_DEPENDENT` / `FRAGILE` |
| 0D.6 | MADRID REAL DATA MVP CLOSURE | `SUPPORTED` / `CONDITION_DEPENDENT` / `INSUFFICIENT_EVIDENCE` / `REFUTED` |
| 0E | BASELINE | `VERIFIED` / `PARTIAL` / `PROXY` / `NO_BASELINE` |
| 0F | STRATEGIC DECISION | `BUILD` / `REPOSITION` / `KILL` |

Every gate is reported in the fixed format: **Evidence · What passed · What
failed · Missing evidence · Risks · Verdict** (VALIDATION_PLAN §3). None of the
verdicts is predetermined.

---

## 0D.1 — REAL INPUT ACQUISITION & PROVENANCE

**Status:** `CLOSED` (2026-09-07). Packaged in **PR #5**
(`research/phase0d-local-retry-2026-09-02`, HEAD `7bc39c9`), **merged by the
owner on 2026-09-13** (merge commit `eb637c2`). The agent does not merge.

**Gate:** `0D.1 REAL INPUT AVAILABLE`.

**Explicit meaning:** at least one priority assumption has genuine,
integrity-verified, semantically usable real input. Satisfied by **A-02**
(real, traceable Madrid fire-station assets).

**Explicit NON-meaning:** *not* a scientific Phase 0D `PASS`, *not* `SUPPORTED`,
*not* `MADRID VALIDATED`, *not* `BUILD`, *not* `SAFE_TO_FLY`, *not* authorization
to enter 0E or to auto-start 0D.2. The scientific reading remains 0C.1's
`CONDITION_DEPENDENT_STRONG` (no support for `BUILD`), and the last formal phase
gate remains `MADRID REAL DATA MVP — FAIL (BLOCKED: EXECUTION ENVIRONMENT
EGRESS)` (2026-08-31), preserved as valid history.

**Acquisition-level input status (not decision level):**

| Assumption | Status | Note |
|---|---|---|
| A-01 | `PARTIAL_REAL_INPUT` | EGIF search interface only; **no** TTFRP baseline |
| A-02 | `USABLE_REAL_INPUT` | real fire-station assets |
| A-03 | `PARTIAL_REAL_INPUT` | bounded ENAIRE + IGN MDT05 GetCoverage + IGN metadata; **no** complete layers |
| A-04 | `PARTIAL_REAL_INPUT` | real AEMET station inventory; **no** weather observations |

**Entry condition:** owner authorization of Phase 0D (2026-08-31); pre-registered
protocol.
**Artifacts:** acquisition scripts (`scripts/acquire_phase0d_*.py`),
payload-free provenance ledger (`outputs/provenance/phase0d/**`, 16 entries),
immutable raw bytes (gitignored `data/raw/phase0d/**`), dated report addenda
(§16, §17), protocol deviations §7.1–§7.3.
**Tests:** `tests/test_phase0d_*` and `tests/test_provenance_ledger.py`
(72 passed at closure).
**Stop condition:** raw-data boundary breach, secret leakage, or evidence
inflation → block the PR.
**Exit gate:** `0D.1 REAL INPUT AVAILABLE` (met).
**Dependencies:** none upstream; blocks 0D.2.

---

## 0D.2 — REAL DATA NORMALIZATION & SEMANTIC FITNESS

**Status:** `EVALUATED` (2026-09-13) on branch
`research/phase0d2-real-data-normalization`, packaged as a draft PR, **pending
human review**. The agent does not merge.

**Gate:** `PARTIAL_NORMALIZATION` — rule pre-registered in
`docs/PHASE_0D2_PREREGISTRATION.md` (commit `b2e9a67`) before any normalization
code or output existed. Evidence and interpretation:
`PHASE_0D2_NORMALIZATION_GATE_REPORT.md`; machine-readable:
`outputs/reports/phase0d2_normalization_report.json`.

| Assumption | Analytical eligibility | Note |
|---|---|---|
| A-01 | `NOT_ELIGIBLE` | `BASELINE_NOT_OBSERVABLE`: 7 interface/metadata artifacts, 0 incident-level records |
| A-02 | `ELIGIBLE_WITHIN_DECLARED_SCOPE` | 13/13 city fire stations canonical in `EPSG:25830`; declared coverage Madrid municipality only |
| A-03 | `NOT_ELIGIBLE` | ENAIRE truncated by source (50/50, `exceededTransferLimit`); MDT05 is a 100 m × 100 m pipeline-proof window |
| A-04 | `NOT_ELIGIBLE` | station inventory only (23 Madrid stations); `WEATHER_EVIDENCE_NOT_OBSERVABLE` |

**Explicit non-meaning:** not `NORMALIZATION_READY`, not `SUPPORTED`, not `BUILD`,
not authorization to start 0D.3.

**Purpose:** transform genuinely acquired real evidence into canonical,
model-ready inputs **without inventing missing information**.

**Pre-registered verdicts (fixed before implementation):**
`NORMALIZATION_READY` / `PARTIAL_NORMALIZATION` / `SEMANTICALLY_INSUFFICIENT`.

**Work, where the evidence supports it:**

- **A-02 — canonical Madrid fire-station geospatial dataset.** Fields: stable
  source identifier, name, geometry, source CRS (if applicable), analytical
  geometry in `EPSG:25830`, source timestamp, source URL / provenance
  reference, SHA-256 linkage, evidence classification.
  *Validation:* valid geometry; coordinate sanity; Madrid bounds/scope sanity;
  duplicate handling; deterministic CRS conversion; explicit null/missing-field
  policy; reproducible counts.
- **A-03 — normalize bounded ENAIRE and IGN evidence honestly.** The canonical
  schema **must** preserve scope/completeness metadata:
  `coverage_extent`, `evidence_scope`, `bounded_sample` (flag),
  `spatial_completeness`, `eligible_for_full_madrid_analysis`.
  **Bounded samples are never promoted to full Madrid layers.**
- **A-04 — represent separately:** (a) station-inventory availability,
  (b) historical fire-day observation availability, (c) weather-falsification
  readiness. Station inventory ≠ historical weather observations.
- **A-01 — represent `BASELINE_NOT_OBSERVABLE`** if no genuine observable
  TTFRP baseline exists. **Never generate a fake TTFRP baseline.**

**Entry condition:** PR #5 merged to `main` by the owner; branch
`research/phase0d2-real-data-normalization` created from updated `main`.
**Artifacts:** canonical schemas; normalization code; validation code/tests;
machine-readable data-quality report; provenance preservation; a
missingness/completeness report; a gate report.
**Tests:** schema validation, CRS-conversion determinism, geometry validity,
Madrid-bounds checks, duplicate handling, missing-field policy, reproducible
counts.
**Stop condition:** any step that would require inventing missing data, promoting
a bounded sample to a full layer, or fabricating a baseline → stop and record
`SEMANTICALLY_INSUFFICIENT` for the affected assumption.
**Exit gate:** `NORMALIZATION & SEMANTIC FITNESS` verdict.
**Dependencies:** 0D.1 (merged). Blocks 0D.3.

> **STOP after the 0D.2 gate evaluation.** Do not change any scientific
> assumption state unless the pre-registered protocol explicitly authorizes a
> transition.

---

## 0D.3 — REALITY SUBSTITUTION / ASSUMPTION REPLACEMENT

**Purpose:** replace synthetic inputs with real evidence **incrementally**, so
that the effect of each substitution remains attributable.

**Pre-registered verdicts:** `SUBSTITUTION_INFORMATIVE` /
`SUBSTITUTION_PARTIAL` / `SUBSTITUTION_UNINFORMATIVE`.

**Design (staged, attribution-preserving):**

```
synthetic reference (0C.1)
  → substitute A-02 only            → measure Δ vs 0C.1
  → add supported/bounded A-03      → measure Δ (only where semantically valid)
  → add A-04 observational evidence → only if obtained and fit for purpose
```

Real is **not** automatically "better": if semantic fitness is poor, a
substitution may be *less* informative, and that is recorded honestly.

**Entry condition:** 0D.2 verdict `NORMALIZATION_READY` or a scoped
`PARTIAL_NORMALIZATION` covering at least A-02.
**Artifacts:** staged substitution runs; reproducible configuration (seeds,
data version, config hash); deltas vs 0C.1; uncertainty/missingness notes.
**Tests:** deterministic rerun; config/seed capture; delta computation.
**Stop condition:** substitution that cannot be attributed (confounded design)
→ redesign or record `SUBSTITUTION_UNINFORMATIVE`.
**Exit gate:** `INCREMENTAL SUBSTITUTION` verdict. No causal claim unless the
design supports it.
**Dependencies:** 0D.2. Blocks 0D.4.

---

## 0D.4 — ADVERSARIAL REAL-DATA FALSIFICATION

**Purpose:** try to **break** the concept. Tests are not designed to protect the
UAS thesis.

**Pre-registered verdicts:** `SURVIVES` / `WEAKENED` / `REFUTED` /
`INCOMPARABLE`.

**Lines of attack (as evidence permits; see PROTOCOL §4, §8):**

- Is transit/flight time actually a **material** TTFRP component (A-01)?
- Does fire-weather feasibility erase the benefit (A-04)?
- Do airspace/geographic constraints collapse eligibility (A-03)?
- Are returns strongly diminishing after a small number of sites (RQ6)?
- Does a simpler camera / tower / hybrid architecture perform comparably?
- Does incomplete LOS / image-equivalence evidence make the architecture
  comparison `INCOMPARABLE`?

**Entry condition:** 0D.3 produced attributable substitution results.
**Artifacts:** documented red-team runs (including negative results);
per-attack evidence tables; adversarial ADR notes.
**Tests:** reproducible attack configurations; bottleneck decomposition;
weather-feasibility gate; diminishing-returns curve.
**Stop condition:** if evidence cannot support a comparison, record
`INCOMPARABLE` rather than forcing a winner.
**Exit gate:** `ADVERSARIAL FALSIFICATION` verdict.
**Dependencies:** 0D.3. Blocks 0D.5.

---

## 0D.5 — ROBUSTNESS, UNCERTAINTY & DATA-QUALITY SENSITIVITY

**Purpose:** test whether any signal survives realistic data quality and
sampling variation.

**Pre-registered verdicts:** `ROBUST` / `CONDITION_DEPENDENT` / `FRAGILE`.

**Required analysis:** missing-data sensitivity; spatial-sampling sensitivity;
input-quality sensitivity; uncertainty propagation; reproducibility;
deterministic rerun; bounded-vs-expanded-layer sensitivity where expanded real
evidence exists.

**Explicitly separate** — do **not** collapse into one score:

```
HYPOTHESIS UNCERTAINTY   (is the thesis right?)
DATA UNCERTAINTY         (is the input good enough to tell?)
```

**Entry condition:** 0D.4 completed.
**Artifacts:** sensitivity tables; uncertainty-propagation notes; a
reproducibility/determinism check.
**Tests:** deterministic rerun; perturbation/sensitivity harness.
**Stop condition:** if data uncertainty dominates hypothesis uncertainty, the
honest reading is `INSUFFICIENT_EVIDENCE`, not a favorable score.
**Exit gate:** `ROBUSTNESS & UNCERTAINTY` verdict.
**Dependencies:** 0D.4. Blocks 0D.6.

---

## 0D.6 — MADRID REAL DATA MVP CLOSURE

**Purpose:** the phase-level gate for real-data falsification.

**Gate format (mandatory):** Evidence · What passed · What failed · Missing
evidence · Risks · Verdict.

**Pre-registered verdicts:** `SUPPORTED` / `CONDITION_DEPENDENT` /
`INSUFFICIENT_EVIDENCE` / `REFUTED`. **No positive verdict is predetermined.**

**Entry condition:** 0D.2–0D.5 gate reports exist.
**Artifacts:** consolidated 0D closure report; machine-readable evidence index.
**Stop condition / boundary:** Phase 0D closure does **not** automatically imply
`BUILD`. It feeds 0E and 0F; it does not replace them.
**Exit gate:** `MADRID REAL DATA MVP` verdict.
**Dependencies:** 0D.2–0D.5. Blocks 0E.

---

## 0E — BASELINE

**Pre-registered verdicts:** `VERIFIED` / `PARTIAL` / `PROXY` / `NO_BASELINE`.

`NO_BASELINE` is preserved as a **scientifically correct possible result**: if
no observable TTFRP baseline exists (see A-01 `BASELINE_NOT_OBSERVABLE`), no
baseline is invented. No proxy is promoted to `VERIFIED`.

**Entry condition:** 0D.6 closed.
**Artifacts:** baseline evidence dossier; provenance; verdict report.
**Stop condition:** no fabricated TTFRP under any verdict.
**Exit gate:** `BASELINE` verdict.
**Dependencies:** 0D.6. Blocks 0F.

---

## 0F — BUILD / REPOSITION / KILL

**Purpose:** the strategic decision gate.

**Pre-registered verdicts:** `BUILD` / `REPOSITION` / `KILL`.

**Inputs:** the **evidence** from 0D and 0E — not merely model performance. The
decision criteria are frozen (VALIDATION_PLAN §2) **before** the final
evaluation. `REPOSITION` and `KILL` are first-class outcomes.

**Entry condition:** 0E closed.
**Artifacts:** decision dossier; frozen criteria; ADR recording the decision.
**Exit gate:** `GO/REPOSITION/KILL` verdict.
**Dependencies:** 0D, 0E.

---

## Milestone / issue plan

**Milestone:** `Phase 0D — Madrid Real-Data Falsification`.

Recommended work items (each: objective · entry condition · artifacts · tests ·
stop condition · exit gate · dependencies as defined in the sections above):

| # | Recommended issue title | State |
|---|---|---|
| 0D.1 | `0D.1 — Acquisition & provenance closure` | CLOSED (PR #5, merged 2026-09-13) |
| 0D.2 | `0D.2 — Normalization & semantic fitness` | EVALUATED — `PARTIAL_NORMALIZATION` (draft PR, pending human review) |
| 0D.3 | `0D.3 — Incremental real-evidence substitution` | Not started — needs owner authorization after 0D.2 review |
| 0D.4 | `0D.4 — Adversarial falsification` | Blocked by 0D.3 |
| 0D.5 | `0D.5 — Robustness & uncertainty` | Blocked by 0D.4 |
| 0D.6 | `0D.6 — Madrid Real Data MVP closure` | Blocked by 0D.2–0D.5 |
| 0E | `Phase 0E — Baseline` | Blocked by 0D.6 |
| 0F | `Phase 0F — BUILD / REPOSITION / KILL` | Blocked by 0D, 0E |

If GitHub milestone/issue creation is available and would not duplicate existing
items, these titles are created under the milestone above. Otherwise this
roadmap is the canonical plan and the titles above are the recommended issues.

---

## 0D.2 entry condition (single source of truth)

`Phase 0D.2` may begin **only** after:

1. the owner has **reviewed and merged PR #5** into `main`; and
2. a new branch `research/phase0d2-real-data-normalization` is created from the
   updated `main`.

Until both hold, **Phase 0D.2 implementation has not started.**

**Status (2026-09-13):** both conditions were met (PR #5 merged at `eb637c2`;
the branch was created from, and fast-forwarded to, that commit). Phase 0D.2 was
executed and its gate evaluated. **Phase 0D.3 has not started.**

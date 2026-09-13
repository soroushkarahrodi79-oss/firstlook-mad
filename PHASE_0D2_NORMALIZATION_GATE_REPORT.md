# PHASE 0D.2 — REAL DATA NORMALIZATION & SEMANTIC FITNESS — GATE REPORT

> **Phase:** 0D.2 · **Date:** 2026-09-13
> **Gate:** `NORMALIZATION & SEMANTIC FITNESS` — **`PARTIAL_NORMALIZATION`**
> **Use:** `RESEARCH / SIMULATION PROTOTYPE ONLY`
> **Pre-registration:** [`docs/PHASE_0D2_PREREGISTRATION.md`](docs/PHASE_0D2_PREREGISTRATION.md),
> committed as `b2e9a67` before any normalization code existed and before the raw
> payload contents were inspected.
> **Machine-readable report:**
> [`outputs/reports/phase0d2_normalization_report.json`](outputs/reports/phase0d2_normalization_report.json)

**Question.** Can the real evidence acquired in Phase 0D.1 be transformed into
trustworthy, canonical, reproducible analytical inputs without inventing
information, inflating coverage or silently substituting proxies?

**Short answer.** Partly. The Madrid **municipal** fire-station dataset (A-02)
normalizes cleanly and is eligible for substitution **only within its declared
municipal scope**. No other target assumption has evidence fit for its role:
A-01 has no observable TTFRP baseline, A-03 has only a service-truncated airspace
sample and a 100 m terrain window, and A-04 has a station inventory but no
weather observations.

`EVIDENCE → INTERPRETATION → DECISION` are kept separate below: §1 is evidence,
§2–§5 interpretation, §6 the decision under the frozen rule.

---

## 1. Evidence

### 1.1 Inputs and integrity

- Inputs: the 16 payload-free ledger entries committed in PR #5
  (`outputs/provenance/phase0d/**`) and their gitignored raw bytes
  (`data/raw/phase0d/**`). No new acquisition; no network access in 0D.2.
- Integrity chain per artifact: raw-byte SHA-256 = local sidecar SHA-256 =
  committed ledger SHA-256, byte count matches, `truncated = false`.
  **16/16 `PASS`, 0 `FAIL`, 0 `RAW_UNAVAILABLE`.**
- Reproduce: `uv run python scripts/normalize_phase0d2.py` (reads the ledger and
  raw evidence; writes the outputs below).

### 1.2 Per-assumption assessment (separate dimensions, no composite score)

| | A-01 | A-02 | A-03 | A-04 |
|---|---|---|---|---|
| Evidence acquired | yes (7 EGIF artifacts) | yes (1) | yes (2 data + 3 metadata) | yes (3) |
| Normalization outcome | `OBSERVABILITY_RECORD_ONLY` | `CANONICAL_DATASET` | `CANONICAL_BOUNDED_SAMPLE` | `CANONICAL_INVENTORY_ONLY` |
| Normalized successfully | no (nothing to normalize) | yes | yes (bounded) | yes (inventory only) |
| Integrity | `PASS` | `PASS` | `PASS` | `PASS` |
| Structural validity | `NOT_NORMALIZED` | `VALID` | `VALID` | `VALID` |
| Semantic fitness | `NOT_FIT_FOR_TARGET_ROLE` | `FIT_WITHIN_DECLARED_SCOPE` | `NOT_FIT_FOR_TARGET_ROLE` | `NOT_FIT_FOR_TARGET_ROLE` |
| Completeness | `NOT_OBSERVED` | `COMPLETE_FOR_DECLARED_SCOPE` | `TRUNCATED_BY_SOURCE` | `NOT_OBSERVED` |
| **Analytical eligibility** | **`NOT_ELIGIBLE`** | **`ELIGIBLE_WITHIN_DECLARED_SCOPE`** | **`NOT_ELIGIBLE`** | **`NOT_ELIGIBLE`** |

### 1.3 A-02 — Madrid fire stations

- Source: Ayuntamiento de Madrid, `datos.madrid.es` JSON-LD
  (`madrid_city_open_data_fire_stations/20260906.raw`, SHA-256 `5c395787…`).
  Declared coverage: **Madrid municipality only** (source fact from
  `data/datasets_manifest.json`, cross-checked by a test).
- 13 source records → **13 canonical**, 0 rejected, 0 duplicate identifiers,
  0 duplicate-coordinate groups, 13/13 inside the municipal envelope,
  reconciliation `13 = 13 + 0`.
- CRS: decimal lat/lon with no CRS declared by the source → recorded as
  `EPSG:4326 (interpreted)`; deterministic `EPSG:4326 → EPSG:25830`
  (`always_xy`, rounded to 1 mm). Canonical extent E 435,063–449,957 m,
  N 4,465,720–4,481,279 m.
- Every canonical record carries its source identifier, source record URI,
  source lat/lon, analytical coordinates, source probe and source SHA-256.
  Operational readiness, drone suitability, availability, dispatch and docking
  capability, land ownership, response timing and permission are all
  `NOT_EVALUATED`.
- Tracked canonical output (CC-BY-4.0, attribution Ayuntamiento de Madrid):
  `outputs/canonical/phase0d2/a02_madrid_city_fire_stations.json`,
  SHA-256 `1437d82a…8feb71`.

### 1.4 A-03 — ENAIRE + IGN bounded evidence

- **ENAIRE UAS geozones** (`enaire_uas_zones_madrid_bbox`, SHA-256 `36f6e58e…`):
  50 features, all `Polygon`, 0 invalid geometries (OGC validity, nothing
  repaired). The request asked for at most 50 records (`resultRecordCount=50`)
  and the service returned `exceededTransferLimit = true` → **`TRUNCATED_BY_SOURCE`**:
  the sample is incomplete even inside its own request envelope
  (lon −4.0…−3.4, lat 40.25…40.65). `bounded_sample = true`,
  `eligible_for_full_madrid_analysis = false`. The record-level canonical
  derivative is gitignored (`data/processed/phase0d2/…`, SHA-256 `f2f163b6…`).
- **IGN MDT05 GetCoverage** (`ign_mdt05_getcoverage_madrid_sample`, SHA-256
  `3d7fe2a1…`): uncompressed GeoTIFF, 20 × 20, 5 m × 5 m, int16,
  `PIXEL_IS_AREA`, `EPSG:25830` declared by GeoKey; extent
  E 440,000–440,100 m, N 4,474,000–4,474,100 m exactly matches the request.
  Values 648–654 m, labelled `sample_window_only`. `completeness = BOUNDED_SAMPLE`,
  `eligible_for_full_madrid_analysis = false`,
  `eligible_for_pipeline_verification = true`; `NOT_ELIGIBLE` by its declared
  acquisition purpose (chain-reproducibility proof, protocol §7.3).
- **IGN metadata** (3 artifacts): integrity only, never normalized as data.

### 1.5 A-04 — AEMET semantic fitness

| Readiness fact | Value |
|---|---|
| `station_inventory_available` | `true` |
| `historical_observations_available` | `false` |
| `fire_day_observations_available` | `false` |
| `weather_falsification_ready` | `false` → `WEATHER_EVIDENCE_NOT_OBSERVABLE` |

- Content types detected (never used to upgrade a ledger classification):
  hop-1 `WRAPPER`, 57-byte artifact `SERVICE_ERROR` ("datos expirados"),
  167,915-byte artifact `STATION_INVENTORY`.
- Inventory decoded in its declared charset (ISO-8859-15): 926 records,
  3 nationwide structural rejections (none in Madrid), 23 records whose source
  field `provincia` is `MADRID` → 23 canonical stations, DMS coordinates parsed
  deterministically. Gitignored canonical derivative, SHA-256 `45227614…`.
- No REAL Madrid fire-date set exists in 0D.1 evidence, so fire-day coverage
  cannot even be tested.

### 1.6 A-01 — TTFRP / EGIF

- 7 EGIF artifacts, all ledger-classified `REAL_METADATA` (search interface,
  region lookups, Madrid-filtered search POST responses).
- `public_interface_available = true`, `incident_level_records_available = false`,
  `usable_timing_record_count = 0` → **`BASELINE_NOT_OBSERVABLE`**.
- `proxy_ttfrp_generated = false`. No dispatch, detection, response or proxy
  TTFRP value was produced. Keyword occurrences in interface HTML are not
  treated as timestamps.

### 1.7 Reproducibility

Two independent runs produced byte-identical outputs:

| Output | SHA-256 | Tracked |
|---|---|---|
| `outputs/reports/phase0d2_normalization_report.json` | `c1e387e5…677e7e8c` | yes |
| `outputs/canonical/phase0d2/a02_madrid_city_fire_stations.json` | `1437d82a…8feb71` | yes |
| `data/processed/phase0d2/a03_enaire_uas_zones_bounded_sample.json` | `f2f163b6…7371944` | no |
| `data/processed/phase0d2/a04_aemet_madrid_station_inventory.json` | `45227614…fe43fe7a` | no |

The test suite also regenerates the committed report and canonical A-02 file
from the local raw evidence and requires byte-for-byte equality (skipped where
the gitignored raw evidence is absent).

## 2. What passed

- The pre-registration was committed before any code existed and before the raw
  contents were inspected; the verdict was computed by code applying that rule.
- The integrity chain holds for all 16 artifacts.
- A-02 normalization is structurally clean (13/13, 0 rejections, 0 duplicates),
  deterministic and fully traceable to source bytes.
- The bounded nature of A-03 is preserved by construction:
  `BoundedEvidenceScope` rejects any bounded, truncated or incomplete scope
  claiming full-Madrid eligibility, and tests cover it.
- A-04 separates inventory from observations and cannot mark weather
  falsification ready without dated wind and visibility observations on
  real fire dates.
- A-01 cannot become a baseline from metadata: metadata artifacts cannot carry
  incident records (enforced by the model).
- Malformed ledgers, payloads and rasters fail explicitly; missing raw evidence
  stays `RAW_UNAVAILABLE` / `UNKNOWN` and is never eligible.
- Tracked outputs contain no credential markers and no third-party record-level
  payload beyond the CC-BY-4.0 A-02 canonical file.

## 3. What failed

- **A-01:** no incident-level records → no observable TTFRP components.
- **A-03 airspace:** ENAIRE response truncated by the service; not usable even
  within its request envelope.
- **A-03 terrain:** only a 100 m × 100 m reproducibility window.
- **A-04:** no weather observations of any kind.
- **A-02 (full domain):** declared coverage is one municipality, not the
  Comunidad de Madrid analytical domain, so only scope-restricted eligibility.

## 4. Missing evidence

- EGIF incident-level records (partes) with detection and first-arrival
  timestamps for Madrid (A-01; the licence for bulk XML reuse is also still
  `UNKNOWN` in the manifest).
- Regional fire-station / INFOMA asset locations with a reusable licence (A-02
  beyond the municipality).
- A complete ENAIRE geozone layer for the analytical domain (paginated, not
  truncated) (A-03).
- Terrain coverage of the analytical domain rather than a 100 m window (A-03).
- AEMET dated observations (wind, visibility) for Madrid stations, which need an
  `AEMET_API_KEY` supplied by the owner (A-04).
- A REAL set of Madrid fire dates to align observations with (A-04, depends on
  A-01-type evidence).

## 5. Risks

- **A-02 scope is small relative to the question.** The bounding box of the 13
  stations is about 14.9 km × 15.6 km (≈232 km², ≈1.9 % of the 12,100 km² 0C.1
  reference synthetic extent), all inside the urban municipality. A future
  A-02-only substitution restricted to that scope may be uninformative for
  wildfire first response. This is recorded for the owner's 0D.3 decision; it is
  not evaluated here.
- **Coordinate precision.** 11 of 13 stations reproject to integer-metre
  eastings with a near-constant 0.117–0.118 m northing fraction. This pattern is
  consistent with the publisher deriving lat/lon from integer-metre projected
  coordinates (not verified). Treat positions as roughly metre-level
  administrative locations, not surveyed points.
- **CRS interpretation.** The source declares no CRS; `EPSG:4326` is an
  interpretation. PROJ treats WGS84 and ETRS89 as coincident here; the
  difference is sub-metre and below the precision above.
- **Licence judgement.** Tracking the A-02 canonical file relies on the
  CC-BY-4.0 licence recorded in the 0B manifest. If the publisher's terms differ,
  that file should be removed from git (hashes and counts would remain).
- **Staleness.** Evidence is dated 2026-09-06/07. ENAIRE zones change on AIRAC
  cycles and the station catalogue can change.
- **Single-environment determinism.** Byte determinism was verified on Windows,
  Python 3.12.10, pyproj 3.7.2 and shapely 2.1.2 only; rounding to 1 mm mitigates
  but does not prove cross-platform identity.
- **Implementation clarifications.** A few cases the pre-registration left
  unspecified were settled conservatively during implementation, before the first
  real-data run, but were not committed separately before it: completeness
  `UNKNOWN` for A-02 duplicate-coordinate flags without rejections; A-03
  assumption-level completeness reported as the worst component; A-04/A-01
  fitness and completeness mapped from eligibility / observability; a GeoJSON
  `crs` member is refused instead of interpreted. None of these enters the
  eligibility rules that decide the gate, and none is triggered by a different
  branch on the real data. **No deviation from §4–§6 of the pre-registration.**

## 6. Verdict

**`PARTIAL_NORMALIZATION`.**

Rule application (pre-registration §6):

- `NORMALIZATION_READY` requires all four targets `ELIGIBLE` → **not met**
  (none is `ELIGIBLE`).
- `PARTIAL_NORMALIZATION` requires not READY and at least one target
  `ELIGIBLE` or `ELIGIBLE_WITHIN_DECLARED_SCOPE` → **met by A-02**
  (`ELIGIBLE_WITHIN_DECLARED_SCOPE`).
- `SEMANTICALLY_INSUFFICIENT` would require all four `NOT_ELIGIBLE` → not the
  case.

Reported alongside, without changing the verdict: eligible assumptions `[]`;
scope-restricted assumptions `[A-02]`; scope-restricted set includes A-02:
`true`; integrity failures `[]`.

## 7. What this phase does NOT prove

- It does **not** show that any fire station is a feasible UAS dock site.
- It does **not** provide a Madrid airspace or terrain layer.
- It does **not** provide weather observations or fire-day weather.
- It does **not** provide or approximate a TTFRP baseline.
- It does **not** move any assumption to `SUPPORTED` or `REFUTED`
  (A-01–A-04 remain `TESTING`), does **not** change the 0C.1 reading
  (`CONDITION_DEPENDENT_STRONG`, no support for `BUILD`), and does **not** change
  the last formal phase gate (`MADRID REAL DATA MVP — FAIL (BLOCKED: EXECUTION
  ENVIRONMENT EGRESS)`, 2026-08-31).
- It is **not** `BUILD`, `SAFE_TO_FLY`, `MADRID VALIDATED`, a Phase 0E baseline or
  authorization to start 0D.3.

## 8. Engineering quality

- `uv run pytest -q` → **165 passed** (72 pre-existing + 93 new; 27 subtests),
  including the real-data byte-for-byte regeneration test.
- `uv run ruff check .` → all checks passed.
- `uv run ruff format --check .` → 69 files already formatted.
- `uv run mypy` (strict) → no issues in 30 source files. Shapely ships no type
  marker; a scoped `ignore_missing_imports` override covers it.
- `git diff --check` → clean.
- Raw evidence untracked; tracked outputs scanned for credential markers and raw
  payload fields (0 matches); no existing test was weakened.

## 9. Stop

Phase 0D.2 ends at this gate. **Phase 0D.3 has NOT started.** No real-evidence
substitution was performed, `BUILD/REPOSITION/KILL` is unchanged, and Phase 0E
has not begun.

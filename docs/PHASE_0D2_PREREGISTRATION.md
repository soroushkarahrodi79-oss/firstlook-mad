# PHASE 0D.2 — PRE-REGISTERED NORMALIZATION & SEMANTIC FITNESS GATE

> **Status:** pre-registered **2026-09-13**, on branch
> `research/phase0d2-real-data-normalization` at base `eb637c2` (PR #5 merged).
> The Phase 0D.2 rules were frozen before normalization implementation, before
> Phase 0D.2 normalized outputs were generated, and before the 0D.2 gate was
> evaluated. The underlying evidence had already been acquired and characterized
> during Phase 0D.1, so this is not a blinded pre-registration independent of
> prior evidence characterization.
>
> *Chronology wording corrected on 2026-09-13 after external methodological
> review. An earlier version of this header also said the rules were fixed
> "before the raw payload contents were inspected for normalization", which
> overstated their independence from the Phase 0D.1 characterization. No rule in
> §4–§6 changed, and no threshold was changed after the Phase 0D.2 normalized
> results were seen.*
>
> **Use:** `RESEARCH / SIMULATION PROTOTYPE ONLY`.
>
> **Companion documents:** `docs/PHASE_0D_ROADMAP.md` (verdict vocabulary),
> `docs/PHASE_0D_PROTOCOL.md` (§4 per-test logic, §5 missing-data rule, §7
> deviations), `PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` §17 (0D.1 evidence).
>
> These rules are frozen. Any change made after normalized outputs exist is a
> dated deviation (see §9), and the verdict under the original rules is still
> reported.

---

## 1. Question

Can the real evidence acquired in Phase 0D.1 be transformed into trustworthy,
canonical, reproducible analytical inputs **without** inventing information,
inflating coverage, or silently substituting proxies?

This is not prediction, not 0D.3 substitution, not Phase 0E, not `BUILD`, and not
Madrid validation. `EVIDENCE → INTERPRETATION → DECISION` stay separate.

## 2. Inputs in scope

Only the 16 payload-free ledger entries under `outputs/provenance/phase0d/**`
(committed in PR #5) and their gitignored raw bytes under
`data/raw/phase0d/**`. No new acquisition is performed in 0D.2.

| Assumption | Artifacts (probe_id) | 0D.1 ledger classification |
|---|---|---|
| A-01 | `egif_public_search_madrid`, `egif_search_landing_session` (×2), `egif_ccaa_lookup`, `egif_provincia_lookup_madrid`, `egif_search_post_madrid` (×2) | `REAL_METADATA` |
| A-02 | `madrid_city_open_data_fire_stations` | `REAL_SOURCE_DATA` |
| A-03 | `enaire_uas_zones_madrid_bbox` | `REAL_BOUNDED_SAMPLE` |
| A-03 | `ign_mdt05_getcoverage_madrid_sample` | `REAL_SOURCE_DATA` (bounded window) |
| A-03 | `ign_mdt05_madrid_capabilities`, `ign_wcs_mdt_capabilities`, `ign_wcs_mdt_describe_5m` | `REAL_METADATA` |
| A-04 | `aemet_madrid_station_inventory` | `REAL_WRAPPER` |
| A-04 | `aemet_madrid_station_inventory_datos` (57 B) | `NOT_USABLE_FOR_TARGET_TEST` |
| A-04 | `aemet_madrid_station_inventory_datos` (167,915 B) | `REAL_SOURCE_DATA` |

The ledger classification is an *input* to 0D.2. 0D.2 never upgrades it.

## 3. Analytical domain and target roles

- **Analytical domain:** Comunidad de Madrid (`docs/PRODUCT_CONTRACT.md`).
  Reference synthetic extent of 0C.1: `EPSG:25830`, E 390,000–500,000 m,
  N 4,410,000–4,520,000 m (`configs/phase0c_synthetic.json`).
- **Analytical CRS:** `EPSG:25830` (ADR-0002).

The *target role* is what each assumption's evidence would replace in the
0D.3 staged substitution (roadmap §0D.3). Fitness is judged against that
role, not against "is it real?".

| Assumption | Target role in 0D.3 / 0D.4 |
|---|---|
| A-01 | Observable, incident-level TTFRP components (timestamps) for Madrid incidents |
| A-02 | Real public-asset **locations** replacing synthetic candidate-site locations (existence and location only) |
| A-03 | Real airspace and terrain constraints over the analytical domain replacing synthetic geometry |
| A-04 | Real fire-day weather **observations** replacing assumed weather scenarios |

## 4. Assessment dimensions (never collapsed into one score)

Every artifact and every assumption is reported on these separate dimensions:

| Dimension | Allowed values |
|---|---|
| `integrity` | `PASS` · `FAIL` · `RAW_UNAVAILABLE` |
| `structural_validity` | `VALID` · `VALID_WITH_FLAGS` · `INVALID` · `NOT_NORMALIZED` |
| `semantic_fitness` | `FIT_FOR_TARGET_ROLE` · `FIT_WITHIN_DECLARED_SCOPE` · `NOT_FIT_FOR_TARGET_ROLE` · `UNKNOWN` |
| `completeness` | `COMPLETE_FOR_ANALYTICAL_DOMAIN` · `COMPLETE_FOR_DECLARED_SCOPE` · `INCOMPLETE_AFTER_REJECTIONS` · `TRUNCATED_BY_SOURCE` · `BOUNDED_SAMPLE` · `NOT_OBSERVED` · `UNKNOWN` |
| `analytical_eligibility` | `ELIGIBLE` · `ELIGIBLE_WITHIN_DECLARED_SCOPE` · `NOT_ELIGIBLE` |

**Integrity (all artifacts).** `PASS` iff the SHA-256 of the local raw bytes
equals both the committed ledger `sha256` and the local sidecar `sha256`, and
`truncated` is `false`. A missing raw file is `RAW_UNAVAILABLE` (unknown stays
unknown; never assumed good). Anything other than `PASS` makes the artifact
`NOT_ELIGIBLE`.

**Unknown stays unknown.** A value that cannot be determined from evidence is
`UNKNOWN` / `NOT_OBSERVED`, never a default favourable value.

## 5. Per-assumption rules

### 5.1 A-02 — Madrid fire stations

Record-level hard checks. A failing record is **rejected with a reason code**,
never repaired, never imputed:

- `R1` non-empty source identifier.
- `R2` non-empty station name.
- `R3` coordinates present, numeric, finite.
- `R4` longitude ∈ [−180, 180], latitude ∈ [−90, 90].
- `R5` inside the Comunidad de Madrid sanity envelope: lon ∈ [−4.60, −3.05],
  lat ∈ [39.88, 41.17].
- `R6` deterministic `EPSG:4326 → EPSG:25830` transform (`always_xy`) yields
  finite coordinates inside the repository's `ProjectedPoint` bounds.

Dataset-level checks:

- `D1` integrity (§4).
- `D2` parse: valid JSON exposing a record list; otherwise an explicit error
  and `structural_validity = INVALID`.
- `D3` duplicate source identifiers: **every** record sharing the identifier
  is rejected (`DUPLICATE_IDENTIFIER`); none is silently chosen.
- `D4` identical coordinates (rounded to 1e-6°) across distinct identifiers:
  flagged (`DUPLICATE_COORDINATES`), records kept, counted.
- `D5` determinism: canonical rows sorted by source identifier; the canonical
  SHA-256 must be identical across two independent runs.
- `D6` reconciliation: `source_records = canonical_records + rejected_records`.
- `D7` soft check (never rejects): count inside the Madrid municipality
  envelope lon ∈ [−3.89, −3.52], lat ∈ [40.31, 40.65].

Source-coordinate interpretation: when the source publishes decimal
latitude/longitude without a CRS declaration, the canonical record states
`source_crs_interpretation = "EPSG:4326 (interpreted: decimal lat/lon, no CRS declared by source)"`.
It is recorded as an interpretation, not as a source fact.

Derived values:

- `structural_validity`: `VALID` iff 0 rejections and 0 `D4` flags;
  `VALID_WITH_FLAGS` iff ≥1 canonical record and (≥1 rejection or ≥1 `D4`
  flag); `INVALID` iff `D2` fails or 0 canonical records.
- `completeness`: the source's declared coverage is a documented **source
  fact** (the publisher's catalogue scope), not inferred from coordinates. If
  the declared coverage is the Comunidad de Madrid and the set is `VALID` →
  `COMPLETE_FOR_ANALYTICAL_DOMAIN`; if it is a sub-scope (e.g. one
  municipality) and `VALID` → `COMPLETE_FOR_DECLARED_SCOPE`; with rejections →
  `INCOMPLETE_AFTER_REJECTIONS`.
- `semantic_fitness`: `FIT_FOR_TARGET_ROLE` iff `VALID` and
  `COMPLETE_FOR_ANALYTICAL_DOMAIN`; `FIT_WITHIN_DECLARED_SCOPE` iff `VALID` and
  `COMPLETE_FOR_DECLARED_SCOPE`; otherwise `NOT_FIT_FOR_TARGET_ROLE`.
- `analytical_eligibility`: `ELIGIBLE` iff integrity `PASS` ∧ `VALID` ∧
  `COMPLETE_FOR_ANALYTICAL_DOMAIN`; `ELIGIBLE_WITHIN_DECLARED_SCOPE` iff
  integrity `PASS` ∧ `VALID` ∧ `COMPLETE_FOR_DECLARED_SCOPE`; otherwise
  `NOT_ELIGIBLE`.

Never inferred for A-02 (each is emitted as `NOT_EVALUATED`): operational
readiness, drone suitability, availability, dispatch capability, docking
capability, land ownership, emergency-response timing, permission.

### 5.2 A-03 — ENAIRE + IGN bounded evidence

**ENAIRE UAS geozones (`enaire_uas_zones_madrid_bbox`).**

- Integrity (§4); GeoJSON `FeatureCollection` parse, else explicit error.
- Geometry: each feature `Polygon`/`MultiPolygon`, finite coordinates in
  lon/lat range, OGC-valid (`shapely.is_valid`). Invalid geometries are
  **counted, never repaired** (no `buffer(0)`, no `make_valid`).
- CRS: RFC 7946 GeoJSON ⇒ `EPSG:4326` (recorded as an interpretation unless a
  `crs` member states otherwise).
- Truncation: `exceededTransferLimit = true` anywhere in the response, **or**
  feature count ≥ the `resultRecordCount` of the request URL ⇒
  `completeness = TRUNCATED_BY_SOURCE`.
- `bounded_sample = true` because the request envelope (lon −4.0…−3.4,
  lat 40.25…40.65) is strictly smaller than the analytical-domain envelope.
- `eligible_for_full_madrid_analysis = true` only if the request envelope
  covers the full analytical-domain envelope **and** the response is not
  truncated.
- `analytical_eligibility`: `ELIGIBLE_WITHIN_DECLARED_SCOPE` iff integrity
  `PASS` ∧ all geometries valid ∧ not truncated; `ELIGIBLE` additionally
  requires `eligible_for_full_madrid_analysis`; otherwise `NOT_ELIGIBLE`.

**IGN MDT05 GetCoverage sample (`ign_mdt05_getcoverage_madrid_sample`).**

- Integrity (§4); TIFF parse of width, height, sample format, pixel scale,
  tie-point, projected CRS GeoKey, nodata. Only uncompressed strips are
  decoded; any other layout is `NOT_NORMALIZED` with an explicit reason.
- `bounded_sample = true`; `coverage_extent` = the requested window;
  `completeness = BOUNDED_SAMPLE`; `eligible_for_full_madrid_analysis = false`.
- Its acquisition purpose was declared in `docs/PHASE_0D_PROTOCOL.md` §7.3 as a
  chain-reproducibility proof. It is therefore `NOT_ELIGIBLE` for analytical
  substitution regardless of its content, and may only be
  `eligible_for_pipeline_verification = true`.
- Sample statistics are labelled `sample_window_only` and never emitted as a
  domain-level value. No extrapolation.

**IGN metadata artifacts.** Recorded as metadata evidence (integrity only);
never normalized into data; `NOT_ELIGIBLE`.

**A-03 roll-up.** `ELIGIBLE` iff an airspace component **and** a terrain
component are both `ELIGIBLE`; `ELIGIBLE_WITHIN_DECLARED_SCOPE` iff at least one
component is `ELIGIBLE_WITHIN_DECLARED_SCOPE` or `ELIGIBLE`; otherwise
`NOT_ELIGIBLE`.

### 5.3 A-04 — AEMET semantic fitness

Four separate booleans, each derived only from artifacts, never from each other
upward:

1. `station_inventory_available` — true iff an integrity-`PASS`,
   `REAL_SOURCE_DATA` artifact of content type `STATION_INVENTORY` parses and
   yields ≥1 valid station record.
2. `historical_observations_available` — true iff an integrity-`PASS`,
   `REAL_SOURCE_DATA` artifact of content type `OBSERVATION_SERIES` (dated
   measurement records) exists. A `STATION_INVENTORY`, `REAL_WRAPPER` or
   `NOT_USABLE_FOR_TARGET_TEST` artifact can **never** set this.
3. `fire_day_observations_available` — true iff (2) ∧ a REAL, integrity-`PASS`
   set of Madrid fire dates exists ∧ the observations cover ≥1 of those dates.
4. `weather_falsification_ready` — true iff (3) ∧ the observed variables
   include both wind and visibility (protocol §4.2).

If (4) is false the A-04 label is `WEATHER_EVIDENCE_NOT_OBSERVABLE`
(protocol §4.2). `analytical_eligibility`: `ELIGIBLE` iff (4); otherwise
`NOT_ELIGIBLE`. The inventory may still be canonicalized (Madrid-province
records selected by the source's own `provincia` field; DMS coordinates parsed
deterministically), but that never changes (2)–(4).

### 5.4 A-01 — TTFRP / EGIF

- `public_interface_available` — true iff ≥1 integrity-`PASS` EGIF artifact
  exists.
- `incident_level_records_available` — true iff an integrity-`PASS`,
  `REAL_SOURCE_DATA` artifact contains parsed incident-level records.
- `ttfrp_baseline_status` — `OBSERVABLE` iff such records carry parsed
  detection/alert **and** first-arrival timestamps; otherwise
  `BASELINE_NOT_OBSERVABLE`.
- Type rule: an artifact classified `REAL_METADATA` can never produce
  `OBSERVABLE`. Keyword occurrences in interface HTML are not timestamps.
- No dispatch, detection, response or proxy TTFRP value is generated.
- `analytical_eligibility`: `ELIGIBLE` iff `OBSERVABLE` with ≥10 usable
  records (protocol §4.1); otherwise `NOT_ELIGIBLE`.
- Baseline **design** is Phase 0E and is out of scope here.

## 6. Gate rule (evaluated only after implementation and tests)

Let `E(a)` be the `analytical_eligibility` of target assumption
`a ∈ {A-01, A-02, A-03, A-04}`.

| Verdict | Rule |
|---|---|
| `NORMALIZATION_READY` | `E(a) = ELIGIBLE` for **all four** targets, and no in-scope artifact has integrity `FAIL`. |
| `PARTIAL_NORMALIZATION` | Not `NORMALIZATION_READY`, and `E(a) ∈ {ELIGIBLE, ELIGIBLE_WITHIN_DECLARED_SCOPE}` for **at least one** target. |
| `SEMANTICALLY_INSUFFICIENT` | `E(a) = NOT_ELIGIBLE` for **all four** targets. |

Exactly one verdict results. The report also lists, without altering the
verdict: the eligible and scope-restricted assumptions, and whether the
scope-restricted set includes A-02 (an input to the owner's 0D.3 entry
decision; 0D.2 does not decide 0D.3 entry).

Packaging blockers (not verdicts): any credential, cookie, token or raw
third-party payload in a tracked output; a failing QA suite. Either stops
packaging.

## 7. Data boundary

- Raw bytes stay in gitignored `data/raw/phase0d/**`; never moved or copied
  into tracked paths.
- Record-level canonical derivatives (station names, coordinates, geometries)
  are written only to gitignored `data/processed/phase0d2/**`. Tracked outputs
  contain schemas, counts, reason codes, identifiers of rejected records,
  hashes, transformation version and readiness states — no third-party
  record-level payload — unless redistribution is verified as legitimate.

## 8. Non-claims (binding)

`fire station ≠ UAS dock` · `bounded sample ≠ full Madrid layer` ·
`station inventory ≠ weather observations` · `EGIF interface ≠ TTFRP baseline` ·
`normalization success ≠ SUPPORTED` · `any 0D.2 verdict ≠ BUILD / SAFE_TO_FLY /
MADRID VALIDATED`. No assumption changes `TESTING → SUPPORTED/REFUTED` in 0D.2.

## 9. Deviations

A change to §4–§6 after normalized outputs exist is recorded with date, reason
and authorizer in `docs/PHASE_0D_PROTOCOL.md` §7 and in the 0D.2 gate report,
and the verdict under these original rules is reported alongside.
Initial state: no deviations.

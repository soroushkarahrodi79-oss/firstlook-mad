# ADR 0002 — Phase 0C analytical CRS and type checker

- **Status:** Accepted
- **Date:** 2026-08-27
- **Scope:** Synthetic model only

## Context

Phase 0C introduces metric distance calculations and typed application code.
ADR-0001 deliberately deferred the analytical CRS and the choice between mypy
and pyright. Phase 0B confirmed that official candidate sources use several
CRSs, including geographic coordinates, EPSG:3857, EPSG:3035 and ETRS89/UTM.

## Decisions

1. The analytical CRS is **ETRS89 / UTM zone 30N (`EPSG:25830`)**. It is metric,
   covers the Madrid study area and aligns with the ETRS89 family used by
   Spanish official cartography. Source-native geometries must be transformed by
   a dedicated ingestion step before metric analysis.
2. Phase 0C accepts only synthetic points expressed directly as explicit
   `easting_m`/`northing_m` in EPSG:25830. It does not silently transform or
   infer a CRS.
3. Domain validators reject degree-like, swapped and out-of-area coordinates.
   This is a guardrail, not a claim that every accepted point lies inside the
   Comunidad de Madrid boundary.
4. The type checker is **mypy in strict mode**. It is Python-native, integrates
   with the existing `uv` workflow and avoids introducing a Node runtime.
5. The CLI uses the standard library `argparse`; no CLI framework is justified
   for the single Phase 0C command.

## Consequences

- Metric calculations never run on EPSG:4326.
- Real-data transformations remain deferred to Phase 0D and require provenance,
  axis-order and round-trip tests.
- `mypy`, Ruff, pytest and deterministic CLI execution are part of the Phase 0C
  gate.
- No numerical TTFRP value produced by 0C is empirical; all performance inputs
  are labelled `ASSUMED` and all incidents/sites are `SYNTHETIC`.


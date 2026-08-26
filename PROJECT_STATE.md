# PROJECT_STATE — FIRSTLOOK-MAD

> Ledger operacional conciso. Permite continuar el proyecto en otra sesión o con
> otro agente. **No** es un diario. Se actualiza al final de cada bloque
> significativo. Al reanudar: `git status` → `git log --oneline -10` → leer este
> archivo → revisar último gate → comprobar tests → continuar.

---

## Current phase
**Phase 0A — Definición.**

## Current gate
**PROJECT DEFINITION REVIEW** — pendiente de veredicto del responsable humano.
(Propuesta del equipo: **PASS WITH CONDITIONS**; ver §Risks/Assumptions.)

## Completed
- Repository audit (repo vacío, rama correcta, sin commits previos).
- Challenge the Idea (supuestos fuertes/débiles, riesgos, tests de falsación).
- Documentos fundacionales de Phase 0A:
  PRODUCT_CONTRACT, RESEARCH_QUESTIONS, CONCEPT_OF_OPERATIONS, SYSTEM_BOUNDARIES,
  REGULATORY_BOUNDARIES, DATA_SOURCES, ASSUMPTIONS, LIMITATIONS, VALIDATION_PLAN,
  ARCHITECTURE, SAFETY_CASE, THREAT_MODEL, ADR-0001.
- Repo meta: README, LICENSE (Apache-2.0 provisional), CONTRIBUTING, SECURITY,
  CITATION.cff, .gitignore, pyproject.toml (deps declaradas, NO instaladas),
  .pre-commit-config.yaml.
- Estructura de carpetas + gitkeeps + READMEs de data/raw y data/synthetic.

## In progress
- Nada activo. A la espera de veredicto del gate 0A.

## Decisions (ver docs/adr/0001)
- Alcance Phase 0 = investigación + simulación; sin control real, sin dispatch.
- Stack: Python 3.12+, uv, Pydantic, pandas, GeoPandas/Shapely/PyProj,
  DuckDB/Parquet, pytest, Ruff, pre-commit. OR-Tools/NetworkX/Rasterio diferidos.
- Sin `SAFE_TO_FLY`; gates first-failure-wins.
- Licencia código: Apache-2.0 (provisional, revisable por el responsable).

## Assumptions (ver docs/ASSUMPTIONS.md)
A-01 tránsito material en TTFRP · A-02 infraestructura reutilizable ·
A-04 meteo de días de fuego no anula viabilidad · A-07 baseline defendible.
Todas `OPEN` (sin verificar).

## Known blockers
- Ninguno técnico para 0A. Para avanzar a 0B se requiere veredicto humano del gate.
- Runtime local es Python 3.11.15; `requires-python>=3.12` a verificar en 0C.
- Type checker (mypy vs pyright) y CRS definitivo: decisiones abiertas (ADR 0C).

## Data status
`NOT_VERIFIED` en su totalidad. Ningún dato real descargado ni cacheado.
Catálogo de fuentes en docs/DATA_SOURCES.md. Feasibility real = Phase 0B.

## Test status
Sin tests aún (no hay código de aplicación). Suite empieza en Phase 0C.

## Last verified commit
`d006d2b` — Phase 0A documentation set (this commit adds the pointer on top).

## Next 3 actions
1. Recibir veredicto humano del gate PROJECT DEFINITION REVIEW (PASS/CONDITIONS/FAIL).
2. Si PASS: iniciar **Phase 0B — Data Feasibility** (probar accesibilidad y schema
   de fuentes; NO descargas masivas) → produce `DATA_FEASIBILITY_REPORT.md`.
3. Confirmar licencia y resolver ADR de type-checker/CRS antes de escribir código.

## Do not do yet
Dashboard · ML · hardware · control de drones · dispatch real · integración 112/
INFOMA · descargas masivas de datos · BVLOS · computer vision en vivo · avanzar a
0B sin el veredicto del gate.

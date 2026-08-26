# PROJECT_STATE — FIRSTLOOK-MAD

> Ledger operacional conciso. Permite continuar el proyecto en otra sesión o con
> otro agente. **No** es un diario. Se actualiza al final de cada bloque
> significativo. Al reanudar: `git status` → `git log --oneline -10` → leer este
> archivo → revisar último gate → comprobar tests → continuar.

---

## Current phase
**Phase 0B — Data Feasibility.**

## Current gate
**DATA FEASIBILITY** — en curso.

Gate anterior: **PROJECT DEFINITION REVIEW — PASS WITH CONDITIONS** (decisión
humana, 2026-08-26). Condiciones vinculantes: priorizar falsación; no asumir
infraestructura operacional, autorización BVLOS ni baseline INFOMA; no fijar aún
un threshold numérico de TTFRP; aceptar resultados negativos.

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
- Gate de Phase 0A cerrado: PROJECT DEFINITION REVIEW — PASS WITH CONDITIONS.

## In progress
- Auditoría de factibilidad de datos y tests baratos de falsación de Phase 0B.

## Decisions (ver docs/adr/0001)
- Alcance Phase 0 = investigación + simulación; sin control real, sin dispatch.
- Stack: Python 3.12+, uv, Pydantic, pandas, GeoPandas/Shapely/PyProj,
  DuckDB/Parquet, pytest, Ruff, pre-commit. OR-Tools/NetworkX/Rasterio diferidos.
- Sin `SAFE_TO_FLY`; gates first-failure-wins.
- Licencia código: Apache-2.0 (confirmada por el responsable para Phase 0B).

## Assumptions (ver docs/ASSUMPTIONS.md)
A-01 tránsito material en TTFRP · A-02 infraestructura reutilizable ·
A-04 meteo de días de fuego no anula viabilidad · A-07 baseline defendible.
Todas `OPEN` (sin verificar).

## Known blockers
- Ninguno impide iniciar 0B.
- Runtime y `requires-python>=3.12` se verificarán sin reducir el requisito.
- Type checker (mypy vs pyright) y CRS analítico definitivo quedan diferidos a 0C.

## Data status
`NOT_VERIFIED` en su totalidad. Ningún dato real descargado ni cacheado.
Catálogo de fuentes en docs/DATA_SOURCES.md. Feasibility real = Phase 0B.

## Test status
Sin tests aún (no hay código de aplicación). Suite empieza en Phase 0C.

## Last verified commit
`d006d2b` — Phase 0A documentation set (this commit adds the pointer on top).

## Next 3 actions
1. Verificar accesibilidad, schema, licencia y relevancia de fuentes críticas.
2. Crear el manifest de procedencia y evidencia reproducible mínima.
3. Emitir el gate DATA FEASIBILITY sin avanzar a Phase 0C.

## Do not do yet
Dashboard · ML · hardware · control de drones · dispatch real · integración 112/
INFOMA · descargas masivas de datos · BVLOS · computer vision en vivo · simulador
de 0C antes de cerrar el gate de datos.

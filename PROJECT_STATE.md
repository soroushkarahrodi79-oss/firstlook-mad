# PROJECT_STATE — FIRSTLOOK-MAD

> Ledger operacional conciso. Permite continuar el proyecto en otra sesión o con
> otro agente. **No** es un diario. Se actualiza al final de cada bloque
> significativo. Al reanudar: `git status` → `git log --oneline -10` → leer este
> archivo → revisar último gate → comprobar tests → continuar.

---

## Current phase
**Phase 0B — Data Feasibility, cerrada. STOP antes de 0C.**

## Current gate
**DATA FEASIBILITY — DATA PARTIAL** (2026-08-26).

Hay datos suficientes para un modelo sintético de sensibilidad/falsación en 0C,
pero no para un baseline TTFRP extremo a extremo, sitios desplegables, permiso
BVLOS ni claims de desempeño real de Madrid. La entrada en 0C requiere decisión
humana explícita sobre estas condiciones.

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
- Repo meta: README, LICENSE (Apache-2.0 confirmada), CONTRIBUTING, SECURITY,
  CITATION.cff, .gitignore, pyproject.toml (deps declaradas, NO instaladas),
  .pre-commit-config.yaml.
- Estructura de carpetas + gitkeeps + READMEs de data/raw y data/synthetic.
- Gate de Phase 0A cerrado: PROJECT DEFINITION REVIEW — PASS WITH CONDITIONS.
- Investigación de 19 fuentes con schema, acceso, licencia, CRS, frescura,
  cobertura, limitaciones y relevance mapping.
- Manifest de procedencia y probes de metadatos reproducibles (7/7 accesibles).
- `DATA_FEASIBILITY_REPORT.md`, observabilidad TTFRP y red-team de alternativas.
- Gate de Phase 0B cerrado: **DATA PARTIAL**.

## In progress
- Ninguno. Stop point previo a Phase 0C.

## Decisions (ver docs/adr/0001)
- Alcance Phase 0 = investigación + simulación; sin control real, sin dispatch.
- Stack: Python 3.12+, uv, Pydantic, pandas, GeoPandas/Shapely/PyProj,
  DuckDB/Parquet, pytest, Ruff, pre-commit. OR-Tools/NetworkX/Rasterio diferidos.
- Sin `SAFE_TO_FLY`; gates first-failure-wins.
- Licencia código: Apache-2.0 (confirmada por el responsable para Phase 0B).
- Phase 0C solo se justifica como simulación sintética de falsación, no como
  predictor de Madrid.
- Comparar una alternativa híbrida cámaras/torres + UAS con la red de docks.
- No fijar threshold numérico TTFRP sin baseline observable.

## Assumptions (ver docs/ASSUMPTIONS.md)
A-01 tránsito material en TTFRP · A-02 infraestructura reutilizable · A-04 meteo
no anula viabilidad · A-07 baseline defendible · A-08 coordinación modelable:
todas `TESTING`. A-01 es la más debilitada; ninguna está `SUPPORTED`.

## Known blockers
- `NO_PUBLIC_TTFRP_BASELINE`: faltan clocks públicos end-to-end.
- `NO_PUBLIC_REGIONAL_SITE_LAYER`: no hay capa regional reutilizable de activos
  INFOMA con coordenadas, aptitud y disponibilidad.
- Histórico EFFIS completo requiere solicitud humana.
- Falta perfil UAS verificable y meteo histórica local de visibilidad/ráfagas.
- Type checker y CRS analítico definitivo quedan diferidos a una eventual 0C.

## Data status
`DATA PARTIAL`: 19 fuentes — 5 `READY`, 9 `PARTIAL`, 1 `BLOCKED`,
4 `REFERENCE_ONLY`. Siete probes oficiales responden. No se descargaron ni
cachearon datasets masivos; `data/raw/` permanece inmutable.

## Test status
`python -m unittest discover -s tests -v` — **7 tests, OK** con Python 3.12.13.
`python -m compileall -q scripts tests` — **OK**. Probe live — **7/7**.

## Last verified commit
`f935b2c` — informe y veredicto de factibilidad (este commit añade el pointer).

## Next 3 actions
1. Obtener decisión humana sobre entrada condicionada en Phase 0C.
2. Si se aprueba, fijar perfiles UAS sintéticos y rangos TTFRP explícitamente
   `ASSUMED`, junto con kill tests de dominancia.
3. Modelar en paralelo red de docks y alternativa híbrida cámaras/torres + UAS.

## Do not do yet
Dashboard · ML · hardware · control de drones · dispatch real · integración 112/
INFOMA · descargas masivas · BVLOS · computer vision en vivo · cualquier trabajo
de Phase 0C sin decisión humana explícita.

# PROJECT_STATE — FIRSTLOOK-MAD

> Ledger operacional conciso. Permite continuar el proyecto en otra sesión o con
> otro agente. **No** es un diario. Se actualiza al final de cada bloque
> significativo. Al reanudar: `git status` → `git log --oneline -10` → leer este
> archivo → revisar último gate → comprobar tests → continuar.

---

## Current phase
**Phase 0C.1 — robustness audit complete. STOP antes de 0D.**

## Current gate
**SYNTHETIC MODEL — PASS** técnico; revisión 0C.1:
**`CONDITION_DEPENDENT_STRONG`** (2026-08-27).

Lectura científica: **PASS WITH CONDITIONS — ROBUSTNESS AUDIT REQUIRED**. La
erosión A→F sobrevive 25 seeds, A-01 es `STRONGLY_CONDITION_DEPENDENT` y el
comparador de cámaras/docks es `INCOMPARABLE`, no una victoria de cámara. No hay
soporte para `BUILD`. La entrada en 0D requiere revisión del PR #2 y decisión
humana explícita.

Gate anterior: **DATA FEASIBILITY — DATA PARTIAL** (2026-08-26). Gate de
definición previo: **PASS WITH CONDITIONS**. Condiciones vinculantes: priorizar
falsación; no asumir infraestructura operacional, autorización BVLOS ni baseline
INFOMA; no fijar threshold numérico de TTFRP; aceptar resultados negativos.

## Completed
- Repository audit (repo vacío, rama correcta, sin commits previos).
- Challenge the Idea (supuestos fuertes/débiles, riesgos, tests de falsación).
- Documentos fundacionales de Phase 0A:
  PRODUCT_CONTRACT, RESEARCH_QUESTIONS, CONCEPT_OF_OPERATIONS, SYSTEM_BOUNDARIES,
  REGULATORY_BOUNDARIES, DATA_SOURCES, ASSUMPTIONS, LIMITATIONS, VALIDATION_PLAN,
  ARCHITECTURE, SAFETY_CASE, THREAT_MODEL, ADR-0001.
- Repo meta: README, LICENSE (Apache-2.0 confirmada), CONTRIBUTING, SECURITY,
  CITATION.cff, .gitignore, pyproject.toml (deps bloqueadas/instaladas en 0C),
  .pre-commit-config.yaml.
- Estructura de carpetas + gitkeeps + READMEs de data/raw y data/synthetic.
- Gate de Phase 0A cerrado: PROJECT DEFINITION REVIEW — PASS WITH CONDITIONS.
- Investigación de 19 fuentes con schema, acceso, licencia, CRS, frescura,
  cobertura, limitaciones y relevance mapping.
- Manifest de procedencia y probes de metadatos reproducibles (7/7 accesibles).
- `DATA_FEASIBILITY_REPORT.md`, observabilidad TTFRP y red-team de alternativas.
- Gate de Phase 0B cerrado: **DATA PARTIAL**.
- ADR-0002: CRS `EPSG:25830`, mypy estricto y CLI argparse.
- Entorno reproducible `uv.lock`; Python 3.12+ verificado.
- Dominio validado, geometría métrica, gate first-failure-wins y modelos A→F.
- Fixtures deterministas: 180 incidentes, 10 sitios, 3 perfiles UAS, 3 cadenas
  TTFRP y 3 escenarios meteo, todos `SYNTHETIC`/`ASSUMED`.
- Tests de cuello de botella, erosión meteo, perfiles, rendimientos decrecientes
  y alternativa cámaras/híbrido.
- `SYNTHETIC_MODEL_REPORT.md` y resultado JSON regenerable.
- Gate de Phase 0C cerrado: **PASS técnico**, señal `REPOSITION` temprana.
- Phase 0C.1: ablación F, comparador simétrico por etapas, 25 seeds, sweep A-01
  0–3.600 s, sensibilidad 90/180/360 y greedy F-aware.
- Resultado 0C.1: `CONDITION_DEPENDENT_STRONG`; cámara como upper bound optimista
  y `INCOMPARABLE` cuando LOS es desconocido.

## In progress
- Ninguno. Stop point previo a Phase 0D.

## Decisions (ver docs/adr/0001)
- Alcance Phase 0 = investigación + simulación; sin control real, sin dispatch.
- Stack: Python 3.12+, uv, Pydantic, pandas, GeoPandas/Shapely/PyProj,
  DuckDB/Parquet, pytest, Ruff, pre-commit. OR-Tools/NetworkX/Rasterio diferidos.
- Sin `SAFE_TO_FLY`; gates first-failure-wins.
- Licencia código: Apache-2.0 (confirmada por el responsable).
- Phase 0C solo se justifica como simulación sintética de falsación, no como
  predictor de Madrid.
- Comparar una alternativa híbrida cámaras/torres + UAS con la red de docks.
- No fijar threshold numérico TTFRP sin baseline observable.
- CRS analítico: ETRS89 / UTM 30N (`EPSG:25830`); nunca distancia en 4326.
- Type checker: mypy estricto. CLI: argparse. Sin OR-Tools/NetworkX/Rasterio.
- `GO_SIMULATION` no significa permiso ni seguridad operacional.

## Assumptions (ver docs/ASSUMPTIONS.md)
A-01, A-02, A-03, A-04, A-06, A-07, A-08 y A-09 están `TESTING`.
A-01 = `STRONGLY_CONDITION_DEPENDENT`; A-04 permanece `TESTING`; A-06 muestra alta
sensibilidad. Ninguna está `SUPPORTED`.

## Known blockers
- `NO_PUBLIC_TTFRP_BASELINE`: faltan clocks públicos end-to-end.
- `NO_PUBLIC_REGIONAL_SITE_LAYER`: no hay capa regional reutilizable de activos
  INFOMA con coordenadas, aptitud y disponibilidad.
- Histórico EFFIS completo requiere solicitud humana.
- Falta perfil UAS verificable y meteo histórica local de visibilidad/ráfagas.
- Línea de visión, equivalencia/calidad de imagen y costes de cámaras/híbrido.
- Distribución real de incidentes, sitios y restricciones históricas.

## Data status
`DATA PARTIAL`: 19 fuentes — 5 `READY`, 9 `PARTIAL`, 1 `BLOCKED`,
4 `REFERENCE_ONLY`. Siete probes oficiales responden. No se descargaron ni
cachearon datasets masivos; `data/raw/` permanece inmutable.

Datos 0C: únicamente `SYNTHETIC`/`ASSUMED`, seed `260827`, configuración y output
versionados. Ninguna cifra es una observación de Madrid.

## Test status
`uv run pytest -q` — **25 passed**. `uv run ruff check .` y
`uv run ruff format --check .` — **PASS**. `uv run mypy` — **PASS**.
CLI determinista — output byte-for-byte reproducible. Phase 0B probes — 7/7.

## Last verified commit
`c890563` — implementación 0C.1 y 25 tests de invariantes; documentación final
se añade en el commit siguiente.

## Next 3 actions
1. Revisar el Draft PR #2 con la evidencia de 0C.1; no entrar aún en 0D.
2. Decidir humanamente si procede un test real-data limitado y adversarial.
3. Si se autoriza después, comparar arquitecturas con gates comunes y evidencia
   LOS/calidad/coste; no construir un sistema operacional.

## Do not do yet
Dashboard · ML · hardware · control de drones · dispatch real · integración 112/
INFOMA · descargas masivas · BVLOS · computer vision en vivo · optimización pesada
· cualquier trabajo de Phase 0D sin decisión humana explícita.

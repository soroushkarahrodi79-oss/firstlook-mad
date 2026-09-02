# PROJECT_STATE — FIRSTLOOK-MAD

> Ledger operacional conciso. Permite continuar el proyecto en otra sesión o con
> otro agente. **No** es un diario. Se actualiza al final de cada bloque
> significativo. Al reanudar: `git status` → `git log --oneline -10` → leer este
> archivo → revisar último gate → comprobar tests → continuar.

---

## Current phase
**Phase 0D — falsación adversarial con datos reales, ejecutada y cerrada.
STOP antes de 0E.**

## Current gate
**MADRID REAL DATA MVP — `FAIL (BLOCKED: EXECUTION ENVIRONMENT EGRESS)`**
(2026-08-31). Señal estratégica: **`INSUFFICIENT EVIDENCE`**.

El propietario autorizó Phase 0D el 2026-08-31. Se pre-registró el protocolo
(`docs/PHASE_0D_PROTOCOL.md`) y se intentó de inmediato la adquisición acotada
contra las 7 fuentes ya validadas como accesibles en 0B más 7 extractos
adicionales pequeños. **Las 7 fallaron el 100% de las veces**, bloqueadas por
la política de salida de red de este entorno de ejecución (`403 Forbidden` en
el túnel del proxy, antes de alcanzar el servidor de destino), confirmado con
un dominio de control no registrado en el proyecto. No se obtuvo ningún byte
de dato externo nuevo. Ningún supuesto A-01–A-04 cambió de estado; todos
permanecen exactamente como los dejó 0C.1. Ver
`PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` para el detalle completo,
incluida la revisión adversarial obligatoria y la acción humana mínima
requerida para reintentar.

Gate anterior: **SYNTHETIC MODEL — PASS** técnico; revisión 0C.1:
**`CONDITION_DEPENDENT_STRONG`** (2026-08-27). Lectura científica: **PASS WITH
CONDITIONS — ROBUSTNESS AUDIT REQUIRED**. La erosión A→F sobrevive 25 seeds,
A-01 es `STRONGLY_CONDITION_DEPENDENT` y el comparador de cámaras/docks es
`INCOMPARABLE`, no una victoria de cámara. No hay soporte para `BUILD`. Esta
lectura de 0C.1 **sigue siendo la última evidencia científica válida**: 0D no
la modificó, porque no logró generar evidencia con la que confrontarla.

Gate anterior a ese: **DATA FEASIBILITY — DATA PARTIAL** (2026-08-26). Gate de
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
- Autorización humana explícita de Phase 0D (propietario, 2026-08-31).
- `docs/PHASE_0D_PROTOCOL.md`: preguntas, evidencia esperada, lógica de
  decisión por test, regla de missing-data y stop rules, pre-registrados
  antes de cualquier intento de adquisición.
- Adquisición acotada 0D.1: `data/phase0d_source_probes.json` +
  `scripts/acquire_phase0d_sources.py`, con clasificación de resultado
  (`ACQUIRED`/`NETWORK_EGRESS_BLOCKED`/`HTTP_ERROR`/`OTHER_ERROR`) y 9 tests
  nuevos (`tests/test_phase0d_acquisition.py`).
- Reintento de las 7 fuentes accesibles en 0B: 0/7 en 2026-08-31 (vs 7/7 en
  2026-08-26), registrado en `data/datasets_manifest.json` →
  `phase0d_reattempt` y en `outputs/reports/phase0d_acquisition_log.json`.
- `PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md`: gate, evidencia, revisión
  adversarial obligatoria (§9 brief) y acción humana mínima requerida.
- `docs/ASSUMPTIONS.md` y `docs/LIMITATIONS.md` actualizados con el bloqueador
  de 0D; ningún supuesto pasó a `SUPPORTED`/`REFUTED`.

## In progress
- Ninguno. Stop point tras el cierre de Phase 0D — no se entra en Phase 0E.

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
sensibilidad. Ninguna está `SUPPORTED`. Phase 0D intentó falsación real para
A-01–A-04 y fue bloqueada antes de alcanzar cualquier fuente externa
(ver Current gate); **ningún estado cambió**.

## Known blockers
- `NO_PUBLIC_TTFRP_BASELINE`: faltan clocks públicos end-to-end.
- `NO_PUBLIC_REGIONAL_SITE_LAYER`: no hay capa regional reutilizable de activos
  INFOMA con coordenadas, aptitud y disponibilidad.
- Histórico EFFIS completo requiere solicitud humana.
- Falta perfil UAS verificable y meteo histórica local de visibilidad/ráfagas.
- Línea de visión, equivalencia/calidad de imagen y costes de cámaras/híbrido.
- Distribución real de incidentes, sitios y restricciones históricas.
- **Nuevo en 0D:** `EXECUTION_ENVIRONMENT_EGRESS_BLOCKED` — este entorno de
  ejecución de agente bloquea la salida de red hacia `servais.enaire.es`,
  `opendata.aemet.es`, `maps.effis.emergency.copernicus.eu`,
  `api-features.idee.es`, `overpass-api.de`, `datos.madrid.es` y
  `servicio.mapa.gob.es` (403 en el túnel del proxy, confirmado también con
  un dominio de control no registrado en el proyecto). No es un hallazgo
  sobre disponibilidad de datos en Madrid — Phase 0B ya probó 7/7 accesibles.
  Acción humana mínima: ejecutar `scripts/acquire_phase0d_sources.py` desde
  un entorno con esos dominios permitidos, o depositar manualmente los
  extractos en `data/raw/` con procedencia.

## Data status
`DATA PARTIAL`: 19 fuentes — 5 `READY`, 9 `PARTIAL`, 1 `BLOCKED`,
4 `REFERENCE_ONLY`. Siete probes oficiales respondieron en 0B (2026-08-26);
el reintento de 0D (2026-08-31) obtuvo 0/7 por el bloqueador de entorno de
ejecución de arriba, no por cambio en las fuentes. No se descargaron ni
cachearon datasets masivos; `data/raw/` permanece inmutable.

Datos 0C: únicamente `SYNTHETIC`/`ASSUMED`, seed `260827`, configuración y output
versionados. Ninguna cifra es una observación de Madrid. Datos 0D: ningún dato
`REAL` nuevo de Madrid se obtuvo; el único artefacto nuevo es el log de
intentos de adquisición (`REAL` sobre el propio entorno de ejecución, no sobre
Madrid) en `outputs/reports/phase0d_acquisition_log.json`.

## Test status
`uv run pytest -q` — **34 passed** (25 de 0C.1 + 9 nuevos de 0D). `uv run ruff
check .` y `uv run ruff format --check .` — **PASS**. `uv run mypy` —
**PASS**. CLI determinista — output byte-for-byte reproducible. Phase 0B
probes — 7/7 (2026-08-26). Phase 0D re-probe — 0/7 (2026-08-31, bloqueador de
entorno, ver Known blockers).

## Last verified commit
Phase 0D quedó fusionada en `main` vía PR #3 (merge commit
`9c302aa338676b789b75d614306d2a05e3b78f33`): protocolo pre-registrado,
adquisición acotada bloqueada + tests, informe de gate, y la actualización de
documentación asociada. Ver `git log` en `main` para el hash exacto más
reciente. No hay trabajo en curso ni PR abierto.

## Next 3 actions
1. Phase 0D ya está fusionada en `main` y cerrada con gate `FAIL (BLOCKED:
   EXECUTION ENVIRONMENT EGRESS)`, señal `INSUFFICIENT EVIDENCE`. No queda
   revisión de PR pendiente.
2. Decidir humanamente cómo desbloquear el acceso de red (allowlist de los 7
   dominios) o depositar manualmente los extractos pequeños ya especificados
   en `data/raw/`, y reintentar 0D.1–0D.6 con datos reales genuinos.
3. No entrar en Phase 0E hasta que exista evidencia real con la que
   confrontar la lectura de 0C.1 (`CONDITION_DEPENDENT_STRONG`, sin soporte
   para `BUILD`).

## Do not do yet
Dashboard · ML · hardware · control de drones · dispatch real · integración 112/
INFOMA · descargas masivas · BVLOS · computer vision en vivo · optimización pesada
· Phase 0E o cualquier trabajo de arquitectura hasta que Phase 0D produzca
evidencia real (bloqueada por entorno de ejecución, ver Current gate) y un
humano la revise.

# PROJECT_STATE — FIRSTLOOK-MAD

> Ledger operacional conciso. Permite continuar el proyecto en otra sesión o con
> otro agente. **No** es un diario. Se actualiza al final de cada bloque
> significativo. Al reanudar: `git status` → `git log --oneline -10` → leer este
> archivo → revisar último gate → comprobar tests → continuar.

---

## Current phase
**Phase 0D.1 — endurecimiento de adquisición local (procedencia), en curso.
STOP antes de 0E. STOP antes de 0D.2 (normalización) hasta nueva
adquisición con el script endurecido.**

## Current gate
**MADRID REAL DATA MVP — `FAIL (BLOCKED: EXECUTION ENVIRONMENT EGRESS)`**
(2026-08-31, entorno de agente Claude Code de esa sesión). Señal
estratégica: **`INSUFFICIENT EVIDENCE`**. Este gate **no se reabre ni se
mejora** por el trabajo de 2026-09-02 descrito abajo — sigue siendo la
última lectura formal de fase hasta que 0D.2–0D.6 se ejecuten sobre datos
reales genuinos.

**2026-09-02 — reintento local + endurecimiento 0D.1 (rama
`research/phase0d-local-retry-2026-09-02`, no fusionada):** el propietario
ejecutó el mismo script sin cambios desde su máquina Windows local (Python
3.14.5) y obtuvo 5/7 HTTP 200 con 0/7 `NETWORK_EGRESS_BLOCKED` — confirma
que el bloqueador de 2026-08-31 era específico de aquel entorno de agente,
no de las fuentes ni de Madrid. Este reintento también reveló que la
implementación clasificaba un HTTP 200/0 bytes de AEMET como `ACQUIRED`.
Corrección aplicada (desviación metodológica fechada, ver
`docs/PHASE_0D_PROTOCOL.md` §7.1–§7.2 y
`PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` §16): nuevo resultado
`EMPTY_RESPONSE`, persistencia inmutable de bytes crudos con SHA-256 y
provenance para probes genuinamente `ACQUIRED`, AEMET consciente de
credenciales (`AEMET_API_KEY`, sin clave hard-codeada ni solicitada), sin
tocar la política TLS de Overpass ni sustituir el endpoint 502 de EFFIS. El
log local del 2026-09-02
(`outputs/reports/phase0d_acquisition_log_local_2026-09-02.json`) se
preserva sin modificar como evidencia del defecto pre-corrección. Ningún
supuesto A-01–A-04 cambió de estado; ninguna adquisición real nueva se
ejecutó bajo el script endurecido en esta tarea.

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
- **2026-09-02:** endurecimiento de adquisición 0D.1: `EMPTY_RESPONSE` y
  `CREDENTIAL_REQUIRED` como resultados explícitos distintos de `ACQUIRED`;
  persistencia inmutable de bytes crudos con SHA-256 + provenance
  (`persist_raw_response` en `scripts/acquire_phase0d_sources.py`, bajo
  `data/raw/phase0d/<probe_id>/`); AEMET consciente de `AEMET_API_KEY` sin
  clave hard-codeada; tests nuevos en `tests/test_phase0d_acquisition.py`;
  desviación metodológica fechada en `docs/PHASE_0D_PROTOCOL.md` §7.1–§7.2;
  adenda en `PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` §16.

## In progress
- Revisión humana del endurecimiento 0D.1 en la rama
  `research/phase0d-local-retry-2026-09-02` (sin fusionar, sin PR abierto por
  este agente). Pendiente: que el propietario ejecute la siguiente
  adquisición acotada con el script endurecido y un nombre de output nuevo
  (no sobrescribir `phase0d_acquisition_log_local_2026-09-02.json`).

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
- **De 0D (2026-08-31), específico de aquel entorno de agente:**
  `EXECUTION_ENVIRONMENT_EGRESS_BLOCKED` — 403 en el túnel del proxy hacia
  los 7 dominios registrados, confirmado también con un dominio de control
  no registrado. **Actualización 2026-09-02:** el reintento local del
  propietario (Windows, Python 3.14.5, mismo script) no reprodujo este
  bloqueo — 0/7 `NETWORK_EGRESS_BLOCKED`. Esto confirma que era específico
  de aquel entorno de agente concreto, no de las fuentes ni de Madrid; no se
  generaliza a "resuelto para siempre" — cada entorno/ejecución debe
  reverificarse.
- **Nuevo, descubierto en el reintento local de 2026-09-02 y ya corregido:**
  defecto de clasificación — HTTP 200 con 0 bytes (AEMET) se marcaba
  `ACQUIRED`/`REAL`. Corregido con el resultado explícito `EMPTY_RESPONSE`
  (ver `docs/PHASE_0D_PROTOCOL.md` §7.1). El log que documenta el defecto se
  conserva sin modificar en
  `outputs/reports/phase0d_acquisition_log_local_2026-09-02.json`.
- **Sigue pendiente:** clave de API AEMET (`AEMET_API_KEY`, no provista ni
  solicitada por este agente); histórico completo de EFFIS (solicitud
  humana); el 502 de EFFIS y el fallo TLS/certificado de Overpass observados
  el 2026-09-02 siguen sin resolver y no se han enmascarado ni sorteado.

## Data status
`DATA PARTIAL`: 19 fuentes — 5 `READY`, 9 `PARTIAL`, 1 `BLOCKED`,
4 `REFERENCE_ONLY`. Siete probes oficiales respondieron en 0B (2026-08-26);
el reintento de 0D (2026-08-31) obtuvo 0/7 por el bloqueador de entorno de
ejecución de arriba, no por cambio en las fuentes. No se descargaron ni
cachearon datasets masivos; `data/raw/` permanece inmutable.

Datos 0C: únicamente `SYNTHETIC`/`ASSUMED`, seed `260827`, configuración y output
versionados. Ninguna cifra es una observación de Madrid. Datos 0D (2026-08-31):
ningún dato `REAL` nuevo de Madrid se obtuvo; el único artefacto nuevo fue el
log de intentos de adquisición (`REAL` sobre el propio entorno de ejecución,
no sobre Madrid) en `outputs/reports/phase0d_acquisition_log.json`. Reintento
local (2026-09-02): 4 respuestas HTTP 200 con cuerpo no vacío (ENAIRE, IGN,
Madrid Open Data, EGIF) fueron clasificadas `ACQUIRED` por la lógica
*pre-endurecimiento*, pero **ningún byte fue persistido** (el script aún no
tenía persistencia de evidencia cruda) — no hay ningún archivo `REAL` de
Madrid en `data/raw/` todavía. `data/raw/phase0d/` es el nuevo destino
determinista para la próxima adquisición ejecutada con el script endurecido.

## Test status
Antes del endurecimiento 0D.1: `uv run pytest -q` — **34 passed** (25 de 0C.1
+ 9 de 0D), `ruff check`/`ruff format --check`/`mypy` — **PASS**. Tras el
endurecimiento 0D.1 (2026-09-02): tests ampliados en
`tests/test_phase0d_acquisition.py` (cuerpo vacío → `EMPTY_RESPONSE`,
persistencia inmutable de bytes crudos, SHA-256, provenance, no-overwrite,
credencial AEMET ausente/no filtrada, TLS/certificado y errores HTTP
preservados como no-`REAL`) — ver resultado exacto en el reporte de esta
sesión. CLI determinista — output byte-for-byte reproducible salvo
timestamps. Phase 0B probes — 7/7 (2026-08-26). Phase 0D re-probe agente
Claude Code — 0/7 (2026-08-31, bloqueador de entorno). Reintento local
propietario — 5/7 HTTP 200, 0/7 bloqueados por red (2026-09-02, ver Current
gate).

## Last verified commit
Phase 0D quedó fusionada en `main` vía PR #3 (merge commit
`9c302aa338676b789b75d614306d2a05e3b78f33`) y housekeeping posterior vía PR #4
(`803abb3`): protocolo pre-registrado, adquisición acotada bloqueada + tests,
informe de gate, y la actualización de documentación asociada. El
endurecimiento 0D.1 (2026-09-02) vive sin commitear/sin PR en la rama
`research/phase0d-local-retry-2026-09-02`, creada sobre ese estado de `main`.
No se ha abierto PR ni fusionado nada para este trabajo todavía.

## Next 3 actions
1. El propietario revisa el endurecimiento 0D.1 en la rama
   `research/phase0d-local-retry-2026-09-02` (script, tests, provenance,
   AEMET credential-aware). No se ha abierto PR ni se ha fusionado nada
   automáticamente.
2. Si se aprueba, el propietario ejecuta la siguiente adquisición acotada
   localmente con el script endurecido, usando un **nombre de output
   nuevo** (no sobrescribir `phase0d_acquisition_log_local_2026-09-02.json`)
   — por ejemplo `--output outputs/reports/phase0d_acquisition_log_local_<fecha>.json`.
   Esta ejecución persistirá bytes crudos reales en `data/raw/phase0d/` con
   provenance completa, y clasificará AEMET honestamente según si
   `AEMET_API_KEY` está definida.
3. No entrar en Phase 0E ni ejecutar 0D.2 (normalización) hasta que exista
   evidencia real persistida con la que confrontar la lectura de 0C.1
   (`CONDITION_DEPENDENT_STRONG`, sin soporte para `BUILD`).

## Do not do yet
Dashboard · ML · hardware · control de drones · dispatch real · integración 112/
INFOMA · descargas masivas · BVLOS · computer vision en vivo · optimización pesada
· Phase 0E o cualquier trabajo de arquitectura hasta que Phase 0D produzca
evidencia real (bloqueada por entorno de ejecución, ver Current gate) y un
humano la revise.

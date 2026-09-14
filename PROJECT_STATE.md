# PROJECT_STATE — FIRSTLOOK-MAD

> Ledger operacional conciso. Permite continuar el proyecto en otra sesión o con
> otro agente. **No** es un diario. Se actualiza al final de cada bloque
> significativo. Al reanudar: `git status` → `git log --oneline -10` → leer este
> archivo → revisar último gate → comprobar tests → continuar.

---

## Current phase
**Phase 0D.3 — sustitución de realidad por etapas. Entry `LIMITED_PROCEED`;
gate 0D.3 evaluado (2026-09-14): `SUBSTITUTION_UNINFORMATIVE`. STOP antes de
0D.4. Ningún supuesto pasó a `SUPPORTED`/`REFUTED`; ninguna decisión
`BUILD/REPOSITION/KILL`; Phase 0E no iniciada.**

## Phase 0D.3 reality-substitution gate (2026-09-14)
**Entry `LIMITED_PROCEED`; veredicto `SUBSTITUTION_UNINFORMATIVE`** por la regla
pre-registrada en `docs/PHASE_0D3_PREREGISTRATION.md` (el diseño se pre-especificó
en la sesión antes de ejecutar el experimento según el flujo registrado; **pero
pre-registro, implementación y salidas se commitearon juntos, así que ese orden
no es verificable de forma independiente desde el historial de Git**; no ciego —
la evidencia 0D.1/0D.2 ya se conocía; ningún umbral cambió tras ver los
resultados). Se sustituyó **una sola** variable sintética —las localizaciones de
sitios candidatos A-02— por los 13 parques reales de 0D.2, sobre una **extensión
envolvente de estaciones igualada** (caja delimitadora de las 13 localizaciones
canónicas en `EPSG:25830`, ≈231,7 km² = 1,9 % del dominio analítico de 0C.1;
**no** es el límite municipal oficial de Madrid ni el soporte legal del dataset
fuente —cuya cobertura declarada `MADRID_MUNICIPALITY` se conserva como hecho de
fuente—, solo un extent derivado del repositorio para mantener el soporte
geográfico constante entre brazos). Solo se compararon métricas
**de geometría** (los modelos/comparadores que leen propiedades operativas quedan
`NOT_EVALUATED`, porque la evidencia real no las establece). Resultado: la
distancia mediana incidente→candidato más cercano sube +5,98 % (bajo el umbral
material pre-registrado de 20 %), la cobertura Modelo-A satura en 1,0 en ambos
brazos (sin cruce de umbral), y la dirección del efecto **no** es estable en los
25 seeds (13 vs 12). `SUBSTITUTION_INFORMATIVE` era inalcanzable por
pre-registro (alcance municipal + demanda sintética). Motor 0C.1 reutilizado sin
duplicar. Informe: `PHASE_0D3_REALITY_SUBSTITUTION_GATE_REPORT.md`; JSON:
`outputs/reports/phase0d3_substitution_manifest.json` y
`outputs/reports/phase0d3_substitution_results.json`. **No** es `SUPPORTED`,
`BUILD`, `SAFE_TO_FLY`, `MADRID VALIDATED`, ni autorización para 0D.4. Ningún
parque se convirtió en dock validado; propiedades operativas siguen
`NOT_EVALUATED`.

## Phase 0D.2 normalization gate (2026-09-13)
**`PARTIAL_NORMALIZATION`**, por la regla pre-registrada en
`docs/PHASE_0D2_PREREGISTRATION.md` (commit `b2e9a67`: reglas fijadas antes de
la implementación de la normalización, antes de generar las salidas normalizadas
de 0D.2 y antes de evaluar el gate; la evidencia ya había sido adquirida y
caracterizada en 0D.1, así que no es un pre-registro ciego; ningún umbral cambió
tras ver los resultados de 0D.2). Elegibilidad analítica
por supuesto (nivel de insumo, no de decisión científica): **A-01 `NOT_ELIGIBLE`**
(`BASELINE_NOT_OBSERVABLE`: 7 artefactos de interfaz EGIF, 0 registros de
incidente); **A-02 `ELIGIBLE_WITHIN_DECLARED_SCOPE`** (13/13 parques municipales
canónicos en EPSG:25830, 0 rechazos; cobertura declarada solo municipio de
Madrid); **A-03 `NOT_ELIGIBLE`** (ENAIRE truncado por la fuente, 50/50 con
`exceededTransferLimit`; MDT05 ventana 100 m × 100 m de prueba de cadena);
**A-04 `NOT_ELIGIBLE`** (inventario 926 estaciones / 23 Madrid; sin
observaciones → `WEATHER_EVIDENCE_NOT_OBSERVABLE`). Integridad 16/16 `PASS`.
Informe: `PHASE_0D2_NORMALIZATION_GATE_REPORT.md`; JSON:
`outputs/reports/phase0d2_normalization_report.json`. **No** es
`NORMALIZATION_READY`, `SUPPORTED`, `BUILD` ni autorización para 0D.3.

## Phase 0D.1 acquisition gate (2026-09-07)
**`0D.1 REAL INPUT AVAILABLE`.** La regla de adquisición pre-registrada declara
`REAL INPUT AVAILABLE` cuando al menos un supuesto prioritario tiene insumo real
genuino, verificado por integridad y semánticamente utilizable — satisfecho por
A-02. **No** se degrada a `PARTIAL REAL INPUT` por que A-01/A-03/A-04 sigan
incompletos (eso sería un cambio de threshold posterior a los resultados).
Insumo real por supuesto (nivel de adquisición, no de decisión científica):
**A-01 `PARTIAL_REAL_INPUT`** (interfaz EGIF, sin baseline TTFRP), **A-02
`USABLE_REAL_INPUT`** (parques de bomberos reales), **A-03 `PARTIAL_REAL_INPUT`**
(muestras acotadas ENAIRE + IGN MDT05 `GetCoverage` + metadatos IGN; no capas
completas), **A-04 `PARTIAL_REAL_INPUT`** (inventario de estaciones AEMET real,
no observaciones meteo). `0D.1 REAL INPUT AVAILABLE` **no** significa Phase 0D
`PASS` científico, `SUPPORTED`, `MADRID VALIDATED`, `BUILD` ni `SAFE_TO_FLY`: no
sustituye el gate científico de §13 del informe de falsación (sigue
`FAIL, BLOCKED: EXECUTION ENVIRONMENT EGRESS`, 2026-08-31) ni la lectura
`CONDITION_DEPENDENT_STRONG` de 0C.1 (sin soporte para `BUILD`). Ver
`PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` §17 y
`docs/PHASE_0D_PROTOCOL.md` §7.3.

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
- **2026-09-07 (0D.1D):** cierre de adquisición acotada. IGN MDT05:
  `GetCoverage` real único y acotado (`scripts/acquire_phase0d_ign_mdt_coverage.py`,
  cobertura `Elevacion25830_5`, EPSG:25830, ventana ~100 m × 100 m, TLS
  verificado) → GeoTIFF genuino de 1.256 B (20×20, 5 m, elevaciones 648–654 m)
  clasificado `REAL_SOURCE_DATA` tras inspeccionar contenido. AEMET segundo
  salto de 167.915 B (`ISO-8859-15`, 926 estaciones, 23 Madrid) reclasificado
  a `REAL_SOURCE_DATA` vía override por SHA-256 de contenido en
  `scripts/provenance_ledger.py` (`ARTIFACT_CLASSIFICATIONS`). Ledger
  payload-free regenerado (16 entradas) bajo `outputs/provenance/phase0d/`;
  integridad SHA-256 reverificada (0 discrepancias), 0 secretos, 0 payload.
  Tests nuevos `tests/test_phase0d_ign_mdt_coverage.py` + caso de override en
  `tests/test_provenance_ledger.py`. Desviación en
  `docs/PHASE_0D_PROTOCOL.md` §7.3; adenda en el informe §17. Empaquetado en
  **PR #5** (abierto, borrador «Do not merge»; pendiente de revisión/fusión
  humana). Fusionado después por el propietario (2026-09-13, merge `eb637c2`).
- **2026-09-13 (0D.2):** gate pre-registrado (`docs/PHASE_0D2_PREREGISTRATION.md`);
  capa de normalización `src/firstlook_mad/normalization/` (integridad
  ledger → sidecar → bytes, CRS `EPSG:4326 → EPSG:25830`, A-02 canónico, A-03
  con alcance acotado explícito, A-04 con cuatro hechos de preparación
  separados, A-01 `BASELINE_NOT_OBSERVABLE`, regla de gate); runner
  `scripts/normalize_phase0d2.py`; informe JSON determinista y derivado canónico
  A-02 (CC-BY-4.0) versionados; derivados ENAIRE/AEMET en `data/processed/`
  (gitignored); 93 tests nuevos; informe de gate
  `PHASE_0D2_NORMALIZATION_GATE_REPORT.md`. Veredicto `PARTIAL_NORMALIZATION`.

## In progress
- **PR borrador de Phase 0D.3** hacia `main`: «Phase 0D.3 — staged reality
  substitution». Entry `LIMITED_PROCEED`, veredicto `SUBSTITUTION_UNINFORMATIVE`.
  Pendiente: **revisión humana**. **No** inicia 0D.4. Este agente **no** fusiona.
- PR de Phase 0D.2 ya fusionado en `main` (merge `abdd260`, PR #14).

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
(ver Current gate); **ningún estado cambió**. Phase 0D.2 (2026-09-13) solo
normalizó la evidencia de 0D.1 y evaluó su aptitud semántica; **ningún estado
cambió** tampoco.

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
- **De 0D.2 (2026-09-13):** A-01 sin registros de incidente EGIF
  (`BASELINE_NOT_OBSERVABLE`); A-02 limitado al municipio de Madrid (13 parques,
  envolvente ≈232 km², ≈1,9 % de la extensión sintética de 0C.1; sin activos
  regionales/INFOMA); A-03 ENAIRE truncado por la fuente (50/50,
  `exceededTransferLimit`) y MDT05 solo ventana de 100 m; A-04 sin
  observaciones meteorológicas (`WEATHER_EVIDENCE_NOT_OBSERVABLE`).

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

Datos 0D.2 (2026-09-13): `data/raw/phase0d/` no se modificó (integridad 16/16
`PASS`). Derivados `DERIVED` desde `REAL`: canónico A-02 versionado
(`outputs/canonical/phase0d2/`, CC-BY-4.0, 13 registros); derivados ENAIRE (50
zonas, acotado y truncado) e inventario AEMET Madrid (23 estaciones) solo en
`data/processed/phase0d2/` (gitignored). Informe de calidad payload-free en
`outputs/reports/phase0d2_normalization_report.json`.

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
gate). Cierre 0D.1D: 72 passed. **0D.2 (2026-09-13, Python 3.12.10):**
`uv run pytest -q` — **165 passed** (72 + 93 nuevos, incluida la regeneración
byte a byte del informe desde la evidencia cruda local); `ruff check`,
`ruff format --check` (69 archivos) y `mypy` estricto (30 archivos) — **PASS**;
dos ejecuciones del runner 0D.2 producen salidas idénticas byte a byte.
**0D.3 (2026-09-14, Python 3.12):** `uv run pytest -q` — **192 passed, 1
skipped** (165 + 28 nuevos en `tests/test_phase0d3_reality_substitution.py`; el
skip es la prueba 0D.2 que requiere evidencia cruda local gitignored, ausente en
cloud); `ruff check`, `ruff format --check` (77 archivos) y `mypy` estricto (35
archivos) — **PASS**; `git diff --check` limpio; dos ejecuciones del runner 0D.3
producen manifest y results idénticos byte a byte; 0C.1 reverificado reproducible
byte a byte desde inputs versionados.

## Last verified commit
Phase 0D quedó fusionada en `main` vía PR #3 (merge commit
`9c302aa338676b789b75d614306d2a05e3b78f33`) y housekeeping posterior vía PR #4
(`803abb3`): protocolo pre-registrado, adquisición acotada bloqueada + tests,
informe de gate, y la actualización de documentación asociada. El
endurecimiento y cierre 0D.1 (2026-09-02 → 2026-09-07) vive en 4 commits
(`9480db8`, `67ab295`, `e93907c`, `7bc39c9`) en la rama
`research/phase0d-local-retry-2026-09-02`, creada sobre ese estado de `main`, y
empaquetado en **PR #5** (abierto, pendiente de fusión humana). Nada de este
trabajo se ha fusionado en `main` todavía.

**Actualización 2026-09-13:** PR #5 fusionado en `main` (merge `eb637c2`). La
rama `research/phase0d2-real-data-normalization` parte de `eb637c2`; sus commits
de 0D.2 (pre-registro `b2e9a67` y siguientes) están en un PR borrador pendiente
de revisión humana, sin fusionar.

## Next 3 actions
1. El propietario revisa y, si procede, **fusiona el PR borrador de 0D.3**
   manualmente. Este agente **no** fusiona. El veredicto
   `SUBSTITUTION_UNINFORMATIVE` confirma la predicción de 0D.2: una sustitución
   solo-A-02 municipal es poco informativa (la evidencia real, a su alcance real,
   aún no mueve la geometría del modelo de forma material ni estable).
2. El propietario decide si autoriza **Phase 0D.4** (falsación adversarial). Nada
   en 0D.3 la habilita automáticamente; 0D.3 no cambia ningún supuesto.
3. Con autorización explícita, cerrar huecos de evidencia sin inflarla, como
   pre-condición para que cualquier sustitución futura sea informativa:
   demanda real de incidentes (A-01, hoy `BASELINE_NOT_OBSERVABLE`), activos
   regionales/INFOMA (A-02 más allá del municipio), capas ENAIRE/terreno
   completas (A-03) y observaciones meteo de días de fuego (A-04). No entrar en
   Phase 0E ni cambiar ningún supuesto a `SUPPORTED`/`REFUTED`.

## Do not do yet
Dashboard · ML · hardware · control de drones · dispatch real · integración 112/
INFOMA · descargas masivas · BVLOS · computer vision en vivo · optimización pesada
· Phase 0E o cualquier trabajo de arquitectura hasta que Phase 0D produzca
evidencia real (bloqueada por entorno de ejecución, ver Current gate) y un
humano la revise.

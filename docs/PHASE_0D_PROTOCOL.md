# PHASE 0D PROTOCOL — MADRID REAL DATA FALSIFICATION (MVP)

> **Fase:** 0D · **Fecha de pre-registro:** 2026-08-31  
> **Autorización:** propietaria del proyecto, 2026-08-31 (satisface el gate humano
> pendiente tras 0C.1)  
> **Uso:** `RESEARCH / SIMULATION PROTOTYPE ONLY`

Este documento se registra **antes** de intentar la adquisición o el análisis
de cualquier resultado de Phase 0D. Fija preguntas, evidencia esperada, lógica
de decisión y stop rules. Cualquier cambio posterior a ver resultados se
documenta como desviación (ver §7) — no se ajustan umbrales para rescatar la
hipótesis.

## 1. Objetivo

Determinar si una cantidad **mínima y trazable** de datos reales de Madrid
puede falsar, debilitar materialmente o acotar los supuestos y conclusiones que
sobrevivieron el experimento sintético de 0C.1. Es una fase **adversarial**, no
de construcción de producto. Un resultado negativo (`REPOSITION`/`KILL`) es
tan válido como uno positivo. No se optimiza el análisis para demostrar que la
red de docks funciona.

## 2. Alcance de ejecución (0D.1–0D.6)

Secuencia acotada, tal como fija `docs/VALIDATION_PLAN.md` §4 y el brief del
propietario:

1. **0D.1** — procedencia + adquisición acotada.
2. **0D.2** — normalización (schema, CRS, alineación temporal, checks de
   calidad y procedencia).
3. **0D.3** — tests adversariales pre-registrados (§4).
4. **0D.4** — sensibilidad ante incertidumbre plausible.
5. **0D.5** — red-team explícito.
6. **0D.6** — informe de gate.

## 3. Preguntas por prioridad (ver `docs/ASSUMPTIONS.md`)

| Prioridad | Supuesto | Pregunta real-data | Evidencia esperada |
|---|---|---|---|
| 1 | A-01 | ¿El tránsito UAS es una fracción material del TTFRP real? | EGIF (partes consolidados) para descomponer tiempos de primera llegada donde estén disponibles |
| 2 | A-04 | ¿La meteo real de días de fuego erosiona sistemáticamente la disponibilidad UAS asumida? | AEMET OpenData / ERA5-Land para fechas EGIF de Madrid |
| 3 | A-03 | ¿La erosión sintética A→F sigue siendo plausible con geometría real de Madrid? | IGN (MDT05, redes), geozonas ENAIRE, límites municipales |
| 4 | A-02 | ¿Existen sitios candidatos reales verificables? | Directorio regional de parques, datos.madrid.es, OpenStreetMap |
| 5 | Comparador | ¿Cámara fija y UAS son comparables con evidencia real? | Ninguna fuente pública identificada cubre LOS/humo/FOV/calidad — ver §16 DATA_FEASIBILITY_REPORT |

## 4. Lógica de decisión por test (fijada antes de ver resultados)

### 4.1 A-01 — cuello de botella TTFRP

- **Fortalece** el supuesto (tránsito material): evidencia real muestra que el
  componente de traslado de un medio aéreo/terrestre representa una fracción
  mediana ≥40% del tiempo hasta primera llegada en una muestra ≥20 incidentes
  Madrid con datos completos.
- **Debilita**: la fracción mediana observable es <20%, o los componentes no
  observables (alerta/verificación) dominan sistemáticamente en la muestra
  disponible.
- **Refuta**: evidencia directa y consistente de que el tiempo de traslado es
  irrelevante frente al resto de la cadena en la mayoría de casos observables.
- **Inconcluso**: la muestra es insuficiente (<10 registros utilizables), o
  EGIF no separa temporalmente alerta/verificación/traslado con calidad
  suficiente.
- **Missing-data**: si no se puede extraer ni un registro real trazable de
  EGIF (por bloqueo de acceso, ausencia de API o licencia insuficiente para
  reuso), el resultado es **`BASELINE_NOT_OBSERVABLE`** — no se convierte en
  soporte para el supuesto ni en refutación.

### 4.2 A-04 — erosión meteorológica

- **Fortalece** el supuesto (meteo no anula el valor): en un muestreo de días
  reales de fuego en Madrid, la fracción de días con viento/visibilidad fuera
  del envelope asumido conservador es <20%.
- **Debilita**: la fracción fuera de envelope es 20–60%.
- **Refuta**: la fracción es >60%, es decir la meteo de días de fuego anula
  sistemáticamente la disponibilidad asumida.
- **Inconcluso**: no hay visibilidad histórica local verificable — el gate
  conservador ya asume 0% ante visibilidad `UNKNOWN`, y eso es una regla de
  diseño, no evidencia de frecuencia real.
- **Missing-data**: si AEMET/ERA5-Land no son accesibles con las credenciales
  disponibles, el resultado es **`WEATHER_EVIDENCE_NOT_OBSERVABLE`**, y A-04
  permanece en su estado previo (no pasa a `SUPPORTED`).

### 4.3 A-03 — geometría real de Madrid

- **Fortalece** el supuesto (los buffers geométricos sobreestiman cobertura):
  la erosión ponderada A→F con geometría real (límites municipales, geozonas,
  relieve) es igual o mayor que la observada en 0C.1 (45,20–72,75 pp).
- **Debilita**: la erosión con geometría real es sustancialmente menor
  (diferencia >20 pp) que en 0C.1, sugiriendo que la geometría sintética
  exageraba el problema.
- **Refuta**: la erosión desaparece casi por completo con geometría real
  (<10 pp).
- **Inconcluso/missing-data**: si solo se puede sustituir una parte de la
  geometría (p. ej. límites municipales reales pero sitios/incidentes
  sintéticos), el resultado se etiqueta explícitamente como **geometría
  parcialmente real** y no se generaliza como "Madrid real".

### 4.4 A-02 — realidad de sitios candidatos

- **Fortalece**: existen ≥5 activos públicos verificables (dirección real,
  coordenadas trazables) geográficamente distribuidos en Madrid, que son
  técnicamente plausibles como candidato de investigación.
- **Debilita**: existen <5, o están fuertemente concentrados (p. ej. todos en
  el mismo distrito), lo que socava la narrativa de "red distribuida".
- **Refuta**: no existe ningún activo público verificable reutilizable como
  candidato de investigación.
- Se distingue explícitamente en todo momento: existencia geográfica ≠
  candidato técnicamente plausible ≠ propiedad pública ≠ accesibilidad ≠
  aptitud ≠ disponibilidad ≠ permiso. Ningún hallazgo de 0D convierte un sitio
  en desplegable.

### 4.5 Comparador cámara/UAS

- Permanece `INCOMPARABLE` salvo que 0D obtenga evidencia defendible para las
  dimensiones ausentes (LOS, oclusión por humo, FOV, capacidad de
  reconocimiento, equivalencia de imagen, disponibilidad de sitio, coste).
  Ninguna dimensión ausente se trata como favorable por defecto.

## 5. Missing-data — regla general

La ausencia de evidencia real **nunca** se convierte en soporte implícito de
viabilidad. Toda tabla de resultados de 0D distingue explícitamente:
`REAL` (observación directa) · `DERIVED` (calculado reproduciblemente desde
`REAL`) · `ASSUMED` (no observado) · `SYNTHETIC` (generado artificialmente).
Un dato `ASSUMED`/`SYNTHETIC` combinado con datos `REAL` en el mismo pipeline
**no** se convierte en `REAL`.

## 6. Stop rules

Se detiene el trabajo adicional de una rama de 0D cuando:

1. La fuente registrada resulta técnicamente inaccesible desde este entorno de
   ejecución (bloqueo de red, credencial no disponible, formulario de solicitud
   humana) — se documenta como bloqueador y se pasa a la siguiente prioridad,
   sin inventar workaround.
2. Un test ya alcanzó una clasificación de decisión clara (fortalece/debilita/
   refuta) con una muestra mínima suficiente — no se amplía la muestra solo
   para "asegurar" el resultado en una dirección.
3. El resultado depende de una fuente cuya licencia o procedencia no puede
   verificarse — no se usa el dato aunque esté técnicamente accesible.

## 7. Desviaciones metodológicas

Cualquier cambio de threshold, alcance o clasificación **después** de ver
evidencia se registra aquí con fecha, motivo y quién lo autorizó. Estado
inicial: sin desviaciones.

### 7.1 — 2026-09-02 — corrección de clasificación de adquisición (HTTP 200 + 0 bytes)

**Motivo:** la ejecución local del propietario el 2026-09-02 (ver
`outputs/reports/phase0d_acquisition_log_local_2026-09-02.json`, preservado
sin modificar como evidencia del defecto) mostró que el probe AEMET
(`aemet_madrid_station_inventory`) devolvió HTTP 200 con **0 bytes** de
cuerpo, y que `scripts/acquire_phase0d_sources.py` lo clasificaba como
`ACQUIRED` / `nature_if_used: REAL`. Un HTTP 200 con cuerpo vacío no puede
constituir evidencia `REAL` adquirida: no hay bytes que persistir, verificar
o normalizar.

**Naturaleza de la corrección:** es una corrección de
provenance/clasificación de ingeniería, **no** un ajuste de threshold
científico ni un intento de rescatar la hipótesis del proyecto. No cambia
ningún umbral de decisión de §4, no mueve ningún supuesto A-01–A-04 de
estado, y no reinterpreta ningún resultado de 0C.1.

**Corrección aplicada:** se añade el resultado explícito `EMPTY_RESPONSE`,
distinto de `ACQUIRED`, `HTTP_ERROR`, `OTHER_ERROR` y
`NETWORK_EGRESS_BLOCKED`. Solo un HTTP exitoso con cuerpo no vacío puede
producir `nature_if_used: REAL`, calcular SHA-256 y persistirse en
`data/raw/phase0d/`. Cubierto por tests nuevos en
`tests/test_phase0d_acquisition.py` (ver también §9 vinculante: `data/raw/`
permanece inmutable).

**Autorizado por:** propietario del proyecto, instrucción de auditoría de
Phase 0D.1 — endurecimiento de adquisición local (2026-09-02).

### 7.2 — 2026-09-02 — fin (local, no generalizable) del bloqueador `EXECUTION_ENVIRONMENT_EGRESS_BLOCKED`

**Motivo:** el mismo script, sin cambios de lógica de red, ejecutado el
2026-09-02 desde el entorno local Windows del propietario alcanzó 5/7
fuentes con HTTP 200 (4 con cuerpo no vacío antes de esta corrección, 1 —
AEMET — con cuerpo vacío) y 0/7 fallos `NETWORK_EGRESS_BLOCKED`, frente a
0/7 accesibles y 7/7 `NETWORK_EGRESS_BLOCKED` el 2026-08-31 en el entorno de
ejecución de agente Claude Code (ver
`PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` §5). Esto confirma que aquel
bloqueador era específico del entorno de agente de esa sesión, no de las
fuentes registradas ni de Madrid — exactamente como se advertía ya en §12 de
ese informe.

**No se actualiza ningún supuesto científico por este hallazgo.** Que un
entorno local pueda alcanzar la mayoría de las fuentes no es, por sí mismo,
evidencia científica sobre A-01–A-04; solo elimina un bloqueador de
infraestructura de ejecución para ese entorno concreto en esa fecha. No se
generaliza a "el acceso de red está resuelto para siempre" — cada ejecución
futura debe volver a verificarse. Ver
`PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` §16 (adenda 2026-09-02) para el
detalle completo, incluida la lista honesta de qué sigue sin observarse.

**Autorizado por:** propietario del proyecto (instrucción de Phase 0D.1,
2026-09-02).

## 8. Preguntas adversariales obligatorias

Ver §9 del brief del propietario — se responden explícitamente en
`PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` §8 (red-team), no se omiten
aunque la respuesta sea "no se pudo probar".

## 9. Reglas de adquisición (recordatorio vinculante)

Antes de incorporar cualquier fuente nueva: (1) qué supuesto/RQ prueba,
(2) procedencia, (3) licencia, (4) fecha/versión de acceso, (5) naturaleza de
evidencia, (6) limitaciones — contrato ya fijado en `docs/DATA_SOURCES.md` §1.
No se scrapea silenciosamente. No se descargan datasets masivos. `data/raw/`
permanece inmutable; los derivados van a `data/interim/`/`data/processed/` vía
script trazable.

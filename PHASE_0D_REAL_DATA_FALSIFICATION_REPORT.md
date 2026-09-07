# PHASE 0D REAL DATA FALSIFICATION REPORT — FIRSTLOOK-MAD

> **Fase:** 0D · **Fecha:** 2026-08-31  
> **Gate:** `MADRID REAL DATA MVP — FAIL (BLOCKED: EXECUTION ENVIRONMENT EGRESS)`  
> **Señal estratégica:** `INSUFFICIENT EVIDENCE`  
> **Uso:** `RESEARCH / SIMULATION PROTOTYPE ONLY`

## 1. Executive verdict

Phase 0D estaba autorizada por el propietario del proyecto (2026-08-31) como
falsación adversarial acotada con datos reales de Madrid, según
`docs/PHASE_0D_PROTOCOL.md`. La adquisición acotada (0D.1) se intentó de
inmediato tras el pre-registro, contra las 7 fuentes ya validadas como
accesibles en Phase 0B más 7 extractos adicionales pequeños y específicos
priorizados por A-01–A-02. **Las 7 fuentes que fueron accesibles en 0B (7/7,
2026-08-26) fallaron el 100% de las veces en este entorno de ejecución
(2026-08-31), con el mismo error de proxy —`Tunnel connection failed: 403
Forbidden`— antes de alcanzar el servidor de destino.** Esto es una política
de salida de red del entorno de ejecución de esta sesión, no una evidencia
sobre Madrid, sobre las fuentes registradas ni sobre los supuestos A-01–A-04.

**No se obtuvo ningún byte de dato externo nuevo.** En consecuencia:

- Ningún supuesto pasa de `TESTING` a `SUPPORTED` o `REFUTED`.
- Ninguna de las 5 preguntas prioritarias del protocolo pudo evaluarse contra
  evidencia real; todas quedan `BASELINE_NOT_OBSERVABLE` /
  `WEATHER_EVIDENCE_NOT_OBSERVABLE` / equivalentes, tal como fija de antemano
  la regla de missing-data del protocolo (§4–5).
- El gate de fase es `FAIL`, y se clasifica explícitamente como
  **`BLOCKED: EXECUTION ENVIRONMENT EGRESS`**, distinto de un `FAIL` por
  evidencia científica desfavorable. La distinción importa: este resultado no
  dice nada sobre si Madrid tiene o no datos reales disponibles — solo dice
  que este entorno de ejecución concreto no pudo alcanzarlos hoy.
- La señal estratégica es `INSUFFICIENT EVIDENCE`, no `KILL` ni `BUILD
  CANDIDATE`: Phase 0C.1 sigue siendo la última lectura científica válida
  (`CONDITION_DEPENDENT_STRONG`, sin soporte para `BUILD`), y Phase 0D no la
  cambia porque no pudo producir evidencia con la que confrontarla.

Este resultado se preserva como negativo, tal como exige el protocolo: no se
fuerza una lectura optimista, no se inventa un workaround de red y no se trata
la ausencia de datos como soporte implícito de ningún supuesto.

## 2. Evidence contract

- Protocolo pre-registrado **antes** de cualquier intento de adquisición:
  [`docs/PHASE_0D_PROTOCOL.md`](docs/PHASE_0D_PROTOCOL.md) (commit previo al
  de adquisición).
- Configuración de adquisición reproducible:
  [`data/phase0d_source_probes.json`](data/phase0d_source_probes.json).
- Script reproducible, sin scraping masivo, sin credenciales fabricadas:
  [`scripts/acquire_phase0d_sources.py`](scripts/acquire_phase0d_sources.py).
- Log de resultado, regenerable con `uv run python
  scripts/acquire_phase0d_sources.py`:
  [`outputs/reports/phase0d_acquisition_log.json`](outputs/reports/phase0d_acquisition_log.json).
- Reintento del probe de 0B (mismo script, mismas 7 URLs, entorno de 0D):
  0/7 accesibles hoy vs 7/7 en 2026-08-26. Diferencia registrada en
  `data/datasets_manifest.json` → `phase0d_reattempt`.
- Nula generación de datos `REAL` nuevos; nula escritura en `data/raw/`.
- Todo output de esta fase distingue explícitamente `REAL` / `DERIVED` /
  `ASSUMED` / `SYNTHETIC` — ver §7.

## 3. What passed

- El protocolo se pre-registró íntegramente antes de ver ningún resultado
  (cumple el principio anti-sesgo de `docs/VALIDATION_PLAN.md` §1).
- La infraestructura de adquisición es reproducible y honesta: cada intento
  fallido se clasifica (`NETWORK_EGRESS_BLOCKED` / `HTTP_ERROR` /
  `OTHER_ERROR`) y ningún resultado no-`ACQUIRED` puede etiquetarse `REAL` —
  esto está garantizado por código y cubierto por tests
  (`tests/test_phase0d_acquisition.py`), no solo por convención documental.
- El bloqueador se diagnosticó con evidencia técnica directa y trazable
  (mensaje de error del proxy, `curl` de control con código HTTP 403 en el
  túnel `CONNECT`, ver §5), no se asumió sin verificar.
- La suite completa de calidad del repositorio permanece verde: `pytest`,
  `ruff check`, `ruff format --check`, `mypy --strict` (ver §9).

## 4. What failed

- Ninguna de las 5 preguntas de prioridad (A-01, A-04, A-03, A-02, comparador)
  pudo contrastarse con datos reales nuevos.
- No se pudo ejecutar 0D.2 (normalización) porque no hay datos reales que
  normalizar.
- No se pudo ejecutar una versión con datos reales de 0D.3 (tests
  adversariales) más allá de las preguntas de razonamiento en §8, que no
  sustituyen evidencia.
- No se pudo ejecutar 0D.4 (sensibilidad) sobre datos reales; sigue existiendo
  la sensibilidad ya documentada en 0C.1 sobre datos sintéticos.
- El comparador cámara/UAS permanece exactamente donde estaba: sin las
  dimensiones LOS/humo/FOV/calidad/coste, ninguna fuente nueva se intentó
  siquiera adquirir para esas dimensiones porque no hay fuente registrada que
  las cubra (confirmado ya en 0B, `DATA_FEASIBILITY_REPORT.md` §16).

## 5. El bloqueador — diagnóstico técnico

Este entorno de ejecución enruta todo el tráfico HTTPS saliente a través de un
proxy de agente (`HTTPS_PROXY`) hacia un proxy de política de organización.
Los dominios de infraestructura de desarrollo (`pypi.org`, `github.com`,
`registry.npmjs.org`, etc.) están permitidos explícitamente
(`noProxy`/allowlist). **Ningún dominio de datos oficiales de Madrid
registrado en el proyecto está en esa lista de permitidos**:

| Dominio | Resultado |
|---|---|
| `servais.enaire.es` (ENAIRE UAS/NOTAM) | `403 Forbidden` en el túnel `CONNECT`, antes del servidor |
| `opendata.aemet.es` | ídem |
| `maps.effis.emergency.copernicus.eu` | ídem |
| `api-features.idee.es` (IGN) | ídem |
| `overpass-api.de` (OSM) | ídem |
| `datos.madrid.es` | ídem |
| `servicio.mapa.gob.es` (EGIF) | ídem |
| `aip.enaire.es`, `www.enaire.es`, `en.wikipedia.org` (control, dominios no registrados) | ídem — confirma que el bloqueo es general, no específico de estas 7 fuentes |

Se verificó con dos herramientas independientes (`WebFetch` y `curl` directo
por `Bash`) y el resultado es idéntico: `curl` reporta explícitamente
`CONNECT tunnel failed, response 403` y el propio proxy documenta esta clase
de fallo como *"the destination host is not allowed by your organization's
egress policy for this session"*, con instrucción explícita de **no
reintentar ni rodear la política**. No se intentó ningún workaround (mirrors,
túneles alternativos, credenciales de terceros).

**Esto es, en sí mismo, el hallazgo dominante de Phase 0D**: la fase no falló
por falta de datos públicos — Phase 0B ya demostró 7/7 fuentes accesibles
técnicamente — sino porque el entorno de ejecución de esta sesión de Claude
Code no tiene permitida la salida de red hacia ningún dominio de datos
oficiales de Madrid/España relevante para el proyecto.

## 6. Missing evidence

Todo lo que Phase 0D se proponía adquirir permanece ausente:

- `NO_PUBLIC_TTFRP_BASELINE` (A-01): sin cambios; EGIF no se pudo consultar en
  esta sesión.
- Meteo real de días de fuego (A-04): sin cambios; AEMET/ERA5-Land no se
  pudieron consultar.
- Geometría real de Madrid (A-03): sin cambios; ENAIRE/IGN no se pudieron
  consultar.
- Sitios candidatos reales verificables (A-02): sin cambios; el directorio
  regional, `datos.madrid.es` y OSM/Overpass no se pudieron consultar.
- Evidencia de comparador cámara/UAS: sin cambios; ninguna fuente nueva
  identificada la cubre, y las ya registradas tampoco se pudieron consultar.

## 7. Evidence classification (obligatoria, ningún campo se difumina)

| Elemento de esta fase | Naturaleza |
|---|---|
| Log de intentos de adquisición (`outputs/reports/phase0d_acquisition_log.json`) | `REAL` — observación directa del comportamiento del entorno de ejecución hoy |
| Clasificación de errores de red (`NETWORK_EGRESS_BLOCKED`) | `DERIVED` — calculada reproduciblemente del log anterior |
| Cualquier cifra de TTFRP, meteo, geometría o sitios de Madrid | **No existe ninguna en esta fase** — no se genera, no se asume, no se simula |
| Supuestos A-01 a A-04 | siguen siendo exactamente los mismos `ASSUMED`/`TESTING` de 0C.1; Phase 0D no los tocó |
| Datos sintéticos de 0C/0C.1 | `SYNTHETIC`, sin cambios, no reutilizados como si fueran reales |

No hay ningún caso en este informe donde un campo `ASSUMED` o `SYNTHETIC`
entre en un pipeline con datos `REAL` y se etiquete implícitamente `REAL`: no
hubo datos `REAL` de Madrid que mezclar.

## 8. Adversarial / red-team review (§9 brief del propietario)

1. **¿Sugiere alguna evidencia real que `T_travel` es una fracción demasiado
   pequeña de TTFRP?** No se pudo obtener evidencia real. Sin cambios sobre
   0C.1 (`STRONGLY_CONDITION_DEPENDENT`).
2. **¿La meteo real de días de fuego hace la disponibilidad UAS asumida
   sustancialmente menos favorable?** No se pudo obtener evidencia real. La
   regla conservadora de 0C (0% ante visibilidad `UNKNOWN`) sigue siendo una
   regla de diseño, no una medición.
3. **¿La geografía real de Madrid hace la erosión A→F más fuerte, más débil o
   inestimable?** Inestimable en esta sesión — no se pudo sustituir ninguna
   geometría sintética por real.
4. **¿Existen sitios candidatos reales plausibles, o la generación sintética
   ocultaba un supuesto de infraestructura fatal?** No se pudo verificar. Esto
   en sí es relevante: **no podemos descartar** que la generación sintética de
   10 sitios uniformes oculte un problema de infraestructura real — Phase 0D
   no logró ni confirmarlo ni descartarlo.
5. **¿Se vuelve preferible una arquitectura de cámara/torre fija bajo
   evidencia comparable?** Sigue sin poder evaluarse; comparador
   `INCOMPARABLE`, sin cambios.
6. **¿El proyecto sigue haciendo una pregunta que los datos públicos no pueden
   responder?** Distinto: la pregunta de 0B/0C ("¿hay datos públicos
   suficientes?") tenía respuesta parcial afirmativa (`DATA PARTIAL`, 7/7
   accesibles). La pregunta que *este entorno* no puede responder es
   operacional/de infraestructura de ejecución, no de existencia de datos.
7. **¿Qué evidencia nueva cambiaría más la conclusión de 0D?** Volver a
   ejecutar exactamente el mismo protocolo y el mismo script
   (`scripts/acquire_phase0d_sources.py`) desde un entorno con salida de red
   permitida hacia los 7+ dominios listados en §5 — o, alternativamente, que
   un humano descargue manualmente los extractos pequeños ya especificados en
   `data/phase0d_source_probes.json` y los deposite en `data/raw/` con su
   procedencia, para que el código de normalización (aún por escribir, porque
   no hay datos que normalizar) los procese.
8. **¿Estamos convirtiendo ausencia de evidencia en evidencia de
   viabilidad?** Explícitamente no: el gate es `FAIL`, no `PASS`; la señal
   estratégica es `INSUFFICIENT EVIDENCE`, no `BUILD CANDIDATE`; y ningún
   supuesto cambió de estado. Este mismo informe es la salvaguarda contra esa
   conversión.

## 9. Engineering quality (§12 brief)

- `uv run pytest -q` → 34 passed (25 previos + 9 nuevos de Phase 0D).
- `uv run ruff check .` → All checks passed.
- `uv run ruff format --check .` → todos los archivos formateados.
- `uv run mypy` (estricto) → sin errores en 12 archivos fuente.
- Ningún test ni regla existente se debilitó para que Phase 0D "pasara".

## 10. Synthetic vs real comparison

| Conclusión de 0C/0C.1 | Estado tras 0D |
|---|---|
| A-01 `STRONGLY_CONDITION_DEPENDENT` | Sin cambios — no contrastada con datos reales |
| A-03 erosión A→F 45,20–72,75 pp (25 seeds sintéticas) | Sin cambios — no contrastada con geometría real |
| A-04 meteo fuera de envelope → 0% cobertura (regla conservadora) | Sin cambios — no contrastada con meteo real |
| Comparador cámara/UAS `INCOMPARABLE` | Sin cambios — sigue `INCOMPARABLE` |
| `NO SUPPORT FOR BUILD` | Sin cambios — sigue sin soporte para `BUILD` |

Ninguna conclusión de 0C.1 sobrevivió, se debilitó, desapareció o se volvió
inestable **por evidencia** en 0D — todas simplemente **permanecen
intocadas**, porque 0D no logró generar evidencia con la que confrontarlas.

## 11. Comparator

**`INCOMPARABLE`** — sin cambios respecto a 0C.1. Justificación: cero
evidencia nueva se obtuvo para LOS, oclusión por humo, campo de visión,
capacidad de reconocimiento, equivalencia de imagen, disponibilidad de sitio
o coste — las dimensiones que ya impedían la comparación en 0C.1.

## 12. Risks / scientific limitations

- El bloqueador es específico de **este entorno de ejecución concreto**; no
  se puede generalizar a "los datos de Madrid no son accesibles" — eso sería
  contradicho directamente por Phase 0B (7/7 accesible el 2026-08-26).
- No se validó si el bloqueo es permanente para futuras sesiones de este
  mismo tipo de entorno o específico de esta ejecución; requiere verificación
  humana en un entorno con política de salida distinta.
- El protocolo pre-registrado (§4 de `docs/PHASE_0D_PROTOCOL.md`) no pudo
  ejercitarse contra ningún dato real, por lo que su calidad como
  instrumento de decisión permanece **no probada empíricamente**, solo
  probada lógicamente (tests unitarios sobre la clasificación).
- Ningún hallazgo de esta fase debe citarse como "Madrid no tiene datos
  públicos utilizables" — esa sería una lectura falsa y contraria a la
  evidencia de 0B.

## 13. Phase 0D gate

**`MADRID REAL DATA MVP — FAIL`**, calificado explícitamente como
**`BLOCKED: EXECUTION ENVIRONMENT EGRESS`** (no `FAIL` por evidencia
científica desfavorable). Interpretación estricta de "MVP operativo mínimo" en
`docs/VALIDATION_PLAN.md`: el MVP de investigación reproducible no pudo
producirse porque su insumo — datos reales — no fue alcanzable desde este
entorno.

## 14. Strategic signal

**`INSUFFICIENT EVIDENCE`** — no `BUILD CANDIDATE`, no `REPOSITION SIGNAL`, no
`KILL SIGNAL`. La última lectura científica válida sigue siendo la de 0C.1:
`CONDITION_DEPENDENT_STRONG`, sin soporte para `BUILD`. Esta señal estratégica
**no** sustituye la decisión formal `BUILD/REPOSITION/KILL` de Phase 0F.

## 15. Acción humana mínima requerida

Para reintentar Phase 0D con posibilidad real de éxito, se necesita **una** de
las siguientes acciones humanas (no técnicas de este agente):

1. Ejecutar `scripts/acquire_phase0d_sources.py` (y, si tiene éxito, extender
   la adquisición según `docs/PHASE_0D_PROTOCOL.md`) desde un entorno cuya
   política de salida de red permita el acceso a: `servais.enaire.es`,
   `opendata.aemet.es`, `maps.effis.emergency.copernicus.eu`,
   `api-features.idee.es`, `overpass-api.de`, `datos.madrid.es`,
   `servicio.mapa.gob.es`, y (si se retoma A-04 con reanálisis) `cds.climate.
   copernicus.eu`.
2. Alternativamente, un humano descarga manualmente los extractos pequeños ya
   especificados (mismas URLs, mismo alcance acotado) y los deposita en
   `data/raw/<fuente>/` con procedencia completa; entonces el trabajo de
   normalización (0D.2, aún sin escribir porque no hay insumo) puede
   ejecutarse sobre datos reales genuinos.
3. Para AEMET específicamente, además del acceso de red, se requiere una
   clave de API gratuita registrada por un humano (ya identificado como
   bloqueador en Phase 0B; sigue sin resolverse).
4. Para el histórico completo de EFFIS, sigue pendiente la solicitud humana ya
   identificada en Phase 0B (`BLOCKED`, sin cambios).

Ninguna de estas acciones fue ni debe ser realizada por este agente sin
autorización e insumo humano explícito (credenciales, entorno, o archivos).

## 16. Adenda — reintento local (2026-09-02) y endurecimiento 0D.1

> Esta adenda documenta un evento posterior al gate original de esta fase
> (§13, fechado 2026-08-31). No reescribe ni invalida ese gate: describe lo
> que ocurrió después y qué se corrigió. Ver desviación metodológica
> completa en `docs/PHASE_0D_PROTOCOL.md` §7.1–§7.2.

### 16.1 Qué demuestra el reintento local — y qué no

El propietario del proyecto ejecutó `scripts/acquire_phase0d_sources.py`
localmente en su máquina Windows el 2026-09-02 (CPython 3.14.5), sin ningún
cambio de código respecto a la versión que produjo el gate `FAIL (BLOCKED:
EXECUTION ENVIRONMENT EGRESS)` de 2026-08-31. Resultado, preservado sin
modificar en
[`outputs/reports/phase0d_acquisition_log_local_2026-09-02.json`](outputs/reports/phase0d_acquisition_log_local_2026-09-02.json):
34 tests previos en verde, 7 probes intentados, 5 clasificados `ACQUIRED`
por la lógica *pre-endurecimiento*, 0 `NETWORK_EGRESS_BLOCKED`, 2 otros
fallos.

**Esto demuestra únicamente** que, desde ese entorno local concreto en esa
fecha concreta, el bloqueador de salida de red de §5 no estaba presente.
**No demuestra**: que los datos reales de Madrid apoyen ningún supuesto
A-01–A-04; que el acceso de red esté "resuelto" de forma permanente o para
cualquier otro entorno; ni que Phase 0D haya avanzado de 0D.1
(procedencia/adquisición) a 0D.2 (normalización) — no se ha normalizado
ningún byte todavía.

### 16.2 El defecto de clasificación descubierto y su corrección

De los 7 probes, el de AEMET (`aemet_madrid_station_inventory`) devolvió
HTTP 200 con **0 bytes** de cuerpo. La implementación anterior lo
clasificaba como `ACQUIRED` con `nature_if_used: REAL` — un HTTP exitoso
vacío se contaba como evidencia adquirida. Esto es un defecto de
procedencia/ingeniería, detectado *después* de ver el resultado, y se
registra como desviación metodológica fechada en
`docs/PHASE_0D_PROTOCOL.md` §7.1: **no** es un ajuste de threshold
científico, **no** cambia ningún supuesto de estado, y **no** es un intento
de rescatar la hipótesis del proyecto — de hecho hace la clasificación más
estricta, no más favorable.

Corrección aplicada en `scripts/acquire_phase0d_sources.py`:

- Nuevo resultado explícito `EMPTY_RESPONSE` (HTTP exitoso, 0 bytes) —
  distinto de `ACQUIRED`, y con `nature_if_used: null`, igual que cualquier
  otro no-`ACQUIRED`.
- `ACQUIRED` ahora requiere HTTP exitoso **y** cuerpo no vacío. Solo en ese
  caso se calcula SHA-256 y se persiste el byte exacto recibido.
- Cubierto por tests explícitos en `tests/test_phase0d_acquisition.py`
  (HTTP 200 + cuerpo vacío → `EMPTY_RESPONSE`, nunca `ACQUIRED`).

El log local del 2026-09-02 **se preserva sin modificar** precisamente
porque es la evidencia de que este defecto existió y de cuándo se corrigió
— no se reescribe el pasado.

### 16.3 Contrato de evidencia cruda (raw evidence)

Antes de este endurecimiento, el script leía el cuerpo de la respuesta en
memoria y lo descartaba: no había ningún artefacto persistido más allá del
log de intentos. Ahora, y solo para probes `ACQUIRED` (HTTP exitoso, cuerpo
no vacío), `persist_raw_response()` guarda el byte exacto recibido, sin
transformar ni normalizar, bajo una ruta determinista y específica de la
fuente:

```
data/raw/phase0d/<probe_id>/<YYYYMMDD>.raw
data/raw/phase0d/<probe_id>/<YYYYMMDD>.raw.provenance.json
```

`data/raw/` permanece **inmutable** (regla vinculante de
`docs/DATA_SOURCES.md` §3): si la ruta determinista del día ya existe con
contenido *distinto* del recién recibido, el archivo existente nunca se
sobrescribe — se usa una ruta determinista específica de esa ejecución
(derivada de su propio timestamp) en su lugar; si incluso esa ruta de
respaldo ya tuviera contenido distinto, la función falla explícitamente en
vez de arriesgar la evidencia. Un reintento el mismo día con bytes
idénticos es idempotente: no reescribe el archivo ni su provenance
original.

Cada archivo persistido tiene una entrada de provenance con, como mínimo:
`probe_id`, `source_url`, `acquired_at_utc`, `http_status`, `content_type`,
`byte_count`, `sha256`, `local_raw_path`, `truncated`, `evidence_nature:
"REAL"` y `config_consulted_at`. Un `truncated: true` identifica
explícitamente una respuesta acotada por `max_bytes`, para que nunca se
confunda con un dataset completo. No se ha ejecutado ninguna adquisición
real bajo este contrato todavía en esta tarea — ver §16.6.

### 16.4 AEMET permanece consciente de credenciales

AEMET OpenData requiere una clave de API gratuita. No se ha inventado, ni
hard-codeado, ni committeado ninguna clave. El probe AEMET declara ahora
`credential_env_var: "AEMET_API_KEY"` en `data/phase0d_source_probes.json`:
si esa variable de entorno no está definida, el probe se clasifica
honestamente `CREDENTIAL_REQUIRED` **sin intentar la petición de red**, en
vez de arriesgarse a que una respuesta sin autenticar (como el HTTP 200/0
bytes observado) se confunda con datos reales. Si la clave está presente,
se envía únicamente como cabecera HTTP (`api_key`), nunca como parámetro de
la URL — de modo que nunca aparece en la URL de provenance, en los logs ni
en los resultados serializados. Cubierto por tests explícitos, incluido uno
que verifica que el valor de la clave no aparece en el resultado
serializado. No se ha solicitado ni se solicitará una clave AEMET al
propietario como parte de esta tarea.

### 16.5 EFFIS, Overpass/TLS y EGIF — sin cambios de política

- **EFFIS**: el HTTP 502 observado se preserva como fallo de
  fuente/petición (`HTTP_ERROR`). No se reintenta automáticamente hasta
  obtener éxito, ni se sustituye silenciosamente por otro endpoint EFFIS.
- **OSM Overpass**: el fallo de verificación TLS/certificado observado
  (`certificate has expired`) se preserva como `OTHER_ERROR`, nunca como
  `ACQUIRED` ni como evidencia `REAL`. No se ha desactivado la verificación
  SSL, no se ha añadido `verify=False` ni `-k`, no se ha manipulado la
  cadena de certificados, y no se ha sustituido silenciosamente por un
  mirror alternativo — cambiar de endpoint alteraría el alcance de
  adquisición pre-registrado y requiere revisión/autorización humana
  separada.
- **EGIF**: sin cambios de endpoint ni de scope.

### 16.6 Qué NO se ha hecho en esta tarea de endurecimiento

- No se ha ejecutado una nueva adquisición en vivo contra las fuentes reales
  desde este endurecimiento: los tests nuevos usan respuestas simuladas
  (`opener` inyectado), no tráfico de red real. `data/raw/phase0d/`
  permanece vacío hasta que el propietario ejecute la siguiente adquisición
  acotada.
- No se ha ejecutado 0D.2 (normalización), 0D.3 (tests adversariales con
  datos reales), 0D.4 (sensibilidad) ni 0D.5 (red-team ampliado).
- Ningún supuesto A-01–A-04 cambió de estado. La lectura científica válida
  sigue siendo la de 0C.1: `CONDITION_DEPENDENT_STRONG`, sin soporte para
  `BUILD`.
- No se ha entrado en Phase 0E.

### 16.7 Python 3.14.5 — nota de entorno

La ejecución local usó CPython 3.14.5. `pyproject.toml` declara
`requires-python = ">=3.12"` (sin cota superior) y Ruff/mypy targetean
semántica `py312`; no se identificó ninguna incompatibilidad verificada del
código de este proyecto bajo 3.14.5 durante este endurecimiento, por lo que
la configuración del proyecto **no se modifica** por esta razón. Para
máxima reproducibilidad frente al target declarado, se recomienda —sin ser
obligatorio— que una futura repetición se ejecute también bajo Python 3.12.

## 17. Adenda — 0D.1D: cierre de adquisición acotada (2026-09-07)

> Esta adenda documenta la adquisición local de 2026-09-07 (Windows, Python
> 3.12.10) bajo el script endurecido y sus derivados. **No** reabre ni mejora
> el gate original de §13 (`FAIL, BLOCKED: EXECUTION ENVIRONMENT EGRESS`,
> 2026-08-31): ese sigue siendo la última lectura formal de fase. Aquí se
> registra qué se adquirió después, con qué naturaleza, y qué explícitamente
> **no** se concluye. Ningún supuesto A-01–A-04 pasa a `SUPPORTED`/`REFUTED`;
> no se ejecuta 0D.2.

### 17.1 Evidencia real acotada aceptada (verificada por contenido)

Cada artefacto se persistió inmutable en `data/raw/phase0d/` (gitignored) con
sidecar SHA-256, y su copia payload-free vive en
`outputs/provenance/phase0d/` (committable, sin bytes crudos, sin
credenciales). Integridad reverificada esta sesión: 16 entradas de ledger,
0 discrepancias de hash, 0 marcadores de secreto, 0 campos de payload.

| Fuente | Supuesto | Clasificación de artefacto | SHA-256 (prefijo) | Naturaleza |
|---|---|---|---|---|
| AEMET inventario de estaciones (2º salto, 167.915 B, 926 estaciones, 23 Madrid) | A-04 | `REAL_SOURCE_DATA` | `fe21a467…` | `REAL` |
| Madrid Open Data — parques de bomberos (16.273 B) | A-02 | `REAL_SOURCE_DATA` | `5c395787…` | `REAL` |
| ENAIRE geozonas UAS (bbox acotado, 268.402 B) | A-03 | `REAL_BOUNDED_SAMPLE` | `36f6e58e…` | `REAL` |
| IGN MDT05 `GetCapabilities`/`DescribeCoverage` | A-03 | `REAL_METADATA` | — | `REAL` |
| **IGN MDT05 `GetCoverage` muestra Madrid (1.256 B GeoTIFF, 20×20, 5 m)** | A-03 | `REAL_SOURCE_DATA` | `3d7fe2a1…` | `REAL` |
| EGIF interfaz de búsqueda pública | A-01 | `REAL_METADATA` | — | `REAL` |

**El GetCoverage MDT05** (nuevo en 0D.1D) prueba de forma reproducible la
cadena `metadatos → payload real de terreno acotado`: petición única, sin
paginación ni recorrido de tiles, ventana fija ~100 m × 100 m centrada en
Madrid, TLS verificado, formato `image/tiff`. El cuerpo es un GeoTIFF genuino
(ETRS89/UTM 30N, posts de 5 m, elevaciones 648–654 m, coherentes con el centro
de Madrid a ~650 m). Ver desviación metodológica fechada en
`docs/PHASE_0D_PROTOCOL.md` §7.3.

### 17.2 Qué NO demuestra (anti-overclaim, vinculante)

- `inventario AEMET ≠ observaciones meteorológicas históricas` — A-04 no tiene
  aún la meteo de días de fuego que su test requiere.
- `muestra MDT05 ≠ terreno completo de Madrid` — es un recorte de 100 m, no un
  MDT de la ciudad.
- `muestra ENAIRE ≠ capa completa de geozonas de Madrid`.
- `interfaz EGIF ≠ baseline TTFRP observable` — sigue `BASELINE_NOT_OBSERVABLE`.
- Ninguna cifra de 0C.1 se contrastó con esta evidencia: no se ha normalizado
  ni un byte (0D.2 no ejecutado). La lectura científica válida sigue siendo
  `CONDITION_DEPENDENT_STRONG`, sin soporte para `BUILD`.

### 17.3 Estado de insumo por supuesto (nivel de adquisición, no de decisión)

| Supuesto | Insumo real | Justificación |
|---|---|---|
| A-01 | `PARTIAL_REAL_INPUT` | Solo interfaz EGIF (metadatos); sin baseline TTFRP. |
| A-02 | `USABLE_REAL_INPUT` | Parques de bomberos reales, trazables (`REAL_SOURCE_DATA`). |
| A-03 | `PARTIAL_REAL_INPUT` | Muestras reales acotadas (ENAIRE bbox + MDT05 GetCoverage) + metadatos IGN; no capas completas. |
| A-04 | `PARTIAL_REAL_INPUT` | Inventario de estaciones real, pero no las observaciones meteorológicas del test. |

### 17.4 Gate de Phase 0D.1

**`0D.1 REAL INPUT AVAILABLE`.** La regla de adquisición pre-registrada para
0D.1 declara `REAL INPUT AVAILABLE` cuando **al menos un** supuesto prioritario
dispone de insumo real genuino, verificado por integridad y semánticamente
utilizable. Esa condición **se cumple** con A-02 (parques de bomberos reales,
`REAL_SOURCE_DATA`, `USABLE_REAL_INPUT`). El gate se evalúa por esa regla, no
por la completitud de todos los supuestos; degradarlo a `PARTIAL REAL INPUT`
por el mero hecho de que A-01/A-03/A-04 sigan incompletos sería un cambio de
threshold **posterior** a observar los resultados, y no se hace.

**Limitación explícita del gate (por supuesto, nivel de insumo):**

- A-01 = `PARTIAL_REAL_INPUT` (interfaz EGIF; sin baseline TTFRP observable).
- A-02 = `USABLE_REAL_INPUT` (parques de bomberos reales y trazables).
- A-03 = `PARTIAL_REAL_INPUT` (muestras acotadas ENAIRE + MDT05 GetCoverage +
  metadatos IGN; no capas completas).
- A-04 = `PARTIAL_REAL_INPUT` (inventario de estaciones AEMET real; no las
  observaciones meteorológicas del test).

Todo se adquirió con TLS verificado, procedencia SHA-256 y evidencia cruda
inmutable gitignored; **no** es `STILL BLOCKED` (la red funcionó y se
persistieron bytes reales verificados por contenido).

**`0D.1 REAL INPUT AVAILABLE` NO significa** —y este límite es vinculante—
ninguna de las siguientes: Phase 0D **PASS científico**, `SUPPORTED`,
`MADRID VALIDATED`, `BUILD`, ni `SAFE_TO_FLY`. Es un subgate de *adquisición*:
**no** sustituye el gate científico de §13 (que sigue
`FAIL, BLOCKED: EXECUTION ENVIRONMENT EGRESS`, 2026-08-31, como última lectura
formal de fase), **no** cambia la lectura `CONDITION_DEPENDENT_STRONG` de 0C.1,
y **no** habilita la decisión `BUILD/REPOSITION/KILL` de 0F. La interpretación
científica a nivel de proyecto permanece **no resuelta / insuficiente para
`BUILD`**.

### 17.5 Calidad de ingeniería (0D.1D, Python 3.12.10)

- `pytest` → 72 passed.
- `ruff check .` → All checks passed.
- `ruff format --check .` → 50 files already formatted.
- `mypy` (estricto) → sin errores en 18 archivos fuente.
- Ningún test ni regla existente se debilitó. `data/raw/` permanece inmutable
  y gitignored; ninguna clave, cookie, token ni valor anti-forgery aparece en
  los artefactos de procedencia committables.

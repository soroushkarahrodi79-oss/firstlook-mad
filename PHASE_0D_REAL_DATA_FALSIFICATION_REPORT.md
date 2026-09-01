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

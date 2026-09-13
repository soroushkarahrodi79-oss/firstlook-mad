# ASSUMPTIONS — FIRSTLOOK-MAD

> **Fase:** 0D — `FAIL (BLOCKED: EXECUTION ENVIRONMENT EGRESS)` · **v0.4.0**
>
> Registro explícito de supuestos. Cada supuesto es **falsable** y tiene un plan
> para verificarlo o refutarlo. Un supuesto **no** es un hecho: se marca como tal
> en todo output derivado (`ASSUMED` / `SIMULATED`).

Identificador: `A-nn`. Estado: `OPEN` (sin verificar) / `TESTING` / `SUPPORTED` /
`REFUTED`.

| ID | Supuesto | Riesgo si es falso | Cómo se prueba | Estado |
|---|---|---|---|---|
| A-01 | El tránsito UAS (`T_travel`) es una fracción **material** del TTFRP | Si `T_alert+T_verif` domina, la red de docks aporta poco → tesis débil | Test del cuello de botella con rangos plausibles (0C) | TESTING |
| A-02 | Existe infraestructura pública reutilizable como sitio candidato | Sin sitios, no hay red | Inventario verificable en 0B | TESTING |
| A-03 | Un buffer geométrico aproxima *pobremente* la cobertura operacional (por eso modelamos A→F) | Sobreestimar cobertura | Comparar Modelo A vs D/E/F (0C/0D) | TESTING |
| A-04 | La meteo de días de fuego no anula sistemáticamente la viabilidad de vuelo | El valor se evapora en los días que importan | Test de erosión meteorológica (0C con datos AEMET/EFFIS en 0D) | TESTING |
| A-05 | El riesgo de incendio es representable por capas separadas antes que por un score compuesto | Índice arbitrario no defendible | Sensitivity analysis sobre pesos (0C/0D) | OPEN |
| A-06 | Los perfiles UAS de referencia son plausibles como *rangos*, no como rendimiento garantizado | Cobertura irreal | Perfiles conservador/optimista con incertidumbre | TESTING |
| A-07 | Existe (o puede construirse) un baseline defendible del desempeño actual | Sin baseline, RQ4 no responde | Investigación de baseline (0E) | TESTING |
| A-08 | La coordinación con aeronaves tripuladas puede modelarse como restricción sin datos operacionales reales | Deconflicción domina y no se captura | Modelado conservador + red-team (0C+) | TESTING |
| A-09 | Un CRS proyectado adecuado para Madrid da errores métricos aceptables | Distancias/tiempos sesgados | Tests de CRS y validación geométrica (0C) | TESTING |
| A-10 | La localización del incidente tiene incertidumbre acotada (`location_uncertainty_m`) | "First look" no fiable | Escenarios con incertidumbre variable (0C) | OPEN |

## Evidencia incorporada en 0B

- **A-01:** debilitado. No hay clocks públicos extremo a extremo y no se ha
  demostrado que `T_travel` domine.
- **A-02:** hay candidatos utilizables en simulación, pero no evidencia de
  permiso, aptitud ni disponibilidad para docks.
- **A-04:** AEMET/ERA5-Land permiten diseñar sensibilidad; faltan visibilidad
  histórica local y un envelope UAS validado.
- **A-07:** EGIF soporta un baseline parcial de primeras llegadas, no TTFRP.
- **A-08:** geozonas y NOTAM son representables, pero la coordinación operacional
  no es pública. Ver `DATA_FEASIBILITY_REPORT.md`.

## Evidencia incorporada en 0C

- **A-01:** `CONDITION_DEPENDENT`. La cuota mediana del tránsito cambia de 67,77%
  a 20,82% al variar solo los tiempos no-vuelo asumidos.
- **A-03:** el experimento reduce la cobertura ponderada sintética de 55,35% en A
  a 10,15% en F. Sigue `TESTING` porque no usa geometría real.
- **A-04:** viento fuera del envelope y visibilidad desconocida producen 0% en el
  gate sintético conservador. No se conoce su frecuencia real.
- **A-06:** tres envelopes asumidos producen coberturas de 6,57%–13,48%; la
  sensibilidad debilita cualquier claim basado en un perfil único.
- **A-09:** `EPSG:25830` queda fijado y los tests rechazan CRS/coordenadas
  incorrectas, pero faltan transformaciones de datos reales.

Ningún supuesto nuevo pasa a `SUPPORTED` en 0C.

## Evidencia incorporada en 0C.1

- **A-01:** `STRONGLY_CONDITION_DEPENDENT`. El crossover discreto baseline es
  600–720 s; los brackets de 25 seeds abarcan extremos 360–840 s.
- **A-03:** la erosión A→F persiste en 25 seeds (45,20–72,75 pp), pero sigue
  `TESTING` porque toda la geometría es sintética.
- **A-04:** permanece `TESTING`; el 0% ante visibilidad desconocida es una regla
  conservadora del gate UAS, no evidencia de frecuencia real ni penalización de
  cámara.
- **A-06:** permanece `TESTING`; todos los perfiles siguen `ASSUMED`.

Ningún supuesto pasa a `SUPPORTED` en 0C.1.

## Evidencia incorporada en 0D

Phase 0D (2026-08-31) fue autorizada por el propietario del proyecto e
intentó falsación adversarial con datos reales de Madrid siguiendo
`docs/PHASE_0D_PROTOCOL.md`. La adquisición acotada (0D.1) se ejecutó de
inmediato tras el pre-registro contra las 7 fuentes ya validadas como
accesibles en 0B más 7 extractos adicionales pequeños. **Las 7 fuentes
fallaron el 100% de las veces**, bloqueadas por la política de salida de red
del entorno de ejecución de esta sesión (`Tunnel connection failed: 403
Forbidden` en el proxy, antes de alcanzar el servidor de destino — ver
`PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` §5). No se obtuvo ningún byte de
dato externo nuevo.

Por tanto, para A-01 a A-04:

- **A-01:** sin cambios. Permanece `STRONGLY_CONDITION_DEPENDENT` (estado de
  0C.1). No se pudo consultar EGIF; resultado clasificado como
  `BASELINE_NOT_OBSERVABLE` según la regla de missing-data del protocolo
  (nunca se convierte en soporte).
- **A-02:** sin cambios. Permanece `TESTING`. No se pudo consultar el
  directorio regional, `datos.madrid.es` ni OpenStreetMap/Overpass.
- **A-03:** sin cambios. Permanece `TESTING`. No se pudo sustituir ninguna
  geometría sintética por geometría real de Madrid (ENAIRE/IGN
  inalcanzables).
- **A-04:** sin cambios. Permanece `TESTING`. No se pudo consultar
  AEMET/ERA5-Land; resultado clasificado como
  `WEATHER_EVIDENCE_NOT_OBSERVABLE`.

**Ningún supuesto pasa a `SUPPORTED` ni a `REFUTED` en 0D.** La ausencia de
evidencia real no se trata como soporte implícito de ningún supuesto ni como
refutación: es, explícitamente, ausencia de evidencia por un bloqueador de
entorno de ejecución, no un hallazgo sobre Madrid. Ver §15 del informe de 0D
para la acción humana mínima requerida antes de poder reintentar esta
evaluación.

### Adenda 0D.1 — adquisición local acotada (2026-09-07)

El bloqueo de egress de 2026-08-31 (arriba) **sigue siendo válido** como
evidencia histórica de aquel entorno de ejecución; **no** se reescribe. Con
posterioridad, una repetición local (Windows, Python 3.12.10) desde un entorno
con salida de red permitida **sí** adquirió insumo real acotado, verificado por
contenido y con procedencia SHA-256 (evidencia cruda inmutable y gitignored).
Subgate de adquisición: **`0D.1 REAL INPUT AVAILABLE`** (satisfecho por A-02).
A nivel de *insumo* (no de decisión científica):

- **A-01:** `PARTIAL_REAL_INPUT` — interfaz de búsqueda EGIF real; sigue sin
  baseline TTFRP observable (`BASELINE_NOT_OBSERVABLE`).
- **A-02:** `USABLE_REAL_INPUT` — parques de bomberos reales de Madrid Open
  Data, para *existencia de activos* únicamente.
- **A-03:** `PARTIAL_REAL_INPUT` — muestras reales acotadas (ENAIRE bbox + IGN
  MDT05 `GetCoverage`) y metadatos IGN; no capas/terreno completos.
- **A-04:** `PARTIAL_REAL_INPUT` — inventario de estaciones AEMET real (926
  estaciones, 23 en Madrid); **no** las observaciones meteorológicas del test.

**Ningún supuesto pasa a `SUPPORTED` ni a `REFUTED`.** No se ejecutó 0D.2
(normalización); la lectura científica sigue insuficiente para `BUILD` y no se
autoriza Phase 0E. Ver `PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` §17 y
`docs/PHASE_0D_PROTOCOL.md` §7.3.

## Supuestos que NO hacemos (explícito)

- **No** asumimos que ninguna infraestructura acepte realmente un dock.
- **No** asumimos permisos BVLOS.
- **No** asumimos que INFOMA tiene mala cobertura actual (podría tener excelente
  cobertura — eso sería un resultado válido: KILL/REPOSITION).
- **No** asumimos que el dron llega antes que las alternativas.

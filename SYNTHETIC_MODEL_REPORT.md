# SYNTHETIC MODEL REPORT — FIRSTLOOK-MAD

> **Fase:** 0C · **Fecha:** 2026-08-27  
> **Gate técnico:** `SYNTHETIC MODEL — PASS`  
> **Lectura científica:** `CONDITION_DEPENDENT / EARLY REPOSITION SIGNAL`  
> **Uso:** `RESEARCH / SIMULATION PROTOTYPE ONLY`

## 1. Executive verdict

El modelo sintético es determinista, reproducible y supera su gate técnico. No
respalda una decisión `BUILD`: la materialidad de `T_travel` depende fuertemente
de los componentes no-vuelo; las restricciones A→F reducen mucho la cobertura;
y los escenarios de viento fuera del envelope o visibilidad desconocida la
erosionan a cero por diseño conservador.

La comparación con cámaras fijas produce una **señal de reposicionamiento**, no
una conclusión: bajo los supuestos elegidos, la cámara proxy cubre más riesgo y
entrega antes una imagen, pero no se han modelado línea de visión, humo, calidad
equivalente ni coste. Phase 0D solo estaría justificada como falsación limitada
con datos reales, no como construcción de un MVP operacional.

## 2. Evidence contract

- 180 incidentes y 10 sitios completamente `SYNTHETIC`.
- Seed fija `260827`; CRS analítico `EPSG:25830`.
- Tres perfiles UAS y tres cadenas TTFRP, todos `ASSUMED` y no calibrados.
- Tres escenarios meteorológicos `ASSUMED`.
- Configuración: [`configs/phase0c_synthetic.json`](configs/phase0c_synthetic.json).
- Resultado regenerable:
  [`outputs/reports/phase0c_synthetic_results.json`](outputs/reports/phase0c_synthetic_results.json).
- Ningún resultado es observación de Madrid, especificación de fabricante,
  autorización, coste ni predicción.

## 3. Implemented model

| Modelo | Añade | Salida deliberadamente optimista/incompleta |
|---|---|---|
| A | Distancia euclídea y alcance | Sin TTFRP ni factores operacionales |
| B | Velocidad y cadena TTFRP | Sin relieve, aire, meteo o reserva |
| C | Multiplicador sintético de relieve | Sin restricciones dinámicas |
| D | Geozona, restricción temporal y conflicto tripulado | Sin meteo/operación completa |
| E | Viento, precipitación, visibilidad y temperatura | Sin reserva/availability/comms/frescura |
| F | Reserva, batería, sitio, comunicaciones, confianza y frescura | Sigue siendo un experimento sintético |

El gate conserva todos los checks y usa el primer estado no-`PASS` como causa
primaria. `UNKNOWN`, `RESTRICTED` y `REQUIRES_AUTHORIZATION` nunca producen
`GO_SIMULATION`. No existe `SAFE_TO_FLY`.

## 4. Progressive A→F evidence

Red de 10 sitios, perfil de referencia, cadena no-vuelo balanceada y meteo dentro
del envelope asumido:

| Modelo | Incidentes cubiertos | Cobertura ponderada por riesgo | Mediana TTFRP sintética |
|---|---:|---:|---:|
| A | 101/180 | 55,35% | No aplica |
| B | 101/180 | 55,35% | 1.694 s |
| C | 81/180 | 44,74% | 1.697 s |
| D | 58/180 | 31,07% | 1.712 s |
| E | 58/180 | 31,07% | 1.712 s |
| F | 17/180 | 10,15% | 1.531 s |

La mediana menor de F **no** es una mejora: es sesgo de selección porque solo
sobrevive un subconjunto más cercano. Comparar medianas sin declarar el conjunto
cubierto sería engañoso.

## 5. Bottleneck falsification — A-01

| Cadena asumida | No-vuelo | Mediana de cuota `T_travel` | Casos donde tránsito domina |
|---|---:|---:|---:|
| Baja | 300 s | 67,77% | 88,24% |
| Balanceada | 900 s | 41,21% | 17,65% |
| Alta | 2.400 s | 20,82% | 0,00% |

**Interpretación:** `CONDITION_DEPENDENT`. A-01 no queda soportado. En la misma
geometría, variar componentes no observables cambia la narrativa de “el tránsito
es el cuello de botella”. La siguiente evidencia debe medir esos componentes,
no refinar primero la optimización de docks.

## 6. Profile sensitivity

Modelo F, 10 sitios, cadena balanceada y meteo dentro del envelope de cada perfil:

| Perfil `ASSUMED` | Incidentes cubiertos | Cobertura ponderada | Mediana TTFRP |
|---|---:|---:|---:|
| Conservador | 9/180 | 6,57% | 1.749 s |
| Referencia | 17/180 | 10,15% | 1.531 s |
| Optimista | 23/180 | 13,48% | 1.498 s |

La cobertura cambia materialmente con el envelope inventado. Tampoco debe leerse
la mediana optimista como peor/mejor sin controlar el cambio del conjunto cubierto.

## 7. Weather erosion — A-04

| Escenario | Cobertura ponderada Modelo F | Resultado |
|---|---:|---|
| Dentro del envelope asumido | 10,15% | 17 incidentes simulables |
| Viento fuera del envelope | 0,00% | `NO_GO` |
| Visibilidad desconocida | 0,00% | `UNKNOWN`, nunca GO |

Esto valida el comportamiento conservador del código, no la frecuencia real de
esas condiciones. A-04 permanece `TESTING` y vulnerable.

## 8. Diminishing returns — RQ6

| Sitios | Cobertura ponderada Modelo F | Ganancia vs paso anterior |
|---:|---:|---:|
| 1 | 2,37% | — |
| 2 | 2,37% | 0,00 pp |
| 3 | 3,05% | +0,67 pp |
| 5 | 5,41% | +2,36 pp |
| 10 | 10,15% | +4,74 pp |

No aparece saturación temprana a 2–3 sitios, pero tampoco una cobertura amplia.
La selección greedy se optimiza sobre cobertura geométrica A, no sobre F; por
tanto no demuestra que 10 sitios sean necesarios, suficientes u óptimos.

## 9. Cheaper-alternative falsification

Con 10 ubicaciones y supuestos de cámara de 15 km/240 s:

| Arquitectura | Cobertura ponderada | Mediana sintética |
|---|---:|---:|
| Docks UAS | 10,15% | 1.531 s |
| Cámaras fijas proxy | 31,27% | 360 s |
| Mejor imagen disponible híbrida | 31,27% | 360 s |

Es una señal adversarial útil: la red de docks no debe ser la arquitectura por
defecto. No es una comparación económica ni de equivalencia de imagen; esos
supuestos favorecen a la cámara y están expuestos precisamente para que puedan
ser reemplazados.

## 10. What passed

- Configuración validada, inmutable y con naturaleza de evidencia explícita.
- CRS métrico único; coordenadas degree-like/swapped rechazadas.
- Resultados byte-for-byte reproducibles con la misma seed.
- Modelos A→F comparables y gate first-failure-wins.
- `UNKNOWN`/autorización/restricción bloquean `GO_SIMULATION`.
- Tests de cuello de botella, meteo, perfiles, rendimientos y alternativa híbrida.
- Separación estructural `evidence` / `interpretation` / `decision`.
- 17 tests, Ruff y mypy estricto pasan.

## 11. What failed or weakened

- A-01 no se soporta; depende de tiempos no observados.
- El modelo F conserva poca cobertura en los tres perfiles asumidos.
- La viabilidad desaparece bajo los dos escenarios meteorológicos adversariales.
- La cámara proxy domina con los supuestos actuales.
- No hay evidencia para fijar un threshold de mejora material.

## 12. Missing evidence

- Distribuciones reales de alerta, verificación, preflight, lanzamiento,
  adquisición y primer análisis.
- Envelope UAS validado y frecuencia conjunta de meteo en días de incendio.
- Sitios regionales aptos/disponibles y restricciones temporales históricas.
- Línea de visión, humo, calidad de imagen y costes de cámaras/docks/híbrido.
- Capacidad, colas y múltiples incidentes simultáneos.

## 13. Red-team findings

1. Los incidentes uniformes no representan riesgo espacial de Madrid.
2. El greedy de A puede seleccionar sitios pobres bajo F.
3. Las exclusiones se cuentan por par sitio-incidente, no como causalidad
   operacional por incidente.
4. El subconjunto superviviente hace incomparables algunas medianas A→F.
5. Los perfiles son envelopes construidos, no rangos validados.
6. El proxy cámara omite sus principales modos de fallo y coste.
7. Una sola seed prueba determinismo, no robustez estadística.
8. El gate no modela autorización real, coordinación ni aeronavegabilidad.

## 14. Gate review — SYNTHETIC MODEL

**Evidence:** configuración versionada, resultado regenerable, 17 tests y matrices
A→F/perfil/meteo/TTFRP/arquitectura.

**What passed:** el modelo ejecuta, es determinista, conserva provenance semántica
y falla de forma conservadora.

**What failed:** la hipótesis no obtiene soporte; los resultados muestran fuerte
dependencia de supuestos y una alternativa potencialmente dominante.

**Missing evidence:** §12.

**Risks:** convertir porcentajes sintéticos en cifras sobre Madrid; optimizar la
arquitectura antes de observar la cadena TTFRP; confundir `GO_SIMULATION` con
permiso o seguridad.

**Verdict:** `SYNTHETIC MODEL — PASS` como gate técnico. Lectura científica:
`CONDITION_DEPENDENT / EARLY REPOSITION SIGNAL`. Si se autoriza Phase 0D, debe ser
un test real-data mínimo orientado a refutar A-01/A-04 y comparar cámaras/híbrido;
no un MVP operacional ni una expansión de arquitectura.

## 15. Phase 0C.1 Robustness Audit

Phase 0C se conserva como resultado histórico, pero su lectura humana pasa a
**PASS WITH CONDITIONS — ROBUSTNESS AUDIT REQUIRED**. La auditoría usa schema
1.1, 25 seeds ordenadas, tamaños 90/180/360, una ablación leave-one-out, un
comparador por etapas y un barrido agregado de 0–3.600 s en pasos de 120 s. Es
una **robustness and parameter sensitivity audit**, no global sensitivity.

### A. F-model ablation

La medida es el aumento de cobertura al retirar un factor del F completo,
manteniendo incidentes, sitios y demás gates constantes: **marginal synthetic
effect under this configuration**.

| Factor retirado | Cobertura recuperada | Incidentes adicionales |
|---|---:|---:|
| range | +21,71 pp | 41 |
| data freshness | +4,42 pp | 9 |
| reserve | +3,33 pp | 6 |
| manned-aircraft conflict | +1,06 pp | 2 |
| communications | +1,00 pp | 2 |
| incident confidence | +0,86 pp | 4 |
| airspace | +0,71 pp | 1 |
| site availability | +0,31 pp | 1 |
| temporary restrictions | +0,30 pp | 2 |
| UAS availability / battery / weather | 0,00 pp | 0 |

Los efectos se solapan, dependen de interacciones entre gates y **no suman** la
erosión A→F. El resultado corrige la lectura basada en conteos de primer fallo:
en esta configuración, range/reserve domina la recuperación marginal; confidence
y freshness importan, pero no explican por sí solas la caída.

### B. Fair architecture comparator

Los factores se separan en comunes pre-observación (alert processing,
confidence, freshness), específicos UAS (range/reserve, disponibilidad,
batería, meteo, aire, conflictos, comunicaciones, preflight/launch) y específicos
de cámara (radio, disponibilidad y comunicaciones). LOS, humo/oclusión, FOV,
reconocimiento y equivalencia permanecen `UNKNOWN / NOT_MODELLED`.

| Etapa | UAS | Cámara proxy |
|---|---:|---:|
| Raw physical reach (`PHYSICAL_PROXY_ONLY`) | 55,35% | 35,10% |
| Tras gates comunes | 27,63% | 17,63% |
| Tras gates específicos | 10,15% | 13,86% optimista |

El contrato de latencia común incluye alert processing, verification y first
analysis; UAS añade preflight, launch, travel y scene acquisition; cámara añade
su latencia específica y de imagen. No se duplican componentes UAS.

`CAMERA_OPTIMISTIC_NO_LOS_PENALTY` es solo un upper bound. Para
`CAMERA_UNKNOWN_LOS`, el resultado es
`NOT_COMPARABLE_UNDER_MISSING_LOS_EVIDENCE`; UNKNOWN no se convierte en cero.
Por ello el veredicto del comparador es **INCOMPARABLE**. El anterior
`camera 31,27% vs dock 10,15%` no soporta ranking. `best_available_observation_proxy`
solo toma la primera observación entre canales independientes; no representa una
arquitectura híbrida implementada.

### C. Multi-seed robustness

En 25 seeds reproducibles:

| Métrica | min | p10 | mediana | p90 | max |
|---|---:|---:|---:|---:|---:|
| A coverage | 49,21% | 53,50% | 58,72% | 69,00% | 76,35% |
| F coverage | 1,00% | 3,43% | 5,39% | 7,87% | 10,15% |
| Erosión A→F | 45,20 pp | 45,77 pp | 54,06 pp | 61,94 pp | 72,75 pp |
| Cámara optimista | 7,32% | 10,21% | 13,48% | 15,74% | 15,96% |

La erosión sobrevive todas las seeds, pero el 10,15% de F era el máximo, no un
valor central. Los tamaños 90/180/360 dan F = 8,70%/10,15%/7,83%; no invierten
la conclusión. Los sitios permanecen idénticos al cambiar `incident_count`.

### D. A-01 dense sensitivity

El barrido usa el conjunto fijo de supervivientes F y cambia únicamente el total
agregado no-vuelo. En la seed baseline, la mayoría deja de estar dominada por
tránsito entre **600–720 s**. Entre seeds, el extremo inferior del bracket varía
360–720 s y el superior 480–840 s (medianas 600/720 s). A-01 pasa a
`STRONGLY_CONDITION_DEPENDENT`.

No hay interpolación: son intervalos discretos de 120 s. El análisis sufre
survivor bias y describe solo incidentes que ya superaron todos los gates F.

### E. Site-selection bias

El greedy F-aware es determinista y recupera frente a selección A +0,64 pp con
1 sitio, +3,40 pp con 2, +4,71 pp con 3 y +4,74 pp con 5. Con los 10 candidatos,
ambos conjuntos coinciden y la ganancia es 0 pp. Por tanto, la selección A sí
perjudicaba redes pequeñas, pero no explica el 10,15% del conjunto completo.

### F. What changed from original 0C interpretation

- **Sobrevive:** la geometría A exagera cobertura; la erosión A→F es estable y
  A-01 depende estructuralmente del tiempo no-vuelo.
- **Se debilita:** no hay evidencia para afirmar ventaja de cámara o híbrido; el
  comparador original era asimétrico.
- **Corrección anti-dock:** la seed baseline era favorable a F frente a las otras
  seeds y selección A perjudicaba redes pequeñas.
- **Posible sesgo pro-dock:** cámara sigue sin penalización LOS/humo/FOV y sus
  latencias son asumidas; tampoco existe equivalencia observacional o económica.
- **A-04:** permanece `TESTING`; los escenarios adversos solo prueban lógica del
  gate, nunca frecuencia meteorológica real.

## 16. Gate review — Phase 0C.1

### Evidence

Output schema 1.1 reproducible; ablación de 12 switches; comparador en tres
etapas; 25 seeds; barrido A-01 de 31 puntos; selección A/F-aware; tamaños
90/180/360; invariantes automatizados.

### Original interpretation

`CONDITION_DEPENDENT / EARLY REPOSITION SIGNAL`, con 55,35%→10,15% y una cámara
proxy presentada como 31,27% frente a docks.

### Robustness findings

La erosión A→F es robusta a seeds; range/reserve es el principal mecanismo
marginal; el valor F puntual no es estable; F-aware ayuda solo con redes parciales.

### What survived

La necesidad de cuestionar dock-only y medir la cadena no-vuelo antes de diseñar
infraestructura distribuida.

### What weakened

La narrativa de superioridad de cámaras/híbrido y cualquier lectura literal del
10,15% como estimador central.

### Fair comparator result

`INCOMPARABLE`: cámara es un upper bound sin LOS/humo/equivalencia/coste.

### A-01 result

`STRONGLY_CONDITION_DEPENDENT`; crossover baseline 600–720 s y multi-seed
360–840 s en los extremos de los brackets.

### Remaining unknowns

Todos los perfiles UAS y tiempos son `ASSUMED`; incidentes/sitios son
`SYNTHETIC`; LOS, humo, FOV, calidad, coste y datos operacionales siguen ausentes.
Los porcentajes no son cobertura real de Madrid.

### Verdict

`CONDITION_DEPENDENT_STRONG`. `NO SUPPORT FOR BUILD`.

### Phase 0D recommendation

`DO NOT PROCEED YET`: primero revisar el Draft PR #2. Una autorización posterior
debe definir un test real-data limitado y simétrico; esta auditoría no inicia 0D.

## 17. Reproduction

```powershell
uv sync --extra dev
uv run firstlook simulate --config configs/phase0c_synthetic.json `
  --output outputs/reports/phase0c_synthetic_results.json
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

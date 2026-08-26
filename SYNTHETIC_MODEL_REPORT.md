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

## 15. Reproduction

```powershell
uv sync --extra dev
uv run firstlook simulate --config configs/phase0c_synthetic.json `
  --output outputs/reports/phase0c_synthetic_results.json
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

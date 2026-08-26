# SYSTEM BOUNDARIES — FIRSTLOOK-MAD

> **Fase:** 0A · **v0.1.0** · **Estado:** `RESEARCH / SIMULATION PROTOTYPE ONLY`

Fronteras técnicas y operativas del sistema. Complementa `PRODUCT_CONTRACT.md`.

---

## 1. Dentro del sistema (IN SCOPE — Phase 0)

- Modelos de dominio: `Incident`, `CandidateDockSite`, `UASPerformanceProfile`,
  `FlightSafetyGate`, capas de riesgo.
- Cálculo de **TTFRP** y su descomposición.
- Modelos de cobertura progresivos (A→F, ver `docs/ARCHITECTURE.md`).
- Optimización de docks (facility location determinista).
- Simulación de escenarios (históricos y sintéticos, nunca mezclados sin marca).
- Provenance / manifest de datasets.
- CLI reproducible y outputs regenerables.

## 2. Fuera del sistema (OUT OF SCOPE — Phase 0)

| Área | Estado |
|---|---|
| Control de UAS real / MAVLink / PX4 / ArduPilot / DJI Dock | OUT — solo adapters mock |
| BVLOS operacional | OUT |
| Dispatch de recursos / recomendación de recursos | OUT |
| Integración 112 / INFOMA / CAD / SMS | OUT |
| Computer vision en vivo / IA térmica | OUT |
| ML / vector DB / LLM orchestration / agentes | OUT |
| Dashboard de producción / app móvil | OUT |
| Cloud / Kubernetes / Docker (salvo necesidad demostrada) | OUT |
| Base de datos operacional / auth | OUT |
| Decisión oficial de vuelo | OUT — imposible por diseño |

## 3. Interfaces abstractas obligatorias

Cualquier componente que *conceptualmente* tocaría hardware o servicios reales se
expone como **interfaz abstracta + implementación mock/simulada**:

- `UASControlPort` → solo `SimulatedUASAdapter` (sin efecto físico).
- `AirspaceProvider` → cache local + `SyntheticAirspaceProvider`.
- `WeatherProvider` → datos simulados / cacheados.
- `AlertSource` → `SyntheticAlertSource` / lector de históricos.

No se implementa **ninguna** ruta que convierta una alerta en una activación física.

## 4. Fronteras de datos

- `data/raw/` es **inmutable** (nunca se modifica destructivamente).
- Reales, derivados y sintéticos viven separados y etiquetados.
- No se versionan datasets enormes ni secretos.

## 5. Frontera de decisión

El sistema produce **evidencia, derivaciones, estimaciones y recomendaciones**.
La **decisión** siempre es humana y externa. El límite entre *Recommendation* y
*Decision* es una frontera dura del producto (ver `decision/`).

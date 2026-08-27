# PRODUCT CONTRACT — FIRSTLOOK-MAD

> **Estado del proyecto:** `RESEARCH / SIMULATION PROTOTYPE ONLY`
> **Fase actual:** Phase 0B — Data Feasibility (cerrada: `DATA PARTIAL`)
> **Versión del documento:** 0.1.0 · **Fecha:** 2026-08-26

Este documento es el **contrato** de lo que el proyecto es y no es. Cualquier
código, dato o afirmación que contradiga este contrato es un defecto.

---

## 1. Qué es FIRSTLOOK-MAD

Un **prototipo de investigación y simulación** (Digital Twin) que evalúa, de forma
reproducible y auditable, si una **red distribuida de puntos potenciales de
despliegue UAS** podría reducir de forma **significativa y defendible** el tiempo
entre una alerta de incendio forestal y la obtención de una **primera imagen
operativa fiable** del incidente, en el ámbito de la Comunidad de Madrid.

El KPI central es **TTFRP — Time To First Reliable Picture**.

## 2. Qué NO es (límites duros — *hard boundaries*)

Este repositorio **NO**:

1. controla drones reales ni emite órdenes de vuelo reales;
2. despacha automáticamente bomberos, helicópteros, vehículos ni recursos públicos;
3. se conecta con Madrid 112, INFOMA ni ningún sistema operacional real;
4. simula poseer permisos BVLOS ni autorizaciones operacionales;
5. presenta una recomendación de IA como decisión oficial;
6. realiza reconocimiento facial ni identificación/seguimiento de personas;
7. afirma certificación, seguridad operacional o *emergency-readiness*.

Todo componente de vuelo usa **interfaces abstractas, simuladores, mocks o adapters
no operativos**. No existe ninguna vía de código capaz de activar físicamente un UAS.

## 3. La hipótesis (lo que probamos)

> **NO** probamos: "los drones sirven para incendios" (ya conocido).
>
> **SÍ** probamos: una red distribuida de puntos de despliegue UAS, integrada con
> GIS, riesgo territorial, restricciones de vuelo y recursos de emergencia
> existentes, puede reducir de forma **significativa y defendible** el TTFRP.

## 4. Cadena operativa conceptual

```
ALERTA → VERIFICACIÓN → FLIGHT SAFETY GATE → SELECCIÓN DEL PUNTO DE DESPLIEGUE
       → TRÁNSITO UAS → FIRST LOOK → SITUATION REPORT → APOYO A LA DECISIÓN
       → RESPUESTA HUMANA
```

El proyecto se centra **inicialmente en las etapas anteriores a una respuesta
operativa real**. La "RESPUESTA HUMANA" queda siempre fuera del sistema.

## 5. Definición de MVP (contrato de éxito técnico)

Un MVP exitoso **NO** es un dron volando. Es:

> Un simulador reproducible y auditable, operable por **CLI**, capaz de evaluar
> escenarios de incidentes, puntos candidatos de despliegue, restricciones,
> perfiles UAS y TTFRP, y de **comparar configuraciones de red** mediante
> métricas transparentes y trazables.

## 6. Los tres resultados válidos

El éxito **científico** es cualquiera de estos; ninguno es un fracaso:

- **BUILD** — la red muestra valor incremental sólido y defendible.
- **REPOSITION** — el concepto vale, pero requiere otra arquitectura (unidades
  móviles, cámaras fijas + UAS, híbrido...).
- **KILL** — restricciones, coste o valor marginal no justifican continuar.

> La misión no es demostrar que la idea es buena. La misión es descubrir si
> resiste el contacto con datos + regulación + geografía + operaciones + coste +
> incertidumbre.

## 7. Reglas de integridad (invariantes del proyecto)

- **Anti-alucinación:** ubicaciones, cifras, capacidades, legislación, tiempos,
  costes, rangos, autorizaciones desconocidos se marcan `UNKNOWN` / `ASSUMPTION` /
  `NOT_VERIFIED`, nunca se inventan.
- **Procedencia:** todo dato responde de dónde salió, cuándo, versión, licencia,
  CRS, transformación, y si es real / derivado / sintético.
- **First failure wins** en gates críticos: un `UNKNOWN` en airspace bloquea el
  gate aunque todo lo demás pase.
- **Nunca** existe el estado `SAFE_TO_FLY`.
- **Separación** permanente entre *Evidence*, *Interpretation* y *Decision*.

## 8. Fuera de alcance en Phase 0 (explícito)

Recomendación de recursos (camiones, bomberos, helicópteros, retardante,
maquinaria, recursos médicos) = **OUT OF SCOPE**. También: alert ingestion real,
112/CAD, MAVLink/PX4/ArduPilot, DJI Dock, BVLOS operacional, dispatch automático,
computer vision en vivo, dashboards de producción, app móvil, ML, cloud, auth.

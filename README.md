# FIRSTLOOK-MAD

**Sistema distribuido de primera respuesta y apoyo a la decisión mediante UAS para
incendios forestales en la Comunidad de Madrid**

> ![status](https://img.shields.io/badge/status-research%20prototype%20%E2%80%94%20simulation%20only-orange)
>
> **Research prototype — simulation only.** Este repositorio **no** controla
> drones, **no** despacha recursos, **no** se conecta a sistemas de emergencia
> reales y **no** produce decisiones oficiales. Ver `docs/SYSTEM_BOUNDARIES.md`.

---

## 1. Problema

El tiempo entre una alerta de incendio forestal y la obtención de una **primera
imagen operativa fiable** del incidente condiciona la respuesta. Reducirlo podría
tener valor — pero solo si es **defendible** frente a datos, regulación, geografía,
operaciones, coste e incertidumbre.

## 2. Hipótesis

> Una red **distribuida** de puntos potenciales de despliegue UAS, integrada con
> GIS, riesgo territorial, restricciones de vuelo y recursos existentes, puede
> reducir de forma significativa y defendible el **TTFRP — Time To First Reliable
> Picture**.

No probamos "los drones sirven para incendios" (ya conocido). Probamos si la **red
distribuida** aporta valor incremental real. Ver `docs/RESEARCH_QUESTIONS.md`.

## 3. Qué hace (objetivo)

Un simulador reproducible y auditable (CLI) que evalúa escenarios de incidentes,
sitios candidatos de despliegue, restricciones, perfiles UAS y TTFRP, y **compara
configuraciones de red** con métricas transparentes.

## 4. Qué NO hace

No vuela drones · no despacha bomberos/helicópteros · no se integra con 112/INFOMA
· no simula permisos BVLOS · no presenta IA como decisión oficial · no identifica
personas. Ver `docs/PRODUCT_CONTRACT.md`.

## 5. Estado actual

**Phase 0D — falsación con datos reales, ejecutada y cerrada.** Gate: `MADRID
REAL DATA MVP — FAIL (BLOCKED: EXECUTION ENVIRONMENT EGRESS)`. Señal
estratégica: `INSUFFICIENT EVIDENCE`. No se obtuvo evidencia real nueva de
Madrid, así que la última lectura científica válida sigue siendo la de Phase
0C.1: `CONDITION_DEPENDENT_STRONG`, sin soporte para `BUILD`. Phase 0E **no**
está autorizada. Próximo paso legítimo: reintentar la adquisición de datos
reales ya definida en Phase 0D desde un entorno con salida de red permitida,
o aportar los pequeños extractos reales especificados con procedencia. Ver
`PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` y `PROJECT_STATE.md`.

## 6. Metodología

Fases con gates (0A definición → 0B datos → 0C modelo sintético → 0D MVP Madrid →
0E baseline → 0F BUILD/REPOSITION/KILL). Separación permanente entre **Evidence**,
**Interpretation** y **Decision**. Ver `docs/VALIDATION_PLAN.md`.

## 7. Arquitectura

Python + GeoPandas/Shapely/PyProj + DuckDB/Parquet + Pydantic, determinista y
auditable. Sin ML salvo necesidad demostrada. Ver `docs/ARCHITECTURE.md`.

## 8. Quickstart

```powershell
uv sync --extra dev
uv run firstlook validate-config --config configs/phase0c_synthetic.json
uv run firstlook simulate --config configs/phase0c_synthetic.json `
  --output outputs/reports/phase0c_synthetic_results.json
uv run pytest -q
```

El resultado es íntegramente sintético y no representa desempeño real de Madrid.

## 9. Datos

Manifest de 19 fuentes (INFOMA, ENAIRE, EASA/BOE, EFFIS, AEMET, IGN, INE y
otras) en `data/datasets_manifest.json`: 5 `READY`, 9 `PARTIAL`, 1 `BLOCKED` y
4 `REFERENCE_ONLY`. No se descargaron datasets masivos. Datos de terceros
conservan su licencia.

## 10. Seguridad

Sistema *safety-adjacent*, **no** certificado ni operacional. Ver
`docs/SAFETY_CASE.md` y `SECURITY.md`.

## 11. Regulación

Restricción de primer orden. Nunca `SAFE_TO_FLY`; estados explícitos de zona.
Ver `docs/REGULATORY_BOUNDARIES.md`.

## 12. Roadmap

Ver `docs/VALIDATION_PLAN.md` y `PROJECT_STATE.md`. Elementos operacionales
(112, MAVLink, DJI Dock, BVLOS, dispatch, CV en vivo) están en roadmap pero
**fuera de alcance** de Phase 0.

## 13. Reproducibilidad

`git clone` + `uv sync --extra dev` reproduce el escenario 0C con seed fija,
configuración versionada y sin credenciales privadas. Ver `docs/ARCHITECTURE.md`.

## 14. Licencia

Código: ver `LICENSE` (Apache-2.0, confirmada; ver ADR-0001). Datos
de terceros: su propia licencia. Citación: `CITATION.cff`.

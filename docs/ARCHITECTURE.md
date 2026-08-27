# ARCHITECTURE — FIRSTLOOK-MAD (Phase 0)

> **Fase:** 0C implementada · **v0.2.0** · **Estado:** `RESEARCH / SIMULATION ONLY`
>
> Propuesta de arquitectura de **Phase 0**. Principio: *core → datos → simulación
> → tests → outputs*. **No** empezar por frontend. **No** sobrearquitectar.
> Cada dependencia debe justificar su existencia (anti stack-inflation).

---

## 1. Principios arquitectónicos

- **Determinista y auditable** antes que "inteligente". Sin ML si una regla
  determinista resuelve el problema.
- **Configuración fuera del código** (`configs/`), constantes centralizadas.
- **Interfaces abstractas** (*ports*) para todo lo que rozaría hardware/servicios
  reales; solo implementaciones mock/simuladas (*adapters*).
- **Provenance de primer orden**: manifest + metadatos obligatorios.
- **CRS explícito y centralizado**: nunca distancias en EPSG:4326.
- **Separación Evidence / Assessment / Recommendation / Human review**.

## 2. Mapa de módulos (`src/firstlook_mad/`)

| Módulo | Responsabilidad | Depende de |
|---|---|---|
| `domain.py` | Entidades, enums, invariantes y configuración | Pydantic |
| `geo.py` | Distancia métrica sobre puntos ya proyectados | domain, stdlib |
| `safety.py` | Gate conservador y causas de exclusión | domain |
| `simulation.py` | TTFRP y modelos progresivos A→F | domain, geo, safety |
| `synthetic.py` | Fixtures deterministas con seed fija | domain, stdlib |
| `validation.py` | Greedy, métricas y falsificación | simulation, synthetic |
| `cli.py` | `simulate` y `validate-config` | synthetic, validation, argparse |

Flujo implementado: `domain` ← `geo`/`safety` ← `simulation` ← `validation` ←
`cli`. Sin ciclos. Ingesta real, optimización no trivial y adapters operacionales
no existen todavía.

## 3. Modelos de cobertura (progresivos, comparables, §9 brief)

| Modelo | Añade | Simplificación que expone |
|---|---|---|
| A | Distancia euclídea | Ignora todo lo operacional |
| B | Tiempo de tránsito (velocidad) | Ignora relieve/aire/energía |
| C | Elevación y relieve | Ignora aire/tiempo/energía |
| D | Airspace constraints | Ignora meteo/energía |
| E | Weather feasibility | Ignora energía |
| F | Energy reserve | Modelo más completo de Phase 0 |

Cada modelo es comparable con los anteriores; las simplificaciones nunca se ocultan.

## 4. Flight Safety Gate (determinista, first-failure-wins)

Factores: `site_available`, `uas_available`, `battery`, `range`, `wind`,
`precipitation`, `visibility`, `temperature`, `airspace`,
`temporary_restriction`, `manned_aircraft_conflict`, `communications`,
`incident_confidence`, `data_freshness`.
Salidas: `GO_SIMULATION` / `NO_GO` / `UNKNOWN` / `REQUIRES_HUMAN_REVIEW`.
Regla dura: cualquier factor crítico `UNKNOWN`/`RESTRICTED` ⇒ **no** `GO_SIMULATION`;
se guardan las razones de exclusión. Sin bypass silencioso.

## 5. Stack propuesto y **justificación por dependencia**

Objetivo del brief: Python moderno, pequeño, reproducible. Justificación:

| Dependencia | Por qué es necesaria | Alternativa descartada |
|---|---|---|
| **Python 3.12+** | Base del brief; tipado moderno | Verificado en 3.12.13 y entorno uv 3.14.5 |
| **uv** | Resolución/lock reproducible y rápido | pip/poetry (menos reproducible/rápido) |
| **Pydantic** | Validación de dominio, invariantes, esquemas serializables | dataclasses (sin validación) |
| **pandas** | Tablas analíticas, KPIs | — |
| **GeoPandas + Shapely + PyProj** | Geometría, CRS, operaciones espaciales correctas | cálculo manual (propenso a error de CRS) |
| **DuckDB + Parquet** | Analítica local sin servidor, columnar, reproducible | SQLite (menos analítico), BD operacional (out of scope) |
| **pytest** | Tests deterministas | unittest (más verboso) |
| **Ruff** | Lint + formato rápido, único tool | flake8+black+isort (3 herramientas) |
| **mypy** | Type checking estricto; decisión ADR-0002 | pyright (otro runtime/toolchain) |
| **pre-commit** | Calidad antes del commit | hooks manuales |

### Dependencias **diferidas** (no instalar hasta que su fase lo exija)

| Diferida | Se añade cuando | Fase |
|---|---|---|
| **OR-Tools** | Se implemente facility location no trivial (valorar antes de algo más pesado) | 0C/0D |
| **NetworkX** | Se necesite modelado de grafos/rutas | 0C+ |
| **Rasterio** | Se requieran rasters (MDT, riesgo raster) reales | 0D |
| Streamlit / Dash | Solo tras MVP CLI demostrado | post-0D |

**No** se añade: React/Next.js, Docker, Kubernetes, cloud, BD operacional, auth,
LLM/agents/vector DB, ML. Justificación en `SYSTEM_BOUNDARIES.md`.

## 6. CRS y geometría

- CRS analítico fijado en ADR-0002: ETRS89 / UTM zona 30N (`EPSG:25830`).
- Todas las transformaciones centralizadas en `geo/`.
- Tests obligatorios: CRS incorrecto, geometría vacía/ inválida, coordenadas
  intercambiadas, punto fuera del territorio esperado.

## 7. Persistencia y outputs

- `data/raw/` inmutable → `data/interim/` → `data/processed/` (Parquet).
- Outputs regenerables en `outputs/` (maps/tables/figures/reports), nunca lógica
  de producción en notebooks.

## 8. Qué NO se construye aún

Phase 0C implementa solo dominio, gate, geometría métrica, simulación sintética,
falsación y CLI. Siguen diferidos datos reales de Madrid, optimización no trivial,
rasters, dashboard, ML y cualquier componente operacional.

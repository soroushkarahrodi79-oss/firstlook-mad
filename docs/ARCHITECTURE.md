# ARCHITECTURE — FIRSTLOOK-MAD (Phase 0 proposal)

> **Fase:** 0A (propuesta) · **v0.1.0** · **Estado:** `RESEARCH / SIMULATION ONLY`
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
| `domain/` | Entidades y enums: `Incident`, `CandidateDockSite`, `UASPerformanceProfile`, `FlightSafetyGate`, estados, invariantes | Pydantic |
| `data/` | Carga, manifest, provenance, lectura sintéticos/fixtures | pandas, DuckDB, Pydantic |
| `geo/` | CRS centralizado, distancias, geometría, validación geométrica | GeoPandas, Shapely, PyProj |
| `airspace/` | Estados de zona (UNKNOWN…), providers abstractos + sintético | domain, geo |
| `simulation/` | TTFRP, modelos de cobertura A→F, escenarios, Monte Carlo | domain, geo, numpy |
| `optimization/` | Facility location (greedy / p-median / MCLP) | OR-Tools *(diferido)*, networkx si aplica |
| `decision/` | Evidence→Assessment→Recommendation (sin decisión oficial) | domain, simulation |
| `validation/` | Métricas, gates, sensitivity analysis, red-team harness | todo lo anterior |
| `cli/` | Comandos reproducibles | Typer/argparse *(a decidir)* |

Flujo de dependencias: `domain` ← `geo`/`data` ← `airspace`/`simulation` ←
`optimization`/`decision` ← `validation` ← `cli`. Sin ciclos.

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
`precipitation`, `visibility`, `temperature`, `airspace`, `uas_geo_zone`,
`temporary_restriction`, `manned_aircraft_conflict`, `communications`,
`incident_confidence`, `data_freshness`.
Salidas: `GO_SIMULATION` / `NO_GO` / `UNKNOWN` / `REQUIRES_HUMAN_REVIEW`.
Regla dura: cualquier factor crítico `UNKNOWN`/`RESTRICTED` ⇒ **no** `GO_SIMULATION`;
se guardan las razones de exclusión. Sin bypass silencioso.

## 5. Stack propuesto y **justificación por dependencia**

Objetivo del brief: Python moderno, pequeño, reproducible. Justificación:

| Dependencia | Por qué es necesaria | Alternativa descartada |
|---|---|---|
| **Python 3.12+** | Base del brief; tipado moderno | (runtime local es 3.11 — fijar `requires-python` y verificar en 0C) |
| **uv** | Resolución/lock reproducible y rápido | pip/poetry (menos reproducible/rápido) |
| **Pydantic** | Validación de dominio, invariantes, esquemas serializables | dataclasses (sin validación) |
| **pandas** | Tablas analíticas, KPIs | — |
| **GeoPandas + Shapely + PyProj** | Geometría, CRS, operaciones espaciales correctas | cálculo manual (propenso a error de CRS) |
| **DuckDB + Parquet** | Analítica local sin servidor, columnar, reproducible | SQLite (menos analítico), BD operacional (out of scope) |
| **pytest** | Tests deterministas | unittest (más verboso) |
| **Ruff** | Lint + formato rápido, único tool | flake8+black+isort (3 herramientas) |
| **mypy o pyright** | Type checking (decidir uno en ADR) | ninguno (inaceptable en safety-adjacent) |
| **pre-commit** | Calidad antes del commit | hooks manuales |

### Dependencias **diferidas** (no instalar hasta que su fase lo exija)

| Diferida | Se añade cuando | Fase |
|---|---|---|
| **OR-Tools** | Se implemente facility location no trivial (valorar antes de algo más pesado) | 0C/0D |
| **NetworkX** | Se necesite modelado de grafos/rutas | 0C+ |
| **Rasterio** | Se requieran rasters (MDT, riesgo raster) reales | 0D |
| **numpy** | Requerido transitivamente; explícito al implementar simulación | 0C |
| Streamlit / Dash | Solo tras MVP CLI demostrado | post-0D |

**No** se añade: React/Next.js, Docker, Kubernetes, cloud, BD operacional, auth,
LLM/agents/vector DB, ML. Justificación en `SYSTEM_BOUNDARIES.md`.

## 6. CRS y geometría

- Un CRS proyectado adecuado para Madrid (candidato a documentar/verificar:
  ETRS89 / UTM zona 30N — `NOT_VERIFIED`, se fija en ADR de 0C).
- Todas las transformaciones centralizadas en `geo/`.
- Tests obligatorios: CRS incorrecto, geometría vacía/ inválida, coordenadas
  intercambiadas, punto fuera del territorio esperado.

## 7. Persistencia y outputs

- `data/raw/` inmutable → `data/interim/` → `data/processed/` (Parquet).
- Outputs regenerables en `outputs/` (maps/tables/figures/reports), nunca lógica
  de producción en notebooks.

## 8. Qué NO se construye aún

Nada de aplicación importante en 0A. En esta fase solo: documentación, estructura
de carpetas y scaffolding técnico mínimo (`pyproject.toml`, gitkeeps). El código de
dominio empieza en Phase 0C, tras los gates de definición (0A) y datos (0B).

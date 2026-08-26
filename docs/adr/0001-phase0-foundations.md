# ADR 0001 — Phase 0 foundations: scope, stack, licence, CRS

- **Status:** Accepted (Phase 0A)
- **Date:** 2026-08-26
- **Deciders:** Equipo multidisciplinar (ver brief maestro)

## Context

Repositorio nuevo y vacío. Se necesita fijar decisiones fundacionales antes de
escribir lógica, evitando stack-inflation y afirmaciones no verificadas.

## Decisions

1. **Alcance Phase 0 = investigación + simulación.** Sin control de UAS real,
   sin dispatch, sin integración operacional. Interfaces abstractas + mocks
   únicamente. (Ver `PRODUCT_CONTRACT.md`, `SYSTEM_BOUNDARIES.md`.)

2. **Stack mínimo reproducible:** Python 3.12+ (runtime local 3.11 detectado —
   `requires-python` fija el objetivo, a verificar en 0C), uv, Pydantic, pandas,
   GeoPandas/Shapely/PyProj, DuckDB+Parquet, pytest, Ruff, type-checker,
   pre-commit. OR-Tools, NetworkX, Rasterio, numpy explícito y viz **diferidos**
   a la fase que los exija. Justificación por dependencia en `ARCHITECTURE.md §5`.

3. **Type checker:** decisión pendiente entre **mypy** y **pyright**; se resolverá
   en un ADR de 0C al introducir código tipado. Ambos aceptables; no bloquea 0A.

4. **CRS proyectado:** candidato **ETRS89 / UTM 30N** para análisis métrico de
   Madrid. Estado `NOT_VERIFIED`; se confirma en ADR de 0C con tests geométricos.
   Regla firme: nunca calcular distancias en EPSG:4326.

5. **Licencia (recomendación, no vinculante aún):** para el **código**, licencia
   permisiva **Apache-2.0** (incluye concesión explícita de patentes, apropiada
   para un proyecto safety-adjacent) o **MIT** (más simple). Los **datos de
   terceros** conservan su propia licencia y no se relicencian. Se crea `LICENSE`
   con Apache-2.0 como opción por defecto revisable; cambiarla es trivial en 0A.

6. **Sin `SAFE_TO_FLY`.** Enum de estados de zona: UNKNOWN / POTENTIALLY_ALLOWED /
   RESTRICTED / REQUIRES_AUTHORIZATION / TEMPORARILY_RESTRICTED / NOT_EVALUATED.

7. **Gates first-failure-wins** para factores críticos de seguridad/regulación.

## Consequences

- Reproducibilidad y auditabilidad priorizadas sobre rapidez de features.
- Algunas decisiones (type checker, CRS definitivo, magnitud de thresholds de
  validación) quedan explícitamente abiertas y trazadas, no ocultas.
- La recomendación de licencia debe confirmarla la persona responsable del repo.

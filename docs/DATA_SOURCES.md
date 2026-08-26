# DATA SOURCES — FIRSTLOOK-MAD

> **Fase:** 0A (catálogo de intención) · **v0.1.0**
>
> **AVISO:** en Phase 0A esto es un **catálogo de candidatas**, no un registro de
> datos descargados. La investigación real de accesibilidad, esquema y licencia
> ocurre en **Phase 0B**. Ninguna fila está verificada todavía
> (`verification_status = NOT_VERIFIED`). No se ha copiado ni cacheado ningún dato.

---

## 1. Metadatos obligatorios por dataset (contrato de procedencia)

Cada dataset que entre al proyecto **debe** registrar en el manifest:

`source` · `source_url_or_id` · `publication_date` · `consulted_date` ·
`version` · `license` · `crs` · `update_frequency` · `fields` · `limitations` ·
`nature` (`REAL` / `DERIVED` / `SYNTHETIC`) · `transformation` · `created_by_script`
· `verification_status`.

## 2. Fuentes candidatas (prioridad según brief §3)

| # | Fuente | Uso previsto | Naturaleza | verification_status |
|---|---|---|---|---|
| 1 | Comunidad de Madrid — INFOMA | Infraestructura de prevención/extinción | REAL | `NOT_VERIFIED` |
| 2 | Agencia de Seguridad y Emergencias Madrid 112 | Contexto de recursos (solo referencia) | REAL | `NOT_VERIFIED` |
| 3 | Comunidad de Madrid — Grupo Especial de Drones | Contexto UAS existente | REAL | `NOT_VERIFIED` |
| 4 | ENAIRE — zonificación geográfica UAS | Airspace / geozonas | REAL | `NOT_VERIFIED` |
| 5 | ENAIRE — AIP / NOTAM | Restricciones dinámicas | REAL | `NOT_VERIFIED` |
| 6 | AESA | Marco regulatorio nacional | REAL | `NOT_VERIFIED` |
| 7 | EASA | Marco regulatorio UE | REAL | `NOT_VERIFIED` |
| 8 | BOE | Normativa publicada | REAL | `NOT_VERIFIED` |
| 9 | Copernicus / EFFIS | Riesgo e histórico de incendios | REAL | `NOT_VERIFIED` |
| 10 | AEMET | Meteorología | REAL | `NOT_VERIFIED` |
| 11 | IGN | Topografía / cartografía base / MDT | REAL | `NOT_VERIFIED` |
| 12 | IDEM / cartografía oficial CM | Cartografía regional | REAL | `NOT_VERIFIED` |
| 13 | Datos abiertos Comunidad de Madrid | Infraestructura / uso del suelo | REAL | `NOT_VERIFIED` |
| 14 | OpenStreetMap | Solo cuando apropiado, con naturaleza declarada | REAL (comunitario) | `NOT_VERIFIED` |

## 3. Reglas de captura (vinculantes desde ya)

- **No** descargar cantidades masivas en 0B: primero probar accesibilidad y schema.
- **No** copiar silenciosamente datos de páginas web.
- **No** convertir información dinámica (NOTAM, meteo, zonas temporales) en verdad
  permanente: se cachea con fecha y se marca la frescura.
- `data/raw/` inmutable; transformaciones producen `data/interim/` y
  `data/processed/`, siempre vía script trazable.
- Datos de terceros conservan su **propia licencia** (ver `LICENSE` / §37 brief).

## 4. Producto de Phase 0B

`DATA_FEASIBILITY_REPORT.md` con veredicto por fuente:
`DATA READY` / `DATA PARTIAL` / `DATA BLOCKED`, y un **manifest** inicial de
datasets accesibles con su esquema real. **No se inicia en esta sesión.**

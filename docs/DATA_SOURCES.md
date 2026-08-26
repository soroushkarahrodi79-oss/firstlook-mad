# DATA SOURCES — FIRSTLOOK-MAD

> **Fase:** 0B cerrada · **v0.3.0** · **Gate:** `DATA PARTIAL`
>
> **AVISO:** el registro canónico es `data/datasets_manifest.json`. La
> verificación de 0B cubre factibilidad y metadatos, no aptitud operacional. No se
> ha copiado ni cacheado ningún dataset masivo.

---

## 1. Metadatos obligatorios por dataset (contrato de procedencia)

Cada dataset que entre al proyecto **debe** registrar en el manifest:

`source` · `source_url_or_id` · `publication_date` · `consulted_date` ·
`version` · `license` · `crs` · `update_frequency` · `fields` · `limitations` ·
`nature` (`REAL` / `DERIVED` / `SYNTHETIC`) · `transformation` · `created_by_script`
· `verification_status`.

## 2. Resultado de factibilidad

| # | Fuente | Uso previsto | feasibility_status |
|---|---|---|---|
| 1 | ENAIRE — zonificación UAS V2 | Restricciones espaciales | `READY` |
| 2 | ENAIRE — NOTAM geoespacial | Restricciones dinámicas | `PARTIAL` |
| 3 | BOE / EASA | Referencia regulatoria | `REFERENCE_ONLY` |
| 4 | AEMET / ERA5-Land | Erosión meteorológica | `PARTIAL` |
| 5 | MITECO EGIF | Incidentes y primeras llegadas | `PARTIAL` |
| 6 | EFFIS actual / histórico | Incendios/perímetros | `PARTIAL` / `BLOCKED` |
| 7 | Comunidad de Madrid / INFOMA | Sitios y red actual | `PARTIAL` / `REFERENCE_ONLY` |
| 8 | Ayuntamiento de Madrid | Parques del municipio | `READY` |
| 9 | OpenStreetMap | Suplemento de sitios | `PARTIAL` |
| 10 | IGN MDT05 / transporte | Topografía y referencia | `READY` |
| 11 | SIOSE AR 2020 / CLC 2018 | Cobertura del suelo, no combustible | `PARTIAL` / `READY` |
| 12 | INE Censo 2021 | Exposición | `PARTIAL` |
| 13 | ASEM 112 | Contexto agregado | `REFERENCE_ONLY` |

## 3. Reglas de captura (vinculantes desde ya)

- **No** descargar cantidades masivas en 0B: primero probar accesibilidad y schema.
- **No** copiar silenciosamente datos de páginas web.
- **No** convertir información dinámica (NOTAM, meteo, zonas temporales) en verdad
  permanente: se cachea con fecha y se marca la frescura.
- `data/raw/` inmutable; transformaciones producen `data/interim/` y
  `data/processed/`, siempre vía script trazable.
- Datos de terceros conservan su **propia licencia** (ver `LICENSE` / §37 brief).

## 4. Productos de Phase 0B

- `DATA_FEASIBILITY_REPORT.md`: evidencia, cobertura de RQ/supuestos, TTFRP,
  red-team y gate.
- `data/datasets_manifest.json`: manifest de 19 fuentes.
- `data/source_probes.json`: configuración reproducible de probes.
- `outputs/reports/source_probe_results.json`: resultado 7/7 accesible.

**Resultado global:** `DATA PARTIAL`. Suficiente para simulación sintética y
falsación en 0C; insuficiente para claims sobre desempeño real de Madrid.

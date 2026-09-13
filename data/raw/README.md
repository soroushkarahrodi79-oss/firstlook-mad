# data/raw — INMUTABLE

Datos originales sin modificar. Nunca se editan destructivamente.
No versionado (ver .gitignore). Cada dataset requiere entrada en el manifest de
procedencia. Ver docs/DATA_SOURCES.md.

## phase0d/

Evidencia cruda persistida por `scripts/acquire_phase0d_sources.py` para
probes genuinamente `ACQUIRED` (HTTP exitoso, cuerpo no vacío). Ruta
determinista por fuente y fecha:

```
data/raw/phase0d/<probe_id>/<YYYYMMDD>.raw
data/raw/phase0d/<probe_id>/<YYYYMMDD>.raw.provenance.json
```

Cada `.raw` contiene exactamente los bytes recibidos, sin transformar. Cada
`.provenance.json` registra `probe_id`, `source_url`, `acquired_at_utc`,
`http_status`, `content_type`, `byte_count`, `sha256`, `local_raw_path`,
`truncated` y `evidence_nature: "REAL"`. El script nunca sobrescribe un
`.raw` existente con contenido distinto: usa una ruta de respaldo específica
de esa ejecución en su lugar. Ver
`docs/PHASE_0D_PROTOCOL.md` §7 y `PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md`
§16 para el contrato completo y su historial de desviaciones.

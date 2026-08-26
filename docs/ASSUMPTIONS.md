# ASSUMPTIONS — FIRSTLOOK-MAD

> **Fase:** 0B cerrada · **v0.2.0**
>
> Registro explícito de supuestos. Cada supuesto es **falsable** y tiene un plan
> para verificarlo o refutarlo. Un supuesto **no** es un hecho: se marca como tal
> en todo output derivado (`ASSUMED` / `SIMULATED`).

Identificador: `A-nn`. Estado: `OPEN` (sin verificar) / `TESTING` / `SUPPORTED` /
`REFUTED`.

| ID | Supuesto | Riesgo si es falso | Cómo se prueba | Estado |
|---|---|---|---|---|
| A-01 | El tránsito UAS (`T_travel`) es una fracción **material** del TTFRP | Si `T_alert+T_verif` domina, la red de docks aporta poco → tesis débil | Test del cuello de botella con rangos plausibles (0C) | TESTING |
| A-02 | Existe infraestructura pública reutilizable como sitio candidato | Sin sitios, no hay red | Inventario verificable en 0B | TESTING |
| A-03 | Un buffer geométrico aproxima *pobremente* la cobertura operacional (por eso modelamos A→F) | Sobreestimar cobertura | Comparar Modelo A vs D/E/F (0C/0D) | OPEN |
| A-04 | La meteo de días de fuego no anula sistemáticamente la viabilidad de vuelo | El valor se evapora en los días que importan | Test de erosión meteorológica (0C con datos AEMET/EFFIS en 0D) | TESTING |
| A-05 | El riesgo de incendio es representable por capas separadas antes que por un score compuesto | Índice arbitrario no defendible | Sensitivity analysis sobre pesos (0C/0D) | OPEN |
| A-06 | Los perfiles UAS de referencia son plausibles como *rangos*, no como rendimiento garantizado | Cobertura irreal | Perfiles conservador/optimista con incertidumbre | OPEN |
| A-07 | Existe (o puede construirse) un baseline defendible del desempeño actual | Sin baseline, RQ4 no responde | Investigación de baseline (0E) | TESTING |
| A-08 | La coordinación con aeronaves tripuladas puede modelarse como restricción sin datos operacionales reales | Deconflicción domina y no se captura | Modelado conservador + red-team (0C+) | TESTING |
| A-09 | Un CRS proyectado adecuado para Madrid da errores métricos aceptables | Distancias/tiempos sesgados | Tests de CRS y validación geométrica (0C) | OPEN |
| A-10 | La localización del incidente tiene incertidumbre acotada (`location_uncertainty_m`) | "First look" no fiable | Escenarios con incertidumbre variable (0C) | OPEN |

## Evidencia incorporada en 0B

- **A-01:** debilitado. No hay clocks públicos extremo a extremo y no se ha
  demostrado que `T_travel` domine.
- **A-02:** hay candidatos utilizables en simulación, pero no evidencia de
  permiso, aptitud ni disponibilidad para docks.
- **A-04:** AEMET/ERA5-Land permiten diseñar sensibilidad; faltan visibilidad
  histórica local y un envelope UAS validado.
- **A-07:** EGIF soporta un baseline parcial de primeras llegadas, no TTFRP.
- **A-08:** geozonas y NOTAM son representables, pero la coordinación operacional
  no es pública. Ver `DATA_FEASIBILITY_REPORT.md`.

## Supuestos que NO hacemos (explícito)

- **No** asumimos que ninguna infraestructura acepte realmente un dock.
- **No** asumimos permisos BVLOS.
- **No** asumimos que INFOMA tiene mala cobertura actual (podría tener excelente
  cobertura — eso sería un resultado válido: KILL/REPOSITION).
- **No** asumimos que el dron llega antes que las alternativas.

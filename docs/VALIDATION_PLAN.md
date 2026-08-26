# VALIDATION PLAN — FIRSTLOOK-MAD

> **Fase:** actualizado al cierre de 0C · **v0.2.0**
>
> La primera gran decisión del proyecto es **BUILD / REPOSITION / KILL**. No
> estamos obligados a demostrar que funciona; queremos **descubrir** si funciona.
> Este plan define *cómo* se decide, separando siempre **Evidence** ·
> **Interpretation** · **Decision**.

---

## 1. Principio anti-sesgo

> Los thresholds de validación se fijan **antes** de ver resultados y **no** se
> ajustan después para forzar un BUILD (§32, §41 brief). Cualquier cambio de
> threshold posterior a ver resultados se registra como desviación en un ADR.

## 2. Thresholds provisionales (a calibrar en 0B/0E, no definitivos)

Marcados `PROVISIONAL` — se confirman cuando exista baseline y calidad de datos.

| Criterio | Métrica | Threshold provisional | Estado |
|---|---|---|---|
| Mejora temporal | Δ mediana TTFRP vs baseline | "material" — magnitud a fijar en 0E | PROVISIONAL |
| Cobertura ponderada | risk-weighted coverage <10 min | idem | PROVISIONAL |
| Robustez | ¿el valor sobrevive gates reales (weather/airspace)? | debe mantenerse tras restricciones | PROVISIONAL |
| Economía de red | nº de docks para cobertura material | rendimientos decrecientes aceptables | PROVISIONAL |
| Alternativa más simple | ¿cámara fija/híbrido iguala resultado? | no debe ser claramente superado | PROVISIONAL |

> **Por qué provisionales:** fijar una cifra dura hoy sería arbitrario. Primero se
> investiga baseline disponible, calidad de datos, variabilidad operacional y qué
> constituye "mejora material" (§22 brief).

## 3. Gates por fase

| Gate | Fase | Veredictos posibles |
|---|---|---|
| PROJECT DEFINITION REVIEW | 0A | PASS / PASS WITH CONDITIONS / FAIL |
| DATA READY | 0B | DATA READY / DATA PARTIAL / DATA BLOCKED |
| SYNTHETIC MODEL | 0C | todos los tests pasan / no |
| MADRID REAL DATA MVP | 0D | MVP operativo mínimo / no |
| BASELINE | 0E | VERIFIED / PARTIAL / PROXY / NO_BASELINE |
| GO/REPOSITION/KILL | 0F | BUILD / REPOSITION / KILL |

Estado de gates a 2026-08-27:

- 0A: `PASS WITH CONDITIONS`.
- 0B: `DATA PARTIAL`.
- 0C: `SYNTHETIC MODEL — PASS` técnico; señal científica
  `CONDITION_DEPENDENT / EARLY REPOSITION SIGNAL`.

Formato de cada gate (§40 brief): **Evidence · What passed · What failed ·
Missing evidence · Risks · Verdict**. Ante `FAIL`, no se continúa.

## 4. Tests de falsación baratos (ejecutar pronto, antes de construir de más)

1. **Cuello de botella** (A-01): descomponer TTFRP con rangos; si el tránsito es
   marginal, la tesis se debilita.
2. **Erosión meteorológica** (A-04): gate de viabilidad sobre meteo de días de
   fuego; si la cobertura colapsa, REPOSITION.
3. **Rendimientos decrecientes** (RQ6): si 2–3 docks capturan casi todo, revisar
   la narrativa de "red distribuida".
4. **Alternativa más barata**: comparar dock vs cámara/torre fija por sitio.

## 5. Red-team obligatorio (§23 brief)

Tras cada fase relevante, revisión adversarial documentada (aunque el resultado
sea negativo). Preguntas guía en `docs/adr/` y `SAFETY_CASE.md`.

## 6. Registro de evidencia

Cada corrida de validación guarda: configuración, seeds, versión de datos,
outputs regenerables. **Evidence** (datos), **Interpretation** (lectura) y
**Decision** (veredicto) se registran por separado, nunca fusionados.

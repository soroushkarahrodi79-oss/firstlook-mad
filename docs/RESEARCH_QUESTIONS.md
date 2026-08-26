# RESEARCH QUESTIONS — FIRSTLOOK-MAD

> **Fase:** evidencia sintética añadida en 0C · **Versión:** 0.2.0 · **Fecha:** 2026-08-27

Preguntas de investigación formales. Cada una tiene: enunciado, por qué importa,
cómo se mediría, y su **test de falsación más barato**. Ninguna respuesta se
asume; todas se investigan.

---

## RQ1 — Cobertura ponderada por riesgo
**¿Qué porcentaje del *riesgo relevante* de incendio forestal puede cubrirse
dentro de determinados tiempos de respuesta (5/10/15 min)?**

- No se optimiza superficie territorial, sino **risk-weighted coverage**.
- Métrica: `Σ(risk_i · reachable_i) / Σ(risk_i)` para cada umbral de tiempo.
- Falsación barata: si con buffers optimistas (Modelo A) la cobertura ponderada
  ya es baja, empeorará con restricciones reales.

## RQ2 — Reutilización de infraestructura
**¿Puede reutilizarse infraestructura pública existente para localizar
hipotéticos Drone Docks?**

- Candidatos *conceptuales*: parques de bomberos, bases forestales,
  helisuperficies, instalaciones de vigilancia, otras infraestructuras públicas.
- **Ninguna** se asume disponible; todas son `candidate_site` con
  `assumed_available` explícito.
- Falsación barata: cuantificar cuántos sitios candidatos son realmente
  verificables en 0B; si son muy pocos, la premisa se debilita.

## RQ3 — Valor temporal (TTFRP)
**¿Cuál sería el TTFRP estimado por incidente desde distintas configuraciones de
red?**

- Métrica: distribución de TTFRP (mediana, p90) por configuración de N docks.
- Falsación barata: **test del cuello de botella** — si `T_alert_processing +
  T_verification` domina, el tránsito importa poco y la tesis se debilita.

## RQ4 — Valor incremental sobre baseline
**¿Cuánto mejora FIRSTLOOK-MAD frente a un baseline realista?**

- Requiere un baseline defendible (ver `VALIDATION_PLAN.md`, Phase 0E).
- Sin baseline verificable, la comparación se declara `PROXY` o `NO_BASELINE`.

## RQ5 — Resiliencia
**¿Qué ocurre bajo condiciones adversas?**

Viento fuerte · mala visibilidad · temperatura extrema · dock fuera de servicio ·
batería insuficiente · comunicación degradada · geozona restrictiva · NOTAM ·
aeronaves tripuladas · incidente mal localizado · múltiples incidentes simultáneos.

- Falsación barata: **test de erosión meteorológica** — aplicar un gate de
  viabilidad a la meteo de días de fuego (calor, sequedad, viento). Si la
  cobertura alcanzable colapsa justo esos días, el valor se evapora → REPOSITION.

## RQ6 — Coste marginal / rendimientos decrecientes
**¿Cuánto valor adicional aporta pasar de 1 → 2 → 3 → 5 → 10 → N puntos?**

- Métrica: *marginal coverage gain* por dock añadido.
- Falsación barata: si 2–3 docks capturan casi toda la cobertura ponderada, la
  narrativa de "red distribuida" está sobrevendida (puede seguir siendo un valor,
  pero menor).

---

## Pregunta transversal (comparación con alternativas)
FIRSTLOOK-MAD no se evalúa en aislamiento. Se compara conceptualmente con: cámaras
fijas, torres de vigilancia, satélite, movilización terrestre, drones desplegados
manualmente, unidades móviles de drones, docks fijos, e **híbridos**. Un resultado
donde un híbrido gana **no es un fracaso** (ver `PRODUCT_CONTRACT.md §6`).

## Estado tras Phase 0C

| Pregunta | Evidencia 0C | Estado |
|---|---|---|
| RQ1 | Cobertura A→F sintética, sin threshold empírico | `TESTING` |
| RQ2 | Solo sitios sintéticos; factibilidad real sigue parcial | `TESTING` |
| RQ3 | Distribuciones TTFRP asumidas y test de cuello de botella | `CONDITION_DEPENDENT` |
| RQ4 | Sin baseline TTFRP público | `BLOCKED` |
| RQ5 | Dos escenarios adversariales erosionan a cero | `TESTING` |
| RQ6 | No hay saturación temprana, pero cobertura F sigue baja | `TESTING` |

La cámara proxy domina bajo sus supuestos; es una señal para estudiar
`REPOSITION`, no una respuesta concluyente a la comparación transversal.

# CONCEPT OF OPERATIONS (CONOPS) — FIRSTLOOK-MAD

> **Estado:** `RESEARCH / SIMULATION PROTOTYPE ONLY` · **Fase:** 0A · **v0.1.0**
> **Aviso:** este CONOPS describe un concepto *simulado*. No refleja ni implica
> ninguna operación real, autorización, ni capacidad desplegada.

---

## 1. Propósito

Describir, a nivel conceptual, la cadena que el simulador modela — y, sobre todo,
**dónde termina el sistema** y empieza el juicio humano.

## 2. Actores (conceptuales, simulados)

| Actor | Rol en el modelo | Real en Phase 0? |
|---|---|---|
| Fuente de alerta | Genera un `Incident` (histórico o sintético) | No — simulado |
| Verificación | Estima confianza / localización | No — parámetro simulado |
| Flight Safety Gate | Decisión determinista GO_SIMULATION / NO_GO / ... | Sí (lógica), pero sin efecto físico |
| Red de docks | Conjunto de `CandidateDockSite` | No — hipotéticos |
| UAS | `UASPerformanceProfile` (no un modelo concreto) | No — perfil paramétrico |
| Decisor humano | **Fuera del sistema**, siempre | N/A |

## 3. Cadena operativa modelada

```
ALERTA ──▶ VERIFICACIÓN ──▶ FLIGHT SAFETY GATE ──▶ SELECCIÓN DE PUNTO
   │            │                   │                      │
 T_alert    T_verif           (GO_SIM / NO_GO         T_launch
 _proc                          / UNKNOWN /
                                REQUIRES_HUMAN)
                                                            ▼
                                     TRÁNSITO UAS ──▶ FIRST LOOK ──▶ SITREP
                                        T_travel      T_scene_acq   T_first_analysis
```

Desde `SITREP` en adelante (**APOYO A LA DECISIÓN → RESPUESTA HUMANA**) el sistema
solo produce *evidencia y sugerencias*; **no** decide ni actúa.

## 4. Descomposición del KPI (TTFRP)

```
TTFRP = T_alert_processing + T_verification + T_preflight_gate + T_launch
      + T_travel + T_scene_acquisition + T_first_analysis
```

En Phase 0 varios componentes son **parámetros simulados**; nunca se oculta su
naturaleza. Cada valor lleva etiqueta de calidad: `OBSERVED / OFFICIAL / DERIVED /
ASSUMED / SIMULATED / ESTIMATED / MISSING`.

## 5. Estados de decisión del Flight Safety Gate

`GO_SIMULATION` · `NO_GO` · `UNKNOWN` · `REQUIRES_HUMAN_REVIEW`.

Regla **first failure wins**: un solo factor crítico en `UNKNOWN`/`RESTRICTED`
degrada la salida a `REQUIRES_HUMAN_REVIEW` o `NO_GO`, sin importar el resto.
`UNKNOWN` **nunca** se convierte automáticamente en `GO_SIMULATION`.

## 6. Lo que el operador humano ve (concepto de futura UI)

Separación visual permanente entre:
- **Observación** — lo que realmente sabemos.
- **Derivación** — lo calculado de forma determinista.
- **Estimación** — lo inferido con incertidumbre.
- **Recomendación** — sugerencia de apoyo, marcada como no-oficial.

Ninguna recomendación se presenta como decisión oficial.

## 7. Frontera del sistema (resumen)

Entra: alertas simuladas, GIS, riesgo, restricciones, perfiles UAS, meteo.
Sale: métricas (TTFRP, coberturas), decisiones de gate simuladas, comparaciones de
red, *situation reports* simulados. **Nunca** sale: una orden de vuelo, un
despacho de recursos, una decisión oficial. Ver `SYSTEM_BOUNDARIES.md`.

# SAFETY CASE — FIRSTLOOK-MAD

> **Fase:** 0A · **v0.1.0** · **Clasificación actual:** `RESEARCH / SIMULATION
> PROTOTYPE ONLY` — **NO** operacional, **NO** certificado, **NO** autorizado.

Este documento se crea desde el inicio (§26 brief) porque el sistema es
*safety-adjacent*: modela decisiones que, en un futuro hipotético y bajo otro
régimen, tendrían consecuencias de seguridad. Tratamos esa adyacencia con rigor
aunque hoy no exista efecto físico.

---

## 1. Clasificación y afirmaciones prohibidas

Distinguimos tres cosas y hoy somos solo la primera:
1. **Software research prototype / simulation** ← *estamos aquí*.
2. Simulación validada.
3. Sistema operacional.

**No** se usan los términos `certified`, `operationally safe`, `authorised`,
`emergency ready` sin evidencia. No los hay hoy.

## 2. Peligros de un sistema como este (aunque simulado) y mitigaciones

| Peligro | Descripción | Mitigación de diseño |
|---|---|---|
| **Automation bias** | Que un humano trate una recomendación como decisión | Separación dura Recommendation ≠ Decision; recomendaciones marcadas no-oficiales |
| **Falsa autorización** | Confundir "zona libre" con "vuelo autorizado" | Enum sin `SAFE_TO_FLY`; estados explícitos; `data_freshness` en el gate |
| **Bypass de gate** | Que un factor crítico se agregue y se pierda | First-failure-wins; sin scores que oculten restricciones; razones de exclusión guardadas |
| **Cobertura ilusoria** | Confundir buffer geométrico con capacidad | Modelos A→F que exponen simplificaciones |
| **Dato caduco** | NOTAM/meteo tratados como permanentes | Frescura obligatoria; caché con fecha |
| **Alcance no autorizado** | Que el repo active hardware | Sin ruta física; solo adapters mock (`SYSTEM_BOUNDARIES.md`) |
| **Privacidad** | Identificación/seguimiento de personas | Prohibido; CV futura solo humo/fuego/perímetro; ver §4 |

## 3. Argumento de seguridad (claim → evidence)

- **Claim:** el prototipo no puede causar una acción física ni un despacho real.
  **Evidence:** no existen adapters operacionales; todos son mocks; ninguna
  dependencia de control de vuelo real (verificable en `pyproject.toml` y `src/`).
- **Claim:** ninguna recomendación se presenta como decisión oficial.
  **Evidence:** arquitectura `decision/` separa evidencia/valoración/recomendación;
  UI futura lo refleja (`CONOPS §6`).
- **Claim:** los gates no ocultan restricciones críticas.
  **Evidence:** regla first-failure-wins y tests dedicados (a implementar 0C).

## 4. Privacidad por diseño (data protection)

Principios activos desde 0A: data minimisation, purpose limitation, retención
mínima, control de acceso, audit trail, redaction, privacy-by-design. **Prohibido**:
reconocimiento facial, identificación o seguimiento de individuos. La eventual
computer vision se limita a humo, fuego, hotspots, perímetro, vegetación,
estructuras y obstáculos.

## 5. Trazabilidad

Toda decisión de gate simulada guarda entradas, factores y razones. Toda métrica
lleva etiqueta de calidad (`OBSERVED/OFFICIAL/DERIVED/ASSUMED/SIMULATED/ESTIMATED/
MISSING`). Provenance obligatoria para todo dato.

## 6. Revisión

Este safety case se revisa en cada gate de fase y tras cada red-team. Cambios de
clasificación (p. ej. de *prototype* a *validated simulation*) requieren un ADR.

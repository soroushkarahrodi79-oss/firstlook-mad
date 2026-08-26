# CONTRIBUTING — FIRSTLOOK-MAD

Gracias por contribuir a un proyecto de investigación reproducible y auditable.
Antes de nada, lee `docs/PRODUCT_CONTRACT.md`: sus fronteras son vinculantes.

## Principios no negociables

- **Nada operacional.** Sin control de UAS real, dispatch, ni integración con
  servicios de emergencia. Solo interfaces abstractas + mocks.
- **No alucinar.** Ubicaciones, cifras, regulación, costes, rangos desconocidos se
  marcan `UNKNOWN` / `ASSUMPTION` / `NOT_VERIFIED`. La evidencia oficial se
  distingue siempre de la inferencia.
- **Procedencia obligatoria** para todo dato (fuente, fecha, versión, licencia,
  CRS, naturaleza real/derivado/sintético).
- **Sin `SAFE_TO_FLY`.** Gates critican con *first-failure-wins*.
- **Separar** Evidence / Interpretation / Decision.

## Flujo de trabajo

1. Trabaja en una rama descriptiva.
2. Commits pequeños y lógicos. Convención: `docs:`, `feat:`, `fix:`, `test:`,
   `refactor:`, `chore:`, `research:`.
3. Antes de commit: revisa el diff, ejecuta tests relevantes, comprueba archivos
   accidentales y secretos.
4. **Sin force-push.** Sin mega-commits.
5. Actualiza `PROJECT_STATE.md` al final de cada bloque significativo.

## Calidad de código (cuando exista código, Phase 0C+)

- Type hints, funciones pequeñas, módulos cohesionados.
- Configuración fuera del código; constantes centralizadas.
- Errores explícitos; **nunca** `except Exception: pass`.
- Sin rutas absolutas, sin datos mágicos.
- Tests deterministas (seeds fijas). Prioriza la lógica crítica sobre el coverage.
- Lint/format con **Ruff**, type-check, y `pre-commit` antes de abrir PR.

## Gates de fase

No se salta de fase sin un **GATE REVIEW** (Evidence · What passed · What failed ·
Missing evidence · Risks · Verdict). Ante `FAIL`, no se continúa. Ver
`docs/VALIDATION_PLAN.md`.

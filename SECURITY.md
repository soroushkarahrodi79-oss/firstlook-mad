# SECURITY POLICY — FIRSTLOOK-MAD

> **Estado:** `RESEARCH / SIMULATION PROTOTYPE ONLY`. Este proyecto **no** es un
> sistema operacional, **no** está certificado y **no** debe usarse para decisiones
> reales de vuelo, despacho o emergencia.

## Alcance de seguridad

En Phase 0 el proyecto es una herramienta local de simulación sin superficie de
red, sin autenticación y sin datos personales. El foco de seguridad es:

1. **No cruzar la frontera operacional** (que el prototipo nunca active hardware
   ni servicios reales). Ver `docs/SYSTEM_BOUNDARIES.md` y `docs/SAFETY_CASE.md`.
2. **Integridad científica y de datos** (procedencia, no alucinación, no mezcla de
   histórico/sintético). Ver `docs/THREAT_MODEL.md`.
3. **No versionar secretos** ni datos de terceros sin licencia.

## Reporte de vulnerabilidades

Al ser un prototipo de investigación, para reportar un problema de seguridad, de
frontera de seguridad, o de integridad de datos, abre una *issue* marcada
`security` (o contacta al responsable del repositorio). No incluyas secretos ni
datos personales en el reporte.

## Prácticas obligatorias

- Sin credenciales en el repo; `.gitignore` cubre patrones comunes de secretos.
- Revisar el diff en busca de secretos antes de cada commit.
- Datos sensibles/grandes fuera del control de versiones.
- Sin reconocimiento facial ni identificación de personas (privacidad por diseño).

# THREAT MODEL — FIRSTLOOK-MAD

> **Fase:** 0A · **v0.1.0** · **Estado:** `RESEARCH / SIMULATION ONLY`

Modelo de amenazas de un prototipo de investigación. No hay superficie de red ni
datos personales en 0A; el foco son amenazas a la **integridad científica** y a la
**frontera de seguridad** (que el prototipo nunca cruce a lo operacional).

---

## 1. Amenazas de integridad (las más relevantes hoy)

| Amenaza | Vector | Mitigación |
|---|---|---|
| Hechos inventados como verdad | Alucinación regulatoria/geográfica | Regla anti-alucinación; `verification_status`; separación evidence/assumption |
| Baseline débil "de conveniencia" | Comparar contra un baseline flojo para forzar BUILD | Baseline defendible obligatorio (0E); estados VERIFIED/PARTIAL/PROXY/NO |
| Threshold-hacking | Ajustar umbrales tras ver resultados | Thresholds pre-registrados; desviaciones vía ADR |
| Cobertura geométrica vendida como operacional | Buffers bonitos | Modelos A→F que exponen simplificaciones |
| Datos caducos como permanentes | NOTAM/meteo | Frescura obligatoria; caché fechada |
| Mezcla histórico/sintético | Escenarios sin marcar | Etiquetado obligatorio; nunca mezclar sin indicar |

## 2. Amenazas a la frontera de seguridad

| Amenaza | Mitigación |
|---|---|
| Que el repo adquiera capacidad de activar hardware | Sin adapters operacionales; solo mocks; sin deps de control de vuelo |
| Bypass silencioso del safety gate | First-failure-wins; sin scores agregados que oculten críticos |
| Recomendación presentada como decisión oficial | Separación dura Recommendation ≠ Decision |

## 3. Amenazas de datos/privacidad (relevantes al crecer)

| Amenaza | Mitigación |
|---|---|
| Identificación/seguimiento de personas | Prohibido por diseño; CV futura solo humo/fuego/perímetro |
| Fuga de secretos en el repo | `.gitignore`; revisión de secretos antes de commit; sin credenciales versionadas |
| Datos de terceros sin licencia | Provenance con licencia obligatoria; datos grandes no versionados |

## 4. Fuera de modelo en 0A

Amenazas de red, autenticación, multiusuario, despliegue cloud: no aplican
todavía (sistema local, sin servicios). Se revisará este modelo si el alcance
cambia.

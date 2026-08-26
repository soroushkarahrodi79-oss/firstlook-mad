# REGULATORY BOUNDARIES — FIRSTLOOK-MAD

> **Fase:** 0B cerrada · **v0.2.0** · **Estado:** `RESEARCH / SIMULATION PROTOTYPE ONLY`
>
> **AVISO DE VERIFICACIÓN:** Phase 0B contrastó el marco y los endpoints listados
> abajo a fecha 2026-08-26. La vigencia debe revisarse de nuevo antes de cada fase
> posterior. Este documento **no** es asesoramiento jurídico ni operacional.

---

## 1. Principio rector

> Una zona **aparentemente libre** en un mapa **NO** implica autorización
> operacional. La aplicación **jamás** transforma "zona disponible" en "vuelo
> autorizado".

Estados de aeroespacio/permiso usados en el modelo (nunca `SAFE_TO_FLY`):

`UNKNOWN` · `POTENTIALLY_ALLOWED` · `RESTRICTED` · `REQUIRES_AUTHORIZATION` ·
`TEMPORARILY_RESTRICTED` · `NOT_EVALUATED`.

## 2. Marco a contemplar (nivel arquitectura)

El sistema debe poder representar, como mínimo:

- Categorías de operación UAS: **Open**, **Specific**, **Certified**.
- **BVLOS** (beyond visual line of sight).
- **SORA** vigente (metodología de evaluación de riesgo operacional).
- *Operational authorisation*.
- **UAS geographical zones** / zonificación.
- Restricciones **temporales** y **NOTAM**.
- Coordinación con **aeronaves tripuladas**.
- Operaciones de **emergencia** (regímenes especiales, si aplican).
- **Privacidad** y **protección de datos** (RGPD/LOPDGDD).
- **Trazabilidad**.

## 3. Autoridades y marcos de referencia

| Entidad / marco | Rol | verification_status |
|---|---|---|
| EASA — Reglamentos (UE) 2019/947 y 2019/945 | Marco UE de UAS | `OFFICIAL_SOURCE_VERIFIED` — Easy Access Rules, junio 2026 |
| Categorías Open / Specific / Certified | Clasificación operacional | `OFFICIAL_SOURCE_VERIFIED` |
| SORA 2.5 | Evaluación de riesgo en Specific | `OFFICIAL_SOURCE_VERIFIED` — paquete AMC/GM vigente consultado |
| AESA (España) | Autoridad aeronáutica nacional | `ROLE_VERIFIED`; condiciones concretas deben revisarse por operación |
| ENAIRE — zonificación UAS | Zonas geográficas UAS | `PROBED_AND_OFFICIAL_DOCUMENTATION_VERIFIED` — API V2 / ED-318 |
| ENAIRE — AIP / NOTAM | Información aeronáutica dinámica | `PROBED_PARTIAL_DOCUMENTATION`; Icaro XXI sigue siendo referencia recomendada |
| RGPD / LOPDGDD | Protección de datos | `REFERENCE_ONLY`; análisis jurídico específico diferido |
| BOE — RD 517/2024 | Zonas geográficas UAS en España | `OFFICIAL_SOURCE_VERIFIED` — texto consolidado consultado |

> Los límites numéricos no se transcriben para evitar convertir información
> dinámica en "verdad permanente". Las fuentes, fecha y versión quedan fijadas en
> `data/datasets_manifest.json` y `DATA_FEASIBILITY_REPORT.md`.

## 4. Consecuencias de diseño (vinculantes ya en 0A)

1. **No existe `SAFE_TO_FLY`** en ningún enum del código.
2. El **Flight Safety Gate** trata airspace/NOTAM/zona temporal como factores de
   **first-failure-wins**: `UNKNOWN` o `RESTRICTED` ⇒ nunca `GO_SIMULATION`.
3. El sistema **no** simula poseer permisos BVLOS.
4. Toda evaluación de zona produce uno de los estados de §1, con procedencia y
   fecha de la fuente. La **frescura del dato** (`data_freshness`) es un factor
   explícito del gate.
5. Emergencia ≠ permiso automático: no se codifica ninguna excepción de
   emergencia que relaje el gate sin revisión humana.

## 5. Privacidad como restricción regulatoria

Ver `SAFETY_CASE.md` y §25 del brief: data minimisation, purpose limitation,
retención, control de acceso, audit trail, redaction, privacidad por diseño.
La eventual visión por computador se limita a humo/fuego/hotspots/perímetro/
vegetación/estructuras/obstáculos — **nunca** identidad humana.

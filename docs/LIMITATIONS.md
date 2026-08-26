# LIMITATIONS — FIRSTLOOK-MAD

> **Fase:** 0A · **v0.1.0** · **Estado:** `RESEARCH / SIMULATION PROTOTYPE ONLY`

Limitaciones conocidas y declaradas. Publicarlas es parte de la integridad
científica del proyecto (§35 brief). Esta lista crece con cada fase.

---

## 1. Limitaciones de alcance

- Es un **prototipo de simulación**, no un sistema operacional. No vuela, no
  despacha, no se conecta a servicios reales.
- Phase 0 **no** aborda recomendación de recursos, computer vision, ni BVLOS real.

## 2. Limitaciones de datos (Phase 0A)

- **Ningún dato real verificado todavía.** Todo hecho regulatorio/geográfico está
  `NOT_VERIFIED` hasta 0B.
- Los datasets sintéticos de 0C son **ilustrativos**, no representativos de Madrid.

## 3. Limitaciones de modelado

- La cobertura por buffer geométrico (Modelo A) **no** representa capacidad
  operacional; los modelos superiores (B–F) reducen pero no eliminan la brecha.
- El TTFRP en 0C usa componentes simulados; su valor absoluto no es una predicción.
- La función de riesgo experimental **no** es "riesgo oficial" y depende de
  pesos revisables.
- La coordinación con aeronaves tripuladas y NOTAM se modela de forma conservadora
  y simplificada.

## 4. Limitaciones de comparación / baseline

- Sin baseline verificado, las mejoras se declaran contra un `PROXY_BASELINE` o
  `NO_BASELINE`, y no se afirma conocer el tiempo de respuesta real de Madrid.

## 5. Limitaciones de generalización

- Resultados válidos solo para el marco de supuestos declarado; sensibilidad alta
  a supuestos = baja generalización (se cuantifica en sensitivity analysis).

## 6. Limitaciones de reproducibilidad

- Reproducible con datos sintéticos y fixtures. La reproducción con datos reales
  depende de la disponibilidad/licencia de terceros, fuera de nuestro control.

## 7. Lo que estas limitaciones implican

Ningún output del proyecto debe leerse como recomendación operacional,
certificación, ni afirmación sobre capacidades reales de INFOMA, 112 o cualquier
organismo. Ver `PRODUCT_CONTRACT.md §2` y `SAFETY_CASE.md`.

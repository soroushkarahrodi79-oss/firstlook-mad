# LIMITATIONS — FIRSTLOOK-MAD

> **Fase:** 0C cerrada · **v0.3.0** · **Estado:** `RESEARCH / SIMULATION PROTOTYPE ONLY`

Limitaciones conocidas y declaradas. Publicarlas es parte de la integridad
científica del proyecto (§35 brief). Esta lista crece con cada fase.

---

## 1. Limitaciones de alcance

- Es un **prototipo de simulación**, no un sistema operacional. No vuela, no
  despacha, no se conecta a servicios reales.
- Phase 0 **no** aborda recomendación de recursos, computer vision, ni BVLOS real.

## 2. Limitaciones de datos (Phase 0B)

- El gate es `DATA PARTIAL`: existen fuentes verificadas, pero no un baseline
  público TTFRP extremo a extremo.
- EGIF aporta primera respuesta parcial, no clocks completos de alerta,
  verificación, gate, lanzamiento, adquisición y análisis.
- La infraestructura regional publicada son directorios/conteos, no una capa
  reutilizable de sitios aptos o autorizados para docks.
- AEMET requiere clave; ERA5-Land es reanálisis. Visibilidad histórica y ráfaga
  local siguen sin cubrirse de forma suficiente.
- El histórico completo EFFIS requiere solicitud y no es una dependencia
  reproducible hoy.
- Los datasets sintéticos de 0C son **ilustrativos**, no representativos de Madrid.

## 3. Limitaciones de modelado

- La cobertura por buffer geométrico (Modelo A) **no** representa capacidad
  operacional; los modelos superiores (B–F) reducen pero no eliminan la brecha.
- El TTFRP en 0C usa componentes simulados; su valor absoluto no es una predicción.
- La función de riesgo experimental **no** es "riesgo oficial" y depende de
  pesos revisables.
- La coordinación con aeronaves tripuladas y NOTAM se modela de forma conservadora
  y simplificada.
- Los 180 incidentes y 10 sitios de 0C son uniformes/sintéticos; no representan
  la distribución territorial ni operativa de Madrid.
- Los tres perfiles UAS, cadenas TTFRP, escenarios meteo y proxy de cámara son
  `ASSUMED`, no calibrados.
- La selección greedy optimiza cobertura geométrica A; no garantiza optimalidad
  bajo F.
- Las medianas A→F pueden cambiar por selección del subconjunto superviviente y
  no deben compararse sin su cobertura asociada.
- No se modelan líneas de visión, humo, calidad equivalente de imagen, costes,
  colas ni incidentes simultáneos.

## 4. Limitaciones de comparación / baseline

- Existe `PARTIAL_OPERATIONAL_RESPONSE_BASELINE`, pero también
  `NO_PUBLIC_TTFRP_BASELINE`. Las mejoras se declaran contra un
  `PROXY_BASELINE`; no se afirma conocer el TTFRP real de Madrid.

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

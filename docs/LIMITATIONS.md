# LIMITATIONS — FIRSTLOOK-MAD

> **Fase:** 0D — `FAIL (BLOCKED: EXECUTION ENVIRONMENT EGRESS)` · **v0.4.0** ·
> **Estado:** `RESEARCH / SIMULATION PROTOTYPE ONLY`

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

## 7. Limitaciones de Phase 0D — bloqueador de entorno de ejecución

- Phase 0D (2026-08-31) intentó adquisición acotada de datos reales contra las
  7 fuentes ya validadas como accesibles en 0B más 7 extractos adicionales
  pequeños. **Las 7 fallaron el 100% de las veces**, bloqueadas por la
  política de salida de red del entorno de ejecución de esta sesión de
  agente (`Tunnel connection failed: 403 Forbidden` en el proxy, antes de
  alcanzar el servidor de destino), verificado con dos herramientas
  independientes y con un dominio de control no registrado en el proyecto
  (confirmando que el bloqueo es general, no específico de estas fuentes).
- Esta es una limitación del **entorno de ejecución concreto**, no una
  evidencia de que Madrid carezca de datos públicos accesibles — Phase 0B ya
  demostró 7/7 fuentes técnicamente accesibles el 2026-08-26. No debe leerse
  como "los datos de Madrid no están disponibles".
- En consecuencia, ningún supuesto A-01 a A-04 cambió de estado en 0D; todos
  permanecen exactamente donde 0C.1 los dejó (ver `docs/ASSUMPTIONS.md`
  §"Evidencia incorporada en 0D").
- **Acción humana mínima requerida** para reintentar con posibilidad real de
  éxito (una de las siguientes):
  1. Ejecutar `scripts/acquire_phase0d_sources.py` desde un entorno cuya
     política de salida de red permita el acceso a: `servais.enaire.es`,
     `opendata.aemet.es`, `maps.effis.emergency.copernicus.eu`,
     `api-features.idee.es`, `overpass-api.de`, `datos.madrid.es`,
     `servicio.mapa.gob.es` y, si se retoma A-04 con reanálisis,
     `cds.climate.copernicus.eu`.
  2. Alternativamente, que un humano descargue manualmente los extractos ya
     especificados en `data/phase0d_source_probes.json` y los deposite en
     `data/raw/<fuente>/` con procedencia completa, para que el trabajo de
     normalización (0D.2, aún sin escribir) pueda ejecutarse sobre datos
     reales genuinos.
  3. Para AEMET específicamente, además del acceso de red, se requiere una
     clave de API gratuita registrada por un humano (bloqueador ya
     identificado en Phase 0B, sin cambios).
  4. Para el histórico completo de EFFIS, sigue pendiente la solicitud humana
     ya identificada en Phase 0B (`BLOCKED`, sin cambios).
- Detalle técnico completo:
  `PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md` §5 y §15.

### 7.1 Transición de estado — adquisición local acotada (2026-09-07)

- El bloqueo de egress de 2026-08-31 **permanece** como resultado histórico
  válido de aquel entorno; esta subsección lo **complementa**, no lo sustituye.
- Una repetición local posterior (Windows, Python 3.12.10, red permitida) sí
  obtuvo bytes reales acotados con TLS verificado y procedencia SHA-256. Subgate
  de adquisición: **`0D.1 REAL INPUT AVAILABLE`** (al menos un supuesto
  prioritario —A-02— con insumo real utilizable). Insumo por supuesto: A-02
  `USABLE_REAL_INPUT`; A-01/A-03/A-04 `PARTIAL_REAL_INPUT` (siguen incompletos:
  sin baseline TTFRP para A-01, sin observaciones meteo para A-04, sin capas
  completas para A-03).
- **Límite vinculante:** `0D.1 REAL INPUT AVAILABLE` es un gate de *adquisición*.
  **No** es Phase 0D `PASS`, `SUPPORTED`, `MADRID VALIDATED`, `BUILD` ni
  `SAFE_TO_FLY`; no cambia ningún supuesto de estado, no ejecuta 0D.2 y no
  autoriza Phase 0E. La evidencia cruda sigue gitignored; solo se publica
  procedencia payload-free. Ver `PHASE_0D_REAL_DATA_FALSIFICATION_REPORT.md`
  §17 y `docs/PHASE_0D_PROTOCOL.md` §7.3.

## 8. Lo que estas limitaciones implican

Ningún output del proyecto debe leerse como recomendación operacional,
certificación, ni afirmación sobre capacidades reales de INFOMA, 112 o cualquier
organismo. Ver `PRODUCT_CONTRACT.md §2` y `SAFETY_CASE.md`.

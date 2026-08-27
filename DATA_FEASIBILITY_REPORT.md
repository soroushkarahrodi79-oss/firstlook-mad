# DATA FEASIBILITY REPORT — FIRSTLOOK-MAD

> **Fase:** 0B · **Fecha de corte:** 2026-08-26  
> **Uso:** `RESEARCH / SIMULATION PROTOTYPE ONLY` · **Veredicto:** `DATA PARTIAL`

## 1. Executive Verdict

Hay datos suficientes para construir en Phase 0C un **modelo sintético de
sensibilidad y falsación**, con procedencia y proxies explícitos. No hay datos
públicos suficientes para afirmar que una red UAS mejora el desempeño real de
Madrid, estimar un TTFRP extremo a extremo, elegir sitios desplegables ni
automatizar una decisión de vuelo.

El gate es **DATA PARTIAL**, no `DATA READY`: geozonas, topografía, cobertura del
suelo y cartografía base son utilizables; meteo, histórico de incendios,
infraestructura candidata y exposición requieren adquisición/normalización
posterior; el baseline TTFRP y los datos históricos completos de EFFIS están
bloqueados o no son públicos. Una zona aparentemente libre **no** equivale a
autorización.

## 2. Evidence Summary

- Se catalogaron 19 fuentes en
  [`data/datasets_manifest.json`](data/datasets_manifest.json), con versión,
  licencia, CRS, cobertura, campos, limitaciones y trazabilidad.
- Siete probes HTTPS acotados confirmaron accesibilidad de metadatos de ENAIRE
  UAS, ENAIRE NOTAM, AEMET, EFFIS, IGN y EGIF. El resultado incluye status,
  tamaño, hash y resumen de schema en
  [`outputs/reports/source_probe_results.json`](outputs/reports/source_probe_results.json).
- No se descargaron datasets masivos ni se escribieron datos en `data/raw/`.
- La evidencia normativa se contrastó con fuentes oficiales vigentes a la fecha
  de corte; no constituye asesoramiento jurídico ni autorización operacional.

## 3. Source-by-Source Assessment

| Fuente | Estado | Hallazgo útil | Restricción decisiva |
|---|---|---|---|
| [ENAIRE zonas UAS V2](https://aip.enaire.es/AIP/UAS-es.html) | `READY` | REST/WFS/WMS y ED-318; geometría y restricciones | Solo investigación; frescura AIRAC; no autoriza vuelo |
| [ENAIRE NOTAM](https://aip.enaire.es/aip/contenido_AIP/GEN/LE_GEN_3_1_es.html) | `PARTIAL` | FeatureServer dinámico con tiempos, Q-code y geometría | Servicio marcado `PRE`; Icaro XXI es la referencia recomendada; sin histórico reproducible |
| [RD 517/2024](https://www.boe.es/eli/es/rd/2024/06/04/517/con) | `REFERENCE_ONLY` | Marco español de zonas UAS y restricciones temporales | Norma, no dato analítico ni permiso |
| [EASA Easy Access Rules UAS](https://www.easa.europa.eu/en/document-library/easy-access-rules/easy-access-rules-unmanned-aircraft-systems) | `REFERENCE_ONLY` | 2019/947, 2019/945 y paquete SORA 2.5 vigente | No presume autorización BVLOS/Specific |
| [AEMET OpenData](https://opendata.aemet.es/dist/) | `PARTIAL` | API documentada; climatología diaria y estaciones | Requiere clave; payload no muestreado; visibilidad histórica y ráfagas locales no cubiertas |
| [ERA5-Land](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land) | `PARTIAL` | Reanálisis horario 1950-presente, CC-BY-4.0 | No es observación; resolución insuficiente para micro-meteo; sin visibilidad verificada |
| [MITECO EGIF](https://www.miteco.gob.es/es/biodiversidad/temas/incendios-forestales/estadisticas-datos.html) | `PARTIAL` | Partes consolidados con detección y primeras llegadas de medios | Exportación web/XML, no API documentada; sin “first reliable picture”; consolidación desigual |
| [EFFIS current](https://forest-fire.emergency.copernicus.eu/applications/data-and-services) | `PARTIAL` | WMS, áreas quemadas y fuegos activos | Detección satelital ≠ inicio/alerta; sesgo por sensor/tamaño; no TTFRP |
| [EFFIS historical extracts](https://forest-fire.emergency.copernicus.eu/downloads-instructions) | `BLOCKED` | Podría aportar histórico armonizado | Requiere formulario y revisión humana; schema/licencia efectiva no verificables sin entrega |
| [Directorio regional de parques](https://www.comunidad.madrid/buscador?f%5B0%5D=search_api_aggregation_1%3AJusticia&f%5B1%5D=field_tags%3A19655&f%5B2%5D=mns_field_center_types%3A%22Protecci%C3%B3n+Ciudadana%22&f%5B3%5D=mns_field_center_types%3A%22Parque+de+Bomberos%22) | `PARTIAL` | Nombres y direcciones oficiales de 29 registros del buscador | HTML, sin API/bulk ni contrato de coordenadas/licencia |
| [Inventario INFOMA 2026](https://www.comunidad.madrid/noticias/2026/06/12/comunidad-madrid-supera-527-millones-euros-prevencion-lucha-incendios-forestales-35-2025) | `REFERENCE_ONLY` | Contexto: parques, brigadas, torres, cámaras, helisuperficies, helicópteros y drones | Conteos, no capa geoespacial ni disponibilidad operacional |
| [Parques de bomberos Madrid ciudad](https://datos.madrid.es/dataset/211642-0-bomberos-parques) | `READY` | Descargas pequeñas, geográficas y CC-BY-4.0 | Solo municipio y 13 parques; no representa red regional ni aptitud para docks |
| [OpenStreetMap fire stations](https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dfire_station) | `PARTIAL` | Suplemento geográfico programático | No autoritativo; cobertura variable; obligaciones ODbL |
| [IGN MDT05](https://centrodedescargas.cnig.es/CentroDescargas/modelo-digital-terreno-mdt05-primera-cobertura) | `READY` | COG 5 m, ETRS89/UTM y licencia compatible CC-BY-4.0 | Descarga por hojas; antigüedad de adquisición variable |
| [SIOSE AR 2020](https://centrodedescargas.cnig.es/CentroDescargas/siose) | `PARTIAL` | Ocupación de suelo oficial de alta resolución | Volumen/schema complejos; **no es modelo de combustible** |
| [CORINE Land Cover 2018](https://land.copernicus.eu/en/products/corine-land-cover/clc2018) | `READY` | Proxy estable, 44 clases, AOI disponible | 25 ha/100 m y año 2018; **no es modelo de combustible** |
| [IGN redes de transporte](https://servicios.idee.es/wfs-inspire/transportes) | `READY` | WFS/OGC oficial, consultas por área | El schema/capa exacta debe fijarse; red vial ≠ tiempo UAS |
| [INE Censo 2021 API](https://www.ine.es/Censo2021/api) | `PARTIAL` | Estadística oficial consultable por POST | Privacidad limita detalle; selección de tablas y geografía pendiente |
| [Memorias ASEM 112](https://www.comunidad.madrid/transparencia/memorias-agencia-seguridad-y-emergencias-madrid-112) | `REFERENCE_ONLY` | Contexto y agregados 2018–2024 | PDFs grandes; sin cadena TTFRP a nivel incidente |

Los términos de reutilización de [EFFIS](https://forest-fire.emergency.copernicus.eu/about-effis/data-license)
son CC-BY-4.0 salvo avisos de terceros. Cada distribución conserva su licencia
propia; la licencia Apache-2.0 del código no se extiende a datos de terceros.

## 4. Critical Datasets

1. **Geozonas UAS ENAIRE:** `READY` para intersectar escenarios de investigación.
2. **EGIF:** `PARTIAL` y crítico para incidentes/primeras llegadas; requiere una
   extracción controlada antes de afirmar cobertura temporal o espacial.
3. **AEMET + ERA5-Land:** `PARTIAL`; combinación plausible para erosionar
   disponibilidad, nunca para certificar condiciones de vuelo.
4. **Sitios regionales:** `PARTIAL`; hay direcciones y conteos, no aptitud,
   permiso, energía, conectividad ni helisuperficie utilizable.
5. **Baseline TTFRP extremo a extremo:** `BLOCKED` por ausencia de clocks
   públicos de alerta, verificación, gate, lanzamiento y primera imagen fiable.

## 5. Blocked/Missing

- `NO_PUBLIC_TTFRP_BASELINE`: no se halló un dataset público incidente-a-incidente
  con todos los componentes de TTFRP.
- `NO_PUBLIC_REGIONAL_SITE_LAYER`: no se halló una capa oficial y reutilizable de
  parques/torres/cámaras/helisuperficies INFOMA con coordenadas y estado.
- Histórico EFFIS completo: requiere solicitud humana; no puede ser dependencia
  reproducible en el estado actual.
- Histórico horario de visibilidad y ráfaga local: no verificado en AEMET/ERA5-Land.
- Perfil operacional UAS: autonomía, viento, lanzamiento y adquisición no se han
  aportado ni verificado; cualquier perfil de 0C será un rango `ASSUMED`.

No se usa `NO_PUBLIC_OPERATIONAL_BASELINE`: EGIF sí ofrece un **baseline parcial
de primera respuesta**. Lo correcto es `PARTIAL_OPERATIONAL_RESPONSE_BASELINE` y,
separadamente, `NO_PUBLIC_TTFRP_BASELINE`.

## 6. Assumption Coverage

| Supuesto | Cobertura de 0B | Estado al cierre | Lectura |
|---|---|---|---|
| A-01 tránsito material | Débil | `TESTING` | No hay clocks para probar qué componente domina; es el supuesto más debilitado |
| A-02 sitios reutilizables | Parcial | `TESTING` | Hay candidatos de investigación, no sitios desplegables |
| A-03 buffers pobres | Datos suficientes | `OPEN` | MDT/geozonas permiten probarlo en 0C, pero aún no se ejecutó |
| A-04 meteo no anula valor | Parcial | `TESTING` | Se puede simular erosión; falta perfil UAS y visibilidad histórica |
| A-05 capas separadas | Datos suficientes | `OPEN` | Capas de terreno/cobertura/exposición existen; hipótesis aún no probada |
| A-06 perfiles UAS plausibles | Ausente | `OPEN` | No hay perfil validado; usar rangos etiquetados |
| A-07 baseline defendible | Parcial | `TESTING` | EGIF aporta primera respuesta, no TTFRP |
| A-08 coordinación modelable | Parcial | `TESTING` | Restricciones públicas existen; coordinación real no es pública |
| A-09 CRS proyectado | Datos suficientes | `OPEN` | CRS de fuentes conocido; error no medido aún |
| A-10 incertidumbre de localización | Ausente | `OPEN` | No se encontró distribución defendible |

## 7. Research Question Coverage

| RQ | Datos disponibles tras 0B | Estado |
|---|---|---|
| RQ1 — dónde puede reducir tiempo | Incendios, terreno, cobertura, exposición y geozonas con grados distintos | `PARTIAL` |
| RQ2 — ubicaciones candidatas | Parques oficiales parciales + ciudad + OSM, sin aptitud | `PARTIAL` |
| RQ3 — ganancia vs complejidad | Inputs espaciales sí; clocks y perfiles no | `PARTIAL` |
| RQ4 — comparación con baseline | EGIF primera llegada, sin TTFRP extremo a extremo | `PARTIAL` |
| RQ5 — degradación por restricciones/meteo | Geozonas robustas; NOTAM/meteo parciales | `PARTIAL` |
| RQ6 — valor por coste/nodos | Conteos/contexto de red actual, sin costes comparables | `UNKNOWN` |

## 8. TTFRP Observability

| Componente | Observable en operación | Público hoy | Proxy defendible | Simulable | Incertidumbre/dominancia |
|---|---|---|---|---|---|
| `T_alert_processing` | Sí | No | EGIF registra detección, no todos los clocks | Sí | Alta; puede dominar |
| `T_verification` | Sí | No | Fuente/circunstancia de detección, muy débil | Sí | Alta; puede dominar |
| `T_preflight_gate` | Sí, en sistema futuro | Inputs parciales | ENAIRE/AEMET/NOTAM | Sí | Alta; autorización y coordinación no observadas |
| `T_launch` | Sí, en sistema futuro | No | Ninguno adquirido | Sí | Media-alta; depende de automatización |
| `T_travel` | Derivable | Geografía sí | Perfiles UAS asumidos | Sí | Controlable en modelo, relevancia total desconocida |
| `T_scene_acquisition` | Sí, en sistema futuro | No | Ninguno robusto | Sí | Media; definición de imagen fiable pendiente |
| `T_first_analysis` | Sí, en sistema futuro | No | Ninguno robusto | Sí | Potencialmente alta por proceso humano |

Conclusión: 0C puede probar condiciones bajo las que `T_travel` importaría, pero
no puede concluir que sea material en Madrid.

## 9. Baseline Feasibility

EGIF permite construir un baseline parcial de tiempos hasta primera llegada de
medios terrestres/aéreos y estudiar cobertura de incidentes, sujeto a validar la
extracción. No representa el primer dato visual fiable ni separa la cadena de
alerta/verificación. La memoria oficial de bomberos de 2015 aporta solo contexto
histórico agregado, no un umbral actual. Por tanto, 0C debe comparar contra un
`PROXY_BASELINE` parametrizado y publicar sensibilidad, nunca “mejora real”.

## 10. Weather-Erosion Feasibility

Es factible unir fecha/localización EGIF con AEMET diaria y ERA5-Land horaria para
construir escenarios meteorológicos. La inferencia sigue siendo parcial porque
la operación depende de ráfagas locales, visibilidad, precipitación, humo,
relieve y un envelope UAS aún no especificado. El modelo debe declarar
missingness, usar varios umbrales asumidos y reportar fracción erosionada por
variable, no un booleano universal de “volable”.

## 11. Candidate-Site Feasibility

Puede construirse un conjunto de candidatos **para experimento** mediante el
directorio regional, la capa municipal y OSM reconciliado. No puede llamarse red
desplegable: faltan coordenadas oficiales regionales en bulk, propiedad/permiso,
obstáculos, potencia, comunicaciones, mantenimiento, seguridad, separación de
aeronaves y disponibilidad. A-02 permanece `TESTING`.

## 12. Regulatory Data Feasibility

Las zonas ENAIRE son técnicamente accesibles y las restricciones temporales se
representan en el marco nacional. NOTAM es dinámico y requiere comprobación de
frescura; el propio servicio público no reemplaza la fuente operacional
recomendada. SORA/Specific/BVLOS y coordinación con aeronaves tripuladas no se
resuelven mediante una intersección GIS. El gate conservará estados conservadores
y nunca emitirá `SAFE_TO_FLY`.

## 13. Provenance/Licensing Risks

- ENAIRE exige atribución y excluye uso operacional del servicio investigado.
- AEMET requiere clave y conservar términos/metadata de cada producto.
- OSM puede activar obligaciones ODbL sobre bases derivadas.
- SIOSE/IGN, Copernicus y el Ayuntamiento permiten reutilización con atribución,
  pero no deben mezclarse sin un ledger de licencias.
- Directorios HTML, PDFs regionales y entregas bajo solicitud no tienen aún un
  contrato de redistribución suficientemente fijado.
- Datos dinámicos deben registrar fecha de consulta, versión/hash y frescura.

## 14. Cheaper Alternative Feasibility

INFOMA 2026 ya declara torres, cámaras y un grupo especial de drones. Eso obliga
a dar a un diseño híbrido cámara fija + UAS la misma prioridad experimental que
una red de docks. No hay datos públicos comparables de rendimiento/coste para
probar que sea más barato o mejor; 0C solo podrá explorar dominios de parámetros,
no coronar una alternativa.

## 15. What We Can Build in Phase 0C

- Generador sintético de incidentes y candidatos con CRS explícito.
- Modelos A→F de cobertura/tiempo con perfiles UAS asumidos y sensibilidad.
- Intersección de geozonas ENAIRE sobre escenarios no operacionales.
- Erosión meteorológica por escenarios, no por predicción certificada.
- Comparación UAS/docks vs cámaras/híbrido mediante rangos transparentes.
- Gate de falsación: identificar cuándo `T_travel` deja de ser relevante.

## 16. What Cannot Be Claimed

- Que Madrid necesita una red UAS o que esta mejora tiempos reales.
- Que un sitio candidato acepta o puede alojar un dock.
- Que una zona es segura/autorizada, que existe permiso BVLOS o que un NOTAM está
  operacionalmente resuelto.
- Que los proxies de cobertura del suelo son combustible o riesgo oficial.
- Que la simulación predice disponibilidad, coste, TTFRP o impacto real.

## 17. Red-Team Findings

1. **Dato que debería existir y no apareció:** capa regional machine-readable de
   activos INFOMA y logs end-to-end de alerta→primera imagen.
2. **Supuesto más debilitado:** A-01; no hay evidencia de que `T_travel` sea
   material frente a alerta, verificación, autorización, lanzamiento y análisis.
3. **Alternativa más barata:** la infraestructura existente de torres/cámaras y
   drones merece rama híbrida prioritaria; los datos de coste no permiten decidir.
4. **Baseline completo:** no es construible con fuentes públicas; el parcial de
   EGIF no debe maquillarse como TTFRP.
5. **Regulación como kill:** una red fija puede quedar teórica si BVLOS/Specific,
   coordinación o restricciones dinámicas dominan; no se asume excepción.
6. **Existencia de 0C:** sí, solo como modelo sintético de sensibilidad y
   falsación, no como modelo predictivo de Madrid.
7. **Kill test fuerte:** si en rangos plausibles verificación/preflight domina, o
   meteo/geozonas eliminan el ahorro de viaje y no existe vía de validación, se
   debe matar o reposicionar la tesis.

## 18. Gate Review — DATA FEASIBILITY

| Criterio | Evidencia | Resultado |
|---|---|---|
| Fuentes críticas identificadas y trazables | Manifest de 19 entradas | `PASS` |
| Accesibilidad/schema probados a bajo coste | 7/7 probes HTTPS correctos | `PASS` |
| Licencia/procedencia registradas | Completa por entrada, con `UNKNOWN` explícitos | `PASS WITH RISKS` |
| Baseline defendible | EGIF parcial; TTFRP no público | `PARTIAL` |
| Meteo para erosión | AEMET/ERA5 accesibles pero incompletos | `PARTIAL` |
| Sitios candidatos | Suficientes para simulación, no despliegue | `PARTIAL` |
| Restricciones regulatorias representables | Geozonas listas; NOTAM/coordinación parciales | `PARTIAL` |
| Riesgo de falsa certeza controlado | Claims prohibidos y provenance gates explícitos | `PASS` |

**Veredicto final: `DATA PARTIAL`.** Phase 0C está justificada únicamente bajo
las condiciones de §15–16. No se recomienda adquirir datos masivos ni avanzar a
un MVP real antes de falsar A-01 y contrastar la alternativa híbrida.


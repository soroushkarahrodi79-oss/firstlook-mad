"""Fabricated Phase 0D.2 test fixtures.

Every value in this module is synthetic test data shaped like the real sources.
Nothing here is Madrid evidence, and nothing here is read from data/raw.
"""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any

FIRE_URL = "https://datos.madrid.es/egob/catalogo/211642-0-bomberos-parques.json"
MDT05_URL = (
    "https://servicios.idee.es/wcs-inspire/mdt?service=WCS&version=2.0.1&request=GetCoverage"
    "&coverageId=Elevacion25830_5&subset=x(440000,440100)&subset=y(4474000,4474100)"
    "&format=image/tiff"
)
AEMET_WRAPPER_URL = (
    "https://opendata.aemet.es/opendata/api/valores/climatologicos/"
    "inventarioestaciones/todasestaciones"
)
AEMET_DATOS_URL = "https://opendata.aemet.es/opendata/sh/fixture00"
EGIF_URL = "https://servicio.mapa.gob.es/incendios/Search/Publico"
ACQUIRED_AT = "2026-09-06T17:38:00+00:00"
PAYLOAD_SENTINEL = "PAYLOAD-SENTINEL-DO-NOT-LEAK"
TIFF_STRIP_OFFSETS_TAG = 273
TIFF_SHORT_FIELD_TYPE = 3
AEMET_WRAPPER = {
    "descripcion": "exito",
    "estado": 200,
    "datos": AEMET_DATOS_URL,
    "metadatos": "https://opendata.aemet.es/opendata/sh/fixture01",
}


def write_artifact(
    root: Path,
    *,
    probe_id: str,
    payload: bytes,
    assumption: str,
    classification: str,
    source_url: str,
    content_type: str | None,
    artifact_name: str = "20260906.raw",
    ledger_sha256: str | None = None,
    truncated: bool = False,
    write_raw: bool = True,
    write_sidecar: bool = True,
) -> tuple[Path, Path]:
    """Write raw bytes, their sidecar and a payload-free ledger entry; return (ledger, raw)."""

    raw_dir, ledger_dir = root / "raw", root / "ledger"
    digest = hashlib.sha256(payload).hexdigest()
    common = {
        "probe_id": probe_id,
        "source_url": source_url,
        "acquired_at_utc": ACQUIRED_AT,
        "http_status": 200,
        "content_type": content_type,
        "byte_count": len(payload),
        "sha256": digest,
        "truncated": truncated,
        "evidence_nature": "REAL",
        "local_raw_path": f"data/raw/phase0d/{probe_id}/{artifact_name}",
    }
    probe_raw = raw_dir / probe_id
    probe_raw.mkdir(parents=True, exist_ok=True)
    if write_raw:
        (probe_raw / artifact_name).write_bytes(payload)
    if write_sidecar:
        sidecar = probe_raw / f"{artifact_name}.provenance.json"
        sidecar.write_text(json.dumps(common), encoding="utf-8")
    entry = {
        "schema_version": "1.0",
        **common,
        "sha256": ledger_sha256 or digest,
        "assumption": assumption,
        "evidence_classification": classification,
    }
    probe_ledger = ledger_dir / probe_id
    probe_ledger.mkdir(parents=True, exist_ok=True)
    ledger_name = artifact_name.replace(".raw", ".provenance.json")
    (probe_ledger / ledger_name).write_text(json.dumps(entry), encoding="utf-8")
    return ledger_dir, raw_dir


# --- A-02 ---------------------------------------------------------------------------------


def fire_station_record(identifier: Any, title: Any, latitude: Any, longitude: Any) -> Any:
    return {
        "@id": f"https://datos.madrid.es/fixture/{identifier}.json",
        "id": identifier,
        "title": title,
        "address": {"locality": "MADRID", "street-address": f"CALLE {PAYLOAD_SENTINEL} 1"},
        "location": {"latitude": latitude, "longitude": longitude},
        "organization": {"organization-desc": f"api_key={PAYLOAD_SENTINEL}"},
    }


def default_fire_station_records() -> list[Any]:
    return [
        fire_station_record("900003", "Fixture Park C", 40.41, -3.70),
        fire_station_record("900001", "Fixture Park A", 40.45, -3.69),
        fire_station_record("900002", "Fixture Park B", 40.39, -3.65),
    ]


def fire_station_payload(records: list[Any]) -> bytes:
    return json.dumps({"@context": {}, "@graph": records}, ensure_ascii=False).encode("utf-8")


# --- A-03 ---------------------------------------------------------------------------------


def enaire_url(envelope: str = "-4.0,40.25,-3.4,40.65", cap: int | None = 50) -> str:
    url = (
        "https://servais.enaire.es/insigniads/rest/services/NSF_SRV/SRV_UAS_ZG_data_V2/"
        f"FeatureServer/2/query?f=geojson&where=1%3D1&outFields=*&geometry={envelope}"
        "&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects"
    )
    return url + (f"&resultRecordCount={cap}" if cap is not None else "")


def _square(lon: float, lat: float, size: float = 0.01) -> list[Any]:
    return [
        [[lon, lat], [lon + size, lat], [lon + size, lat + size], [lon, lat + size], [lon, lat]]
    ]


def _bowtie(lon: float, lat: float, size: float = 0.01) -> list[Any]:
    return [
        [[lon, lat], [lon + size, lat + size], [lon + size, lat], [lon, lat + size], [lon, lat]]
    ]


def enaire_payload(
    feature_count: int = 3,
    *,
    exceeded: bool = False,
    invalid_first: bool = False,
    extra: dict[str, Any] | None = None,
) -> bytes:
    features = []
    for index in range(feature_count):
        lon = -3.9 + 0.05 * index
        rings = _bowtie(lon, 40.3) if invalid_first and index == 0 else _square(lon, 40.3)
        features.append(
            {
                "type": "Feature",
                "id": 100 + index,
                "geometry": {"type": "Polygon", "coordinates": rings},
                "properties": {
                    "identifier": f"FIX{index}",
                    "name": f"Fixture zone {index}",
                    "type": "PROHIBITED",
                    "lower": 0,
                    "lowerReference": "AGL",
                    "upper": 120,
                    "upperReference": "AGL",
                    "uom": "M",
                    "message": PAYLOAD_SENTINEL,
                },
            }
        )
    payload: dict[str, Any] = {"type": "FeatureCollection", "features": features}
    if exceeded:
        payload["exceededTransferLimit"] = True
        payload["properties"] = {"exceededTransferLimit": True}
    payload.update(extra or {})
    return json.dumps(payload).encode("utf-8")


def geotiff_bytes(
    *,
    width: int = 20,
    height: int = 20,
    origin_x: float = 440000.0,
    origin_y: float = 4474100.0,
    scale: float = 5.0,
    epsg: int | None = 25830,
    compression: int = 1,
    values: list[int] | None = None,
    nodata: str | None = None,
) -> bytes:
    """Minimal little-endian, uncompressed, int16 single-band GeoTIFF."""

    samples = values if values is not None else [648 + index % 7 for index in range(width * height)]
    pixels = struct.pack(f"<{width * height}h", *samples)
    geokeys = [1, 1, 0, 1, 1025, 0, 1, 1]
    if epsg is not None:
        geokeys = [1, 1, 0, 2, 1025, 0, 1, 1, 3072, 0, 1, epsg]
    external: list[tuple[int, int, int, bytes]] = [
        (33550, 12, 3, struct.pack("<3d", scale, scale, 0.0)),
        (33922, 12, 6, struct.pack("<6d", 0.0, 0.0, 0.0, origin_x, origin_y, 0.0)),
        (34735, 3, len(geokeys), struct.pack(f"<{len(geokeys)}H", *geokeys)),
    ]
    if nodata is not None:
        text = nodata.encode("ascii") + b"\x00"  # callers use >4 bytes: stored out of line
        external.append((42113, 2, len(text), text))
    inline = [
        (256, 3, width),
        (257, 3, height),
        (258, 3, 16),
        (259, 3, compression),
        (273, 4, -1),
        (277, 3, 1),
        (279, 4, len(pixels)),
        (339, 3, 2),
    ]
    entry_count = len(inline) + len(external)
    data_offset = 8 + 2 + entry_count * 12 + 4
    blobs = b""
    entries: list[tuple[int, bytes]] = []
    for tag, field_type, count, blob in external:
        entries.append(
            (tag, struct.pack("<HHII", tag, field_type, count, data_offset + len(blobs)))
        )
        blobs += blob
    pixel_offset = data_offset + len(blobs)
    for tag, field_type, value in inline:
        stored = pixel_offset if tag == TIFF_STRIP_OFFSETS_TAG else value
        packed = (
            struct.pack("<HH", stored, 0)
            if field_type == TIFF_SHORT_FIELD_TYPE
            else struct.pack("<I", stored)
        )
        entries.append((tag, struct.pack("<HHI", tag, field_type, 1) + packed))
    entries.sort()
    ifd = struct.pack("<H", entry_count) + b"".join(entry for _, entry in entries)
    return b"II*\x00" + struct.pack("<I", 8) + ifd + struct.pack("<I", 0) + blobs + pixels


# --- A-04 ---------------------------------------------------------------------------------


def aemet_station(
    identifier: str,
    name: str,
    province: str,
    *,
    latitude: str = "402400N",
    longitude: str = "034100W",
    altitude: str = "667",
) -> dict[str, str]:
    return {
        "indicativo": identifier,
        "nombre": name,
        "provincia": province,
        "latitud": latitude,
        "longitud": longitude,
        "altitud": altitude,
        "indsinop": "",
    }


def default_aemet_stations() -> list[dict[str, str]]:
    return [
        aemet_station(
            "F001X",
            "FIXTURE ESTACIÓN NORTE",
            "MADRID",
            latitude="404736N",
            longitude="040039W",
            altitude="1892",
        ),
        aemet_station("F002X", "FIXTURE ESTACIÓN SUR", "MADRID"),
        aemet_station(
            "F900B",
            "FIXTURE COSTA",
            "BARCELONA",
            latitude="412300N",
            longitude="021000E",
            altitude="12",
        ),
    ]


def aemet_inventory_payload(stations: list[dict[str, str]]) -> bytes:
    return json.dumps(stations, ensure_ascii=False).encode("iso-8859-15")


# --- Whole 0D.1-shaped evidence tree ---------------------------------------------------------


def build_evidence_tree(root: Path, *, fire_records: list[Any] | None = None) -> tuple[Path, Path]:
    """Fixture ledger + raw tree shaped like Phase 0D.1; returns (ledger_dir, raw_dir)."""

    specs: list[dict[str, Any]] = [
        {
            "probe_id": "egif_public_search_madrid",
            "payload": b"<html><form>fixture search form: deteccion llegada</form></html>",
            "assumption": "A-01",
            "classification": "REAL_METADATA",
            "source_url": EGIF_URL,
            "content_type": "text/html; charset=utf-8",
        },
        {
            "probe_id": "egif_provincia_lookup_madrid",
            "payload": b'[{"Selected":false,"Text":"MADRID","Value":"28"}]',
            "assumption": "A-01",
            "classification": "REAL_METADATA",
            "source_url": EGIF_URL + "/fixture-lookup",
            "content_type": "application/json; charset=utf-8",
        },
        {
            "probe_id": "madrid_city_open_data_fire_stations",
            "payload": fire_station_payload(
                fire_records if fire_records is not None else default_fire_station_records()
            ),
            "assumption": "A-02",
            "classification": "REAL_SOURCE_DATA",
            "source_url": FIRE_URL,
            "content_type": "application/json",
        },
        {
            "probe_id": "enaire_uas_zones_madrid_bbox",
            "payload": enaire_payload(3, exceeded=True),
            "assumption": "A-03",
            "classification": "REAL_BOUNDED_SAMPLE",
            "source_url": enaire_url(),
            "content_type": "application/geo+json; charset=UTF-8",
        },
        {
            "probe_id": "ign_mdt05_getcoverage_madrid_sample",
            "artifact_name": "20260907.raw",
            "payload": geotiff_bytes(),
            "assumption": "A-03",
            "classification": "REAL_SOURCE_DATA",
            "source_url": MDT05_URL,
            "content_type": "image/tiff",
        },
        {
            "probe_id": "ign_wcs_mdt_describe_5m",
            "payload": b"<wcs:CoverageDescriptions>fixture</wcs:CoverageDescriptions>",
            "assumption": "A-03",
            "classification": "REAL_METADATA",
            "source_url": "https://servicios.idee.es/wcs-inspire/mdt?request=DescribeCoverage",
            "content_type": "text/xml",
        },
        {
            "probe_id": "aemet_madrid_station_inventory",
            "payload": json.dumps(AEMET_WRAPPER).encode("iso-8859-15"),
            "assumption": "A-04",
            "classification": "REAL_WRAPPER",
            "source_url": AEMET_WRAPPER_URL,
            "content_type": "application/json;charset=ISO-8859-15",
        },
        {
            "probe_id": "aemet_madrid_station_inventory_datos",
            "payload": b'{\n  "descripcion" : "datos expirados",\n  "estado" : 404\n}',
            "assumption": "A-04",
            "classification": "NOT_USABLE_FOR_TARGET_TEST",
            "source_url": AEMET_DATOS_URL,
            "content_type": "application/json;charset=ISO-8859-15",
        },
        {
            "probe_id": "aemet_madrid_station_inventory_datos",
            "artifact_name": "20260906T191152Z.raw",
            "payload": aemet_inventory_payload(default_aemet_stations()),
            "assumption": "A-04",
            "classification": "REAL_SOURCE_DATA",
            "source_url": AEMET_DATOS_URL,
            "content_type": "text/plain;charset=ISO-8859-15",
        },
    ]
    for spec in specs:
        write_artifact(root, **spec)
    return root / "ledger", root / "raw"

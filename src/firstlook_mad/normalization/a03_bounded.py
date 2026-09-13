"""A-03: bounded ENAIRE airspace and IGN MDT05 terrain evidence, with scope preserved.

A bounded sample is never promoted to a full Madrid layer. Every canonical A-03
representation carries explicit scope metadata, and ``BoundedEvidenceScope``
refuses by construction any combination that would make bounded, truncated or
incomplete evidence eligible for full-Madrid analysis. Raster statistics are
labelled ``sample_window_only`` and never extrapolated.
"""

from __future__ import annotations

import math
import re
import struct
from collections import Counter
from enum import StrEnum
from typing import Literal, TypeGuard
from urllib.parse import parse_qs, urlparse

from pydantic import JsonValue, model_validator
from pyproj import Transformer
from shapely.errors import ShapelyError
from shapely.geometry import shape

from firstlook_mad.domain import ANALYTICAL_CRS, FrozenModel
from firstlook_mad.normalization.crs import COORDINATE_DECIMALS, project_lon_lat
from firstlook_mad.normalization.evidence import ArtifactEvidence, decode_json_payload
from firstlook_mad.normalization.models import (
    ANALYTICAL_EPSG_CODE,
    COMUNIDAD_MADRID_ENVELOPE,
    GEOGRAPHIC_CRS,
    MAX_ABS_LATITUDE,
    MAX_ABS_LONGITUDE,
    NORMALIZATION_VERSION,
    Completeness,
    Eligibility,
    Envelope,
    Integrity,
    MalformedEvidenceError,
    StructuralValidity,
    UnsupportedRasterLayoutError,
    is_json_number,
    non_blank_text,
    permits_substitution,
)
from firstlook_mad.normalization.serialization import canonical_json_bytes, sha256_hex

ENAIRE_PROBE_ID = "enaire_uas_zones_madrid_bbox"
MDT05_PROBE_ID = "ign_mdt05_getcoverage_madrid_sample"
ENAIRE_CRS_BASIS = "interpreted: RFC 7946 GeoJSON coordinates are lon/lat (EPSG:4326)"
ENAIRE_USAGE_NOTICE = (
    "ENAIRE AIS data: attribution required; never for operational use. Bounded research "
    "sample, possibly truncated by the service; not a complete Madrid geozone layer."
)
MDT05_DECLARED_PURPOSE = "chain reproducibility proof (docs/PHASE_0D_PROTOCOL.md section 7.3)"
EXTENT_TOLERANCE_M = 1e-6

_ENVELOPE_PARTS = 4
_MIN_POSITION_LENGTH = 2
_POLYGON_TYPES = frozenset({"Polygon", "MultiPolygon"})
_SUBSET_PATTERN = re.compile(r"^(x|y)\((-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)\)$")


class EvidenceScope(StrEnum):
    REQUEST_ENVELOPE_SUBSET_OF_DOMAIN = "REQUEST_ENVELOPE_SUBSET_OF_ANALYTICAL_DOMAIN"
    REQUEST_ENVELOPE_COVERS_DOMAIN = "REQUEST_ENVELOPE_COVERS_ANALYTICAL_DOMAIN"
    FIXED_WINDOW_PIPELINE_SAMPLE = "FIXED_WINDOW_PIPELINE_REPRODUCIBILITY_SAMPLE"


class BoundedEvidenceScope(FrozenModel):
    source_probe_id: str
    source_sha256: str
    acquisition_timestamp_utc: str
    evidence_scope: EvidenceScope
    coverage_extent: Envelope
    crs: str
    crs_basis: str
    source_resolution: str
    bounded_sample: bool
    completeness: Completeness
    eligible_for_full_madrid_analysis: bool
    eligible_for_pipeline_verification: bool
    analytical_eligibility: Eligibility

    @model_validator(mode="after")
    def forbid_extrapolation(self) -> BoundedEvidenceScope:
        domain_complete = self.completeness is Completeness.COMPLETE_FOR_ANALYTICAL_DOMAIN
        if self.eligible_for_full_madrid_analysis and (self.bounded_sample or not domain_complete):
            raise ValueError(
                "bounded, truncated or incomplete evidence cannot be eligible for "
                "full-Madrid analysis"
            )
        if (
            self.analytical_eligibility is Eligibility.ELIGIBLE
            and not self.eligible_for_full_madrid_analysis
        ):
            raise ValueError("ELIGIBLE requires eligibility for full-Madrid analysis")
        if self.completeness is Completeness.TRUNCATED_BY_SOURCE and permits_substitution(
            self.analytical_eligibility
        ):
            raise ValueError("evidence truncated by its source cannot be eligible")
        return self


# --- ENAIRE UAS geozones ---------------------------------------------------------------


class CanonicalAirspaceZone(FrozenModel):
    source_object_id: int | str | None
    zone_identifier: str | None
    zone_name: str | None
    zone_type: str | None
    lower_limit: float | None
    lower_reference: str | None
    upper_limit: float | None
    upper_reference: str | None
    unit_of_measure: str | None
    geometry_type: str
    geometry_valid: bool
    geometry_coordinates_analytical: JsonValue


class CanonicalAirspaceSample(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    normalization_version: str = NORMALIZATION_VERSION
    scope: BoundedEvidenceScope
    source_url: str
    analytical_crs: str = ANALYTICAL_CRS
    usage_notice: str = ENAIRE_USAGE_NOTICE
    zones: tuple[CanonicalAirspaceZone, ...]


class AirspaceSampleAssessment(FrozenModel):
    scope: BoundedEvidenceScope
    request_envelope: Envelope
    feature_count: int
    geometry_type_counts: dict[str, int]
    invalid_geometry_count: int
    duplicate_object_id_count: int
    exceeded_transfer_limit: bool
    result_record_count_cap: int | None
    structural_validity: StructuralValidity
    canonical_sha256: str


def parse_esri_query_request(source_url: str) -> tuple[Envelope, int | None]:
    """Envelope and record cap exactly as requested in the committed source URL."""

    query = parse_qs(urlparse(source_url).query)
    geometry = query.get("geometry", [])
    if len(geometry) != 1 or query.get("inSR") != ["4326"]:
        raise MalformedEvidenceError("ENAIRE request URL lacks a single EPSG:4326 envelope")
    parts = geometry[0].split(",")
    cap_values = query.get("resultRecordCount", [])
    try:
        if len(parts) != _ENVELOPE_PARTS:
            raise ValueError("expected four envelope values")
        min_x, min_y, max_x, max_y = (float(part) for part in parts)
        envelope = Envelope(crs=GEOGRAPHIC_CRS, min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)
        cap = int(cap_values[0]) if cap_values else None
    except ValueError as exc:
        raise MalformedEvidenceError(
            f"ENAIRE request URL has an invalid envelope or record cap ({exc})"
        ) from exc
    return envelope, cap


def normalize_airspace_sample(
    raw: bytes, *, source: ArtifactEvidence, transformer: Transformer
) -> tuple[AirspaceSampleAssessment, CanonicalAirspaceSample]:
    request_envelope, cap = parse_esri_query_request(source.source_url)
    payload = decode_json_payload(raw, content_type=source.content_type, where=source.ref)
    collection, features = _feature_collection(payload, source.ref)
    zones = tuple(
        sorted((_canonical_zone(feature, transformer) for feature in features), key=_zone_key)
    )
    exceeded = _exceeded_transfer_limit(collection)
    truncated = exceeded or (cap is not None and len(features) >= cap)
    covers_domain = request_envelope.covers(COMUNIDAD_MADRID_ENVELOPE)
    invalid = sum(1 for zone in zones if not zone.geometry_valid)
    validity = StructuralValidity.VALID if invalid == 0 else StructuralValidity.VALID_WITH_FLAGS
    if truncated:
        completeness = Completeness.TRUNCATED_BY_SOURCE
    elif covers_domain:
        completeness = Completeness.COMPLETE_FOR_ANALYTICAL_DOMAIN
    else:
        completeness = Completeness.COMPLETE_FOR_DECLARED_SCOPE
    eligibility = _airspace_eligibility(source.integrity, validity, completeness)

    scope = BoundedEvidenceScope(
        source_probe_id=source.probe_id,
        source_sha256=source.sha256,
        acquisition_timestamp_utc=source.acquired_at_utc,
        evidence_scope=(
            EvidenceScope.REQUEST_ENVELOPE_COVERS_DOMAIN
            if covers_domain
            else EvidenceScope.REQUEST_ENVELOPE_SUBSET_OF_DOMAIN
        ),
        coverage_extent=request_envelope,
        crs=GEOGRAPHIC_CRS,
        crs_basis=ENAIRE_CRS_BASIS,
        source_resolution="vector polygons (no raster resolution)",
        bounded_sample=not covers_domain,
        completeness=completeness,
        eligible_for_full_madrid_analysis=eligibility is Eligibility.ELIGIBLE,
        eligible_for_pipeline_verification=source.integrity is Integrity.PASS,
        analytical_eligibility=eligibility,
    )
    sample = CanonicalAirspaceSample(scope=scope, source_url=source.source_url, zones=zones)
    object_ids = Counter(
        zone.source_object_id for zone in zones if zone.source_object_id is not None
    )
    assessment = AirspaceSampleAssessment(
        scope=scope,
        request_envelope=request_envelope,
        feature_count=len(features),
        geometry_type_counts=dict(sorted(Counter(zone.geometry_type for zone in zones).items())),
        invalid_geometry_count=invalid,
        duplicate_object_id_count=sum(1 for count in object_ids.values() if count > 1),
        exceeded_transfer_limit=exceeded,
        result_record_count_cap=cap,
        structural_validity=validity,
        canonical_sha256=sha256_hex(canonical_json_bytes(sample)),
    )
    return assessment, sample


def _airspace_eligibility(
    integrity: Integrity, validity: StructuralValidity, completeness: Completeness
) -> Eligibility:
    if (
        integrity is not Integrity.PASS
        or validity is not StructuralValidity.VALID
        or completeness is Completeness.TRUNCATED_BY_SOURCE
    ):
        return Eligibility.NOT_ELIGIBLE
    if completeness is Completeness.COMPLETE_FOR_ANALYTICAL_DOMAIN:
        return Eligibility.ELIGIBLE
    return Eligibility.ELIGIBLE_WITHIN_DECLARED_SCOPE


def _feature_collection(payload: object, where: str) -> tuple[dict[str, object], list[object]]:
    features = payload.get("features") if isinstance(payload, dict) else None
    if (
        not isinstance(payload, dict)
        or payload.get("type") != "FeatureCollection"
        or not isinstance(features, list)
    ):
        raise MalformedEvidenceError(f"{where}: expected a GeoJSON FeatureCollection")
    if "crs" in payload:
        raise MalformedEvidenceError(
            f"{where}: declares a non-RFC 7946 crs member; not interpreted"
        )
    feature_list: list[object] = list(features)
    return payload, feature_list


def _exceeded_transfer_limit(collection: dict[str, object]) -> bool:
    properties = collection.get("properties")
    nested = isinstance(properties, dict) and properties.get("exceededTransferLimit") is True
    return collection.get("exceededTransferLimit") is True or nested


def _is_position(value: object) -> TypeGuard[list[int | float]]:
    return (
        isinstance(value, list)
        and len(value) >= _MIN_POSITION_LENGTH
        and all(is_json_number(component) for component in value)
    )


def _finite_lon_lat_positions(coordinates: object) -> bool:
    if _is_position(coordinates):
        lon, lat = float(coordinates[0]), float(coordinates[1])
        return (
            math.isfinite(lon)
            and math.isfinite(lat)
            and abs(lon) <= MAX_ABS_LONGITUDE
            and abs(lat) <= MAX_ABS_LATITUDE
        )
    return (
        isinstance(coordinates, list)
        and bool(coordinates)
        and all(_finite_lon_lat_positions(item) for item in coordinates)
    )


def _project_coordinates(coordinates: object, transformer: Transformer) -> JsonValue:
    if _is_position(coordinates):
        easting, northing = project_lon_lat(
            transformer, float(coordinates[0]), float(coordinates[1])
        )
        position: list[JsonValue] = [
            round(easting, COORDINATE_DECIMALS),
            round(northing, COORDINATE_DECIMALS),
        ]
        return position
    if isinstance(coordinates, list):
        return [_project_coordinates(item, transformer) for item in coordinates]
    return None


def _geometry_is_valid(geometry: dict[str, object]) -> bool:
    """OGC validity of the source geometry; invalid geometries are never repaired."""

    try:
        return bool(shape(geometry).is_valid)
    except (ValueError, TypeError, AttributeError, ShapelyError):
        return False


def _optional_number(properties: dict[str, object], key: str) -> float | None:
    value = properties.get(key)
    return float(value) if is_json_number(value) and math.isfinite(float(value)) else None


def _canonical_zone(feature: object, transformer: Transformer) -> CanonicalAirspaceZone:
    item: dict[str, object] = feature if isinstance(feature, dict) else {}
    raw_geometry, raw_properties = item.get("geometry"), item.get("properties")
    geometry: dict[str, object] = raw_geometry if isinstance(raw_geometry, dict) else {}
    properties: dict[str, object] = raw_properties if isinstance(raw_properties, dict) else {}
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    well_formed = geometry_type in _POLYGON_TYPES and _finite_lon_lat_positions(coordinates)
    object_id = item.get("id")
    return CanonicalAirspaceZone(
        source_object_id=(
            object_id
            if isinstance(object_id, int | str) and not isinstance(object_id, bool)
            else None
        ),
        zone_identifier=non_blank_text(properties.get("identifier")),
        zone_name=non_blank_text(properties.get("name")),
        zone_type=non_blank_text(properties.get("type")),
        lower_limit=_optional_number(properties, "lower"),
        lower_reference=non_blank_text(properties.get("lowerReference")),
        upper_limit=_optional_number(properties, "upper"),
        upper_reference=non_blank_text(properties.get("upperReference")),
        unit_of_measure=non_blank_text(properties.get("uom")),
        geometry_type=geometry_type if isinstance(geometry_type, str) else "MISSING",
        geometry_valid=well_formed and _geometry_is_valid(geometry),
        geometry_coordinates_analytical=(
            _project_coordinates(coordinates, transformer) if well_formed else None
        ),
    )


def _zone_key(zone: CanonicalAirspaceZone) -> tuple[int, int, str]:
    object_id = zone.source_object_id
    if isinstance(object_id, int):
        return (0, object_id, "")
    return (1, 0, object_id or "")


# --- IGN MDT05 GetCoverage sample -------------------------------------------------------

_TIFF_HEADER_LENGTH = 8
_TIFF_CLASSIC_MAGIC = 42
_TIFF_BIG_MAGIC = 43
_IFD_ENTRY_LENGTH = 12
_INLINE_VALUE_BYTES = 4
_ASCII_FIELD_TYPE = 2
_UNCOMPRESSED = 1
_MIN_PIXEL_SCALE_VALUES = 2
_TIEPOINT_VALUES = 6
# TIFF field type -> (struct code, bytes per component, components per value).
_FIELD_TYPES: dict[int, tuple[str, int, int]] = {
    1: ("B", 1, 1),
    2: ("s", 1, 1),
    3: ("H", 2, 1),
    4: ("I", 4, 1),
    5: ("I", 4, 2),
    6: ("b", 1, 1),
    7: ("B", 1, 1),
    8: ("h", 2, 1),
    9: ("i", 4, 1),
    10: ("i", 4, 2),
    11: ("f", 4, 1),
    12: ("d", 8, 1),
}
# (BitsPerSample, SampleFormat) -> struct code.
_SAMPLE_CODES: dict[tuple[int, int], str] = {
    (8, 1): "B",
    (8, 2): "b",
    (16, 1): "H",
    (16, 2): "h",
    (32, 1): "I",
    (32, 2): "i",
    (32, 3): "f",
    (64, 3): "d",
}
_TAG_WIDTH = 256
_TAG_HEIGHT = 257
_TAG_BITS_PER_SAMPLE = 258
_TAG_COMPRESSION = 259
_TAG_STRIP_OFFSETS = 273
_TAG_SAMPLES_PER_PIXEL = 277
_TAG_STRIP_BYTE_COUNTS = 279
_TAG_SAMPLE_FORMAT = 339
_TAG_PIXEL_SCALE = 33550
_TAG_TIEPOINT = 33922
_TAG_GEOKEY_DIRECTORY = 34735
_TAG_GDAL_NODATA = 42113
_GEOKEY_HEADER_LENGTH = 4
_GEOKEY_ENTRY_LENGTH = 4
_GEOKEY_RASTER_TYPE = 1025
_GEOKEY_PROJECTED_CRS = 3072
_RASTER_TYPES = {1: "PIXEL_IS_AREA", 2: "PIXEL_IS_POINT"}

TagValue = tuple[float, ...] | str


class GeoTiffSummary(FrozenModel):
    width: int
    height: int
    bits_per_sample: int
    sample_format: int
    compression: int
    pixel_scale_x: float
    pixel_scale_y: float
    extent: Envelope
    projected_crs_epsg: int | None
    raster_type: str | None
    nodata: str | None
    sample_window_value_count: int
    sample_window_min: float | None
    sample_window_max: float | None
    statistic_scope: Literal["sample_window_only"] = "sample_window_only"


class TerrainSampleAssessment(FrozenModel):
    scope: BoundedEvidenceScope
    raster: GeoTiffSummary
    requested_extent: Envelope
    extent_matches_request: bool
    declared_acquisition_purpose: str
    structural_validity: StructuralValidity


def parse_wcs_subset_request(source_url: str) -> Envelope:
    """Requested window from the committed WCS GetCoverage URL (native EPSG:25830)."""

    query = parse_qs(urlparse(source_url).query)
    coverage_ids = query.get("coverageId", [])
    if len(coverage_ids) != 1 or str(ANALYTICAL_EPSG_CODE) not in coverage_ids[0]:
        raise MalformedEvidenceError("WCS request does not name a single EPSG:25830 coverage")
    bounds: dict[str, tuple[float, float]] = {}
    for subset in query.get("subset", []):
        match = _SUBSET_PATTERN.match(subset)
        if match is None:
            raise MalformedEvidenceError(f"unrecognised WCS subset {subset!r}")
        bounds[match.group(1)] = (float(match.group(2)), float(match.group(3)))
    if set(bounds) != {"x", "y"}:
        raise MalformedEvidenceError("WCS request must subset both x and y")
    try:
        return Envelope(
            crs=ANALYTICAL_CRS,
            min_x=bounds["x"][0],
            max_x=bounds["x"][1],
            min_y=bounds["y"][0],
            max_y=bounds["y"][1],
        )
    except ValueError as exc:
        raise MalformedEvidenceError(f"WCS subset window is empty or reversed ({exc})") from exc


def parse_geotiff(data: bytes) -> GeoTiffSummary:
    """Read a small uncompressed single-band GeoTIFF with the standard library only."""

    order = _tiff_byte_order(data)
    tags = _read_first_ifd(data, order)
    compression = _int_tag(tags, _TAG_COMPRESSION, default=_UNCOMPRESSED)
    samples_per_pixel = _int_tag(tags, _TAG_SAMPLES_PER_PIXEL, default=1)
    if compression != _UNCOMPRESSED or samples_per_pixel != 1:
        raise UnsupportedRasterLayoutError(
            f"only uncompressed single-band rasters are decoded "
            f"(compression={compression}, samples_per_pixel={samples_per_pixel})"
        )
    width, height = _int_tag(tags, _TAG_WIDTH), _int_tag(tags, _TAG_HEIGHT)
    bits = _int_tag(tags, _TAG_BITS_PER_SAMPLE)
    sample_format = _int_tag(tags, _TAG_SAMPLE_FORMAT, default=1)
    code = _SAMPLE_CODES.get((bits, sample_format))
    if code is None:
        raise UnsupportedRasterLayoutError(f"unsupported sample type {bits}-bit/{sample_format}")

    nodata_value = tags.get(_TAG_GDAL_NODATA)
    nodata = non_blank_text(nodata_value)
    values = _exclude_nodata(
        _decode_samples(data, tags, order=order, code=code, count=width * height), nodata
    )
    scale = _numbers(tags, _TAG_PIXEL_SCALE, minimum=_MIN_PIXEL_SCALE_VALUES)
    tiepoint = _numbers(tags, _TAG_TIEPOINT, minimum=_TIEPOINT_VALUES)
    epsg, raster_type = _read_geokeys(tags.get(_TAG_GEOKEY_DIRECTORY))
    origin_x = tiepoint[3] - tiepoint[0] * scale[0]
    origin_y = tiepoint[4] + tiepoint[1] * scale[1]
    try:
        extent = Envelope(
            crs=f"EPSG:{epsg}" if epsg is not None else "UNDECLARED",
            min_x=origin_x,
            min_y=origin_y - height * scale[1],
            max_x=origin_x + width * scale[0],
            max_y=origin_y,
        )
    except ValueError as exc:
        raise MalformedEvidenceError(f"GeoTIFF georeferencing yields no extent ({exc})") from exc
    return GeoTiffSummary(
        width=width,
        height=height,
        bits_per_sample=bits,
        sample_format=sample_format,
        compression=compression,
        pixel_scale_x=scale[0],
        pixel_scale_y=scale[1],
        extent=extent,
        projected_crs_epsg=epsg,
        raster_type=raster_type,
        nodata=nodata,
        sample_window_value_count=len(values),
        sample_window_min=min(values) if values else None,
        sample_window_max=max(values) if values else None,
    )


def assess_terrain_sample(raw: bytes, *, source: ArtifactEvidence) -> TerrainSampleAssessment:
    requested = parse_wcs_subset_request(source.source_url)
    raster = parse_geotiff(raw)
    crs_declared = raster.projected_crs_epsg == ANALYTICAL_EPSG_CODE
    matches = crs_declared and _extents_match(raster.extent, requested)
    validity = StructuralValidity.VALID if matches else StructuralValidity.VALID_WITH_FLAGS
    scope = BoundedEvidenceScope(
        source_probe_id=source.probe_id,
        source_sha256=source.sha256,
        acquisition_timestamp_utc=source.acquired_at_utc,
        evidence_scope=EvidenceScope.FIXED_WINDOW_PIPELINE_SAMPLE,
        coverage_extent=requested,
        crs=ANALYTICAL_CRS if crs_declared else "UNDECLARED",
        crs_basis=(
            "declared by GeoTIFF ProjectedCSTypeGeoKey"
            if crs_declared
            else "not declared by the payload"
        ),
        source_resolution=f"{raster.pixel_scale_x:g} m x {raster.pixel_scale_y:g} m",
        bounded_sample=True,
        completeness=Completeness.BOUNDED_SAMPLE,
        eligible_for_full_madrid_analysis=False,
        eligible_for_pipeline_verification=source.integrity is Integrity.PASS and matches,
        # Declared acquisition purpose is a reproducibility proof, never a terrain layer.
        analytical_eligibility=Eligibility.NOT_ELIGIBLE,
    )
    return TerrainSampleAssessment(
        scope=scope,
        raster=raster,
        requested_extent=requested,
        extent_matches_request=matches,
        declared_acquisition_purpose=MDT05_DECLARED_PURPOSE,
        structural_validity=validity,
    )


def rollup_a03_eligibility(
    airspace: Eligibility | None, terrain: Eligibility | None
) -> Eligibility:
    components = [
        component if component is not None else Eligibility.NOT_ELIGIBLE
        for component in (airspace, terrain)
    ]
    if all(component is Eligibility.ELIGIBLE for component in components):
        return Eligibility.ELIGIBLE
    if any(permits_substitution(component) for component in components):
        return Eligibility.ELIGIBLE_WITHIN_DECLARED_SCOPE
    return Eligibility.NOT_ELIGIBLE


def _extents_match(actual: Envelope, requested: Envelope) -> bool:
    pairs = (
        (actual.min_x, requested.min_x),
        (actual.min_y, requested.min_y),
        (actual.max_x, requested.max_x),
        (actual.max_y, requested.max_y),
    )
    return actual.crs == requested.crs and all(
        abs(left - right) <= EXTENT_TOLERANCE_M for left, right in pairs
    )


def _tiff_byte_order(data: bytes) -> str:
    if len(data) < _TIFF_HEADER_LENGTH:
        raise MalformedEvidenceError("payload is too short for a TIFF header")
    order = {b"II": "<", b"MM": ">"}.get(data[:2])
    if order is None:
        raise MalformedEvidenceError("payload is not a TIFF (no byte-order mark)")
    (magic,) = struct.unpack_from(f"{order}H", data, 2)
    if magic == _TIFF_BIG_MAGIC:
        raise UnsupportedRasterLayoutError("BigTIFF is not decoded")
    if magic != _TIFF_CLASSIC_MAGIC:
        raise MalformedEvidenceError("payload is not a TIFF (bad magic number)")
    return order


def _read_first_ifd(data: bytes, order: str) -> dict[int, TagValue]:
    tags: dict[int, TagValue] = {}
    try:
        (ifd_offset,) = struct.unpack_from(f"{order}I", data, 4)
        (entry_count,) = struct.unpack_from(f"{order}H", data, ifd_offset)
        for index in range(entry_count):
            entry_offset = ifd_offset + 2 + index * _IFD_ENTRY_LENGTH
            tag, field_type, count = struct.unpack_from(f"{order}HHI", data, entry_offset)
            tags[tag] = _read_field(data, order, field_type, count, entry_offset + 8)
    except struct.error as exc:
        raise MalformedEvidenceError("TIFF directory extends past the end of the payload") from exc
    return tags


def _read_field(
    data: bytes, order: str, field_type: int, count: int, field_offset: int
) -> TagValue:
    if field_type not in _FIELD_TYPES:
        raise MalformedEvidenceError(f"unsupported TIFF field type {field_type}")
    code, size, components = _FIELD_TYPES[field_type]
    total = size * components * count
    start = field_offset
    if total > _INLINE_VALUE_BYTES:
        (start,) = struct.unpack_from(f"{order}I", data, field_offset)
    chunk = data[start : start + total]
    if len(chunk) != total:
        raise MalformedEvidenceError("TIFF field value extends past the end of the payload")
    if field_type == _ASCII_FIELD_TYPE:
        try:
            return chunk.rstrip(b"\x00").decode("ascii")
        except UnicodeDecodeError as exc:
            raise MalformedEvidenceError("TIFF ASCII field is not ASCII") from exc
    return tuple(
        float(value) for value in struct.unpack(f"{order}{count * components}{code}", chunk)
    )


def _numbers(tags: dict[int, TagValue], tag: int, *, minimum: int = 1) -> tuple[float, ...]:
    value = tags.get(tag)
    if not isinstance(value, tuple) or len(value) < minimum:
        raise MalformedEvidenceError(f"required numeric TIFF tag {tag} is missing or short")
    return value


def _int_tag(tags: dict[int, TagValue], tag: int, *, default: int | None = None) -> int:
    if tag not in tags and default is not None:
        return default
    return int(_numbers(tags, tag)[0])


def _decode_samples(
    data: bytes, tags: dict[int, TagValue], *, order: str, code: str, count: int
) -> tuple[float, ...]:
    offsets = _numbers(tags, _TAG_STRIP_OFFSETS)
    byte_counts = _numbers(tags, _TAG_STRIP_BYTE_COUNTS)
    if len(offsets) != len(byte_counts):
        raise MalformedEvidenceError("TIFF strip offsets and byte counts disagree")
    pixels = b"".join(
        data[int(offset) : int(offset) + int(length)]
        for offset, length in zip(offsets, byte_counts, strict=True)
    )
    if len(pixels) != count * struct.calcsize(f"{order}{code}"):
        raise MalformedEvidenceError("TIFF strips do not hold width x height samples")
    return tuple(float(value) for value in struct.unpack(f"{order}{count}{code}", pixels))


def _read_geokeys(directory: TagValue | None) -> tuple[int | None, str | None]:
    if not isinstance(directory, tuple) or len(directory) < _GEOKEY_HEADER_LENGTH:
        return None, None
    keys: dict[int, int] = {}
    for index in range(int(directory[3])):
        start = _GEOKEY_HEADER_LENGTH + index * _GEOKEY_ENTRY_LENGTH
        entry = directory[start : start + _GEOKEY_ENTRY_LENGTH]
        if len(entry) == _GEOKEY_ENTRY_LENGTH and int(entry[1]) == 0:
            keys[int(entry[0])] = int(entry[3])
    return keys.get(_GEOKEY_PROJECTED_CRS), _RASTER_TYPES.get(keys.get(_GEOKEY_RASTER_TYPE, 0))


def _exclude_nodata(values: tuple[float, ...], nodata: str | None) -> tuple[float, ...]:
    finite = tuple(value for value in values if math.isfinite(value))
    if nodata is None:
        return finite
    try:
        sentinel = float(nodata)
    except ValueError:
        return finite
    return tuple(value for value in finite if value != sentinel)

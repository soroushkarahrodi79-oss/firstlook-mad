"""A-02: canonical Madrid fire-station dataset (asset existence and location only).

A real fire station is not a validated UAS dock. Operational readiness, drone
suitability, availability, dispatch or docking capability, land ownership,
permission and emergency-response timing are never inferred: each is emitted as
``NOT_EVALUATED``.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Literal

from pyproj import Transformer

from firstlook_mad.domain import ANALYTICAL_CRS, FrozenModel
from firstlook_mad.normalization.crs import COORDINATE_DECIMALS, to_analytical_point
from firstlook_mad.normalization.evidence import ArtifactEvidence, decode_json_payload
from firstlook_mad.normalization.models import (
    COMUNIDAD_MADRID_ENVELOPE,
    MADRID_MUNICIPALITY_ENVELOPE,
    MAX_ABS_LATITUDE,
    MAX_ABS_LONGITUDE,
    NORMALIZATION_VERSION,
    NOT_EVALUATED,
    Completeness,
    Eligibility,
    Integrity,
    MalformedEvidenceError,
    StructuralValidity,
    is_json_number,
    non_blank_text,
)

FIRE_STATION_PROBE_ID = "madrid_city_open_data_fire_stations"
SOURCE_CRS_INTERPRETATION = "EPSG:4326 (interpreted: decimal lat/lon, no CRS declared by source)"
DUPLICATE_COORDINATE_DECIMALS = 6
NOT_INFERRED_PROPERTIES = (
    "availability",
    "dispatch_capability",
    "docking_capability",
    "drone_suitability",
    "emergency_response_timing",
    "land_ownership",
    "operational_readiness",
    "permission",
)


class DeclaredCoverage(StrEnum):
    COMUNIDAD_DE_MADRID = "COMUNIDAD_DE_MADRID"
    MADRID_MUNICIPALITY = "MADRID_MUNICIPALITY"


class SourceDescriptor(FrozenModel):
    """Publisher facts copied from ``data/datasets_manifest.json``.

    Coverage and licence are documented source facts; they are never inferred
    from the payload's coordinates.
    """

    manifest_dataset_id: str
    declared_coverage: DeclaredCoverage
    license: str
    attribution: str


MADRID_CITY_FIRE_STATIONS = SourceDescriptor(
    manifest_dataset_id="madrid_city_fire_stations_open_data",
    declared_coverage=DeclaredCoverage.MADRID_MUNICIPALITY,
    license="CC-BY-4.0",
    attribution="Ayuntamiento de Madrid",
)


class RejectionReason(StrEnum):
    INVALID_IDENTIFIER = "INVALID_IDENTIFIER"
    MISSING_NAME = "MISSING_NAME"
    MISSING_COORDINATES = "MISSING_COORDINATES"
    NON_NUMERIC_COORDINATES = "NON_NUMERIC_COORDINATES"
    NON_FINITE_COORDINATES = "NON_FINITE_COORDINATES"
    COORDINATES_OUT_OF_RANGE = "COORDINATES_OUT_OF_RANGE"
    OUTSIDE_MADRID_ENVELOPE = "OUTSIDE_MADRID_ENVELOPE"
    PROJECTION_OUT_OF_BOUNDS = "PROJECTION_OUT_OF_BOUNDS"
    DUPLICATE_IDENTIFIER = "DUPLICATE_IDENTIFIER"


class RejectedRecord(FrozenModel):
    source_index: int
    source_identifier: str | None
    reasons: tuple[RejectionReason, ...]


class CanonicalFireStation(FrozenModel):
    source_identifier: str
    source_record_uri: str | None
    station_name: str
    source_latitude: float
    source_longitude: float
    source_crs_interpretation: str
    easting_m: float
    northing_m: float
    analytical_crs: str
    source_probe_id: str
    source_sha256: str
    evidence_nature: Literal["DERIVED"] = "DERIVED"


class CanonicalFireStationDataset(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    normalization_version: str = NORMALIZATION_VERSION
    source_probe_id: str
    source_url: str
    source_acquired_at_utc: str
    source_sha256: str
    source_evidence_classification: str
    source_manifest_dataset_id: str
    declared_coverage: DeclaredCoverage
    license: str
    attribution: str
    analytical_crs: str = ANALYTICAL_CRS
    coordinate_decimals: int = COORDINATE_DECIMALS
    record_order: Literal["source_identifier_lexicographic"] = "source_identifier_lexicographic"
    not_inferred: dict[str, str]
    records: tuple[CanonicalFireStation, ...]


class A02QualityChecks(FrozenModel):
    source_record_count: int
    canonical_record_count: int
    rejected_records: tuple[RejectedRecord, ...]
    duplicate_identifiers: tuple[str, ...]
    duplicate_coordinate_groups: tuple[tuple[str, ...], ...]
    inside_municipality_envelope_count: int
    easting_range_m: tuple[float, float] | None
    northing_range_m: tuple[float, float] | None
    reconciliation_ok: bool


class A02Normalization(FrozenModel):
    dataset: CanonicalFireStationDataset
    checks: A02QualityChecks
    structural_validity: StructuralValidity
    completeness: Completeness


@dataclass(frozen=True)
class _Screened:
    index: int
    identifier: str | None
    station: CanonicalFireStation | None
    reasons: tuple[RejectionReason, ...]


def extract_source_records(payload: object) -> list[object]:
    graph = payload.get("@graph") if isinstance(payload, dict) else None
    if not isinstance(graph, list):
        raise MalformedEvidenceError(
            "fire-station payload: expected a JSON-LD object with an '@graph' record list"
        )
    records: list[object] = list(graph)
    return records


def normalize_fire_stations(
    raw: bytes,
    *,
    source: ArtifactEvidence,
    transformer: Transformer,
    descriptor: SourceDescriptor = MADRID_CITY_FIRE_STATIONS,
) -> A02Normalization:
    payload = decode_json_payload(raw, content_type=source.content_type, where=source.ref)
    source_records = extract_source_records(payload)
    screened = [
        _screen_record(index, record, source=source, transformer=transformer)
        for index, record in enumerate(source_records)
    ]
    screened, duplicated = _flag_duplicate_identifiers(screened)
    stations = sorted(
        (item for entry in screened if not entry.reasons and (item := entry.station) is not None),
        key=lambda station: station.source_identifier,
    )
    rejected = tuple(
        RejectedRecord(
            source_index=entry.index, source_identifier=entry.identifier, reasons=entry.reasons
        )
        for entry in screened
        if entry.reasons
    )
    groups = _duplicate_coordinate_groups(stations)
    validity = _structural_validity(len(stations), len(rejected), groups)
    dataset = CanonicalFireStationDataset(
        source_probe_id=source.probe_id,
        source_url=source.source_url,
        source_acquired_at_utc=source.acquired_at_utc,
        source_sha256=source.sha256,
        source_evidence_classification=source.ledger_classification,
        source_manifest_dataset_id=descriptor.manifest_dataset_id,
        declared_coverage=descriptor.declared_coverage,
        license=descriptor.license,
        attribution=descriptor.attribution,
        not_inferred=dict.fromkeys(NOT_INFERRED_PROPERTIES, NOT_EVALUATED),
        records=tuple(stations),
    )
    checks = A02QualityChecks(
        source_record_count=len(source_records),
        canonical_record_count=len(stations),
        rejected_records=rejected,
        duplicate_identifiers=duplicated,
        duplicate_coordinate_groups=groups,
        inside_municipality_envelope_count=sum(
            1
            for station in stations
            if MADRID_MUNICIPALITY_ENVELOPE.contains(
                station.source_longitude, station.source_latitude
            )
        ),
        easting_range_m=_value_range([station.easting_m for station in stations]),
        northing_range_m=_value_range([station.northing_m for station in stations]),
        reconciliation_ok=len(source_records) == len(stations) + len(rejected),
    )
    return A02Normalization(
        dataset=dataset,
        checks=checks,
        structural_validity=validity,
        completeness=_completeness(validity, len(rejected), descriptor.declared_coverage),
    )


def a02_eligibility(
    integrity: Integrity, validity: StructuralValidity, completeness: Completeness
) -> Eligibility:
    if integrity is not Integrity.PASS or validity is not StructuralValidity.VALID:
        return Eligibility.NOT_ELIGIBLE
    if completeness is Completeness.COMPLETE_FOR_ANALYTICAL_DOMAIN:
        return Eligibility.ELIGIBLE
    if completeness is Completeness.COMPLETE_FOR_DECLARED_SCOPE:
        return Eligibility.ELIGIBLE_WITHIN_DECLARED_SCOPE
    return Eligibility.NOT_ELIGIBLE


def _screen_record(
    index: int, raw_record: object, *, source: ArtifactEvidence, transformer: Transformer
) -> _Screened:
    record: dict[str, object] = raw_record if isinstance(raw_record, dict) else {}
    identifier = non_blank_text(record.get("id"))
    name = non_blank_text(record.get("title"))
    reasons: list[RejectionReason] = []
    if identifier is None:
        reasons.append(RejectionReason.INVALID_IDENTIFIER)
    if name is None:
        reasons.append(RejectionReason.MISSING_NAME)

    coordinates = _screen_coordinates(record)
    if isinstance(coordinates, RejectionReason):
        return _Screened(index, identifier, None, (*reasons, coordinates))
    lon, lat = coordinates
    point = to_analytical_point(transformer, lon, lat)
    if point is None:
        reasons.append(RejectionReason.PROJECTION_OUT_OF_BOUNDS)
    if reasons or identifier is None or name is None or point is None:
        return _Screened(index, identifier, None, tuple(reasons))

    station = CanonicalFireStation(
        source_identifier=identifier,
        source_record_uri=non_blank_text(record.get("@id")),
        station_name=name,
        source_latitude=lat,
        source_longitude=lon,
        source_crs_interpretation=SOURCE_CRS_INTERPRETATION,
        easting_m=point.easting_m,
        northing_m=point.northing_m,
        analytical_crs=point.crs,
        source_probe_id=source.probe_id,
        source_sha256=source.sha256,
    )
    return _Screened(index, identifier, station, ())


def _screen_coordinates(record: dict[str, object]) -> tuple[float, float] | RejectionReason:
    """Return (lon, lat) or the first failing pre-registered coordinate check."""

    location = record.get("location")
    if not isinstance(location, dict) or not {"latitude", "longitude"} <= location.keys():
        return RejectionReason.MISSING_COORDINATES
    lat, lon = location["latitude"], location["longitude"]
    if not (is_json_number(lat) and is_json_number(lon)):
        return RejectionReason.NON_NUMERIC_COORDINATES
    lat_value, lon_value = float(lat), float(lon)
    if not (math.isfinite(lat_value) and math.isfinite(lon_value)):
        return RejectionReason.NON_FINITE_COORDINATES
    if abs(lat_value) > MAX_ABS_LATITUDE or abs(lon_value) > MAX_ABS_LONGITUDE:
        return RejectionReason.COORDINATES_OUT_OF_RANGE
    if not COMUNIDAD_MADRID_ENVELOPE.contains(lon_value, lat_value):
        return RejectionReason.OUTSIDE_MADRID_ENVELOPE
    return lon_value, lat_value


def _flag_duplicate_identifiers(
    screened: list[_Screened],
) -> tuple[list[_Screened], tuple[str, ...]]:
    """Reject every record sharing an identifier; none is silently preferred."""

    counts = Counter(entry.identifier for entry in screened if entry.identifier is not None)
    duplicated = tuple(sorted(identifier for identifier, count in counts.items() if count > 1))
    flagged = [
        replace(entry, station=None, reasons=(*entry.reasons, RejectionReason.DUPLICATE_IDENTIFIER))
        if entry.identifier in duplicated
        else entry
        for entry in screened
    ]
    return flagged, duplicated


def _duplicate_coordinate_groups(
    stations: list[CanonicalFireStation],
) -> tuple[tuple[str, ...], ...]:
    groups: defaultdict[tuple[float, float], list[str]] = defaultdict(list)
    for station in stations:
        key = (
            round(station.source_latitude, DUPLICATE_COORDINATE_DECIMALS),
            round(station.source_longitude, DUPLICATE_COORDINATE_DECIMALS),
        )
        groups[key].append(station.source_identifier)
    return tuple(sorted(tuple(sorted(ids)) for ids in groups.values() if len(ids) > 1))


def _structural_validity(
    canonical_count: int, rejected_count: int, duplicate_groups: tuple[tuple[str, ...], ...]
) -> StructuralValidity:
    if canonical_count == 0:
        return StructuralValidity.INVALID
    if rejected_count or duplicate_groups:
        return StructuralValidity.VALID_WITH_FLAGS
    return StructuralValidity.VALID


def _completeness(
    validity: StructuralValidity, rejected_count: int, coverage: DeclaredCoverage
) -> Completeness:
    if rejected_count:
        return Completeness.INCOMPLETE_AFTER_REJECTIONS
    if validity is not StructuralValidity.VALID:
        return Completeness.UNKNOWN
    if coverage is DeclaredCoverage.COMUNIDAD_DE_MADRID:
        return Completeness.COMPLETE_FOR_ANALYTICAL_DOMAIN
    return Completeness.COMPLETE_FOR_DECLARED_SCOPE


def _value_range(values: list[float]) -> tuple[float, float] | None:
    return (min(values), max(values)) if values else None

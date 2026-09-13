"""A-04: AEMET semantic fitness, keeping station inventory apart from observations.

Four readiness facts are derived separately and only from evidence: station
inventory, historical observations, fire-day observations and
weather-falsification readiness. A station inventory never implies the other
three, and no weather value is ever generated.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator
from pyproj import Transformer

from firstlook_mad.domain import ANALYTICAL_CRS, FrozenModel
from firstlook_mad.normalization.crs import to_analytical_point
from firstlook_mad.normalization.evidence import ArtifactEvidence, decode_json_payload
from firstlook_mad.normalization.models import (
    COMUNIDAD_MADRID_ENVELOPE,
    MAX_ABS_LATITUDE,
    MAX_ABS_LONGITUDE,
    NORMALIZATION_VERSION,
    REAL_SOURCE_DATA,
    Eligibility,
    Integrity,
    MalformedEvidenceError,
    StructuralValidity,
    non_blank_text,
)
from firstlook_mad.normalization.serialization import canonical_json_bytes, sha256_hex

MADRID_PROVINCE_LABEL = "MADRID"
REQUIRED_FIRE_DAY_VARIABLES = frozenset({"visibility", "wind"})
OBSERVABLE_LABEL = "WEATHER_EVIDENCE_OBSERVABLE"
NOT_OBSERVABLE_LABEL = "WEATHER_EVIDENCE_NOT_OBSERVABLE"
_DMS_PATTERN = re.compile(r"^(\d{2})(\d{2})(\d{2})([NSEW])$")
_BASE_SIXTY = 60
_SECONDS_PER_DEGREE = 3600.0
_INVENTORY_KEYS = frozenset({"indicativo", "latitud", "longitud"})


class AemetContentType(StrEnum):
    STATION_INVENTORY = "STATION_INVENTORY"
    OBSERVATION_SERIES = "OBSERVATION_SERIES"
    WRAPPER = "WRAPPER"
    SERVICE_ERROR = "SERVICE_ERROR"
    UNRECOGNIZED = "UNRECOGNIZED"


def detect_aemet_content_type(payload: object) -> AemetContentType:
    """What the payload *is*; never used to upgrade a ledger classification."""

    if isinstance(payload, dict):
        if isinstance(payload.get("datos"), str):
            return AemetContentType.WRAPPER
        if "estado" in payload:
            return AemetContentType.SERVICE_ERROR
        return AemetContentType.UNRECOGNIZED
    if isinstance(payload, list) and payload and all(isinstance(item, dict) for item in payload):
        if all("fecha" in item for item in payload):
            return AemetContentType.OBSERVATION_SERIES
        if all(item.keys() >= _INVENTORY_KEYS for item in payload):
            return AemetContentType.STATION_INVENTORY
    return AemetContentType.UNRECOGNIZED


def parse_aemet_dms(value: str, *, axis: Literal["latitude", "longitude"]) -> float:
    """Parse AEMET ``ddmmss[NSEW]`` into signed decimal degrees, deterministically."""

    hemispheres, limit = (
        ("NS", MAX_ABS_LATITUDE) if axis == "latitude" else ("EW", MAX_ABS_LONGITUDE)
    )
    match = _DMS_PATTERN.match(value)
    if match is None or match.group(4) not in hemispheres:
        raise ValueError(f"not an AEMET ddmmss{hemispheres} {axis}: {value!r}")
    degrees, minutes, seconds = (int(match.group(group)) for group in (1, 2, 3))
    if minutes >= _BASE_SIXTY or seconds >= _BASE_SIXTY or degrees > limit:
        raise ValueError(f"out-of-range AEMET {axis}: {value!r}")
    magnitude = degrees + minutes / _BASE_SIXTY + seconds / _SECONDS_PER_DEGREE
    return -magnitude if match.group(4) in "SW" else magnitude


class InventoryRejectionReason(StrEnum):
    MISSING_IDENTIFIER = "MISSING_IDENTIFIER"
    MISSING_NAME = "MISSING_NAME"
    MISSING_PROVINCE = "MISSING_PROVINCE"
    INVALID_LATITUDE = "INVALID_LATITUDE"
    INVALID_LONGITUDE = "INVALID_LONGITUDE"
    OUTSIDE_MADRID_ENVELOPE = "OUTSIDE_MADRID_ENVELOPE"
    PROJECTION_OUT_OF_BOUNDS = "PROJECTION_OUT_OF_BOUNDS"
    DUPLICATE_IDENTIFIER = "DUPLICATE_IDENTIFIER"


class InventoryRejectedRecord(FrozenModel):
    source_index: int
    station_identifier: str | None
    reasons: tuple[InventoryRejectionReason, ...]


class CanonicalWeatherStation(FrozenModel):
    station_identifier: str
    station_name: str
    source_province: str
    altitude_m: float | None
    source_latitude_dms: str
    source_longitude_dms: str
    latitude: float
    longitude: float
    easting_m: float
    northing_m: float
    analytical_crs: str
    source_probe_id: str
    source_sha256: str
    record_kind: Literal["STATION_INVENTORY_ENTRY_NOT_AN_OBSERVATION"] = (
        "STATION_INVENTORY_ENTRY_NOT_AN_OBSERVATION"
    )
    evidence_nature: Literal["DERIVED"] = "DERIVED"


class CanonicalWeatherStationInventory(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    normalization_version: str = NORMALIZATION_VERSION
    source_probe_id: str
    source_url: str
    source_acquired_at_utc: str
    source_sha256: str
    source_evidence_classification: str
    selection_rule: Literal["source field provincia == MADRID (publisher label)"] = (
        "source field provincia == MADRID (publisher label)"
    )
    analytical_crs: str = ANALYTICAL_CRS
    content_notice: Literal["STATION INVENTORY ONLY: contains no weather observations"] = (
        "STATION INVENTORY ONLY: contains no weather observations"
    )
    records: tuple[CanonicalWeatherStation, ...]


class InventoryQuality(FrozenModel):
    source_record_count: int
    nationwide_rejected_record_count: int
    duplicate_identifiers: tuple[str, ...]
    madrid_province_record_count: int
    madrid_canonical_record_count: int
    madrid_rejected_records: tuple[InventoryRejectedRecord, ...]
    madrid_altitude_unparsed_count: int
    structural_validity: StructuralValidity
    canonical_sha256: str


@dataclass(frozen=True)
class _ScreenedStation:
    index: int
    identifier: str | None
    is_madrid: bool
    station: CanonicalWeatherStation | None
    reasons: tuple[InventoryRejectionReason, ...]


def normalize_station_inventory(
    raw: bytes, *, source: ArtifactEvidence, transformer: Transformer
) -> tuple[CanonicalWeatherStationInventory, InventoryQuality]:
    payload = decode_json_payload(raw, content_type=source.content_type, where=source.ref)
    if not isinstance(payload, list) or (
        detect_aemet_content_type(payload) is not AemetContentType.STATION_INVENTORY
    ):
        raise MalformedEvidenceError(f"{source.ref}: payload is not an AEMET station inventory")
    screened = [
        _screen_station(index, record, source=source, transformer=transformer)
        for index, record in enumerate(payload)
    ]
    counts = Counter(entry.identifier for entry in screened if entry.identifier is not None)
    duplicated = tuple(sorted(identifier for identifier, count in counts.items() if count > 1))
    screened = [
        replace(
            entry,
            station=None,
            reasons=(*entry.reasons, InventoryRejectionReason.DUPLICATE_IDENTIFIER),
        )
        if entry.identifier in duplicated
        else entry
        for entry in screened
    ]
    madrid = [entry for entry in screened if entry.is_madrid]
    stations = sorted(
        (item for entry in madrid if not entry.reasons and (item := entry.station) is not None),
        key=lambda station: station.station_identifier,
    )
    madrid_rejected = tuple(
        InventoryRejectedRecord(
            source_index=entry.index, station_identifier=entry.identifier, reasons=entry.reasons
        )
        for entry in madrid
        if entry.reasons
    )
    inventory = CanonicalWeatherStationInventory(
        source_probe_id=source.probe_id,
        source_url=source.source_url,
        source_acquired_at_utc=source.acquired_at_utc,
        source_sha256=source.sha256,
        source_evidence_classification=source.ledger_classification,
        records=tuple(stations),
    )
    if not stations:
        validity = StructuralValidity.INVALID
    elif madrid_rejected:
        validity = StructuralValidity.VALID_WITH_FLAGS
    else:
        validity = StructuralValidity.VALID
    quality = InventoryQuality(
        source_record_count=len(payload),
        nationwide_rejected_record_count=sum(1 for entry in screened if entry.reasons),
        duplicate_identifiers=duplicated,
        madrid_province_record_count=len(madrid),
        madrid_canonical_record_count=len(stations),
        madrid_rejected_records=madrid_rejected,
        madrid_altitude_unparsed_count=sum(1 for station in stations if station.altitude_m is None),
        structural_validity=validity,
        canonical_sha256=sha256_hex(canonical_json_bytes(inventory)),
    )
    return inventory, quality


def _screen_station(
    index: int, raw_record: object, *, source: ArtifactEvidence, transformer: Transformer
) -> _ScreenedStation:
    record: dict[str, object] = raw_record if isinstance(raw_record, dict) else {}
    identifier = non_blank_text(record.get("indicativo"))
    name = non_blank_text(record.get("nombre"))
    province = non_blank_text(record.get("provincia"))
    latitude_text = non_blank_text(record.get("latitud"))
    longitude_text = non_blank_text(record.get("longitud"))
    latitude = _dms_or_none(latitude_text, "latitude")
    longitude = _dms_or_none(longitude_text, "longitude")
    reasons = [
        reason
        for missing, reason in (
            (identifier is None, InventoryRejectionReason.MISSING_IDENTIFIER),
            (name is None, InventoryRejectionReason.MISSING_NAME),
            (province is None, InventoryRejectionReason.MISSING_PROVINCE),
            (latitude is None, InventoryRejectionReason.INVALID_LATITUDE),
            (longitude is None, InventoryRejectionReason.INVALID_LONGITUDE),
        )
        if missing
    ]
    is_madrid = province is not None and province.strip().upper() == MADRID_PROVINCE_LABEL
    if (
        reasons
        or not is_madrid
        or identifier is None
        or name is None
        or province is None
        or latitude_text is None
        or longitude_text is None
        or latitude is None
        or longitude is None
    ):
        return _ScreenedStation(index, identifier, is_madrid, None, tuple(reasons))
    if not COMUNIDAD_MADRID_ENVELOPE.contains(longitude, latitude):
        return _ScreenedStation(
            index, identifier, is_madrid, None, (InventoryRejectionReason.OUTSIDE_MADRID_ENVELOPE,)
        )
    point = to_analytical_point(transformer, longitude, latitude)
    if point is None:
        return _ScreenedStation(
            index, identifier, is_madrid, None, (InventoryRejectionReason.PROJECTION_OUT_OF_BOUNDS,)
        )
    station = CanonicalWeatherStation(
        station_identifier=identifier,
        station_name=name,
        source_province=province,
        altitude_m=_altitude(record.get("altitud")),
        source_latitude_dms=latitude_text,
        source_longitude_dms=longitude_text,
        latitude=latitude,
        longitude=longitude,
        easting_m=point.easting_m,
        northing_m=point.northing_m,
        analytical_crs=point.crs,
        source_probe_id=source.probe_id,
        source_sha256=source.sha256,
    )
    return _ScreenedStation(index, identifier, is_madrid, station, ())


def _dms_or_none(value: str | None, axis: Literal["latitude", "longitude"]) -> float | None:
    if value is None:
        return None
    try:
        return parse_aemet_dms(value, axis=axis)
    except ValueError:
        return None


def _altitude(value: object) -> float | None:
    """Altitude is optional: an unparseable value stays ``None`` and is counted."""

    text = non_blank_text(value)
    if text is None:
        return None
    try:
        return float(int(text))
    except ValueError:
        return None


# --- Readiness ---------------------------------------------------------------------------


class WeatherArtifactEvidence(FrozenModel):
    artifact_ref: str
    integrity: Integrity
    ledger_classification: str
    content_type: AemetContentType | None
    valid_madrid_record_count: int = Field(default=0, ge=0)
    observed_dates: tuple[str, ...] = ()
    observed_variables: tuple[str, ...] = ()

    @model_validator(mode="after")
    def content_type_bounds_what_it_can_carry(self) -> WeatherArtifactEvidence:
        is_series = self.content_type is AemetContentType.OBSERVATION_SERIES
        if not is_series and (self.observed_dates or self.observed_variables):
            raise ValueError("only an OBSERVATION_SERIES artifact can carry observations")
        if self.content_type is not AemetContentType.STATION_INVENTORY and (
            self.valid_madrid_record_count
        ):
            raise ValueError("only a STATION_INVENTORY artifact can carry station records")
        return self


class A04Readiness(FrozenModel):
    station_inventory_available: bool
    historical_observations_available: bool
    fire_day_observations_available: bool
    weather_falsification_ready: bool
    evidence_label: Literal["WEATHER_EVIDENCE_OBSERVABLE", "WEATHER_EVIDENCE_NOT_OBSERVABLE"]

    @model_validator(mode="after")
    def enforce_dependency_chain(self) -> A04Readiness:
        if self.fire_day_observations_available and not self.historical_observations_available:
            raise ValueError("fire-day observations require historical observations")
        if self.weather_falsification_ready and not self.fire_day_observations_available:
            raise ValueError("weather falsification readiness requires fire-day observations")
        expected = OBSERVABLE_LABEL if self.weather_falsification_ready else NOT_OBSERVABLE_LABEL
        if self.evidence_label != expected:
            raise ValueError("evidence_label contradicts weather_falsification_ready")
        return self


def derive_a04_readiness(
    artifacts: Sequence[WeatherArtifactEvidence], *, fire_dates: frozenset[str]
) -> A04Readiness:
    usable = [
        artifact
        for artifact in artifacts
        if artifact.integrity is Integrity.PASS
        and artifact.ledger_classification == REAL_SOURCE_DATA
    ]
    inventory = any(
        artifact.content_type is AemetContentType.STATION_INVENTORY
        and artifact.valid_madrid_record_count > 0
        for artifact in usable
    )
    series = [
        artifact
        for artifact in usable
        if artifact.content_type is AemetContentType.OBSERVATION_SERIES and artifact.observed_dates
    ]
    covering = [artifact for artifact in series if fire_dates.intersection(artifact.observed_dates)]
    variables = {variable for artifact in covering for variable in artifact.observed_variables}
    ready = bool(covering) and variables >= REQUIRED_FIRE_DAY_VARIABLES
    return A04Readiness(
        station_inventory_available=inventory,
        historical_observations_available=bool(series),
        fire_day_observations_available=bool(covering),
        weather_falsification_ready=ready,
        evidence_label="WEATHER_EVIDENCE_OBSERVABLE"
        if ready
        else "WEATHER_EVIDENCE_NOT_OBSERVABLE",
    )


def a04_eligibility(readiness: A04Readiness) -> Eligibility:
    if readiness.weather_falsification_ready:
        return Eligibility.ELIGIBLE
    return Eligibility.NOT_ELIGIBLE

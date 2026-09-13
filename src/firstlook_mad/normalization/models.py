"""Shared typed vocabulary for Phase 0D.2 canonical evidence and data quality.

Integrity, structural validity, semantic fitness, completeness and analytical
eligibility are deliberately separate fields. There is no composite quality
score anywhere in this package.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import TypeGuard

from pydantic import model_validator

from firstlook_mad.domain import FrozenModel

NORMALIZATION_VERSION = "0D.2-1.0.0"
PREREGISTRATION_DOC = "docs/PHASE_0D2_PREREGISTRATION.md"
GEOGRAPHIC_CRS = "EPSG:4326"
ANALYTICAL_EPSG_CODE = 25830
REAL_SOURCE_DATA = "REAL_SOURCE_DATA"
REAL_BOUNDED_SAMPLE = "REAL_BOUNDED_SAMPLE"
REAL_METADATA = "REAL_METADATA"
NOT_EVALUATED = "NOT_EVALUATED"
TARGET_ASSUMPTIONS = ("A-01", "A-02", "A-03", "A-04")
MAX_ABS_LATITUDE = 90.0
MAX_ABS_LONGITUDE = 180.0


class Integrity(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    RAW_UNAVAILABLE = "RAW_UNAVAILABLE"


class StructuralValidity(StrEnum):
    VALID = "VALID"
    VALID_WITH_FLAGS = "VALID_WITH_FLAGS"
    INVALID = "INVALID"
    NOT_NORMALIZED = "NOT_NORMALIZED"


class SemanticFitness(StrEnum):
    FIT_FOR_TARGET_ROLE = "FIT_FOR_TARGET_ROLE"
    FIT_WITHIN_DECLARED_SCOPE = "FIT_WITHIN_DECLARED_SCOPE"
    NOT_FIT_FOR_TARGET_ROLE = "NOT_FIT_FOR_TARGET_ROLE"
    UNKNOWN = "UNKNOWN"


class Completeness(StrEnum):
    COMPLETE_FOR_ANALYTICAL_DOMAIN = "COMPLETE_FOR_ANALYTICAL_DOMAIN"
    COMPLETE_FOR_DECLARED_SCOPE = "COMPLETE_FOR_DECLARED_SCOPE"
    INCOMPLETE_AFTER_REJECTIONS = "INCOMPLETE_AFTER_REJECTIONS"
    TRUNCATED_BY_SOURCE = "TRUNCATED_BY_SOURCE"
    BOUNDED_SAMPLE = "BOUNDED_SAMPLE"
    NOT_OBSERVED = "NOT_OBSERVED"
    UNKNOWN = "UNKNOWN"


class Eligibility(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    ELIGIBLE_WITHIN_DECLARED_SCOPE = "ELIGIBLE_WITHIN_DECLARED_SCOPE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


class NormalizationOutcome(StrEnum):
    CANONICAL_DATASET = "CANONICAL_DATASET"
    CANONICAL_BOUNDED_SAMPLE = "CANONICAL_BOUNDED_SAMPLE"
    CANONICAL_INVENTORY_ONLY = "CANONICAL_INVENTORY_ONLY"
    OBSERVABILITY_RECORD_ONLY = "OBSERVABILITY_RECORD_ONLY"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    FAILED = "FAILED"


CANONICAL_OUTCOMES = frozenset(
    {
        NormalizationOutcome.CANONICAL_DATASET,
        NormalizationOutcome.CANONICAL_BOUNDED_SAMPLE,
        NormalizationOutcome.CANONICAL_INVENTORY_ONLY,
    }
)


class GateVerdict(StrEnum):
    NORMALIZATION_READY = "NORMALIZATION_READY"
    PARTIAL_NORMALIZATION = "PARTIAL_NORMALIZATION"
    SEMANTICALLY_INSUFFICIENT = "SEMANTICALLY_INSUFFICIENT"


class MalformedEvidenceError(ValueError):
    """A ledger entry, sidecar or payload cannot be interpreted.

    Always raised explicitly: malformed evidence is never skipped, guessed at or
    repaired.
    """


class UnsupportedRasterLayoutError(MalformedEvidenceError):
    """A raster uses a layout this deliberately small reader does not decode."""


class Envelope(FrozenModel):
    """Axis-aligned extent: lon/lat degrees in EPSG:4326, metres in EPSG:25830."""

    crs: str
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @model_validator(mode="after")
    def validate_order(self) -> Envelope:
        if self.min_x >= self.max_x or self.min_y >= self.max_y:
            raise ValueError("envelope bounds are empty or reversed")
        return self

    def contains(self, x: float, y: float) -> bool:
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def covers(self, other: Envelope) -> bool:
        if self.crs != other.crs:
            raise ValueError("cannot compare envelopes expressed in different CRS")
        return (
            self.min_x <= other.min_x
            and self.min_y <= other.min_y
            and self.max_x >= other.max_x
            and self.max_y >= other.max_y
        )


# Pre-registered sanity envelopes (docs/PHASE_0D2_PREREGISTRATION.md section 5.1).
COMUNIDAD_MADRID_ENVELOPE = Envelope(
    crs=GEOGRAPHIC_CRS, min_x=-4.60, min_y=39.88, max_x=-3.05, max_y=41.17
)
MADRID_MUNICIPALITY_ENVELOPE = Envelope(
    crs=GEOGRAPHIC_CRS, min_x=-3.89, min_y=40.31, max_x=-3.52, max_y=40.65
)


def permits_substitution(eligibility: Eligibility) -> bool:
    return eligibility is not Eligibility.NOT_ELIGIBLE


def fitness_from_eligibility(eligibility: Eligibility) -> SemanticFitness:
    return {
        Eligibility.ELIGIBLE: SemanticFitness.FIT_FOR_TARGET_ROLE,
        Eligibility.ELIGIBLE_WITHIN_DECLARED_SCOPE: SemanticFitness.FIT_WITHIN_DECLARED_SCOPE,
        Eligibility.NOT_ELIGIBLE: SemanticFitness.NOT_FIT_FOR_TARGET_ROLE,
    }[eligibility]


def aggregate_integrity(values: Iterable[Integrity]) -> Integrity:
    """FAIL dominates, then RAW_UNAVAILABLE; no evidence at all is unavailable."""

    observed = set(values)
    if Integrity.FAIL in observed:
        return Integrity.FAIL
    if not observed or Integrity.RAW_UNAVAILABLE in observed:
        return Integrity.RAW_UNAVAILABLE
    return Integrity.PASS


def non_blank_text(value: object) -> str | None:
    """Return the source string verbatim when it has visible content, else ``None``."""

    return value if isinstance(value, str) and value.strip() else None


def is_json_number(value: object) -> TypeGuard[int | float]:
    return isinstance(value, int | float) and not isinstance(value, bool)

"""A-01: TTFRP baseline observability from EGIF evidence.

``public EGIF interface available != observable incident-level TTFRP baseline``.
No detection, dispatch, response or proxy TTFRP value is ever generated here;
baseline design belongs to Phase 0E.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from firstlook_mad.domain import FrozenModel
from firstlook_mad.normalization.models import REAL_SOURCE_DATA, Eligibility, Integrity

# docs/PHASE_0D_PROTOCOL.md section 4.1: fewer usable records is inconclusive.
MIN_USABLE_RECORDS_FOR_ELIGIBILITY = 10


class BaselineStatus(StrEnum):
    OBSERVABLE = "OBSERVABLE"
    BASELINE_NOT_OBSERVABLE = "BASELINE_NOT_OBSERVABLE"


class IncidentTimingRecord(FrozenModel):
    """Timestamps of one incident exactly as parsed from a source; never imputed."""

    incident_identifier: str = Field(min_length=1)
    detection_at_utc: datetime | None
    first_arrival_at_utc: datetime | None

    @model_validator(mode="after")
    def require_timezone(self) -> IncidentTimingRecord:
        for value in (self.detection_at_utc, self.first_arrival_at_utc):
            if value is not None and value.tzinfo is None:
                raise ValueError("incident timestamps must be timezone-aware")
        return self

    @property
    def usable(self) -> bool:
        return (
            self.detection_at_utc is not None
            and self.first_arrival_at_utc is not None
            and self.first_arrival_at_utc >= self.detection_at_utc
        )


class EgifArtifactEvidence(FrozenModel):
    artifact_ref: str
    integrity: Integrity
    ledger_classification: str
    incident_records: tuple[IncidentTimingRecord, ...] = ()

    @model_validator(mode="after")
    def metadata_cannot_carry_records(self) -> EgifArtifactEvidence:
        if self.incident_records and self.ledger_classification != REAL_SOURCE_DATA:
            raise ValueError(
                f"{self.ledger_classification} artifacts cannot carry incident-level records"
            )
        return self


class A01Observability(FrozenModel):
    public_interface_available: bool
    incident_level_records_available: bool
    usable_timing_record_count: int = Field(ge=0)
    ttfrp_baseline_status: BaselineStatus
    proxy_ttfrp_generated: Literal[False] = False
    minimum_usable_records_for_eligibility: int = MIN_USABLE_RECORDS_FOR_ELIGIBILITY

    @model_validator(mode="after")
    def status_matches_evidence(self) -> A01Observability:
        observable = self.incident_level_records_available and self.usable_timing_record_count > 0
        if (self.ttfrp_baseline_status is BaselineStatus.OBSERVABLE) != observable:
            raise ValueError("ttfrp_baseline_status contradicts the incident-level evidence")
        if self.minimum_usable_records_for_eligibility != MIN_USABLE_RECORDS_FOR_ELIGIBILITY:
            raise ValueError("the pre-registered minimum usable record count cannot be changed")
        return self


def derive_a01_observability(artifacts: Sequence[EgifArtifactEvidence]) -> A01Observability:
    verified = [artifact for artifact in artifacts if artifact.integrity is Integrity.PASS]
    records = [
        record
        for artifact in verified
        if artifact.ledger_classification == REAL_SOURCE_DATA
        for record in artifact.incident_records
    ]
    usable = sum(1 for record in records if record.usable)
    return A01Observability(
        public_interface_available=bool(verified),
        incident_level_records_available=bool(records),
        usable_timing_record_count=usable,
        ttfrp_baseline_status=(
            BaselineStatus.OBSERVABLE
            if records and usable
            else BaselineStatus.BASELINE_NOT_OBSERVABLE
        ),
    )


def a01_eligibility(observability: A01Observability) -> Eligibility:
    observable = observability.ttfrp_baseline_status is BaselineStatus.OBSERVABLE
    if observable and (
        observability.usable_timing_record_count >= MIN_USABLE_RECORDS_FOR_ELIGIBILITY
    ):
        return Eligibility.ELIGIBLE
    return Eligibility.NOT_ELIGIBLE

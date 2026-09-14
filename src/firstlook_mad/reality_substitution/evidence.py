"""Load the tracked canonical A-02 evidence for Phase 0D.3 substitution.

This module never reconstructs, fabricates or proxies the evidence. If the
tracked canonical file is missing or its integrity linkage cannot be preserved,
loading fails explicitly (Phase 0D.3 pre-registration §2).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import Field

from firstlook_mad.domain import (
    ANALYTICAL_CRS,
    CandidateSite,
    EvidenceNature,
    FrozenModel,
    ProjectedPoint,
)

CANONICAL_A02_PATH = Path("outputs/canonical/phase0d2/a02_madrid_city_fire_stations.json")
EXPECTED_RECORD_COUNT = 13
EXPECTED_SOURCE_SHA256 = "5c3957873878d30c93556c75544b6d7740c648b84b0424682dfac655842f8eb6"

# Operational properties the real A-02 evidence does NOT establish. They stay
# NOT_EVALUATED and are represented as ``None`` on the CandidateSite; they are
# never invented (Phase 0D.3 pre-registration §6).
NOT_EVALUATED_OPERATIONAL_PROPERTIES = (
    "assumed_available",
    "uas_available",
    "communications_available",
    "camera_available",
    "camera_communications_available",
)


class MissingCanonicalA02Error(FileNotFoundError):
    """The tracked canonical A-02 file is absent; it is never reconstructed."""


class CanonicalA02IntegrityError(ValueError):
    """The canonical A-02 file is present but fails a pre-registered check."""


class CanonicalA02Evidence(FrozenModel):
    """The real A-02 evidence and the provenance needed for the manifest."""

    source_url: str
    source_sha256: str
    source_evidence_classification: str
    declared_coverage: str
    analytical_crs: str
    normalization_version: str
    not_inferred: dict[str, str]
    canonical_output_sha256: str
    record_count: int = Field(ge=1)
    sites: tuple[CandidateSite, ...]


def _canonical_output_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_canonical_a02(path: Path = CANONICAL_A02_PATH) -> CanonicalA02Evidence:
    """Load and integrity-check the tracked canonical A-02 dataset.

    Raises explicitly rather than substituting a proxy when the file is missing
    or malformed (pre-registration §2, §9 -> SUBSTITUTION_INVALID).
    """

    if not path.exists():
        raise MissingCanonicalA02Error(
            f"canonical A-02 evidence not found at {path}; Phase 0D.3 does not "
            "reconstruct or fabricate it"
        )
    output_sha256 = _canonical_output_sha256(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise CanonicalA02IntegrityError("canonical A-02 payload is not a JSON object")

    records = document.get("records")
    if not isinstance(records, list) or not records:
        raise CanonicalA02IntegrityError("canonical A-02 payload has no records list")
    if len(records) != EXPECTED_RECORD_COUNT:
        raise CanonicalA02IntegrityError(
            f"expected {EXPECTED_RECORD_COUNT} A-02 records, found {len(records)}"
        )

    source_sha256 = document.get("source_sha256")
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise CanonicalA02IntegrityError(
            "canonical A-02 source_sha256 does not match the pre-registered value"
        )

    analytical_crs = document.get("analytical_crs")
    if analytical_crs != ANALYTICAL_CRS:
        raise CanonicalA02IntegrityError(
            f"canonical A-02 analytical_crs must be {ANALYTICAL_CRS}, found {analytical_crs}"
        )

    sites = tuple(_to_candidate_site(index, record) for index, record in enumerate(records))
    return CanonicalA02Evidence(
        source_url=str(document.get("source_url", "")),
        source_sha256=str(source_sha256),
        source_evidence_classification=str(document.get("source_evidence_classification", "")),
        declared_coverage=str(document.get("declared_coverage", "")),
        analytical_crs=str(analytical_crs),
        normalization_version=str(document.get("normalization_version", "")),
        not_inferred=dict(document.get("not_inferred", {})),
        canonical_output_sha256=output_sha256,
        record_count=len(records),
        sites=sites,
    )


def _to_candidate_site(index: int, record: object) -> CandidateSite:
    if not isinstance(record, dict):
        raise CanonicalA02IntegrityError(f"A-02 record {index} is not an object")
    identifier = record.get("source_identifier")
    easting = record.get("easting_m")
    northing = record.get("northing_m")
    if not isinstance(identifier, str) or not identifier.strip():
        raise CanonicalA02IntegrityError(f"A-02 record {index} has no source identifier")
    if not isinstance(easting, int | float) or isinstance(easting, bool):
        raise CanonicalA02IntegrityError(f"A-02 record {identifier} has non-numeric easting")
    if not isinstance(northing, int | float) or isinstance(northing, bool):
        raise CanonicalA02IntegrityError(f"A-02 record {identifier} has non-numeric northing")
    # Operational properties are None: NOT_EVALUATED, never invented.
    return CandidateSite(
        site_id=f"A02-{identifier}",
        point=ProjectedPoint(easting_m=float(easting), northing_m=float(northing)),
        assumed_available=None,
        uas_available=None,
        communications_available=None,
        camera_available=None,
        camera_communications_available=None,
        nature=EvidenceNature.DERIVED,
    )

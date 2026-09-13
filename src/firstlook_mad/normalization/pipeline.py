"""Phase 0D.2 pipeline: evidence -> per-assumption assessment -> pre-registered gate.

``run_normalization`` only reads; ``write_run`` is the single place that writes.
For every assumption the report keeps integrity, structural validity, semantic
fitness, completeness and analytical eligibility as separate fields.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pyproj import Transformer

from firstlook_mad.domain import ANALYTICAL_CRS, FrozenModel
from firstlook_mad.normalization.a01_ttfrp import (
    A01Observability,
    BaselineStatus,
    EgifArtifactEvidence,
    a01_eligibility,
    derive_a01_observability,
)
from firstlook_mad.normalization.a02_fire_stations import (
    FIRE_STATION_PROBE_ID,
    MADRID_CITY_FIRE_STATIONS,
    NOT_INFERRED_PROPERTIES,
    SOURCE_CRS_INTERPRETATION,
    A02QualityChecks,
    DeclaredCoverage,
    a02_eligibility,
    normalize_fire_stations,
)
from firstlook_mad.normalization.a03_bounded import (
    ENAIRE_PROBE_ID,
    MDT05_PROBE_ID,
    AirspaceSampleAssessment,
    TerrainSampleAssessment,
    assess_terrain_sample,
    normalize_airspace_sample,
    rollup_a03_eligibility,
)
from firstlook_mad.normalization.a04_weather import (
    A04Readiness,
    AemetContentType,
    CanonicalWeatherStationInventory,
    InventoryQuality,
    WeatherArtifactEvidence,
    a04_eligibility,
    derive_a04_readiness,
    detect_aemet_content_type,
    normalize_station_inventory,
)
from firstlook_mad.normalization.crs import make_analytical_transformer
from firstlook_mad.normalization.evidence import (
    ArtifactEvidence,
    LoadedArtifact,
    decode_json_payload,
    load_evidence,
)
from firstlook_mad.normalization.gate import GateDecision, evaluate_gate
from firstlook_mad.normalization.models import (
    CANONICAL_OUTCOMES,
    COMUNIDAD_MADRID_ENVELOPE,
    NORMALIZATION_VERSION,
    NOT_EVALUATED,
    PREREGISTRATION_DOC,
    REAL_BOUNDED_SAMPLE,
    REAL_METADATA,
    REAL_SOURCE_DATA,
    Completeness,
    Eligibility,
    Envelope,
    Integrity,
    MalformedEvidenceError,
    NormalizationOutcome,
    SemanticFitness,
    StructuralValidity,
    aggregate_integrity,
    fitness_from_eligibility,
    permits_substitution,
)
from firstlook_mad.normalization.serialization import (
    assert_no_secret_markers,
    canonical_json_bytes,
    sha256_hex,
)

REPORT_PATH = "outputs/reports/phase0d2_normalization_report.json"
A02_CANONICAL_PATH = "outputs/canonical/phase0d2/a02_madrid_city_fire_stations.json"
A03_AIRSPACE_PROCESSED_PATH = "data/processed/phase0d2/a03_enaire_uas_zones_bounded_sample.json"
A04_INVENTORY_PROCESSED_PATH = "data/processed/phase0d2/a04_aemet_madrid_station_inventory.json"

TARGET_ROLES = {
    "A-01": "observable incident-level TTFRP components (timestamps) for Madrid incidents",
    "A-02": "real public-asset locations replacing synthetic candidate-site locations "
    "(existence and location only)",
    "A-03": "real airspace and terrain constraints over the analytical domain replacing "
    "synthetic geometry",
    "A-04": "real fire-day weather observations replacing assumed weather scenarios",
}
NON_CLAIMS = (
    "fire station != UAS dock",
    "bounded sample != full Madrid layer",
    "station inventory != weather observations",
    "EGIF interface != TTFRP baseline",
    "normalization success != SUPPORTED",
    "no 0D.2 verdict implies BUILD, SAFE_TO_FLY or MADRID VALIDATED",
    "no assumption changes TESTING -> SUPPORTED/REFUTED in 0D.2",
)
STOP_RULE = (
    "Phase 0D.2 ends at this gate: it does not start 0D.3, perform real-evidence "
    "substitution, change BUILD/REPOSITION/KILL or begin Phase 0E."
)
FIRE_DATE_SOURCE = (
    "none: no integrity-verified REAL Madrid fire-date set exists in the 0D.1 evidence "
    "(A-01 has no incident-level records)"
)
_COMPLETENESS_WORST_FIRST = (
    Completeness.TRUNCATED_BY_SOURCE,
    Completeness.UNKNOWN,
    Completeness.INCOMPLETE_AFTER_REJECTIONS,
    Completeness.NOT_OBSERVED,
    Completeness.BOUNDED_SAMPLE,
    Completeness.COMPLETE_FOR_DECLARED_SCOPE,
    Completeness.COMPLETE_FOR_ANALYTICAL_DOMAIN,
)


class A01Details(FrozenModel):
    kind: Literal["A-01"] = "A-01"
    observability: A01Observability
    note: str


class A02Details(FrozenModel):
    kind: Literal["A-02"] = "A-02"
    source_manifest_dataset_id: str
    declared_coverage: DeclaredCoverage
    license: str
    attribution: str
    source_crs_interpretation: str
    not_inferred: dict[str, str]
    checks: A02QualityChecks | None


class A03Details(FrozenModel):
    kind: Literal["A-03"] = "A-03"
    airspace: AirspaceSampleAssessment | None
    terrain: TerrainSampleAssessment | None
    metadata_only_artifacts: tuple[str, ...]


class A04Details(FrozenModel):
    kind: Literal["A-04"] = "A-04"
    readiness: A04Readiness
    artifact_content_types: dict[str, str]
    inventory_quality: InventoryQuality | None
    fire_date_source: str


class AssumptionAssessment(FrozenModel):
    assumption: str
    target_role: str
    evidence_acquired: bool
    artifacts: tuple[str, ...]
    normalization_outcome: NormalizationOutcome
    normalized_successfully: bool
    integrity: Integrity
    structural_validity: StructuralValidity
    semantic_fitness: SemanticFitness
    completeness: Completeness
    analytical_eligibility: Eligibility
    eligible_for_downstream_substitution: bool
    scope_restrictions: tuple[str, ...]
    blockers: tuple[str, ...]
    reason: str
    details: A01Details | A02Details | A03Details | A04Details = Field(discriminator="kind")

    @model_validator(mode="after")
    def derived_flags_are_consistent(self) -> AssumptionAssessment:
        if self.eligible_for_downstream_substitution != permits_substitution(
            self.analytical_eligibility
        ):
            raise ValueError("substitution flag contradicts analytical_eligibility")
        if self.normalized_successfully != (self.normalization_outcome in CANONICAL_OUTCOMES):
            raise ValueError("normalized_successfully contradicts normalization_outcome")
        return self


class CanonicalOutputRecord(FrozenModel):
    relative_path: str
    sha256: str
    record_count: int
    tracked_in_git: bool
    redistribution_basis: str


class NormalizationReport(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    phase: Literal["0D.2"] = "0D.2"
    normalization_version: str = NORMALIZATION_VERSION
    preregistration: str = PREREGISTRATION_DOC
    analytical_crs: str = ANALYTICAL_CRS
    analytical_domain_envelope: Envelope = COMUNIDAD_MADRID_ENVELOPE
    artifacts: tuple[ArtifactEvidence, ...]
    assumptions: tuple[AssumptionAssessment, ...]
    gate: GateDecision
    canonical_outputs: tuple[CanonicalOutputRecord, ...]
    non_claims: tuple[str, ...] = NON_CLAIMS
    stop_rule: str = STOP_RULE


@dataclass(frozen=True)
class CanonicalOutput:
    record: CanonicalOutputRecord
    content: bytes


@dataclass(frozen=True)
class NormalizationRun:
    report: NormalizationReport
    outputs: tuple[CanonicalOutput, ...]

    def report_bytes(self) -> bytes:
        return canonical_json_bytes(self.report)


def run_normalization(*, ledger_dir: Path, raw_dir: Path) -> NormalizationRun:
    artifacts = load_evidence(ledger_dir, raw_dir)
    transformer = make_analytical_transformer()
    a01 = _assess_a01(artifacts)
    a02, a02_outputs = _assess_a02(artifacts, transformer)
    a03, a03_outputs = _assess_a03(artifacts, transformer)
    a04, a04_outputs = _assess_a04(artifacts, transformer)
    assessments = (a01, a02, a03, a04)
    gate = evaluate_gate(
        {assessment.assumption: assessment.analytical_eligibility for assessment in assessments},
        integrity_failures=[
            artifact.evidence.ref
            for artifact in artifacts
            if artifact.evidence.integrity is Integrity.FAIL
        ],
    )
    outputs = (*a02_outputs, *a03_outputs, *a04_outputs)
    report = NormalizationReport(
        artifacts=tuple(artifact.evidence for artifact in artifacts),
        assumptions=assessments,
        gate=gate,
        canonical_outputs=tuple(output.record for output in outputs),
    )
    run = NormalizationRun(report=report, outputs=outputs)
    assert_no_secret_markers(run.report_bytes(), where=REPORT_PATH)
    for output in outputs:
        if output.record.tracked_in_git:
            assert_no_secret_markers(output.content, where=output.record.relative_path)
    return run


def write_run(run: NormalizationRun, *, output_root: Path) -> tuple[Path, ...]:
    targets = [(output.record.relative_path, output.content) for output in run.outputs]
    targets.append((REPORT_PATH, run.report_bytes()))
    written: list[Path] = []
    for relative_path, content in targets:
        path = output_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        written.append(path)
    return tuple(written)


def _assessment(
    assumption: str,
    *,
    artifacts: Sequence[LoadedArtifact],
    outcome: NormalizationOutcome,
    structural: StructuralValidity,
    fitness: SemanticFitness,
    completeness: Completeness,
    eligibility: Eligibility,
    details: A01Details | A02Details | A03Details | A04Details,
    reason: str,
    blockers: Sequence[str] = (),
    scope_restrictions: Sequence[str] = (),
) -> AssumptionAssessment:
    return AssumptionAssessment(
        assumption=assumption,
        target_role=TARGET_ROLES[assumption],
        evidence_acquired=bool(artifacts),
        artifacts=tuple(artifact.evidence.ref for artifact in artifacts),
        normalization_outcome=outcome,
        normalized_successfully=outcome in CANONICAL_OUTCOMES,
        integrity=aggregate_integrity(artifact.evidence.integrity for artifact in artifacts),
        structural_validity=structural,
        semantic_fitness=fitness,
        completeness=completeness,
        analytical_eligibility=eligibility,
        eligible_for_downstream_substitution=permits_substitution(eligibility),
        scope_restrictions=tuple(scope_restrictions),
        blockers=tuple(blockers),
        reason=reason,
        details=details,
    )


def _unassessable(
    assumption: str,
    artifacts: Sequence[LoadedArtifact],
    *,
    details: A01Details | A02Details | A03Details | A04Details,
    blocker: str,
    failed: bool,
) -> AssumptionAssessment:
    """Unknown stays unknown: no favourable default for anything not normalized."""

    return _assessment(
        assumption,
        artifacts=artifacts,
        outcome=NormalizationOutcome.FAILED if failed else NormalizationOutcome.NOT_ATTEMPTED,
        structural=StructuralValidity.INVALID if failed else StructuralValidity.NOT_NORMALIZED,
        fitness=SemanticFitness.UNKNOWN,
        completeness=Completeness.UNKNOWN,
        eligibility=Eligibility.NOT_ELIGIBLE,
        details=details,
        reason=blocker,
        blockers=(blocker,),
    )


def _single_verified_source(
    candidates: Sequence[LoadedArtifact], *, allowed: frozenset[str], label: str
) -> tuple[LoadedArtifact | None, str]:
    sources = [a for a in candidates if a.evidence.ledger_classification in allowed]
    if len(sources) != 1:
        return None, f"{label}: expected exactly one data artifact, found {len(sources)}"
    source = sources[0]
    if source.verified_bytes is None:
        detail = f"{source.evidence.integrity}: {source.evidence.integrity_detail}"
        return None, f"{label}: {source.evidence.ref} not verified ({detail})"
    return source, ""


def _any_verified(artifacts: Sequence[LoadedArtifact]) -> bool:
    return any(artifact.evidence.integrity is Integrity.PASS for artifact in artifacts)


# --- A-01 --------------------------------------------------------------------------------


def _assess_a01(artifacts: Sequence[LoadedArtifact]) -> AssumptionAssessment:
    egif = [artifact for artifact in artifacts if artifact.evidence.assumption == "A-01"]
    evidence = [
        EgifArtifactEvidence(
            artifact_ref=artifact.evidence.ref,
            integrity=artifact.evidence.integrity,
            ledger_classification=artifact.evidence.ledger_classification,
        )
        for artifact in egif
    ]
    observability = derive_a01_observability(evidence)
    eligibility = a01_eligibility(observability)
    observable = observability.ttfrp_baseline_status is BaselineStatus.OBSERVABLE
    blockers: list[str] = []
    if any(
        artifact.evidence.ledger_classification == REAL_SOURCE_DATA
        and artifact.evidence.integrity is Integrity.PASS
        for artifact in egif
    ):
        blockers.append(
            "an A-01 REAL_SOURCE_DATA artifact exists but 0D.2 has no incident-record parser; "
            "it stays unobserved"
        )
    if not observable:
        blockers.append(
            "no integrity-verified incident-level records with detection and first-arrival "
            "timestamps (BASELINE_NOT_OBSERVABLE)"
        )
    classifications = sorted({artifact.evidence.ledger_classification for artifact in egif})
    return _assessment(
        "A-01",
        artifacts=egif,
        outcome=(
            NormalizationOutcome.OBSERVABILITY_RECORD_ONLY
            if egif
            else NormalizationOutcome.NOT_ATTEMPTED
        ),
        structural=StructuralValidity.VALID if observable else StructuralValidity.NOT_NORMALIZED,
        fitness=(
            fitness_from_eligibility(eligibility)
            if _any_verified(egif)
            else SemanticFitness.UNKNOWN
        ),
        completeness=Completeness.UNKNOWN if observable else Completeness.NOT_OBSERVED,
        eligibility=eligibility,
        details=A01Details(
            observability=observability,
            note=(
                "public EGIF interface available != observable incident-level TTFRP baseline; "
                "no proxy TTFRP generated; baseline design belongs to Phase 0E"
            ),
        ),
        reason=(
            f"{len(egif)} EGIF artifacts classified {classifications}; "
            f"ttfrp_baseline_status={observability.ttfrp_baseline_status}"
        ),
        blockers=blockers,
    )


# --- A-02 --------------------------------------------------------------------------------


def _assess_a02(
    artifacts: Sequence[LoadedArtifact], transformer: Transformer
) -> tuple[AssumptionAssessment, tuple[CanonicalOutput, ...]]:
    candidates = [a for a in artifacts if a.evidence.probe_id == FIRE_STATION_PROBE_ID]
    descriptor = MADRID_CITY_FIRE_STATIONS

    def details(checks: A02QualityChecks | None) -> A02Details:
        return A02Details(
            source_manifest_dataset_id=descriptor.manifest_dataset_id,
            declared_coverage=descriptor.declared_coverage,
            license=descriptor.license,
            attribution=descriptor.attribution,
            source_crs_interpretation=SOURCE_CRS_INTERPRETATION,
            not_inferred=dict.fromkeys(NOT_INFERRED_PROPERTIES, NOT_EVALUATED),
            checks=checks,
        )

    source, blocker = _single_verified_source(
        candidates, allowed=frozenset({REAL_SOURCE_DATA}), label="A-02"
    )
    if source is None or source.verified_bytes is None:
        unassessed = _unassessable(
            "A-02", candidates, details=details(None), blocker=blocker, failed=False
        )
        return unassessed, ()
    try:
        result = normalize_fire_stations(
            source.verified_bytes,
            source=source.evidence,
            transformer=transformer,
            descriptor=descriptor,
        )
    except MalformedEvidenceError as exc:
        failed = _unassessable(
            "A-02", candidates, details=details(None), blocker=f"A-02: {exc}", failed=True
        )
        return failed, ()

    eligibility = a02_eligibility(
        source.evidence.integrity, result.structural_validity, result.completeness
    )
    checks = result.checks
    content = canonical_json_bytes(result.dataset)
    output = CanonicalOutput(
        record=CanonicalOutputRecord(
            relative_path=A02_CANONICAL_PATH,
            sha256=sha256_hex(content),
            record_count=checks.canonical_record_count,
            tracked_in_git=True,
            redistribution_basis=(
                f"{descriptor.license} per data/datasets_manifest.json "
                f"({descriptor.manifest_dataset_id}); attribution: {descriptor.attribution}"
            ),
        ),
        content=content,
    )
    blockers: list[str] = []
    if checks.rejected_records:
        blockers.append(f"{len(checks.rejected_records)} source records rejected")
    if checks.duplicate_coordinate_groups:
        blockers.append(
            f"{len(checks.duplicate_coordinate_groups)} duplicate-coordinate groups need review"
        )
    if descriptor.declared_coverage is not DeclaredCoverage.COMUNIDAD_DE_MADRID:
        blockers.append(
            "full analytical-domain substitution blocked: declared source coverage is "
            f"{descriptor.declared_coverage}, not the Comunidad de Madrid"
        )
    assessment = _assessment(
        "A-02",
        artifacts=candidates,
        outcome=NormalizationOutcome.CANONICAL_DATASET,
        structural=result.structural_validity,
        fitness=fitness_from_eligibility(eligibility),
        completeness=result.completeness,
        eligibility=eligibility,
        details=details(checks),
        reason=(
            f"{checks.canonical_record_count} of {checks.source_record_count} source records "
            f"canonicalized; {len(checks.rejected_records)} rejected; "
            f"{len(checks.duplicate_coordinate_groups)} duplicate-coordinate groups; "
            f"declared coverage {descriptor.declared_coverage}"
        ),
        blockers=blockers,
        scope_restrictions=(
            (
                f"restricted to declared coverage {descriptor.declared_coverage}; existence and "
                "location only (operational properties NOT_EVALUATED)"
            ),
        ),
    )
    return assessment, (output,)


# --- A-03 --------------------------------------------------------------------------------


def _assess_a03(
    artifacts: Sequence[LoadedArtifact], transformer: Transformer
) -> tuple[AssumptionAssessment, tuple[CanonicalOutput, ...]]:
    a03 = [artifact for artifact in artifacts if artifact.evidence.assumption == "A-03"]
    airspace, airspace_outputs, airspace_blockers = _airspace_component(a03, transformer)
    terrain, terrain_blockers = _terrain_component(a03)
    components = [c.scope for c in (airspace, terrain) if c is not None]
    eligibility = rollup_a03_eligibility(
        airspace.scope.analytical_eligibility if airspace else None,
        terrain.scope.analytical_eligibility if terrain else None,
    )
    structural_values = (
        airspace.structural_validity if airspace else StructuralValidity.NOT_NORMALIZED,
        terrain.structural_validity if terrain else StructuralValidity.NOT_NORMALIZED,
    )
    completeness_values = {scope.completeness for scope in components}
    if airspace is None or terrain is None:
        completeness_values.add(Completeness.UNKNOWN)
    if components:
        outcome = NormalizationOutcome.CANONICAL_BOUNDED_SAMPLE
    else:
        outcome = NormalizationOutcome.FAILED if a03 else NormalizationOutcome.NOT_ATTEMPTED
    assessment = _assessment(
        "A-03",
        artifacts=a03,
        outcome=outcome,
        structural=_rollup_structural(structural_values),
        fitness=fitness_from_eligibility(eligibility) if components else SemanticFitness.UNKNOWN,
        completeness=next(c for c in _COMPLETENESS_WORST_FIRST if c in completeness_values),
        eligibility=eligibility,
        details=A03Details(
            airspace=airspace,
            terrain=terrain,
            metadata_only_artifacts=tuple(
                a.evidence.ref for a in a03 if a.evidence.ledger_classification == REAL_METADATA
            ),
        ),
        reason=(
            "; ".join(
                f"{scope.source_probe_id}: {scope.evidence_scope}, {scope.completeness}, "
                f"eligible_for_full_madrid_analysis={scope.eligible_for_full_madrid_analysis}"
                for scope in components
            )
            or "no A-03 data component normalized"
        ),
        blockers=(*airspace_blockers, *terrain_blockers),
        scope_restrictions=tuple(
            f"{scope.source_probe_id}: bounded_sample={scope.bounded_sample}; coverage_extent "
            f"{scope.coverage_extent.crs} [{scope.coverage_extent.min_x}, "
            f"{scope.coverage_extent.min_y}, {scope.coverage_extent.max_x}, "
            f"{scope.coverage_extent.max_y}]"
            for scope in components
        ),
    )
    return assessment, airspace_outputs


def _airspace_component(
    a03: Sequence[LoadedArtifact], transformer: Transformer
) -> tuple[AirspaceSampleAssessment | None, tuple[CanonicalOutput, ...], tuple[str, ...]]:
    candidates = [a for a in a03 if a.evidence.probe_id == ENAIRE_PROBE_ID]
    source, blocker = _single_verified_source(
        candidates, allowed=frozenset({REAL_BOUNDED_SAMPLE}), label="A-03 airspace"
    )
    if source is None or source.verified_bytes is None:
        return None, (), (blocker,)
    try:
        assessment, sample = normalize_airspace_sample(
            source.verified_bytes, source=source.evidence, transformer=transformer
        )
    except MalformedEvidenceError as exc:
        return None, (), (f"A-03 airspace: {exc}",)
    content = canonical_json_bytes(sample)
    output = CanonicalOutput(
        record=CanonicalOutputRecord(
            relative_path=A03_AIRSPACE_PROCESSED_PATH,
            sha256=sha256_hex(content),
            record_count=len(sample.zones),
            tracked_in_git=False,
            redistribution_basis=(
                "ENAIRE AIS terms (attribution required; never for operational use): "
                "record-level derivative kept in gitignored data/processed"
            ),
        ),
        content=content,
    )
    blockers: list[str] = []
    if assessment.scope.completeness is Completeness.TRUNCATED_BY_SOURCE:
        blockers.append(
            "ENAIRE response truncated by source "
            f"(exceededTransferLimit={assessment.exceeded_transfer_limit}, "
            f"{assessment.feature_count} features, "
            f"resultRecordCount cap {assessment.result_record_count_cap})"
        )
    if assessment.scope.bounded_sample:
        blockers.append("ENAIRE request envelope is a bounded subset of the analytical domain")
    if assessment.invalid_geometry_count:
        blockers.append(f"{assessment.invalid_geometry_count} invalid geometries (not repaired)")
    return assessment, (output,), tuple(blockers)


def _terrain_component(
    a03: Sequence[LoadedArtifact],
) -> tuple[TerrainSampleAssessment | None, tuple[str, ...]]:
    candidates = [a for a in a03 if a.evidence.probe_id == MDT05_PROBE_ID]
    source, blocker = _single_verified_source(
        candidates, allowed=frozenset({REAL_SOURCE_DATA}), label="A-03 terrain"
    )
    if source is None or source.verified_bytes is None:
        return None, (blocker,)
    try:
        assessment = assess_terrain_sample(source.verified_bytes, source=source.evidence)
    except MalformedEvidenceError as exc:
        return None, (f"A-03 terrain: {exc}",)
    extent = assessment.requested_extent
    width, height = extent.max_x - extent.min_x, extent.max_y - extent.min_y
    return assessment, (
        f"MDT05 artifact is a fixed {width:g} m x {height:g} m pipeline-reproducibility window "
        "(declared purpose), not a terrain layer",
    )


def _rollup_structural(values: Sequence[StructuralValidity]) -> StructuralValidity:
    if all(value is StructuralValidity.VALID for value in values):
        return StructuralValidity.VALID
    parsed = {StructuralValidity.VALID, StructuralValidity.VALID_WITH_FLAGS}
    if any(value in parsed for value in values):
        return StructuralValidity.VALID_WITH_FLAGS
    if StructuralValidity.INVALID in values:
        return StructuralValidity.INVALID
    return StructuralValidity.NOT_NORMALIZED


# --- A-04 --------------------------------------------------------------------------------

_InventoryResult = tuple[CanonicalWeatherStationInventory, InventoryQuality]


def _assess_a04(
    artifacts: Sequence[LoadedArtifact], transformer: Transformer
) -> tuple[AssumptionAssessment, tuple[CanonicalOutput, ...]]:
    a04 = [artifact for artifact in artifacts if artifact.evidence.assumption == "A-04"]
    results = [_weather_evidence(artifact, transformer) for artifact in a04]
    evidence = [result[0] for result in results]
    inventories = [item for result in results if (item := result[1]) is not None]
    blockers = [message for result in results if (message := result[2])]

    readiness = derive_a04_readiness(evidence, fire_dates=frozenset())
    eligibility = a04_eligibility(readiness)
    quality: InventoryQuality | None = None
    outputs: tuple[CanonicalOutput, ...] = ()
    if len(inventories) == 1:
        inventory, quality = inventories[0]
        content = canonical_json_bytes(inventory)
        outputs = (
            CanonicalOutput(
                record=CanonicalOutputRecord(
                    relative_path=A04_INVENTORY_PROCESSED_PATH,
                    sha256=sha256_hex(content),
                    record_count=len(inventory.records),
                    tracked_in_git=False,
                    redistribution_basis=(
                        "AEMET OpenData reuse terms (product notice must be retained): "
                        "record-level derivative kept in gitignored data/processed"
                    ),
                ),
                content=content,
            ),
        )
    elif len(inventories) > 1:
        blockers.append("more than one station-inventory artifact; none chosen silently")
    if not readiness.historical_observations_available:
        blockers.append("no integrity-verified REAL observation series (dated measurements)")
    if not readiness.fire_day_observations_available:
        blockers.append("no REAL Madrid fire-date set with covering observations")
    if not readiness.weather_falsification_ready:
        blockers.append(
            "wind and visibility fire-day observations unavailable "
            "(WEATHER_EVIDENCE_NOT_OBSERVABLE)"
        )

    if readiness.weather_falsification_ready:
        outcome = NormalizationOutcome.CANONICAL_DATASET
    elif quality is not None:
        outcome = NormalizationOutcome.CANONICAL_INVENTORY_ONLY
    else:
        outcome = NormalizationOutcome.NOT_ATTEMPTED
    assessment = _assessment(
        "A-04",
        artifacts=a04,
        outcome=outcome,
        structural=quality.structural_validity if quality else StructuralValidity.NOT_NORMALIZED,
        fitness=(
            fitness_from_eligibility(eligibility) if _any_verified(a04) else SemanticFitness.UNKNOWN
        ),
        completeness=(
            Completeness.UNKNOWN
            if readiness.weather_falsification_ready
            else Completeness.NOT_OBSERVED
        ),
        eligibility=eligibility,
        details=A04Details(
            readiness=readiness,
            artifact_content_types={
                item.artifact_ref: str(item.content_type) if item.content_type else "UNVERIFIED"
                for item in evidence
            },
            inventory_quality=quality,
            fire_date_source=FIRE_DATE_SOURCE,
        ),
        reason=(
            f"station_inventory_available={readiness.station_inventory_available}; "
            f"historical_observations_available={readiness.historical_observations_available}; "
            f"fire_day_observations_available={readiness.fire_day_observations_available}; "
            f"weather_falsification_ready={readiness.weather_falsification_ready}"
        ),
        blockers=blockers,
        scope_restrictions=(
            "station inventory describes where stations are, not what they observed",
        ),
    )
    return assessment, outputs


def _weather_evidence(
    artifact: LoadedArtifact, transformer: Transformer
) -> tuple[WeatherArtifactEvidence, _InventoryResult | None, str]:
    evidence = artifact.evidence

    def item(
        content_type: AemetContentType | None, madrid_records: int = 0
    ) -> WeatherArtifactEvidence:
        return WeatherArtifactEvidence(
            artifact_ref=evidence.ref,
            integrity=evidence.integrity,
            ledger_classification=evidence.ledger_classification,
            content_type=content_type,
            valid_madrid_record_count=madrid_records,
        )

    if artifact.verified_bytes is None:
        return item(None), None, f"{evidence.ref} not verified ({evidence.integrity})"
    try:
        payload = decode_json_payload(
            artifact.verified_bytes, content_type=evidence.content_type, where=evidence.ref
        )
    except MalformedEvidenceError as exc:
        return item(AemetContentType.UNRECOGNIZED), None, str(exc)
    content_type = detect_aemet_content_type(payload)
    if content_type is AemetContentType.OBSERVATION_SERIES:
        return (
            item(content_type),
            None,
            f"{evidence.ref} looks like an observation series but 0D.2 has no observation "
            "parser; it stays unobserved",
        )
    if (
        content_type is not AemetContentType.STATION_INVENTORY
        or evidence.ledger_classification != REAL_SOURCE_DATA
    ):
        return item(content_type), None, ""
    try:
        inventory, quality = normalize_station_inventory(
            artifact.verified_bytes, source=evidence, transformer=transformer
        )
    except MalformedEvidenceError as exc:
        return item(content_type), None, str(exc)
    return item(content_type, quality.madrid_canonical_record_count), (inventory, quality), ""

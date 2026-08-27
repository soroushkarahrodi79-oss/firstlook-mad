"""Validated domain models for the Phase 0C synthetic experiment."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

ANALYTICAL_CRS = "EPSG:25830"
MIN_ROBUSTNESS_SEEDS = 2


class FrozenModel(BaseModel):
    """Immutable, strict model used for auditable simulation inputs."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class EvidenceNature(StrEnum):
    ASSUMED = "ASSUMED"
    SYNTHETIC = "SYNTHETIC"


class ZoneState(StrEnum):
    UNKNOWN = "UNKNOWN"
    POTENTIALLY_ALLOWED = "POTENTIALLY_ALLOWED"
    RESTRICTED = "RESTRICTED"
    REQUIRES_AUTHORIZATION = "REQUIRES_AUTHORIZATION"
    TEMPORARILY_RESTRICTED = "TEMPORARILY_RESTRICTED"
    NOT_EVALUATED = "NOT_EVALUATED"


class GateOutcome(StrEnum):
    GO_SIMULATION = "GO_SIMULATION"
    NO_GO = "NO_GO"
    UNKNOWN = "UNKNOWN"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


class FactorState(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


class CoverageModel(StrEnum):
    A_DISTANCE = "A_DISTANCE"
    B_TRAVEL_TIME = "B_TRAVEL_TIME"
    C_RELIEF = "C_RELIEF"
    D_AIRSPACE = "D_AIRSPACE"
    E_WEATHER = "E_WEATHER"
    F_ENERGY = "F_ENERGY"


class ProjectedPoint(FrozenModel):
    crs: str = ANALYTICAL_CRS
    easting_m: float = Field(ge=250_000.0, le=750_000.0)
    northing_m: float = Field(ge=3_900_000.0, le=4_900_000.0)

    @model_validator(mode="after")
    def require_analytical_crs(self) -> ProjectedPoint:
        if self.crs != ANALYTICAL_CRS:
            raise ValueError(f"metric analysis requires {ANALYTICAL_CRS}")
        return self


class Incident(FrozenModel):
    incident_id: str = Field(min_length=1)
    point: ProjectedPoint
    risk_weight: float = Field(gt=0.0)
    terrain_multiplier: float = Field(ge=1.0, le=2.0)
    airspace: ZoneState
    temporary_restriction: bool | None
    manned_aircraft_conflict: bool | None
    incident_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    data_age_minutes: float | None = Field(default=None, ge=0.0)
    nature: EvidenceNature = EvidenceNature.SYNTHETIC


class CandidateSite(FrozenModel):
    site_id: str = Field(min_length=1)
    point: ProjectedPoint
    assumed_available: bool | None
    uas_available: bool | None
    communications_available: bool | None
    camera_available: bool | None
    camera_communications_available: bool | None
    nature: EvidenceNature = EvidenceNature.SYNTHETIC


class UASPerformanceProfile(FrozenModel):
    profile_id: str = Field(min_length=1)
    cruise_speed_mps: float = Field(gt=0.0)
    max_sortie_distance_m: float = Field(gt=0.0)
    reserve_fraction: float = Field(ge=0.0, lt=0.5)
    max_wind_mps: float = Field(gt=0.0)
    max_precipitation_mm_h: float = Field(ge=0.0)
    min_visibility_m: float = Field(gt=0.0)
    min_temperature_c: float
    max_temperature_c: float
    minimum_battery_fraction: float = Field(gt=0.0, le=1.0)
    nature: EvidenceNature = EvidenceNature.ASSUMED

    @model_validator(mode="after")
    def validate_temperature_range(self) -> UASPerformanceProfile:
        if self.min_temperature_c >= self.max_temperature_c:
            raise ValueError("min_temperature_c must be below max_temperature_c")
        return self


class TTFRPAssumptions(FrozenModel):
    scenario_id: str = Field(min_length=1)
    alert_processing_s: float = Field(ge=0.0)
    verification_s: float = Field(ge=0.0)
    preflight_gate_s: float = Field(ge=0.0)
    launch_s: float = Field(ge=0.0)
    scene_acquisition_s: float = Field(ge=0.0)
    first_analysis_s: float = Field(ge=0.0)
    nature: EvidenceNature = EvidenceNature.ASSUMED

    @property
    def non_travel_seconds(self) -> float:
        return (
            self.alert_processing_s
            + self.verification_s
            + self.preflight_gate_s
            + self.launch_s
            + self.scene_acquisition_s
            + self.first_analysis_s
        )


class WeatherScenario(FrozenModel):
    scenario_id: str = Field(min_length=1)
    wind_mps: float | None = Field(default=None, ge=0.0)
    precipitation_mm_h: float | None = Field(default=None, ge=0.0)
    visibility_m: float | None = Field(default=None, ge=0.0)
    temperature_c: float | None = None
    nature: EvidenceNature = EvidenceNature.ASSUMED


class CameraAssumptions(FrozenModel):
    radius_m: float = Field(gt=0.0)
    picture_latency_s: float = Field(ge=0.0)
    architecture_specific_latency_s: float = Field(ge=0.0)
    nature: EvidenceNature = EvidenceNature.ASSUMED


class GatePolicy(FrozenModel):
    """Switches used only for transparent synthetic ablation."""

    range: bool = True
    reserve: bool = True
    site_availability: bool = True
    uas_availability: bool = True
    battery: bool = True
    communications: bool = True
    incident_confidence: bool = True
    data_freshness: bool = True
    airspace: bool = True
    temporary_restriction: bool = True
    manned_aircraft_conflict: bool = True
    weather: bool = True


class SyntheticBounds(FrozenModel):
    min_easting_m: float
    max_easting_m: float
    min_northing_m: float
    max_northing_m: float

    @model_validator(mode="after")
    def validate_bounds(self) -> SyntheticBounds:
        if self.min_easting_m >= self.max_easting_m:
            raise ValueError("easting bounds are reversed")
        if self.min_northing_m >= self.max_northing_m:
            raise ValueError("northing bounds are reversed")
        ProjectedPoint(easting_m=self.min_easting_m, northing_m=self.min_northing_m)
        ProjectedPoint(easting_m=self.max_easting_m, northing_m=self.max_northing_m)
        return self


class SyntheticConfig(FrozenModel):
    schema_version: str
    scenario_id: str
    crs: str
    seed: int = Field(ge=0)
    incident_count: int = Field(ge=1, le=100_000)
    site_count: int = Field(ge=1, le=1_000)
    bounds: SyntheticBounds
    network_sizes: tuple[int, ...]
    profiles: tuple[UASPerformanceProfile, ...]
    reference_profile_id: str
    ttfrp_scenarios: tuple[TTFRPAssumptions, ...]
    weather_scenarios: tuple[WeatherScenario, ...]
    camera: CameraAssumptions
    battery_fraction: float = Field(gt=0.0, le=1.0)
    max_data_age_minutes: float = Field(gt=0.0)
    minimum_incident_confidence: float = Field(ge=0.0, le=1.0)
    robustness_seeds: tuple[int, ...]
    sample_sizes: tuple[int, ...]
    a01_sweep_max_seconds: int = Field(ge=0)
    a01_sweep_step_seconds: int = Field(gt=0)
    assumptions_note: str = Field(min_length=1)
    nature: EvidenceNature = EvidenceNature.SYNTHETIC

    @model_validator(mode="after")
    def validate_config(self) -> SyntheticConfig:
        if self.crs != ANALYTICAL_CRS:
            raise ValueError(f"config CRS must be {ANALYTICAL_CRS}")
        if not self.network_sizes:
            raise ValueError("network_sizes must not be empty")
        if tuple(sorted(set(self.network_sizes))) != self.network_sizes:
            raise ValueError("network_sizes must be unique and increasing")
        if self.network_sizes[-1] > self.site_count:
            raise ValueError("network size exceeds site count")
        if not self.profiles or not self.ttfrp_scenarios or not self.weather_scenarios:
            raise ValueError("TTFRP and weather scenarios are required")
        if len(set(self.robustness_seeds)) < MIN_ROBUSTNESS_SEEDS:
            raise ValueError("at least two unique robustness seeds are required")
        if not self.sample_sizes or any(size < 1 for size in self.sample_sizes):
            raise ValueError("sample_sizes must contain positive values")
        if self.a01_sweep_max_seconds % self.a01_sweep_step_seconds != 0:
            raise ValueError("A-01 sweep max must be divisible by its step")
        profile_ids = [profile.profile_id for profile in self.profiles]
        if len(set(profile_ids)) != len(profile_ids):
            raise ValueError("profile ids must be unique")
        if self.reference_profile_id not in profile_ids:
            raise ValueError("reference_profile_id is not present in profiles")
        return self

    @property
    def reference_profile(self) -> UASPerformanceProfile:
        return next(
            profile for profile in self.profiles if profile.profile_id == self.reference_profile_id
        )


class FactorCheck(FrozenModel):
    factor: str
    state: FactorState
    detail: str


class GateResult(FrozenModel):
    outcome: GateOutcome
    primary_reason: str | None
    checks: tuple[FactorCheck, ...]


class PairEvaluation(FrozenModel):
    incident_id: str
    site_id: str
    model: CoverageModel
    feasible: bool
    distance_m: float = Field(ge=0.0)
    effective_distance_m: float = Field(ge=0.0)
    travel_seconds: float | None = Field(default=None, ge=0.0)
    ttfrp_seconds: float | None = Field(default=None, ge=0.0)
    gate: GateResult

"""Deterministic generation of explicitly synthetic incidents and sites."""

from __future__ import annotations

import json
import random
from pathlib import Path

from firstlook_mad.domain import (
    CandidateSite,
    Incident,
    ProjectedPoint,
    SyntheticConfig,
    ZoneState,
)

SITE_STREAM_REFERENCE_INCIDENTS = 180


def _site_random_stream(seed: int) -> random.Random:
    """Preserve the 0C baseline sites without coupling them to sample size."""

    generator = random.Random(seed)
    for index in range(SITE_STREAM_REFERENCE_INCIDENTS):
        if index % 31 != 0:
            generator.random()
        if index % 41 != 0:
            generator.random()
        for _ in range(4):
            generator.random()
    return generator


def load_config(path: Path) -> SyntheticConfig:
    """Load and validate a Phase 0C configuration."""

    document = json.loads(path.read_text(encoding="utf-8"))
    return SyntheticConfig.model_validate(document)


def _zone_for(index: int) -> ZoneState:
    if index % 29 == 0:
        return ZoneState.UNKNOWN
    if index % 13 == 0:
        return ZoneState.RESTRICTED
    if index % 11 == 0:
        return ZoneState.REQUIRES_AUTHORIZATION
    return ZoneState.POTENTIALLY_ALLOWED


def generate_inputs(config: SyntheticConfig) -> tuple[list[Incident], list[CandidateSite]]:
    """Generate repeatable fixtures; no values represent real Madrid assets."""

    incident_generator = random.Random(config.seed)
    site_generator = _site_random_stream(config.seed)
    bounds = config.bounds
    incidents: list[Incident] = []
    for index in range(config.incident_count):
        confidence = None if index % 31 == 0 else incident_generator.uniform(0.70, 1.0)
        data_age = None if index % 41 == 0 else incident_generator.uniform(0.0, 120.0)
        incidents.append(
            Incident(
                incident_id=f"SYN-INC-{index:04d}",
                point=ProjectedPoint(
                    easting_m=incident_generator.uniform(
                        bounds.min_easting_m, bounds.max_easting_m
                    ),
                    northing_m=incident_generator.uniform(
                        bounds.min_northing_m,
                        bounds.max_northing_m,
                    ),
                ),
                risk_weight=incident_generator.uniform(0.5, 5.0),
                terrain_multiplier=incident_generator.uniform(1.0, 1.35),
                airspace=_zone_for(index),
                temporary_restriction=index % 17 == 0,
                manned_aircraft_conflict=(None if index % 23 == 0 else index % 19 == 0),
                incident_confidence=confidence,
                data_age_minutes=data_age,
            )
        )

    sites: list[CandidateSite] = []
    for index in range(config.site_count):
        sites.append(
            CandidateSite(
                site_id=f"SYN-SITE-{index:03d}",
                point=ProjectedPoint(
                    easting_m=site_generator.uniform(bounds.min_easting_m, bounds.max_easting_m),
                    northing_m=site_generator.uniform(
                        bounds.min_northing_m,
                        bounds.max_northing_m,
                    ),
                ),
                assumed_available=index % 7 != 0,
                uas_available=index % 8 != 0,
                communications_available=index % 9 != 0,
                camera_available=index % 6 != 0,
                camera_communications_available=index % 10 != 0,
            )
        )
    return incidents, sites

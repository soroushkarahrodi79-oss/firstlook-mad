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

    generator = random.Random(config.seed)
    bounds = config.bounds
    incidents: list[Incident] = []
    for index in range(config.incident_count):
        confidence = None if index % 31 == 0 else generator.uniform(0.70, 1.0)
        data_age = None if index % 41 == 0 else generator.uniform(0.0, 120.0)
        incidents.append(
            Incident(
                incident_id=f"SYN-INC-{index:04d}",
                point=ProjectedPoint(
                    easting_m=generator.uniform(bounds.min_easting_m, bounds.max_easting_m),
                    northing_m=generator.uniform(
                        bounds.min_northing_m,
                        bounds.max_northing_m,
                    ),
                ),
                risk_weight=generator.uniform(0.5, 5.0),
                terrain_multiplier=generator.uniform(1.0, 1.35),
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
                    easting_m=generator.uniform(bounds.min_easting_m, bounds.max_easting_m),
                    northing_m=generator.uniform(
                        bounds.min_northing_m,
                        bounds.max_northing_m,
                    ),
                ),
                assumed_available=index % 7 != 0,
                uas_available=index % 8 != 0,
                communications_available=index % 9 != 0,
            )
        )
    return incidents, sites

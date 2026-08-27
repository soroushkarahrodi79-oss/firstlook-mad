"""Conservative, deterministic simulation gate with explicit failure order."""

from __future__ import annotations

from firstlook_mad.domain import (
    CandidateSite,
    FactorCheck,
    FactorState,
    GateOutcome,
    GatePolicy,
    GateResult,
    Incident,
    UASPerformanceProfile,
    WeatherScenario,
    ZoneState,
)


def _known_boolean(name: str, value: bool | None, *, fail_when: bool) -> FactorCheck:
    if value is None:
        return FactorCheck(factor=name, state=FactorState.UNKNOWN, detail="value unavailable")
    failed = value is fail_when
    state = FactorState.FAIL if failed else FactorState.PASS
    return FactorCheck(factor=name, state=state, detail=f"observed={value}")


def _threshold(
    name: str,
    value: float | None,
    *,
    passes: bool,
    detail: str,
) -> FactorCheck:
    if value is None:
        return FactorCheck(factor=name, state=FactorState.UNKNOWN, detail="value unavailable")
    return FactorCheck(
        factor=name,
        state=FactorState.PASS if passes else FactorState.FAIL,
        detail=detail,
    )


def _airspace_check(state: ZoneState) -> FactorCheck:
    if state is ZoneState.POTENTIALLY_ALLOWED:
        factor_state = FactorState.PASS
    elif state is ZoneState.REQUIRES_AUTHORIZATION:
        factor_state = FactorState.REQUIRES_HUMAN_REVIEW
    elif state in {ZoneState.UNKNOWN, ZoneState.NOT_EVALUATED}:
        factor_state = FactorState.UNKNOWN
    else:
        factor_state = FactorState.FAIL
    return FactorCheck(factor="airspace", state=factor_state, detail=f"zone={state.value}")


def _result(checks: list[FactorCheck]) -> GateResult:
    first = next((check for check in checks if check.state is not FactorState.PASS), None)
    if first is None:
        return GateResult(
            outcome=GateOutcome.GO_SIMULATION,
            primary_reason=None,
            checks=tuple(checks),
        )
    outcomes = {
        FactorState.FAIL: GateOutcome.NO_GO,
        FactorState.UNKNOWN: GateOutcome.UNKNOWN,
        FactorState.REQUIRES_HUMAN_REVIEW: GateOutcome.REQUIRES_HUMAN_REVIEW,
    }
    return GateResult(
        outcome=outcomes[first.state],
        primary_reason=first.factor,
        checks=tuple(checks),
    )


def assess_gate(
    *,
    incident: Incident,
    site: CandidateSite,
    profile: UASPerformanceProfile,
    weather: WeatherScenario,
    effective_distance_m: float,
    battery_fraction: float,
    max_data_age_minutes: float,
    minimum_incident_confidence: float,
    policy: GatePolicy,
) -> GateResult:
    """Evaluate ordered factors; any non-pass state prevents GO_SIMULATION."""

    checks: list[FactorCheck] = []
    if policy.site_availability:
        checks.append(_known_boolean("site_available", site.assumed_available, fail_when=False))
    if policy.uas_availability:
        checks.append(_known_boolean("uas_available", site.uas_available, fail_when=False))
    if policy.battery:
        checks.append(
            _threshold(
                "battery",
                battery_fraction,
                passes=battery_fraction >= profile.minimum_battery_fraction,
                detail=(
                    f"battery={battery_fraction:.3f}; "
                    f"minimum={profile.minimum_battery_fraction:.3f}"
                ),
            )
        )

    if policy.range:
        reserve = profile.reserve_fraction if policy.reserve else 0.0
        usable_sortie_m = profile.max_sortie_distance_m * battery_fraction * (1.0 - reserve)
        required_sortie_m = 2.0 * effective_distance_m
        checks.append(
            _threshold(
                "range",
                required_sortie_m,
                passes=required_sortie_m <= usable_sortie_m,
                detail=f"required={required_sortie_m:.1f}; usable={usable_sortie_m:.1f}",
            )
        )

    if policy.weather:
        checks.extend(
            [
                _threshold(
                    "wind",
                    weather.wind_mps,
                    passes=(
                        weather.wind_mps is not None and weather.wind_mps <= profile.max_wind_mps
                    ),
                    detail=f"wind={weather.wind_mps}; max={profile.max_wind_mps}",
                ),
                _threshold(
                    "precipitation",
                    weather.precipitation_mm_h,
                    passes=(
                        weather.precipitation_mm_h is not None
                        and weather.precipitation_mm_h <= profile.max_precipitation_mm_h
                    ),
                    detail=(
                        f"precip={weather.precipitation_mm_h}; max={profile.max_precipitation_mm_h}"
                    ),
                ),
                _threshold(
                    "visibility",
                    weather.visibility_m,
                    passes=(
                        weather.visibility_m is not None
                        and weather.visibility_m >= profile.min_visibility_m
                    ),
                    detail=(f"visibility={weather.visibility_m}; min={profile.min_visibility_m}"),
                ),
                _threshold(
                    "temperature",
                    weather.temperature_c,
                    passes=(
                        weather.temperature_c is not None
                        and profile.min_temperature_c
                        <= weather.temperature_c
                        <= profile.max_temperature_c
                    ),
                    detail=(
                        f"temperature={weather.temperature_c}; "
                        f"range=[{profile.min_temperature_c}, {profile.max_temperature_c}]"
                    ),
                ),
            ]
        )

    if policy.airspace:
        checks.append(_airspace_check(incident.airspace))
    if policy.temporary_restriction:
        checks.append(
            _known_boolean(
                "temporary_restriction",
                incident.temporary_restriction,
                fail_when=True,
            )
        )
    if policy.manned_aircraft_conflict:
        checks.append(
            _known_boolean(
                "manned_aircraft_conflict",
                incident.manned_aircraft_conflict,
                fail_when=True,
            )
        )
    if policy.communications:
        checks.append(
            _known_boolean(
                "communications",
                site.communications_available,
                fail_when=False,
            )
        )
    if policy.incident_confidence:
        checks.append(
            _threshold(
                "incident_confidence",
                incident.incident_confidence,
                passes=(
                    incident.incident_confidence is not None
                    and incident.incident_confidence >= minimum_incident_confidence
                ),
                detail=(
                    f"confidence={incident.incident_confidence}; "
                    f"minimum={minimum_incident_confidence}"
                ),
            )
        )
    if policy.data_freshness:
        checks.append(
            _threshold(
                "data_freshness",
                incident.data_age_minutes,
                passes=(
                    incident.data_age_minutes is not None
                    and incident.data_age_minutes <= max_data_age_minutes
                ),
                detail=(f"age={incident.data_age_minutes}; max={max_data_age_minutes} minutes"),
            )
        )
    return _result(checks)

"""Pre-registered Phase 0D.2 gate (docs/PHASE_0D2_PREREGISTRATION.md section 6)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from firstlook_mad.domain import FrozenModel
from firstlook_mad.normalization.models import (
    TARGET_ASSUMPTIONS,
    Eligibility,
    GateVerdict,
    permits_substitution,
)

GATE_RULE = (
    "NORMALIZATION_READY iff all four targets are ELIGIBLE and no in-scope artifact has "
    "integrity FAIL; PARTIAL_NORMALIZATION iff not READY and at least one target is "
    "ELIGIBLE or ELIGIBLE_WITHIN_DECLARED_SCOPE; SEMANTICALLY_INSUFFICIENT iff all four "
    "targets are NOT_ELIGIBLE"
)


class GateDecision(FrozenModel):
    verdict: GateVerdict
    rule: str
    eligibility_by_assumption: dict[str, Eligibility]
    eligible_assumptions: tuple[str, ...]
    scope_restricted_assumptions: tuple[str, ...]
    scope_restricted_includes_a02: bool
    integrity_failures: tuple[str, ...]


def evaluate_gate(
    eligibility: Mapping[str, Eligibility], *, integrity_failures: Sequence[str] = ()
) -> GateDecision:
    """Apply the frozen rule; a missing or extra assumption is an error, never a default."""

    if set(eligibility) != set(TARGET_ASSUMPTIONS):
        raise ValueError(
            f"gate requires exactly {list(TARGET_ASSUMPTIONS)}; got {sorted(eligibility)}"
        )
    ordered = {assumption: eligibility[assumption] for assumption in TARGET_ASSUMPTIONS}
    eligible = tuple(a for a, value in ordered.items() if value is Eligibility.ELIGIBLE)
    scoped = tuple(
        a for a, value in ordered.items() if value is Eligibility.ELIGIBLE_WITHIN_DECLARED_SCOPE
    )
    if len(eligible) == len(TARGET_ASSUMPTIONS) and not integrity_failures:
        verdict = GateVerdict.NORMALIZATION_READY
    elif any(permits_substitution(value) for value in ordered.values()):
        verdict = GateVerdict.PARTIAL_NORMALIZATION
    else:
        verdict = GateVerdict.SEMANTICALLY_INSUFFICIENT
    return GateDecision(
        verdict=verdict,
        rule=GATE_RULE,
        eligibility_by_assumption=ordered,
        eligible_assumptions=eligible,
        scope_restricted_assumptions=scoped,
        scope_restricted_includes_a02="A-02" in scoped,
        integrity_failures=tuple(sorted(integrity_failures)),
    )

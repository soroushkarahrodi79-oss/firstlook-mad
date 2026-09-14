"""Phase 0D.4 — adversarial falsification of the frozen Phase 0C.1 mechanism.

This package *stresses* the frozen Phase 0C.1 engine; it does not build a second
model. Every stress reuses ``generate_inputs``, ``evaluate_network``,
``greedy_site_order`` and ``euclidean_distance_m`` unchanged. All parameters are
frozen in :mod:`firstlook_mad.adversarial.stresses` before results, per
``docs/PHASE_0D4_PREREGISTRATION.md`` (commits ``3a64b1d`` → ``4512090``).

Two reporting layers are kept strictly separate:

* the **formal 0D.4 gate**, driven only by the *evidence-qualified critical set*
  {T3-REAL, T4-REAL, T5} — the real-data adversarial questions; and
* the **diagnostic battery** {T1, T2, T3-SYNTH, T4-SYNTH, T6}, which
  characterises the *synthetic* mechanism's fragility but never drives the
  formal gate.
"""

from __future__ import annotations

from firstlook_mad.adversarial.experiment import (
    build_manifest,
    build_results,
    run_adversarial,
)

__all__ = ["build_manifest", "build_results", "run_adversarial"]

"""Phase 0D.3 — staged reality substitution.

Orchestrates a single, attribution-preserving substitution of the synthetic
A-02 candidate-site locations by the real Phase 0D.2 canonical fire-station
locations, over a matched geographic support, comparing geometry-only metrics.
It reuses the frozen Phase 0C.1 engine and never builds a second model.
"""

from __future__ import annotations

from firstlook_mad.reality_substitution.pipeline import run_phase0d3

__all__ = ["run_phase0d3"]

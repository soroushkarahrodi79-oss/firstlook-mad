"""Small metric geometry core for already-projected synthetic points."""

from __future__ import annotations

import math

from firstlook_mad.domain import ANALYTICAL_CRS, ProjectedPoint


def euclidean_distance_m(left: ProjectedPoint, right: ProjectedPoint) -> float:
    """Return planar distance after refusing any non-analytical CRS."""

    if left.crs != ANALYTICAL_CRS or right.crs != ANALYTICAL_CRS:
        raise ValueError(f"distance requires {ANALYTICAL_CRS}")
    return math.hypot(left.easting_m - right.easting_m, left.northing_m - right.northing_m)

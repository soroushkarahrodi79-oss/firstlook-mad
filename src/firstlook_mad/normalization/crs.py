"""Deterministic EPSG:4326 -> EPSG:25830 conversion for canonical records."""

from __future__ import annotations

import math

from pydantic import ValidationError
from pyproj import Transformer

from firstlook_mad.domain import ANALYTICAL_CRS, ProjectedPoint
from firstlook_mad.normalization.models import GEOGRAPHIC_CRS

# Canonical metric coordinates are rounded to 1 mm so their bytes are reproducible.
COORDINATE_DECIMALS = 3


def make_analytical_transformer() -> Transformer:
    """Transformer with explicit lon/lat (x/y) axis order."""

    return Transformer.from_crs(GEOGRAPHIC_CRS, ANALYTICAL_CRS, always_xy=True)


def project_lon_lat(transformer: Transformer, lon: float, lat: float) -> tuple[float, float]:
    easting, northing = transformer.transform(lon, lat)
    return float(easting), float(northing)


def to_analytical_point(transformer: Transformer, lon: float, lat: float) -> ProjectedPoint | None:
    """Project one position; ``None`` if non-finite or outside ``ProjectedPoint`` bounds."""

    easting, northing = project_lon_lat(transformer, lon, lat)
    if not (math.isfinite(easting) and math.isfinite(northing)):
        return None
    try:
        return ProjectedPoint(
            easting_m=round(easting, COORDINATE_DECIMALS),
            northing_m=round(northing, COORDINATE_DECIMALS),
        )
    except ValidationError:
        return None

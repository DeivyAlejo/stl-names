"""Geometry operations for printer-friendly corner smoothing."""
from __future__ import annotations

from shapely.geometry import Polygon


def round_tight_corners(profile: Polygon, radius_mm: float) -> Polygon:
    """Round tight and narrow corners while preserving overall shape.

    This uses a morphological closing operation (`+radius` then `-radius`) which:
    - smooths acute corners and narrow angle joins,
    - keeps global dimensions much closer than a simple outward buffer,
    - improves manufacturability for FDM printers at letter joints.
    """
    if radius_mm <= 0:
        return profile

    smoothed = profile.buffer(radius_mm, join_style=1).buffer(-radius_mm, join_style=1)
    smoothed = smoothed.buffer(0)

    if smoothed.is_empty:
        # Fallback to original geometry if smoothing collapses tiny features.
        return profile

    return smoothed

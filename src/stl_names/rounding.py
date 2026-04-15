"""Geometry operations for printer-friendly corner smoothing."""
from __future__ import annotations

from shapely.geometry import Polygon


def round_tight_corners(profile: Polygon, radius_mm: float) -> Polygon:
    """Round all corners while preserving overall shape.

    Applies two complementary morphological operations in sequence:

    1. **Opening** (``-radius`` then ``+radius``): erodes then re-expands the
       shape, rounding sharp *convex* outward corners (e.g. letter stroke tips,
       serif-like points, acute joins in display fonts like Lobster).

    2. **Closing** (``+radius`` then ``-radius``): expands then contracts the
       shape, filling narrow concave notches and rounding *concave* inward
       corners produced at letter-connection points.

    Together the two passes ensure that all corners — whether pointing inward
    or outward — are smoothed uniformly regardless of font style.
    """
    if radius_mm <= 0:
        return profile

    # Pass 1 — opening: rounds convex outward corners.
    opened = profile.buffer(-radius_mm, join_style=1).buffer(radius_mm, join_style=1)
    if opened.is_empty:
        # Opening collapsed a very thin feature; keep original for this pass.
        opened = profile

    # Pass 2 — closing: fills concave notches and rounds inward corners.
    smoothed = opened.buffer(radius_mm, join_style=1).buffer(-radius_mm, join_style=1)
    smoothed = smoothed.buffer(0)

    if smoothed.is_empty:
        return profile

    return smoothed

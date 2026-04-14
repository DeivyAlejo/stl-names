"""Build rectangular base strip that connects letters at the bottom."""
from __future__ import annotations

from shapely.geometry import Polygon, box


def build_base_polygon(
    text_polygon: Polygon,
    base_height_mm: float,
) -> Polygon:
    """Return a rectangle spanning the full X-width of *text_polygon*.

    The strip is placed at the bottom of the text bounding box and extends
    downward by *base_height_mm*, connecting all letters via a solid base.

    Parameters
    ----------
    text_polygon   : Merged 2D profile of all placed glyphs.
    base_height_mm : Height (Y-dimension) of the base strip in mm.
    """
    min_x, min_y, max_x, _max_y = text_polygon.bounds
    return box(min_x, min_y - base_height_mm, max_x, min_y)

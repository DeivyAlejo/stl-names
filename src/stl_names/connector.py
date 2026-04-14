"""Auto-shift letter connection logic."""
from __future__ import annotations

from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

_CONNECT_STEP_MM = 0.05     # shift step size in mm
_MAX_SHIFT_FRACTION = 0.85  # max fraction of advance width to attempt shifting
_OVERLAP_MM = 0.2           # desired X-overlap between adjacent glyphs in mm


class GlyphConnectionError(ValueError):
    """Raised when letters cannot be connected without a base."""


def place_and_connect(
    outlines: list[tuple[Polygon | None, float]],
    name: str,
    use_base: bool,
    connect_step_mm: float = _CONNECT_STEP_MM,
    max_shift_fraction: float = _MAX_SHIFT_FRACTION,
    overlap_mm: float = _OVERLAP_MM,
) -> list[tuple[Polygon | None, float]]:
    """Place glyphs sequentially; auto-shift for connection when use_base is False.

    Returns list of (translated_polygon_or_None, x_offset) pairs.
    """
    if not outlines:
        return []

    placed: list[tuple[Polygon | None, float]] = []
    cursor = 0.0

    for i, (poly, adv) in enumerate(outlines):
        x_pos = cursor

        if not use_base and i > 0 and poly is not None:
            # Find last non-None placed polygon to connect against
            prev_poly: Polygon | None = next(
                (p for p, _ in reversed(placed) if p is not None), None
            )
            if prev_poly is not None:
                x_pos = _find_connection_x(
                    prev_poly=prev_poly,
                    curr_poly=poly,
                    start_x=cursor,
                    adv=adv,
                    step=connect_step_mm,
                    max_fraction=max_shift_fraction,
                    overlap_mm=overlap_mm,
                    char_prev=name[i - 1],
                    char_curr=name[i],
                )

        translated = affinity.translate(poly, xoff=x_pos) if poly is not None else None
        placed.append((translated, x_pos))
        cursor = x_pos + adv

    return placed


def merge_placed_glyphs(placed: list[tuple[Polygon | None, float]]) -> Polygon:
    """Union all placed non-None glyph polygons into a single 2D profile."""
    polys = [p for p, _ in placed if p is not None and not p.is_empty]
    if not polys:
        raise ValueError("No glyph polygons to merge; the name may contain only whitespace.")
    return unary_union(polys)


def _find_connection_x(
    prev_poly: Polygon,
    curr_poly: Polygon,
    start_x: float,
    adv: float,
    step: float,
    max_fraction: float,
    overlap_mm: float,
    char_prev: str,
    char_curr: str,
) -> float:
    """Return the x position where curr_poly overlaps prev_poly by overlap_mm.

    Starts at start_x and shifts left in steps until overlap is achieved, or raises
    GlyphConnectionError if max shift is reached without connection.
    """
    max_shift = adv * max_fraction
    shift = 0.0
    current = affinity.translate(curr_poly, xoff=start_x)

    while not _has_overlap(prev_poly, current, overlap_mm=overlap_mm) and shift < max_shift:
        shift += step
        current = affinity.translate(curr_poly, xoff=start_x - shift)

    if not _has_overlap(prev_poly, current, overlap_mm=overlap_mm):
        raise GlyphConnectionError(
            f"Cannot connect '{char_curr}' to '{char_prev}' with the selected font.\n"
            "Options:\n"
            "  1. Enable the base (--base / BASE=True) to connect letters via a bottom strip.\n"
            "  2. Use a cursive font where letters naturally touch."
        )

    return start_x - shift


def _has_overlap(a: Polygon, b: Polygon, overlap_mm: float = _OVERLAP_MM) -> bool:
    """True if polygons overlap with at least overlap_mm along X and non-zero area."""
    intersection = a.intersection(b)
    if intersection.is_empty or intersection.area <= 0:
        return False

    min_x, _min_y, max_x, _max_y = intersection.bounds
    x_overlap = max_x - min_x
    return x_overlap >= max(0.0, overlap_mm)

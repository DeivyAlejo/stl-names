"""Extract scaled 2D glyph outlines from a font as Shapely polygons."""
from __future__ import annotations

import numpy as np
from fontTools.pens.recordingPen import RecordingPen
from shapely.geometry import Polygon

from .font_loader import get_char_cmap, get_font_metrics, get_glyph_set, load_font

_CURVE_SAMPLES = 24  # line segments per Bezier curve
_REFERENCE_SCALE_CHARS = ("a", "e", "o")


def build_name_outlines(
    name: str,
    font_path_or_name: str,
    target_height_mm: float,
) -> list[tuple[Polygon | None, float]]:
    """Return (scaled_glyph_polygon, advance_width_mm) for each character.

    Polygon is None for whitespace-only glyphs (space, etc.).
    advance_width_mm is always the natural advance in mm.
    """
    font = load_font(font_path_or_name)
    glyph_set = get_glyph_set(font)
    cmap = get_char_cmap(font)
    metrics = get_font_metrics(font)
    scale = _compute_scale_from_reference_letters(
        name,
        glyph_set,
        cmap,
        target_height_mm,
        metrics,
    )

    result: list[tuple[Polygon | None, float]] = []
    for char in name:
        code = ord(char)
        glyph_name = cmap.get(code)
        if glyph_name is None:
            raise ValueError(
                f"Character '{char}' (U+{code:04X}) not found in the selected font."
            )
        glyph = glyph_set.get(glyph_name)
        if glyph is None:
            raise ValueError(f"Glyph '{glyph_name}' is missing from the font glyph set.")

        advance_width_mm = glyph.width * scale
        poly = _glyph_to_polygon(glyph, scale)
        result.append((poly, advance_width_mm))

    return result


def _compute_scale_from_reference_letters(
    name: str,
    glyph_set,
    cmap: dict[int, str],
    target_height_mm: float,
    metrics: dict,
) -> float:
    """Compute a uniform scale anchored to reference lowercase glyphs.

    Tries lowercase `a`, `e`, and `o` (or uppercase variants when lowercase is
    missing) to make size consistent across names regardless of first letter
    shape (for example names starting with descenders like J/j).

    Fallback order if references are unavailable:
    1) first drawable glyph from *name*
    2) cap-height font metric
    """
    reference_heights: list[float] = []

    for char in _REFERENCE_SCALE_CHARS:
        glyph = _get_glyph_for_char(char, glyph_set, cmap)
        if glyph is None:
            glyph = _get_glyph_for_char(char.upper(), glyph_set, cmap)
        if glyph is None:
            continue

        glyph_height = _get_glyph_height_units(glyph)
        if glyph_height > 0:
            reference_heights.append(glyph_height)

    if reference_heights:
        reference_height = sum(reference_heights) / len(reference_heights)
        return target_height_mm / reference_height

    for char in name:
        glyph = _get_glyph_for_char(char, glyph_set, cmap)
        if glyph is None:
            continue

        glyph_height_units = _get_glyph_height_units(glyph)
        if glyph_height_units > 0:
            return target_height_mm / glyph_height_units

    cap_height = metrics.get("cap_height", 0)
    if cap_height <= 0:
        raise ValueError("Font cap-height metric is invalid; cannot determine size scale.")
    return target_height_mm / cap_height


def _get_glyph_for_char(char: str, glyph_set, cmap: dict[int, str]):
    """Return glyph for *char* when available in cmap and glyph set."""
    glyph_name = cmap.get(ord(char))
    if glyph_name is None:
        return None
    return glyph_set.get(glyph_name)


def _get_glyph_height_units(glyph) -> float:
    """Return unscaled glyph bbox height in font units."""
    poly = _glyph_to_polygon(glyph, scale=1.0)
    if poly is None or poly.is_empty:
        return 0.0
    _min_x, min_y, _max_x, max_y = poly.bounds
    return max(0.0, max_y - min_y)


def _glyph_to_polygon(glyph, scale: float) -> Polygon | None:
    """Convert a single font glyph to a scaled Shapely polygon (or None)."""
    pen = RecordingPen()
    glyph.draw(pen)

    contours = _recording_to_contours(pen.value)
    if not contours:
        return None

    scaled = [c * scale for c in contours]

    # Build polygon using even-odd XOR fill to correctly handle counters (holes)
    result: Polygon = Polygon()
    for contour in scaled:
        if len(contour) < 3:
            continue
        try:
            poly = Polygon(contour).buffer(0)  # fix any topology issues
        except Exception:
            continue
        if poly.is_empty:
            continue
        result = result.symmetric_difference(poly)

    if result.is_empty:
        return None
    return result.buffer(0)


def _recording_to_contours(value: list) -> list[np.ndarray]:
    """Convert RecordingPen value to a list of (N, 2) coordinate arrays."""
    contours: list[np.ndarray] = []
    current: list[np.ndarray] = []
    current_pos = np.zeros(2)

    for op, args in value:
        if op == "moveTo":
            current = [np.array(args[0], dtype=float)]
            current_pos = np.array(args[0], dtype=float)
        elif op == "lineTo":
            pt = np.array(args[0], dtype=float)
            current.append(pt)
            current_pos = pt.copy()
        elif op == "qCurveTo":
            off_curves = [np.array(p, dtype=float) for p in args[:-1]]
            end_pt = np.array(args[-1], dtype=float)
            pts = _tessellate_qspline(current_pos, off_curves, end_pt)
            current.extend(pts)
            current_pos = end_pt.copy()
        elif op == "curveTo":
            p1 = np.array(args[0], dtype=float)
            p2 = np.array(args[1], dtype=float)
            p3 = np.array(args[2], dtype=float)
            pts = _tessellate_cubic(current_pos, p1, p2, p3)
            current.extend(pts)
            current_pos = p3.copy()
        elif op in ("closePath", "endPath"):
            if len(current) >= 3:
                contours.append(np.array(current))
            current = []

    return contours


def _tessellate_cubic(
    p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray
) -> list[np.ndarray]:
    """Tessellate a cubic Bezier to points; excludes start, includes end."""
    t = np.linspace(0, 1, _CURVE_SAMPLES + 1)[1:]
    mt = 1 - t
    pts = (
        mt[:, None] ** 3 * p0
        + 3 * (mt[:, None] ** 2 * t[:, None]) * p1
        + 3 * (mt[:, None] * t[:, None] ** 2) * p2
        + t[:, None] ** 3 * p3
    )
    return [pts[i] for i in range(len(pts))]


def _tessellate_qspline(
    start: np.ndarray,
    off_curves: list[np.ndarray],
    end: np.ndarray,
) -> list[np.ndarray]:
    """Tessellate a TrueType quadratic spline (one or many off-curve points)."""
    if len(off_curves) == 1:
        return _qbezier(start, off_curves[0], end)

    # Multiple off-curves: compute implied on-curve points at midpoints
    on_pts: list[np.ndarray] = [start]
    for i in range(len(off_curves) - 1):
        on_pts.append((off_curves[i] + off_curves[i + 1]) / 2)
    on_pts.append(end)

    result: list[np.ndarray] = []
    for i, off in enumerate(off_curves):
        result.extend(_qbezier(on_pts[i], off, on_pts[i + 1]))
    return result


def _qbezier(
    p0: np.ndarray, p1: np.ndarray, p2: np.ndarray
) -> list[np.ndarray]:
    """Quadratic Bezier tessellation; excludes start, includes end."""
    t = np.linspace(0, 1, _CURVE_SAMPLES + 1)[1:]
    mt = 1 - t
    pts = mt[:, None] ** 2 * p0 + 2 * mt[:, None] * t[:, None] * p1 + t[:, None] ** 2 * p2
    return [pts[i] for i in range(len(pts))]

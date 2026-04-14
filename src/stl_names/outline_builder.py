"""Extract scaled 2D glyph outlines from a font as Shapely polygons."""
from __future__ import annotations

import numpy as np
from fontTools.pens.recordingPen import RecordingPen
from shapely.geometry import Polygon

from .font_loader import get_char_cmap, get_font_metrics, get_glyph_set, load_font

_CURVE_SAMPLES = 24  # line segments per Bezier curve


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
    scale = target_height_mm / metrics["cap_height"]

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

"""High-level name-to-STL generation API.

Used by both the runner scripts and the CLI commands.
"""
from __future__ import annotations

from pathlib import Path

from shapely import affinity
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon
from shapely.ops import unary_union

from .base_builder import build_base_polygon
from .connector import GlyphConnectionError, merge_placed_glyphs, place_and_connect
from .exporter import (
    PrinterLengthError,
    check_printer_limits,
    export_stl,
    get_output_path,
)
from .mesh_builder import build_mesh, orient_mesh_for_bed
from .outline_builder import build_name_outlines
from .rounding import round_tight_corners


def generate_name(
    name: str,
    font: str,
    height_mm: float = 20.0,
    thickness_mm: float = 5.0,
    base: bool = False,
    base_height_mm: float = 2.0,
    rounded: bool = False,
    corner_radius_mm: float = 0.4,
    keep_ij_dots: bool = True,
    bed_face: str = "bottom",
    out_dir: str = "output",
) -> Path:
    """Generate a 3D-printable STL file for *name*.

    Parameters
    ----------
    name            : Text to generate (case-sensitive glyph shapes).
    font            : Path to a .ttf/.otf file, or a system font family name.
    height_mm       : Height in mm anchored to font reference letters (a/e/o)
                      for consistent scaling across different names.
    thickness_mm    : Z-depth of the extruded solid in mm (print thickness).
    base            : If True, add a rectangular strip below the letters to
                      connect them (useful for non-cursive fonts).
    base_height_mm  : Y-height of the base strip in mm (only used when base=True).
    rounded         : If True, smooth narrow/tight corners at letter joints.
    corner_radius_mm: Smoothing radius in mm (only used when rounded=True).
    keep_ij_dots    : If True, keep lowercase i/j dots and move them to attach to
                      the stem before rounding. If False, remove those dots.
    bed_face        : Which face should go against the print bed: "bottom" or "top".
    out_dir         : Directory for output files (created if it does not exist).

    Returns
    -------
    Path to the generated STL file.

    Raises
    ------
    PrinterLengthError    : Model exceeds 28 cm; STL not written.
    GlyphConnectionError  : Letters cannot be connected; base disabled.
    FileNotFoundError     : Font file or system font name not found.
    ValueError            : Unsupported character, empty name, invalid bed_face, etc.
    """
    if not name.strip():
        raise ValueError("Name must not be empty.")

    # 1. Extract glyph outlines (scaled to height_mm)
    outlines = build_name_outlines(name, font, height_mm)

    # 2. Place glyphs and auto-shift for connection (or native spacing with base)
    placed = place_and_connect(outlines, name=name, use_base=base)

    # 2b. Normalize lowercase i/j dots before merge and optional rounding.
    placed = _process_ij_dots(placed, name=name, keep_ij_dots=keep_ij_dots)

    # 3. Merge all placed glyphs into one 2D profile
    text_profile: Polygon = merge_placed_glyphs(placed)

    # 3b. Smooth tight/narrow corners if requested
    if rounded and corner_radius_mm > 0:
        text_profile = round_tight_corners(text_profile, corner_radius_mm)

    # 4. Optionally build and union the base strip
    base_profile: Polygon | None = None
    if base:
        base_profile = build_base_polygon(text_profile, base_height_mm)

    # 5. Check printer build-length limits on the full 2D extent
    check_profile = text_profile.union(base_profile) if base_profile is not None else text_profile
    check_printer_limits(check_profile, name)

    # 6. Extrude to 3D mesh
    mesh = build_mesh(text_profile, base_profile, thickness_mm)

    # 6b. Orient selected face against bed
    mesh = orient_mesh_for_bed(mesh, bed_face=bed_face)

    # 7. Write STL
    out_path = get_output_path(name, out_dir)
    export_stl(mesh, out_path)

    return out_path


_DOT_ATTACH_OVERLAP_MM = 0.02
_DOT_ATTACH_STEP_MM = 0.05


def _process_ij_dots(
    placed: list[tuple[Polygon | None, float]],
    name: str,
    keep_ij_dots: bool,
) -> list[tuple[Polygon | None, float]]:
    """Attach or remove detached dots for lowercase i/j glyphs."""
    if not placed:
        return placed

    updated: list[tuple[Polygon | None, float]] = []
    for i, (poly, x_pos) in enumerate(placed):
        char = name[i] if i < len(name) else ""
        if poly is None or char not in {"i", "j"}:
            updated.append((poly, x_pos))
            continue

        body, dots, others = _split_ij_components(poly)
        if body is None or not dots:
            updated.append((poly, x_pos))
            continue

        if keep_ij_dots:
            moved_dots = [_attach_dot_to_body(dot, body) for dot in dots]
            new_poly = unary_union([body, *moved_dots, *others]).buffer(0)
        else:
            new_poly = unary_union([body, *others]).buffer(0)

        updated.append((new_poly, x_pos))

    return updated


def _split_ij_components(poly: Polygon) -> tuple[Polygon | None, list[Polygon], list[Polygon]]:
    """Return (body, candidate_dots, other_components) for an i/j glyph geometry."""
    components = _polygon_components(poly)
    if len(components) < 2:
        return None, [], []

    body = max(components, key=lambda p: p.area)
    body_top = body.bounds[3]

    dots: list[Polygon] = []
    others: list[Polygon] = []
    for comp in components:
        if comp.equals(body):
            continue

        _min_x, min_y, _max_x, _max_y = comp.bounds
        is_above_body = min_y >= body_top - 1e-6
        is_small = comp.area <= body.area * 0.5
        if is_above_body and is_small:
            dots.append(comp)
        else:
            others.append(comp)

    return body, dots, others


def _attach_dot_to_body(dot: Polygon, body: Polygon) -> Polygon:
    """Translate a detached dot downward until it touches or overlaps the body."""
    if dot.intersects(body) or dot.touches(body):
        return dot

    body_top = body.bounds[3]
    dot_min_y = dot.bounds[1]
    initial_shift = body_top - dot_min_y + _DOT_ATTACH_OVERLAP_MM
    moved = affinity.translate(dot, yoff=initial_shift)

    if moved.intersects(body) or moved.touches(body):
        return moved

    body_height = max(0.0, body.bounds[3] - body.bounds[1])
    max_extra_shift = body_height * 2.0
    shifted = 0.0
    while shifted < max_extra_shift:
        moved = affinity.translate(moved, yoff=-_DOT_ATTACH_STEP_MM)
        shifted += _DOT_ATTACH_STEP_MM
        if moved.intersects(body) or moved.touches(body):
            return moved

    return moved


def _polygon_components(poly: Polygon) -> list[Polygon]:
    """Extract polygon-only components from Polygon/MultiPolygon geometry."""
    if isinstance(poly, MultiPolygon):
        return [p for p in poly.geoms if not p.is_empty]
    if isinstance(poly, Polygon):
        return [poly] if not poly.is_empty else []
    return []

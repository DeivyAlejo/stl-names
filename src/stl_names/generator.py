"""High-level name-to-STL generation API.

Used by both the runner scripts and the CLI commands.
"""
from __future__ import annotations

from pathlib import Path

from shapely.geometry import Polygon

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
    bed_face: str = "bottom",
    out_dir: str = "output",
) -> Path:
    """Generate a 3D-printable STL file for *name*.

    Parameters
    ----------
    name            : Text to generate (case-sensitive glyph shapes).
    font            : Path to a .ttf/.otf file, or a system font family name.
    height_mm       : Cap-height of the letters in mm (controls overall text size).
    thickness_mm    : Z-depth of the extruded solid in mm (print thickness).
    base            : If True, add a rectangular strip below the letters to
                      connect them (useful for non-cursive fonts).
    base_height_mm  : Y-height of the base strip in mm (only used when base=True).
    rounded         : If True, smooth narrow/tight corners at letter joints.
    corner_radius_mm: Smoothing radius in mm (only used when rounded=True).
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

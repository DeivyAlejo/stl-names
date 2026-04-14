"""Extrude 2D profile to a watertight 3D mesh."""
from __future__ import annotations

import trimesh
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union


def build_mesh(
    text_profile: Polygon,
    base_profile: Polygon | None,
    thickness_mm: float,
) -> trimesh.Trimesh:
    """Extrude the combined 2D profile to a 3D watertight mesh.

    Parameters
    ----------
    text_profile  : Merged 2D polygon of the name.
    base_profile  : Optional base rectangle polygon.
    thickness_mm  : Z-depth of the extruded solid in mm.
    """
    if base_profile is not None:
        combined: Polygon = unary_union([text_profile, base_profile])
    else:
        combined = text_profile

    combined = combined.buffer(0)  # ensure valid geometry

    if combined.is_empty:
        raise ValueError("The combined 2D profile is empty; cannot extrude to a mesh.")

    mesh = _extrude(combined, thickness_mm)

    if not mesh.is_watertight:
        trimesh.repair.fill_holes(mesh)

    return mesh


def _extrude(profile: Polygon | MultiPolygon, height: float) -> trimesh.Trimesh:
    """Extrude a Shapely polygon (or MultiPolygon) to a trimesh solid."""
    if isinstance(profile, MultiPolygon):
        parts = [trimesh.creation.extrude_polygon(p, height) for p in profile.geoms]
        return trimesh.util.concatenate(parts)
    return trimesh.creation.extrude_polygon(profile, height)

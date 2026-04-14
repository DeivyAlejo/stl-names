"""Tests for mesh orientation relative to print bed."""
import numpy as np
from shapely.geometry import box

from stl_names.mesh_builder import build_mesh, orient_mesh_for_bed


def test_orient_mesh_bottom_normalizes_to_z_zero():
    mesh = build_mesh(box(0, 0, 10, 5), None, thickness_mm=2.0)
    oriented = orient_mesh_for_bed(mesh, bed_face="bottom")

    min_z = float(oriented.bounds[0][2])
    max_z = float(oriented.bounds[1][2])
    assert abs(min_z) < 1e-9
    assert abs(max_z - 2.0) < 1e-9


def test_orient_mesh_top_flips_model_over_x():
    mesh = build_mesh(box(0, 0, 10, 5), None, thickness_mm=2.0)
    bottom = orient_mesh_for_bed(mesh, bed_face="bottom")
    top = orient_mesh_for_bed(mesh, bed_face="top")

    # Both must rest on bed at z=0 and preserve total thickness.
    assert abs(float(top.bounds[0][2])) < 1e-9
    assert abs(float(top.bounds[1][2]) - float(bottom.bounds[1][2])) < 1e-9

    # Top orientation should invert Y distribution versus bottom orientation.
    # (Flipping 180° around X changes the sign of Y.)
    y_bottom = bottom.vertices[:, 1]
    y_top = top.vertices[:, 1]
    assert np.isclose(y_bottom.min(), -y_top.max())
    assert np.isclose(y_bottom.max(), -y_top.min())


def test_orient_mesh_for_bed_rejects_invalid_face():
    mesh = build_mesh(box(0, 0, 10, 5), None, thickness_mm=2.0)
    try:
        orient_mesh_for_bed(mesh, bed_face="side")
    except ValueError as exc:
        assert "bed_face" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid bed_face")

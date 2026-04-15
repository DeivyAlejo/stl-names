"""Tests for tight-corner rounding behavior."""
import pytest
from shapely.geometry import Polygon

from stl_names.rounding import round_tight_corners


def test_round_tight_corners_keeps_valid_geometry():
    # Polygon with a narrow notch and tight angles near the top center.
    poly = Polygon([(0, 0), (10, 0), (10, 10), (6, 10), (5, 6), (4, 10), (0, 10)])
    smoothed = round_tight_corners(poly, 0.4)

    assert not smoothed.is_empty
    assert smoothed.is_valid


def test_round_tight_corners_noop_when_radius_zero():
    poly = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
    smoothed = round_tight_corners(poly, 0.0)
    assert smoothed.equals(poly)


def test_round_tight_corners_rounds_convex_corner():
    # Right-angle square: all four corners are sharp convex outward corners.
    # After rounding the bounding box must shrink slightly (opening removes
    # protruding material) and the area must be less than the original.
    poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    smoothed = round_tight_corners(poly, 0.4)

    assert not smoothed.is_empty
    assert smoothed.is_valid
    # Area must decrease because convex corners are replaced by arcs.
    assert smoothed.area < poly.area


def test_round_tight_corners_rounds_concave_notch():
    # Polygon with a narrow inward notch: closing pass must fill/smooth it.
    poly = Polygon([(0, 0), (10, 0), (10, 10), (6, 10), (5, 6), (4, 10), (0, 10)])
    smoothed = round_tight_corners(poly, 0.4)

    # After smoothing the notch the area must be larger than the original
    # (concave material is filled in) while still smaller than the convex hull.
    assert smoothed.area > poly.area
    assert smoothed.area < poly.convex_hull.area


def test_round_tight_corners_acute_spike_removed():
    # Very sharp spike pointing outward — a common feature in Lobster-style fonts.
    # After rounding the spike tip must be clipped (convex opening removes it).
    spike = Polygon([(0, 0), (5, 0), (2.5, 20), (2.5, 20)])  # thin tall triangle
    if not spike.is_valid:
        spike = spike.buffer(0)
    if spike.is_empty:
        pytest.skip("degenerate spike geometry")

    smoothed = round_tight_corners(spike, 0.4)

    assert not smoothed.is_empty
    # The very tip (y > 19) should be clipped by the opening pass.
    assert smoothed.bounds[3] < spike.bounds[3]


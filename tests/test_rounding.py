"""Tests for tight-corner rounding behavior."""
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

"""Tests for lowercase i/j dot handling before rounding."""

from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

from stl_names.generator import _process_ij_dots


def _component_count(poly: Polygon) -> int:
    if isinstance(poly, MultiPolygon):
        return len(list(poly.geoms))
    return 1


def test_keep_ij_dots_attaches_dot_for_i():
    body = box(0, 0, 4, 10)
    dot = box(1, 12, 3, 14)
    glyph = unary_union([body, dot])

    placed = [(glyph, 0.0)]
    updated = _process_ij_dots(placed, name="i", keep_ij_dots=True)

    new_poly, _ = updated[0]
    assert new_poly is not None
    assert _component_count(new_poly) == 1



def test_remove_ij_dots_removes_dot_for_j():
    body = box(0, 0, 3, 11)
    dot = box(0.8, 13, 2.2, 14.5)
    glyph = unary_union([body, dot])

    placed = [(glyph, 0.0)]
    updated = _process_ij_dots(placed, name="j", keep_ij_dots=False)

    new_poly, _ = updated[0]
    assert new_poly is not None
    assert new_poly.bounds[3] <= body.bounds[3] + 1e-9
    assert new_poly.area < glyph.area



def test_non_ij_letters_are_unchanged():
    body = box(0, 0, 4, 10)
    dot = box(1, 12, 3, 14)
    glyph = unary_union([body, dot])

    placed = [(glyph, 0.0)]
    updated = _process_ij_dots(placed, name="a", keep_ij_dots=False)

    new_poly, _ = updated[0]
    assert new_poly is not None
    assert new_poly.equals(glyph)



def test_keep_mode_noop_when_dot_already_connected():
    connected_i = box(0, 0, 4, 14)

    placed = [(connected_i, 0.0)]
    updated = _process_ij_dots(placed, name="i", keep_ij_dots=True)

    new_poly, _ = updated[0]
    assert new_poly is not None
    assert new_poly.equals(connected_i)

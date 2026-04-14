"""Tests for connector module: placement and connection logic."""
import pytest
from shapely.geometry import box

from stl_names.connector import (
    GlyphConnectionError,
    _has_overlap,
    merge_placed_glyphs,
    place_and_connect,
)


def _rect_at(x, y, w=5.0, h=10.0):
    return box(x, y, x + w, y + h)


def test_place_single_glyph_always_at_origin():
    outlines = [(_rect_at(0, 0), 6.0)]
    placed = place_and_connect(outlines, name="A", use_base=False)
    assert len(placed) == 1
    poly, x = placed[0]
    assert poly is not None
    assert abs(x) < 0.01


def test_native_spacing_with_base_enabled():
    """With base=True, letters should stay at native advance positions."""
    outlines = [(_rect_at(0, 0), 6.0), (_rect_at(0, 0), 6.0)]
    placed = place_and_connect(outlines, name="AB", use_base=True)
    _, x1 = placed[1]
    assert abs(x1 - 6.0) < 0.01


def test_already_overlapping_needs_no_shift():
    """Adjacent glyphs that already overlap at native spacing need no extra shift."""
    outlines = [(_rect_at(0, 0, w=6.0), 6.0), (_rect_at(0, 0, w=4.0), 5.0)]
    placed = place_and_connect(outlines, name="AB", use_base=False, overlap_mm=0.0)
    _, x1 = placed[1]
    assert x1 <= 6.01


def test_auto_shift_creates_required_overlap():
    """Glyphs with a gap should be shifted until required overlap is reached."""
    outlines = [(_rect_at(0, 0, w=5.0), 10.0), (_rect_at(0, 0, w=5.0), 10.0)]
    placed = place_and_connect(outlines, name="AB", use_base=False, overlap_mm=0.2)
    poly_a, _ = placed[0]
    poly_b, x1 = placed[1]
    assert _has_overlap(poly_a, poly_b, overlap_mm=0.2)
    assert x1 < 10.0


def test_impossible_connection_raises_error():
    """Glyphs too far apart should raise GlyphConnectionError."""
    outlines = [(_rect_at(0, 0, w=1.0), 50.0), (_rect_at(0, 0, w=1.0), 50.0)]
    with pytest.raises(GlyphConnectionError, match="base"):
        place_and_connect(outlines, name="AB", use_base=False)


def test_merge_placed_glyphs_union():
    r1 = _rect_at(0, 0)
    r2 = _rect_at(4, 0)
    placed = [(r1, 0.0), (r2, 4.0)]
    merged = merge_placed_glyphs(placed)
    assert not merged.is_empty
    assert merged.area < r1.area + r2.area


def test_merge_skips_none():
    r1 = _rect_at(0, 0)
    placed = [(None, 0.0), (r1, 6.0)]
    merged = merge_placed_glyphs(placed)
    assert not merged.is_empty


def test_has_overlap_true():
    r1 = _rect_at(0, 0, w=5.0)
    r2 = _rect_at(3, 0, w=5.0)
    assert _has_overlap(r1, r2, overlap_mm=0.2)


def test_has_overlap_false():
    r1 = _rect_at(0, 0, w=5.0)
    r2 = _rect_at(6, 0, w=5.0)
    assert not _has_overlap(r1, r2, overlap_mm=0.2)


def test_has_overlap_touching_false_for_positive_threshold():
    """Touching-only edges are not enough when overlap threshold > 0."""
    r1 = _rect_at(0, 0, w=5.0)
    r2 = _rect_at(5, 0, w=5.0)
    assert not _has_overlap(r1, r2, overlap_mm=0.2)

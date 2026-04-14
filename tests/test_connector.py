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
    _, x0 = placed[0]
    _, x1 = placed[1]
    assert abs(x1 - 6.0) < 0.01   # exactly one advance width apart


def test_already_overlapping_needs_no_shift():
    """Adjacent glyphs that already overlap at native spacing need zero shift."""
    # two rects that overlap at x=5-6
    outlines = [(_rect_at(0, 0, w=6.0), 6.0), (_rect_at(0, 0, w=4.0), 5.0)]
    placed = place_and_connect(outlines, name="AB", use_base=False, overlap_mm=0.0)
    _, x0 = placed[0]
    _, x1 = placed[1]
    # Second rect may be at 6.0 if already overlapping
    assert x1 <= 6.01


def test_auto_shift_creates_overlap():
    """Glyphs with a gap should be shifted until they overlap."""
    # Glyph A: x 0-5; advance 10 -> gap of 5 mm before glyph B at 10-15
    # Glyph B: x 0-5, will be shifted left to overlap
    outlines = [(_rect_at(0, 0, w=5.0), 10.0), (_rect_at(0, 0, w=5.0), 10.0)]
    placed = place_and_connect(outlines, name="AB", use_base=False)
    poly_a, _ = placed[0]
    poly_b, x1 = placed[1]
    # After connection poly_b should be shifted left and overlap with poly_a
    assert _has_overlap(poly_a, poly_b)
    # Also check that poly_b was indeed shifted left from default position
    assert x1 < 10.0


def test_impossible_connection_raises_error():
    """Glyphs too far apart should raise GlyphConnectionError."""
    # Huge advance (50 mm) but glyph only 1 mm wide -> max_shift = 42.5 mm,
    # still not enough to cover 49 mm gap
    outlines = [(_rect_at(0, 0, w=1.0), 50.0), (_rect_at(0, 0, w=1.0), 50.0)]
    with pytest.raises(GlyphConnectionError, match="base"):
        place_and_connect(outlines, name="AB", use_base=False)


def test_merge_placed_glyphs_union():
    r1 = _rect_at(0, 0)
    r2 = _rect_at(4, 0)   # overlapping
    placed = [(r1, 0.0), (r2, 4.0)]
    merged = merge_placed_glyphs(placed)
    assert not merged.is_empty
    # Merged area should be less than sum of individual areas (they overlap)
    assert merged.area < r1.area + r2.area


def test_merge_skips_none():
    r1 = _rect_at(0, 0)
    placed = [(None, 0.0), (r1, 6.0)]
    merged = merge_placed_glyphs(placed)
    assert not merged.is_empty


def test_has_overlap_true():
    r1 = _rect_at(0, 0, w=5.0)
    r2 = _rect_at(3, 0, w=5.0)
    assert _has_overlap(r1, r2)


def test_has_overlap_false():
    r1 = _rect_at(0, 0, w=5.0)
    r2 = _rect_at(6, 0, w=5.0)
    assert not _has_overlap(r1, r2)


def test_has_overlap_touching():
    """Touching counts as overlap for 3D printing."""
    r1 = _rect_at(0, 0, w=5.0)
    r2 = _rect_at(5, 0, w=5.0)
    assert _has_overlap(r1, r2)

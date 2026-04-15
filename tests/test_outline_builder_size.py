"""Tests for reference-letter-based height scaling in outline builder."""

import pytest

from stl_names import outline_builder


class FakeGlyph:
    def __init__(self, width: float, height: float, empty: bool = False, min_y: float = 0.0):
        self.width = width
        self._height = height
        self._empty = empty
        self._min_y = min_y

    def draw(self, pen):
        if self._empty:
            return
        max_y = self._min_y + self._height
        pen.moveTo((0.0, self._min_y))
        pen.lineTo((100.0, self._min_y))
        pen.lineTo((100.0, max_y))
        pen.lineTo((0.0, max_y))
        pen.closePath()


def _patch_outline_dependencies(monkeypatch, glyph_set, cmap, metrics):
    monkeypatch.setattr(outline_builder, "load_font", lambda _font: object())
    monkeypatch.setattr(outline_builder, "get_glyph_set", lambda _font: glyph_set)
    monkeypatch.setattr(outline_builder, "get_char_cmap", lambda _font: cmap)
    monkeypatch.setattr(outline_builder, "get_font_metrics", lambda _font: metrics)



def _height(poly) -> float:
    _min_x, min_y, _max_x, max_y = poly.bounds
    return max_y - min_y



def test_height_uses_reference_letters_when_available(monkeypatch):
    glyph_set = {
        "space": FakeGlyph(width=200.0, height=0.0, empty=True),
        "a": FakeGlyph(width=300.0, height=500.0),
        "e": FakeGlyph(width=280.0, height=520.0),
        "o": FakeGlyph(width=290.0, height=480.0),
        "A": FakeGlyph(width=400.0, height=700.0),
        "b": FakeGlyph(width=300.0, height=500.0),
    }
    cmap = {
        ord(" "): "space",
        ord("a"): "a",
        ord("e"): "e",
        ord("o"): "o",
        ord("A"): "A",
        ord("b"): "b",
    }
    metrics = {"upm": 1000, "ascender": 800, "cap_height": 1000}
    _patch_outline_dependencies(monkeypatch, glyph_set, cmap, metrics)

    outlines = outline_builder.build_name_outlines(" Ab", "dummy-font", 20.0)

    space_poly, space_adv = outlines[0]
    a_poly, a_adv = outlines[1]
    b_poly, _b_adv = outlines[2]

    assert space_poly is None
    scale = 20.0 / 500.0  # average of a/e/o heights: (500 + 520 + 480) / 3
    assert space_adv == pytest.approx(200.0 * scale)
    assert a_poly is not None
    assert b_poly is not None
    assert _height(a_poly) == pytest.approx(700.0 * scale)
    assert _height(b_poly) == pytest.approx(500.0 * scale)
    assert a_adv == pytest.approx(400.0 * scale)



def test_height_consistent_for_names_starting_with_descender(monkeypatch):
    glyph_set = {
        "a": FakeGlyph(width=300.0, height=500.0),
        "e": FakeGlyph(width=280.0, height=520.0),
        "o": FakeGlyph(width=290.0, height=480.0),
        "J": FakeGlyph(width=380.0, height=900.0, min_y=-200.0),
        "A": FakeGlyph(width=400.0, height=700.0),
    }
    cmap = {ord("a"): "a", ord("e"): "e", ord("o"): "o", ord("J"): "J", ord("A"): "A"}
    metrics = {"upm": 1000, "ascender": 800, "cap_height": 1000}
    _patch_outline_dependencies(monkeypatch, glyph_set, cmap, metrics)

    outlines_j = outline_builder.build_name_outlines("Ja", "dummy-font", 20.0)
    outlines_a = outline_builder.build_name_outlines("Aa", "dummy-font", 20.0)

    j_poly, _ = outlines_j[0]
    a_after_j, _ = outlines_j[1]
    a_poly, _ = outlines_a[0]

    assert j_poly is not None
    assert a_after_j is not None
    assert a_poly is not None

    expected_scale = 20.0 / 500.0
    assert _height(j_poly) == pytest.approx(900.0 * expected_scale)
    assert _height(a_after_j) == pytest.approx(500.0 * expected_scale)
    assert _height(a_poly) == pytest.approx(700.0 * expected_scale)



def test_scale_falls_back_to_cap_height_when_no_drawable_glyph(monkeypatch):
    glyph_set = {"space": FakeGlyph(width=200.0, height=0.0, empty=True)}
    cmap = {ord(" "): "space"}
    metrics = {"upm": 1000, "ascender": 800, "cap_height": 1000}
    _patch_outline_dependencies(monkeypatch, glyph_set, cmap, metrics)

    outlines = outline_builder.build_name_outlines(" ", "dummy-font", 20.0)

    poly, adv = outlines[0]
    assert poly is None
    assert adv == pytest.approx(4.0)

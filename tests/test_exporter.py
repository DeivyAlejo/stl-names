"""Tests for exporter utilities: filename sanitization and printer limits."""
import warnings

import pytest
from shapely.geometry import box

from stl_names.exporter import (
    MAX_LENGTH_MM,
    WARN_LENGTH_MM,
    PrinterLengthError,
    check_printer_limits,
    sanitize_filename,
)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Sofia", "sofia"),
        ("Ana", "ana"),
        ("ANA", "ana"),
        ("Jean-Pierre", "jean-pierre"),
        ("O'Brien", "o_brien"),
        ("name with spaces", "name_with_spaces"),
        ("  __  ", "name"),           # degenerates to fallback
        ("Mia & Leo", "mia_leo"),
    ],
)
def test_sanitize_filename(name, expected):
    assert sanitize_filename(name) == expected


def test_printer_limits_ok():
    small = box(0, 0, 100, 20)      # 100 mm = 10 cm, well within limits
    check_printer_limits(small, "short")   # should not raise or warn


def test_printer_limits_warning():
    wide = box(0, 0, WARN_LENGTH_MM + 5, 20)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_printer_limits(wide, "longname")
    assert len(caught) == 1
    assert issubclass(caught[0].category, UserWarning)
    assert "23" in str(caught[0].message)


def test_printer_limits_error():
    too_wide = box(0, 0, MAX_LENGTH_MM + 5, 20)
    with pytest.raises(PrinterLengthError, match="28"):
        check_printer_limits(too_wide, "verylongname")

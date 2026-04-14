"""Tests for batch file parsing and duplicate handling."""
import textwrap
from pathlib import Path

import pytest

from stl_names.batch import parse_names_file
from stl_names.exporter import sanitize_filename


def _write_names(tmp_path: Path, content: str) -> Path:
    filepath = tmp_path / "names.txt"
    filepath.write_text(textwrap.dedent(content), encoding="utf-8")
    return filepath


def test_parse_skips_blank_lines(tmp_path):
    p = _write_names(tmp_path, """
        Ana

        Sofia

    """)
    names = parse_names_file(p)
    assert names == ["Ana", "Sofia"]


def test_parse_skips_comments(tmp_path):
    p = _write_names(tmp_path, """
        # This is a comment
        Ana
        # Another comment
        Sofia
    """)
    names = parse_names_file(p)
    assert names == ["Ana", "Sofia"]


def test_parse_preserves_case(tmp_path):
    p = _write_names(tmp_path, "Ana\nANA\nana\n")
    names = parse_names_file(p)
    assert names == ["Ana", "ANA", "ana"]


def test_duplicate_detection_via_sanitize():
    """Case-variant names that sanitize to the same key are detected as duplicates."""
    assert sanitize_filename("Ana") == sanitize_filename("ANA") == sanitize_filename("ana")

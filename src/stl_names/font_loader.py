"""Font loading: accepts a file path (.ttf/.otf) or a system font name."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

_SYSTEM_FONT_DIRS: list[Path] = []
if sys.platform == "linux":
    _SYSTEM_FONT_DIRS = [
        Path.home() / ".local/share/fonts",
        Path("/usr/local/share/fonts"),
        Path("/usr/share/fonts"),
    ]
elif sys.platform == "darwin":
    _SYSTEM_FONT_DIRS = [
        Path.home() / "Library/Fonts",
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
    ]
elif sys.platform == "win32":
    _SYSTEM_FONT_DIRS = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts",
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
    ]


def load_font(font: str) -> TTFont:
    """Load a TTFont from a file path (.ttf/.otf) or a system font family name."""
    path = Path(font)
    if path.suffix.lower() in (".ttf", ".otf"):
        if not path.exists():
            raise FileNotFoundError(f"Font file not found: {path}")
        return TTFont(str(path))

    found = _find_system_font(font)
    if found is None:
        searched = ", ".join(str(d) for d in _SYSTEM_FONT_DIRS if d.exists())
        raise FileNotFoundError(
            f"System font '{font}' not found. Searched: {searched}\n"
            "Tip: provide an explicit .ttf/.otf file path instead."
        )
    return TTFont(str(found))


def _find_system_font(name: str) -> Path | None:
    """Search system font directories for a font whose filename matches *name*."""
    pattern = re.compile(re.escape(name), re.IGNORECASE)
    for directory in _SYSTEM_FONT_DIRS:
        if not directory.exists():
            continue
        for ext in ("*.ttf", "*.otf", "*.TTF", "*.OTF"):
            for candidate in directory.rglob(ext):
                if pattern.search(candidate.stem):
                    return candidate
    return None


def get_glyph_set(font: TTFont):
    """Return the TTFont glyph set."""
    return font.getGlyphSet()


def get_char_cmap(font: TTFont) -> dict[int, str]:
    """Return best-table codepoint -> glyph-name mapping."""
    cmap_table = font.getBestCmap()
    if cmap_table is None:
        raise ValueError("Font has no valid cmap table.")
    return cmap_table


def get_font_metrics(font: TTFont) -> dict:
    """Return key vertical metrics (in font units)."""
    head = font["head"]
    upm = head.unitsPerEm
    os2 = font.get("OS/2")
    cap_height = upm
    ascender = upm
    if os2:
        if getattr(os2, "sCapHeight", 0) > 0:
            cap_height = os2.sCapHeight
        elif getattr(os2, "sTypoAscender", 0) > 0:
            cap_height = os2.sTypoAscender
        if getattr(os2, "sTypoAscender", 0) > 0:
            ascender = os2.sTypoAscender
    return {"upm": upm, "ascender": ascender, "cap_height": cap_height}

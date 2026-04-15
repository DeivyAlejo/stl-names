#!/usr/bin/env python3
"""
Non-CLI runner for batch STL generation from a TXT file.

Edit the CONFIG section below with your settings, then run:

    uv run scripts/run_batch.py

The TXT file should have one name per line.
Blank lines and lines starting with # are ignored.
Duplicate names (case-insensitive) are skipped and reported.

No command-line arguments are needed.
"""

# ============================================================
# CONFIG – edit these values
# ============================================================

NAMES_FILE      = "names.txt"                    # TXT file with one name per line
FONT            = "fonts/Cookie-Regular.ttf" # .ttf/.otf path, or system font name
HEIGHT_MM       = 16.0                           # Letter height anchor in mm (uses reference a/e/o)
THICKNESS_MM    = 3.0                            # Z-depth (print thickness) in mm
BASE            = False                          # True = add a connecting base strip
BASE_HEIGHT_MM  = 2.0                            # Height of base strip in mm (BASE=True only)
ROUNDED         = True                          # True = round tight letter corners
CORNER_RADIUS_MM = 0.4                           # Corner radius in mm (ROUNDED=True only)
KEEP_IJ_DOTS    = True                           # True = attach lowercase i/j dots; False = remove them
BED_FACE        = "top"                      # Face on bed: "bottom" or "top"
OUT_DIR         = "output"                       # Output directory (created if missing)

# ============================================================
# Execution – do not edit below this line
# ============================================================

import sys
from pathlib import Path

# Allow running directly from the project root without installing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from stl_names.batch import process_batch


def run() -> None:
    print("=" * 50)
    print(f"  Names file: {NAMES_FILE}")
    print(f"  Font      : {FONT}")
    print(f"  Height    : {HEIGHT_MM} mm")
    print(f"  Thickness : {THICKNESS_MM} mm")
    if BASE:
        print(f"  Base      : yes ({BASE_HEIGHT_MM} mm high)")
    else:
        print("  Base      : no  (auto-connection enabled)")
    if ROUNDED:
        print(f"  Rounded   : yes ({CORNER_RADIUS_MM} mm radius)")
    else:
        print("  Rounded   : no")
    print(f"  i/j dots  : {'attach' if KEEP_IJ_DOTS else 'remove'}")
    print(f"  Bed Face  : {BED_FACE}")
    print(f"  Output    : {OUT_DIR}/")
    print("=" * 50)
    print()

    results = process_batch(
        names_file=NAMES_FILE,
        font=FONT,
        height_mm=HEIGHT_MM,
        thickness_mm=THICKNESS_MM,
        base=BASE,
        base_height_mm=BASE_HEIGHT_MM,
        rounded=ROUNDED,
        corner_radius_mm=CORNER_RADIUS_MM,
        keep_ij_dots=KEEP_IJ_DOTS,
        bed_face=BED_FACE,
        out_dir=OUT_DIR,
    )

    has_errors = any(v.startswith("error") for v in results.values())
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    run()

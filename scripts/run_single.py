#!/usr/bin/env python3
"""
Non-CLI runner for single-name STL generation.

Edit the CONFIG section below with your settings, then run:

    uv run scripts/run_single.py

No command-line arguments are needed.
"""

# ============================================================
# CONFIG – edit these values
# ============================================================

NAME           = "Sofia"                         # Name to generate (case-sensitive)
FONT           = "fonts/Cookie-Regular.ttf"  # .ttf/.otf path, or system font name
HEIGHT_MM      = 20.0                            # Letter cap-height in mm
THICKNESS_MM   = 5.0                             # Z-depth (print thickness) in mm
BASE           = False                           # True = add a connecting base strip
BASE_HEIGHT_MM = 2.0                             # Height of base strip in mm (BASE=True only)
ROUNDED        = True                           # True = round the letter corners
CORNER_RADIUS_MM = 0.4                           # Corner radius in mm (ROUNDED=True only)
OUT_DIR        = "output"                        # Output directory (created if missing)

# ============================================================
# Execution – do not edit below this line
# ============================================================

import sys
import warnings
from pathlib import Path

# Allow running directly from the project root without installing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from stl_names.connector import GlyphConnectionError
from stl_names.exporter import PrinterLengthError
from stl_names.generator import generate_name


def run() -> None:
    print("=" * 50)
    print(f"  Name      : {NAME}")
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
    print(f"  Output    : {OUT_DIR}/")
    print("=" * 50)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            out_path = generate_name(
                name=NAME,
                font=FONT,
                height_mm=HEIGHT_MM,
                thickness_mm=THICKNESS_MM,
                base=BASE,
                base_height_mm=BASE_HEIGHT_MM,
                rounded=ROUNDED,
                corner_radius_mm=CORNER_RADIUS_MM,
                out_dir=OUT_DIR,
            )
        except PrinterLengthError as exc:
            print(f"\nERROR (printer size limit): {exc}")
            sys.exit(1)
        except GlyphConnectionError as exc:
            print(f"\nERROR (letter connection): {exc}")
            sys.exit(1)
        except FileNotFoundError as exc:
            print(f"\nERROR (font not found): {exc}")
            sys.exit(1)
        except ValueError as exc:
            print(f"\nERROR: {exc}")
            sys.exit(1)
        except Exception as exc:
            print(f"\nERROR ({type(exc).__name__}): {exc}")
            sys.exit(1)

    for w in caught:
        print(f"WARNING: {w.message}")

    print(f"\nDone -> {out_path}")


if __name__ == "__main__":
    run()

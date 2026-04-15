"""Batch processing of names from a TXT file."""
from __future__ import annotations

from pathlib import Path

from .connector import GlyphConnectionError
from .exporter import PrinterLengthError, sanitize_filename
from .generator import generate_name


def parse_names_file(path: str | Path) -> list[str]:
    """Read names from a file: one per line; ignore blank lines and # comments."""
    names: list[str] = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            names.append(line)
    return names


def process_batch(
    names_file: str,
    font: str,
    height_mm: float = 20.0,
    thickness_mm: float = 5.0,
    base: bool = False,
    base_height_mm: float = 2.0,
    rounded: bool = False,
    corner_radius_mm: float = 0.4,
    keep_ij_dots: bool = True,
    bed_face: str = "bottom",
    out_dir: str = "output",
) -> dict[str, str]:
    """Process all names in *names_file* and return a result summary.

    Duplicate names (same sanitized filename, case-insensitive) are skipped.
    The returned dict maps each name to either the output path or an error/skip message.
    """
    names = parse_names_file(names_file)
    seen: dict[str, str] = {}       # sanitized_key -> first original name
    results: dict[str, str] = {}

    for name in names:
        key = sanitize_filename(name)

        if key in seen:
            msg = f"skipped: same filename as already-processed '{seen[key]}' ({key}.stl)"
            print(f"  [skip] '{name}' -> {msg}")
            results[name] = msg
            continue

        seen[key] = name

        try:
            out_path = generate_name(
                name=name,
                font=font,
                height_mm=height_mm,
                thickness_mm=thickness_mm,
                base=base,
                base_height_mm=base_height_mm,
                rounded=rounded,
                corner_radius_mm=corner_radius_mm,
                keep_ij_dots=keep_ij_dots,
                bed_face=bed_face,
                out_dir=out_dir,
            )
            print(f"  [ok]   '{name}' -> {out_path}")
            results[name] = str(out_path)
        except PrinterLengthError as exc:
            msg = f"error (printer size): {exc}"
            print(f"  [err]  '{name}': {exc}")
            results[name] = msg
        except GlyphConnectionError as exc:
            msg = f"error (connection): {exc}"
            print(f"  [err]  '{name}': {exc}")
            results[name] = msg
        except Exception as exc:  # noqa: BLE001
            msg = f"error ({type(exc).__name__}): {exc}"
            print(f"  [err]  '{name}': {type(exc).__name__}: {exc}")
            results[name] = msg

    total = len(names)
    ok = sum(1 for v in results.values() if not v.startswith(("error", "skipped")))
    skipped = sum(1 for v in results.values() if v.startswith("skipped"))
    errors = total - ok - skipped
    print(f"\nBatch complete: {ok} generated, {skipped} skipped, {errors} failed out of {total}.")

    return results

"""STL export, filename sanitization, and printer limit checks."""
from __future__ import annotations

import re
import warnings
from pathlib import Path

import trimesh
from shapely.geometry import Polygon

WARN_LENGTH_MM = 230.0   # 23 cm -> warn and continue
MAX_LENGTH_MM = 280.0    # 28 cm -> hard error, do not generate


class PrinterLengthError(ValueError):
    """Raised when the name exceeds the printer maximum build length."""


def check_printer_limits(polygon: Polygon, name: str) -> None:
    """Emit a warning above 23 cm or raise PrinterLengthError above 28 cm."""
    min_x, _min_y, max_x, _max_y = polygon.bounds
    length_mm = max_x - min_x
    length_cm = length_mm / 10.0

    if length_mm > MAX_LENGTH_MM:
        raise PrinterLengthError(
            f"'{name}' is {length_cm:.1f} cm long, which exceeds the maximum "
            f"printer build size of {MAX_LENGTH_MM / 10:.0f} cm. "
            "STL not generated. Try a smaller height or a shorter name."
        )

    if length_mm > WARN_LENGTH_MM:
        warnings.warn(
            f"'{name}' is {length_cm:.1f} cm long, which exceeds the "
            f"recommended build size of {WARN_LENGTH_MM / 10:.0f} cm. "
            "Generation will continue, but the print may not fit on the bed.",
            UserWarning,
            stacklevel=3,
        )


def sanitize_filename(name: str) -> str:
    """Return a safe, lowercase filename stem for *name*.

    Converts to lowercase, replaces any character that is not
    alphanumeric, hyphen, or underscore with an underscore, then
    collapses consecutive underscores.
    """
    lower = name.lower()
    safe = re.sub(r"[^\w\-]", "_", lower, flags=re.ASCII)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe or "name"


def get_output_path(name: str, out_dir: str | Path) -> Path:
    """Resolve and return the output STL path, creating the directory if needed."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    return out_path / (sanitize_filename(name) + ".stl")


def export_stl(mesh: trimesh.Trimesh, path: Path) -> None:
    """Export *mesh* as a binary STL file to *path*."""
    mesh.export(str(path))

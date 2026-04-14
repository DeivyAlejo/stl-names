"""CLI entrypoint for batch TXT-based STL generation."""
from __future__ import annotations

import typer

from .batch import process_batch

app = typer.Typer(help="Generate 3D-printable STLs for a list of names from a TXT file.")


@app.command()
def main(
    names_file: str = typer.Argument(..., help="TXT file with one name per line."),
    font: str = typer.Option(..., "--font", "-f", help="Font .ttf/.otf path or system font name."),
    height: float = typer.Option(20.0, "--height", "-H", help="Letter cap-height in mm."),
    thickness: float = typer.Option(5.0, "--thickness", "-t", help="Z-depth (thickness) in mm."),
    base: bool = typer.Option(False, "--base/--no-base", help="Add rectangular base strip."),
    base_height: float = typer.Option(2.0, "--base-height", help="Height of base strip in mm."),
    rounded: bool = typer.Option(False, "--rounded/--no-rounded", help="Round the letter corners."),
    corner_radius: float = typer.Option(0.4, "--corner-radius", help="Corner radius in mm."),
    bed_face: str = typer.Option("bottom", "--bed-face", help="Face against bed: top or bottom."),
    out_dir: str = typer.Option("output", "--out-dir", "-o", help="Output directory."),
) -> None:
    """Generate STL files for all names listed in NAMES_FILE."""
    results = process_batch(
        names_file=names_file,
        font=font,
        height_mm=height,
        thickness_mm=thickness,
        base=base,
        base_height_mm=base_height,
        rounded=rounded,
        corner_radius_mm=corner_radius,
        bed_face=bed_face,
        out_dir=out_dir,
    )
    has_errors = any(v.startswith("error") for v in results.values())
    if has_errors:
        raise typer.Exit(1)

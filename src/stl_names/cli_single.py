"""CLI entrypoint for single-name STL generation."""
from __future__ import annotations

import typer

from .connector import GlyphConnectionError
from .exporter import PrinterLengthError
from .generator import generate_name

app = typer.Typer(help="Generate a 3D-printable STL for a single name.")


@app.command()
def main(
    name: str = typer.Argument(..., help="Name to generate (case-sensitive)."),
    font: str = typer.Option(..., "--font", "-f", help="Font .ttf/.otf path or system font name."),
    height: float = typer.Option(20.0, "--height", "-H", help="Height in mm anchored to reference letters (a/e/o)."),
    thickness: float = typer.Option(5.0, "--thickness", "-t", help="Z-depth (thickness) in mm."),
    base: bool = typer.Option(False, "--base/--no-base", help="Add rectangular base strip."),
    base_height: float = typer.Option(2.0, "--base-height", help="Height of base strip in mm."),
    rounded: bool = typer.Option(False, "--rounded/--no-rounded", help="Round the letter corners."),
    corner_radius: float = typer.Option(0.4, "--corner-radius", help="Corner radius in mm."),
    keep_ij_dots: bool = typer.Option(
        True,
        "--keep-ij-dots/--remove-ij-dots",
        help="Keep lowercase i/j dots and attach them to the stem, or remove those dots.",
    ),
    bed_face: str = typer.Option("bottom", "--bed-face", help="Face against bed: top or bottom."),
    out_dir: str = typer.Option("output", "--out-dir", "-o", help="Output directory."),
) -> None:
    """Generate a 3D-printable STL for NAME using the specified font and parameters."""
    try:
        out_path = generate_name(
            name=name,
            font=font,
            height_mm=height,
            thickness_mm=thickness,
            base=base,
            base_height_mm=base_height,
            rounded=rounded,
            corner_radius_mm=corner_radius,
            keep_ij_dots=keep_ij_dots,
            bed_face=bed_face,
            out_dir=out_dir,
        )
        typer.echo(f"Generated: {out_path}")
    except (PrinterLengthError, GlyphConnectionError, FileNotFoundError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    except Exception as exc:
        typer.echo(f"Unexpected error ({type(exc).__name__}): {exc}", err=True)
        raise typer.Exit(1)

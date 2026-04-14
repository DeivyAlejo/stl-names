# STL Names Generator

Generate 3D-printable STL files from names using custom fonts.

This project converts text into connected 3D solids for name tags, signs, and decorative prints. It supports cursive and non-cursive fonts, automatic letter connection, optional base strip, corner smoothing, batch generation, and print-bed orientation control.

## What This Project Does

- Generates one STL from one name.
- Generates many STLs from a TXT file (one name per line).
- Keeps uppercase/lowercase differences in glyph geometry.
- Supports font selection by:
  - font file path (`.ttf`/`.otf`), or
  - system font name.
- Supports printer constraints:
  - warning if model length is above 23 cm,
  - blocking error if model length is above 28 cm.
- Supports optional rectangular base for disconnected fonts.
- Supports tight-corner smoothing for better printability at joins.
- Supports bed-facing orientation (`bottom` or `top`).

## Main Features

- Auto-connect letters by shifting glyphs until overlap is reached.
- Configurable dimensions:
  - letter height (mm),
  - thickness/depth (mm),
  - base height (mm).
- Rounded/tight-corner smoothing:
  - enable/disable,
  - configurable radius (default `0.4` mm).
- Bed face selection:
  - `bottom` (default),
  - `top` (flipped for opposite face on bed).
- Safe output naming:
  - lowercase filenames,
  - sanitized characters,
  - duplicate filename detection in batch mode.

## Project Structure

- `scripts/run_single.py`: non-CLI single-name runner (edit config in file).
- `scripts/run_batch.py`: non-CLI batch runner (edit config in file).
- `src/stl_names/`: core library and CLI modules.
- `names.txt`: sample batch input.
- `fonts/`: place your `.ttf`/`.otf` files here.
- `output/`: generated STL output.

## Requirements

- `uv` installed.
- Python `3.14` available to uv.
  - Current environment in this repo resolves to Python `3.14.3`.

## Quick Start With uv

### Linux/macOS

1. Clone and enter project:

```bash
git clone <your-repo-url>
cd stl-names
```

2. Create/install environment and dependencies:

```bash
uv sync --extra dev
```

3. (Optional) run tests:

```bash
uv run pytest tests/ -q
```

### Windows (PowerShell)

1. Clone and enter project:

```powershell
git clone <your-repo-url>
cd stl-names
```

2. Create/install environment and dependencies:

```powershell
uv sync --extra dev
```

3. (Optional) run tests:

```powershell
uv run pytest tests/ -q
```

## Run Without CLI (Recommended)

Edit config values in the runner files, then run.

### Linux/macOS

Single name:

```bash
uv run scripts/run_single.py
```

Batch from TXT:

```bash
uv run scripts/run_batch.py
```

### Windows (PowerShell)

Single name:

```powershell
uv run scripts/run_single.py
```

Batch from TXT:

```powershell
uv run scripts/run_batch.py
```

### Important Runner Config Fields

In both runner files you can set:

- `FONT`
- `HEIGHT_MM`
- `THICKNESS_MM`
- `BASE` and `BASE_HEIGHT_MM`
- `ROUNDED` and `CORNER_RADIUS_MM`
- `BED_FACE` (`"bottom"` or `"top"`)
- `OUT_DIR`

In `run_batch.py`, also set:

- `NAMES_FILE`

## CLI Usage Examples

The project defines two commands in `pyproject.toml`:

- `stl-single`
- `stl-batch`

You can run them through uv.

### Linux/macOS

Single name:

```bash
uv run stl-single "Sofia" \
  --font "fonts/Parisienne-Regular.ttf" \
  --height 20 \
  --thickness 4 \
  --rounded --corner-radius 0.4 \
  --bed-face bottom \
  --out-dir output
```

Single name with base (for non-cursive font):

```bash
uv run stl-single "LUCAS" \
  --font "fonts/Roboto-Bold.ttf" \
  --height 18 \
  --thickness 4 \
  --base --base-height 2.0 \
  --bed-face top \
  --out-dir output
```

Batch:

```bash
uv run stl-batch names.txt \
  --font "fonts/Parisienne-Regular.ttf" \
  --height 20 \
  --thickness 4 \
  --rounded --corner-radius 0.4 \
  --bed-face bottom \
  --out-dir output
```

### Windows (PowerShell)

Single name:

```powershell
uv run stl-single "Sofia" --font "fonts/Parisienne-Regular.ttf" --height 20 --thickness 4 --rounded --corner-radius 0.4 --bed-face bottom --out-dir output
```

Batch:

```powershell
uv run stl-batch names.txt --font "fonts/Parisienne-Regular.ttf" --height 20 --thickness 4 --rounded --corner-radius 0.4 --bed-face bottom --out-dir output
```

## Batch Input Format

`names.txt` format:

- one name per line,
- blank lines ignored,
- lines starting with `#` treated as comments,
- duplicate output filenames are skipped and reported.

Example:

```text
# Sample names
Sofia
Maria
ANA
ana
```

`ANA` and `ana` map to the same lowercase output filename and one will be skipped.

## Output Behavior

- Files are written to `output/` by default.
- STL filename is based on sanitized lowercase name.
- Printer length guard:
  - `> 23 cm`: warning, file still generated.
  - `> 28 cm`: error, file is not generated.

## Troubleshooting

- Font not found:
  - check the path in `FONT`, or
  - use a valid system font name.
- Letters fail to connect:
  - try a more cursive font,
  - increase overlap-friendly styling,
  - or enable `BASE = True`.
- No visible rounded effect:
  - increase `CORNER_RADIUS_MM` (for example `0.6` or `0.8`).

## Current Status

- Core generation implemented.
- Non-CLI runners implemented.
- CLI commands implemented.
- Tests passing in current environment.

"""fetch_tiger_shapefiles.py

Downloads U.S. Census TIGER/Line shapefiles required by the Displacement Defense Atlas
directly from the Census Bureau FTP. Files are written to data/raw/tiger/ which is
excluded from git via .gitignore (*.shp, *.dbf, *.shx, etc.).

Usage:
    python scripts/pipeline/fetch_tiger_shapefiles.py

Run this once after cloning the repo, or any time you need to refresh the source files.
No API key required — all files are public Census Bureau data.

Outputs (written to data/raw/tiger/):
    tl_2023_48_tract/       — Texas census tracts (TIGER 2023)
    tl_2023_48113_edges/    — Dallas County road edges (for I-30 overlay)
    tl_2023_us_county/      — County boundaries (for map extent clipping)
"""

import os
import io
import zipfile
import urllib.request
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "raw", "tiger"
)

TIGER_BASE = "https://www2.census.gov/geo/tiger/TIGER2023"

# (label, remote_url, local_subfolder)
FILES = [
    (
        "Texas census tracts (2023)",
        f"{TIGER_BASE}/TRACT/tl_2023_48_tract.zip",
        "tl_2023_48_tract",
    ),
    (
        "Dallas County road edges (2023) — for I-30 overlay",
        f"{TIGER_BASE}/EDGES/tl_2023_48113_edges.zip",
        "tl_2023_48113_edges",
    ),
    (
        "US county boundaries (2023) — for map extent clipping",
        f"{TIGER_BASE}/COUNTY/tl_2023_us_county.zip",
        "tl_2023_us_county",
    ),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def download_and_extract(label: str, url: str, dest_dir: str) -> None:
    """Download a zip from `url` and extract into `dest_dir`."""
    if os.path.isdir(dest_dir) and os.listdir(dest_dir):
        print(f"  [skip] {label} — already present at {dest_dir}")
        return

    print(f"  [download] {label}")
    print(f"             {url}")

    os.makedirs(dest_dir, exist_ok=True)

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
    except Exception as exc:
        print(f"  [ERROR] Failed to download {url}: {exc}", file=sys.stderr)
        raise

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(dest_dir)

    print(f"  [ok]     Extracted to {dest_dir}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("Displacement Defense Atlas — TIGER Shapefile Fetch")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for label, url, subfolder in FILES:
        dest = os.path.join(OUTPUT_DIR, subfolder)
        download_and_extract(label, url, dest)

    print()
    print("Done. All TIGER shapefiles are in data/raw/tiger/")
    print("These files are git-ignored — do not commit them.")
    print()
    print("To load in geopandas:")
    print("  import geopandas as gpd")
    print("  tracts = gpd.read_file('data/raw/tiger/tl_2023_48_tract/tl_2023_48_tract.shp')")
    print("  tracts = tracts[tracts['COUNTYFP'] == '113']  # Dallas County only")


if __name__ == "__main__":
    main()

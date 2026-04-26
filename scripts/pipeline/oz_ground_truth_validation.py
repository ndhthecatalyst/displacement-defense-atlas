"""
oz_ground_truth_validation.py
=============================
Falsification cross-check for the QOZ polygon layer.

Reads `data/raw/layer3_tif_oz/oz_investments_ground_truth.csv` — the
hand-curated ledger of documented OZ investments in Dallas County —
and verifies that each investment geocodes to a tract whose GEOID is in
our QOZ layer (`outputs/geojson/dallas_qoz_tracts.geojson`).

If more than --max-mismatch-pct (default 5%) of ground-truth investments
fall outside the QOZ polygon set, the script exits non-zero. That
condition means the QOZ layer is wrong (vintage mismatch, missing PR
tracts, FIPS issue) and any "0 OZ in 54 South Susceptible" claim in
the thesis is non-falsifiable until corrected.

USAGE:

    python -m scripts.pipeline.oz_ground_truth_validation \\
        [--max-mismatch-pct 0.05]
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("oz-validate")

REPO = Path(__file__).resolve().parents[2]
GT   = REPO / "data" / "raw" / "layer3_tif_oz" / "oz_investments_ground_truth.csv"
QOZ  = REPO / "outputs" / "geojson" / "dallas_qoz_tracts.geojson"
OUT  = REPO / "outputs" / "tables" / "oz_validation_report.csv"


def main(max_mismatch_pct: float) -> int:
    if not GT.exists():
        log.error("MISSING INPUT: %s", GT)
        log.error("  This is the falsification ledger of documented OZ investments.")
        log.error("  See data/raw/layer3_tif_oz/README.md → 'Ground-truth ledger' for sources.")
        log.error("  Without it the OZ join cannot be cross-validated.")
        return 2

    if not QOZ.exists():
        log.error("MISSING INPUT: %s", QOZ)
        log.error("  Run scripts/pipeline/build_layer3_tif_oz.py first.")
        return 2

    gt = pd.read_csv(GT, dtype={"claimed_oz_geoid": str})
    log.info("Ground-truth ledger: %d documented investments", len(gt))

    required = {"project_name", "lat", "lon"}
    missing = required - set(gt.columns)
    if missing:
        log.error("Ground-truth file missing required columns: %s", missing)
        return 2

    points = gpd.GeoDataFrame(
        gt.copy(),
        geometry=[Point(x, y) for x, y in zip(gt["lon"], gt["lat"])],
        crs="EPSG:4326",
    )
    qoz = gpd.read_file(QOZ).to_crs("EPSG:4326")

    joined = gpd.sjoin(points, qoz[["GEOID10", "geometry"]], how="left", predicate="within")
    joined["computed_geoid"] = joined["GEOID10"].astype(str)
    joined["claimed_geoid"]  = joined.get("claimed_oz_geoid", pd.Series([""] * len(joined))).fillna("").astype(str)
    joined["match"] = (
        (joined["computed_geoid"].notna())
        & (joined["computed_geoid"] != "nan")
        & (
            (joined["claimed_geoid"] == "")
            | (joined["claimed_geoid"] == joined["computed_geoid"])
        )
    )

    n        = len(joined)
    n_in_qoz = int(joined["computed_geoid"].notna().sum() - (joined["computed_geoid"] == "nan").sum())
    n_match  = int(joined["match"].sum())
    miss_pct = 1.0 - (n_in_qoz / n) if n else 0.0
    log.info("  ✓ in QOZ polygon:    %d / %d (%.1f%%)", n_in_qoz, n, 100.0 * n_in_qoz / max(n, 1))
    log.info("  ✓ claimed=computed:  %d / %d (%.1f%%)", n_match, n, 100.0 * n_match / max(n, 1))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = [c for c in [
        "project_name", "address", "lat", "lon", "qof_name", "year_announced",
        "dollars_invested", "asset_type", "claimed_geoid", "computed_geoid",
        "match", "source_url",
    ] if c in joined.columns]
    joined[cols].to_csv(OUT, index=False)
    log.info("✓ wrote %s", OUT.relative_to(REPO))

    if miss_pct > max_mismatch_pct:
        log.error("FAIL: %.1f%% of ground-truth investments fall outside QOZ polygons (threshold %.1f%%)",
                  100.0 * miss_pct, 100.0 * max_mismatch_pct)
        log.error("  → QOZ layer likely wrong vintage or missing tracts. Investigate before publishing.")
        return 1
    log.info("PASS: ground-truth coverage within tolerance.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--max-mismatch-pct", type=float, default=0.05)
    args = p.parse_args()
    sys.exit(main(max_mismatch_pct=args.max_mismatch_pct))

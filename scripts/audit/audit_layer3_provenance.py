"""
audit_layer3_provenance.py
==========================
Diff the previous Layer 3 implementation against the new authoritative
pipeline.

Compares:
  - Hardcoded TIF bounding boxes in scripts/pipeline/atlas_v0_build.py
    against the official TIF subdistrict polygons in
    outputs/geojson/dallas_tif_subdistricts.geojson
  - Hardcoded 30-GEOID OZ list in scripts/pipeline/atlas_v0_build.py
    against the HUD QOZ Dallas County set in
    outputs/geojson/dallas_qoz_tracts.geojson

Writes the diff to outputs/tables/layer3_provenance_audit.csv with
columns:

    layer, source, item, in_old, in_new, status

`status` ∈ {"in_both", "in_old_only", "in_new_only"}.

Use case: shows the fellowship reviewer exactly what changed when we
moved from hardcoded approximations to authoritative joins. Run after
build_layer3_tif_oz.py has produced its outputs.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd
import geopandas as gpd

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("audit-l3")

REPO = Path(__file__).resolve().parents[2]

# Hardcoded values from atlas_v0_build.py — kept verbatim for the diff.
OLD_TIF_NAMES = {
    "Vickery Meadow TIF", "Sports Arena TIF", "Cedars TIF",
    "State-Thomas TIF", "Uptown TIF", "Design District TIF",
    "Deep Ellum TIF", "MLK Jr. TIF", "Farmers Market TIF",
    "Davis Garden TIF", "Fort Worth Ave TIF", "Grand Park South TIF",
    "Southwestern Medical TIF", "Skillman Corridor TIF",
    "Mall Area Redevelopment TIF", "TOD TIF (DART stations)",
    "Riverfront TIF", "City Center TIF",
}

OLD_OZ_GEOIDS = {
    "48113010800","48113011100","48113011200","48113011500","48113011600",
    "48113012100","48113012200","48113012500","48113012600","48113012700",
    "48113013400","48113013700","48113013800","48113013900","48113014000",
    "48113014100","48113014600","48113015300","48113015400","48113016200",
    "48113016300","48113016800","48113016900","48113017200","48113017300",
    "48113017700","48113018000","48113018100","48113018200","48113018300",
}


def main() -> int:
    rows = []

    # ---- TIF diff ----
    tif_path = REPO / "outputs" / "geojson" / "dallas_tif_subdistricts.geojson"
    if not tif_path.exists():
        log.error("New TIF layer missing: %s — run build_layer3_tif_oz.py first.", tif_path)
        return 2
    tif = gpd.read_file(tif_path)
    name_col = next(
        (c for c in ["subdistrict_name", "DISTRICT", "Name", "NAME", "district_name"]
         if c in tif.columns),
        None,
    )
    new_tif_names = set(tif[name_col].astype(str)) if name_col else set()

    for n in sorted(OLD_TIF_NAMES | new_tif_names):
        in_old = n in OLD_TIF_NAMES
        in_new = n in new_tif_names
        rows.append({
            "layer": "TIF",
            "source": "district_name" if name_col else "(no name col)",
            "item": n,
            "in_old": int(in_old),
            "in_new": int(in_new),
            "status": "in_both" if (in_old and in_new) else ("in_old_only" if in_old else "in_new_only"),
        })

    # ---- OZ diff ----
    qoz_path = REPO / "outputs" / "geojson" / "dallas_qoz_tracts.geojson"
    if not qoz_path.exists():
        log.error("New QOZ layer missing: %s — run build_layer3_tif_oz.py first.", qoz_path)
        return 2
    qoz = gpd.read_file(qoz_path)
    new_oz_geoids = set(qoz["GEOID10"].astype(str).str.zfill(11))

    for g in sorted(OLD_OZ_GEOIDS | new_oz_geoids):
        in_old = g in OLD_OZ_GEOIDS
        in_new = g in new_oz_geoids
        rows.append({
            "layer": "OZ",
            "source": "GEOID10",
            "item": g,
            "in_old": int(in_old),
            "in_new": int(in_new),
            "status": "in_both" if (in_old and in_new) else ("in_old_only" if in_old else "in_new_only"),
        })

    out = REPO / "outputs" / "tables" / "layer3_provenance_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)

    # Headline counts
    df = pd.DataFrame(rows)
    log.info("===== Layer 3 provenance audit =====")
    for layer in ["TIF", "OZ"]:
        sub = df[df["layer"] == layer]
        log.info("  %s — in_both: %d, in_old_only: %d, in_new_only: %d",
                 layer,
                 (sub["status"] == "in_both").sum(),
                 (sub["status"] == "in_old_only").sum(),
                 (sub["status"] == "in_new_only").sum())
    log.info("✓ wrote %s", out.relative_to(REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())

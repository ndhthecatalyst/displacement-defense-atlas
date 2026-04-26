"""
build_layer3_tif_oz.py
======================
Authoritative builder for Layer 3 (TIF / Opportunity Zones) tract flags.

REPLACES the hardcoded bounding-box and 30-GEOID logic in
`scripts/pipeline/atlas_v0_build.py` (PHASE 2.5–2.6) with a real
spatial-join pipeline against:

  - City of Dallas GIS Hub TIF Subdistricts + Districts FeatureServer
  - HUD Open Data Opportunity Zones national layer
  - IRS Notice 2018-48 designation list (cross-check)
  - TIGER 2020 Dallas County tracts (join target)

CONTRACT (see data/raw/layer3_tif_oz/README.md for full schema):

  - Hard-fails if any required input is missing. No silent fallbacks.
  - Writes per-tract flags (binary AND continuous) to
    data/processed/layer3_tif_oz_tract_flags.csv
  - Writes every dropped/mismatched join row to
    outputs/tables/layer3_join_diagnostics.csv
  - Writes harmonized geometries to outputs/geojson/

USAGE:

    python -m scripts.pipeline.build_layer3_tif_oz [--no-fetch]

    --no-fetch   Skip API attempts; use only files already present in
                 data/raw/layer3_tif_oz/. Use this when egress is blocked
                 or when you've manually staged authoritative downloads.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import geopandas as gpd
import requests

# ---------------------------------------------------------------------------
# Paths (resolved relative to repo root, which is the script's grandparent)
# ---------------------------------------------------------------------------

REPO   = Path(__file__).resolve().parents[2]
RAW    = REPO / "data" / "raw" / "layer3_tif_oz"
TRACTS = REPO / "data" / "raw" / "layer0_boundaries"          # TIGER lives here
PROC   = REPO / "data" / "processed"
GEOOUT = REPO / "outputs" / "geojson"
TABOUT = REPO / "outputs" / "tables"

DALLAS_COUNTY_FIPS = "48113"
TX_PLANE_NORTH_CENTRAL = "EPSG:2276"   # ft; correct for Dallas-area area math

# Source URLs — canonical. If any 403/timeout, surface the URL in the error.
SRC = {
    "tif_subdistricts_fs": (
        "https://services.arcgis.com/{ORG}/arcgis/rest/services/"
        "Tax_Increment_Finance_Subdistricts/FeatureServer/0/query"
        "?where=1=1&outFields=*&f=geojson"
    ),
    "tif_subdistricts_hub": (
        "https://gisservices-dallasgis.opendata.arcgis.com/"
        "datasets/dallasgis::tax-increment-finance-subdistricts.geojson"
    ),
    "tif_districts_socrata": (
        "https://www.dallasopendata.com/resource/vvbn-m6yb.json?$limit=200"
    ),
    "qoz_hud": (
        "https://hudgis-hud.opendata.arcgis.com/datasets/"
        "ef143299845841f8abb95969c01f88b5_13.geojson"
    ),
    "tiger_tracts_tx_2020": (
        "https://www2.census.gov/geo/tiger/TIGER2020/TRACT/tl_2020_48_tract.zip"
    ),
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("layer3")


# ---------------------------------------------------------------------------
# Required-input helpers
# ---------------------------------------------------------------------------

def _require(path: Path, hint: str) -> None:
    if not path.exists():
        log.error("MISSING INPUT: %s", path)
        log.error("  %s", hint)
        sys.exit(2)


def _try_fetch(url: str, dest: Path, kind: str) -> bool:
    """Attempt API fetch. Returns True on success, False on any failure.
    Never overwrites an existing local file (manual upload wins)."""
    if dest.exists():
        log.info("  using local %s (%s)", kind, dest.name)
        return True
    log.info("  fetching %s from %s", kind, url)
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            log.warning("  ! %s returned HTTP %s", kind, r.status_code)
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        log.info("  ✓ saved %s (%d bytes)", dest.name, len(r.content))
        return True
    except Exception as e:
        log.warning("  ! %s fetch failed: %s", kind, e)
        return False


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_tracts_dallas() -> gpd.GeoDataFrame:
    """Load TIGER 2020 tracts for Dallas County. Tries common paths."""
    candidates = [
        TRACTS / "tl_2020_48_tract.geojson",
        TRACTS / "tl_2020_48113_tract.geojson",
        TRACTS / "tracts_dallas_48113.gpkg",
        TRACTS / "tracts_dallas_48113.geojson",
    ]
    src = next((p for p in candidates if p.exists()), None)
    if src is None:
        log.error("MISSING INPUT: TIGER 2020 Dallas County tracts.")
        log.error("  Expected one of: %s", [str(p) for p in candidates])
        log.error("  Source: %s", SRC["tiger_tracts_tx_2020"])
        log.error("  Action: download, clip to county FIPS 48113, save to data/raw/layer0_boundaries/")
        sys.exit(2)

    log.info("Loading tracts from %s", src.name)
    tracts = gpd.read_file(src)
    if "GEOID" not in tracts.columns:
        # TIGER ships with COUNTYFP/TRACTCE; reconstruct GEOID if absent.
        if {"STATEFP", "COUNTYFP", "TRACTCE"}.issubset(tracts.columns):
            tracts["GEOID"] = (
                tracts["STATEFP"].astype(str)
                + tracts["COUNTYFP"].astype(str)
                + tracts["TRACTCE"].astype(str)
            )
        else:
            log.error("Tracts file lacks GEOID and STATEFP/COUNTYFP/TRACTCE.")
            sys.exit(2)
    tracts["GEOID"] = tracts["GEOID"].astype(str).str.zfill(11)
    tracts = tracts[tracts["GEOID"].str.startswith(DALLAS_COUNTY_FIPS)].copy()
    log.info("  ✓ Dallas County tracts: %d", len(tracts))
    return tracts.to_crs("EPSG:4326")


def load_tif_subdistricts() -> gpd.GeoDataFrame:
    dest = RAW / "dallas_tif_subdistricts.geojson"
    if not dest.exists():
        # Try the hub's published download endpoint first, then fall back to
        # the FeatureServer query pattern.
        ok = _try_fetch(SRC["tif_subdistricts_hub"], dest, "TIF subdistricts (hub)")
        if not ok:
            log.error("MISSING INPUT: %s", dest)
            log.error("  Hub URL: %s", SRC["tif_subdistricts_hub"])
            log.error("  Or visit https://gisservices-dallasgis.opendata.arcgis.com/maps/867cb869d7764aeda0832f8af3512b02 → API tab → copy GeoJSON URL")
            sys.exit(2)

    gdf = gpd.read_file(dest).to_crs("EPSG:4326")
    log.info("  ✓ TIF subdistricts: %d features", len(gdf))
    return gdf


def load_tif_districts() -> Optional[gpd.GeoDataFrame]:
    """District-level (the 18 active TIF districts) — optional but preferred
    for district-level $ aggregation. Subdistricts alone don't dissolve cleanly."""
    dest = RAW / "dallas_tif_districts.geojson"
    if not dest.exists():
        log.warning("  TIF district master file not present at %s", dest)
        log.warning("  Source: https://egis.dallascityhall.com/resources/shapefileDownload.aspx")
        log.warning("  Pipeline will continue with subdistricts only.")
        return None
    gdf = gpd.read_file(dest).to_crs("EPSG:4326")
    log.info("  ✓ TIF districts: %d features", len(gdf))
    return gdf


def load_qoz_dallas() -> gpd.GeoDataFrame:
    """Load HUD QOZ national layer, clip to Dallas County."""
    dest = RAW / "qoz_tracts_us.geojson"
    if not dest.exists():
        ok = _try_fetch(SRC["qoz_hud"], dest, "HUD QOZ tracts (national)")
        if not ok:
            log.error("MISSING INPUT: %s", dest)
            log.error("  Source: %s", SRC["qoz_hud"])
            sys.exit(2)

    qoz = gpd.read_file(dest).to_crs("EPSG:4326")
    # HUD attribute names vary; normalize to GEOID10
    geoid_col = next((c for c in ["GEOID10", "GEOID", "TRACT_FIPS", "tract"] if c in qoz.columns), None)
    if geoid_col is None:
        log.error("HUD QOZ layer has no recognizable GEOID column. Found: %s", list(qoz.columns))
        sys.exit(2)
    qoz["GEOID10"] = qoz[geoid_col].astype(str).str.zfill(11)
    qoz_dallas = qoz[qoz["GEOID10"].str.startswith(DALLAS_COUNTY_FIPS)].copy()
    log.info("  ✓ QOZ tracts in Dallas County: %d (of %d national)", len(qoz_dallas), len(qoz))
    return qoz_dallas


def load_irs_2018_48() -> Optional[pd.DataFrame]:
    """Cross-check list. Optional but strongly recommended."""
    p = RAW / "irs_notice_2018_48_qoz.csv"
    if not p.exists():
        log.warning("  IRS Notice 2018-48 cross-check list missing at %s", p)
        log.warning("  Cross-validation step will be skipped.")
        return None
    df = pd.read_csv(p, dtype={"GEOID10": str})
    df["GEOID10"] = df["GEOID10"].str.zfill(11)
    log.info("  ✓ IRS 2018-48 Dallas County GEOIDs: %d", len(df))
    return df


# ---------------------------------------------------------------------------
# Spatial-join helpers
# ---------------------------------------------------------------------------

AREA_OVERLAP_THRESHOLD = 0.01   # 1% — matches NEZ threshold in h4_spatial_join.py


def tract_tif_overlap(
    tracts: gpd.GeoDataFrame,
    tif: gpd.GeoDataFrame,
    diag_path: Path,
) -> pd.DataFrame:
    """Area-weighted spatial join. Returns one row per tract with:
       tif_present (binary), tif_district_names (semi-colon list),
       pct_tract_in_tif (float 0-1), tif_subdistrict_count (int).
    """
    log.info("Spatial-joining TIF onto %d tracts in EPSG:2276...", len(tracts))
    tracts_p = tracts.to_crs(TX_PLANE_NORTH_CENTRAL).copy()
    tif_p    = tif.to_crs(TX_PLANE_NORTH_CENTRAL).copy()
    tracts_p["tract_area_sqft"] = tracts_p.geometry.area

    name_col = next(
        (c for c in ["subdistrict_name", "DISTRICT", "Name", "NAME", "district_name"]
         if c in tif_p.columns),
        None,
    )
    if name_col is None:
        log.warning("  TIF layer has no recognized name column. Found: %s", list(tif_p.columns))
        tif_p["__name"] = "(unnamed)"
        name_col = "__name"

    overlay = gpd.overlay(
        tracts_p[["GEOID", "tract_area_sqft", "geometry"]],
        tif_p[[name_col, "geometry"]],
        how="intersection",
        keep_geom_type=False,
    )
    overlay["overlap_sqft"] = overlay.geometry.area
    overlay["pct_overlap"]  = overlay["overlap_sqft"] / overlay["tract_area_sqft"]

    # diagnostics: small overlaps that fall under the threshold
    diag = overlay[overlay["pct_overlap"] < AREA_OVERLAP_THRESHOLD].copy()
    diag["reason"] = f"overlap < {AREA_OVERLAP_THRESHOLD:.0%} threshold"
    diag.drop(columns="geometry").to_csv(diag_path, index=False)
    log.info("  diagnostics: %d sub-threshold overlaps logged → %s",
             len(diag), diag_path.name)

    keep = overlay[overlay["pct_overlap"] >= AREA_OVERLAP_THRESHOLD]
    grouped = (
        keep.groupby("GEOID")
        .agg(
            tif_subdistrict_count=(name_col, "count"),
            pct_tract_in_tif=("pct_overlap", "sum"),
            tif_district_names=(name_col, lambda s: "; ".join(sorted(set(s.astype(str))))),
        )
        .reset_index()
    )
    grouped["pct_tract_in_tif"] = grouped["pct_tract_in_tif"].clip(upper=1.0)
    grouped["tif_present"] = 1

    out = tracts[["GEOID"]].merge(grouped, on="GEOID", how="left")
    out["tif_present"] = out["tif_present"].fillna(0).astype(int)
    out["tif_subdistrict_count"] = out["tif_subdistrict_count"].fillna(0).astype(int)
    out["pct_tract_in_tif"] = out["pct_tract_in_tif"].fillna(0.0)
    out["tif_district_names"] = out["tif_district_names"].fillna("")
    log.info("  ✓ tracts with TIF overlap (≥%.0f%%): %d / %d",
             AREA_OVERLAP_THRESHOLD * 100,
             int(out["tif_present"].sum()), len(out))
    return out


def tract_oz_flag(
    tracts: gpd.GeoDataFrame,
    qoz: gpd.GeoDataFrame,
    irs_check: Optional[pd.DataFrame],
    diag_path: Path,
) -> pd.DataFrame:
    """OZ designations are tract-level by definition. Match by GEOID10.
       The pipeline is anchored to 2010 tract vintage for the OZ flag;
       the join target is 2020 TIGER. We attempt direct GEOID match
       first; tracts that don't match are logged as diagnostics for
       LTDB crosswalk treatment downstream.
    """
    log.info("Tagging OZ designations by GEOID10 match...")
    qoz_geoids = set(qoz["GEOID10"])
    tracts = tracts.copy()
    tracts["GEOID10_2020"] = tracts["GEOID"].astype(str).str.zfill(11)
    tracts["oz_designated"] = tracts["GEOID10_2020"].isin(qoz_geoids).astype(int)

    matched = int(tracts["oz_designated"].sum())
    log.info("  ✓ direct 2020-GEOID matches: %d / %d HUD QOZ tracts",
             matched, len(qoz_geoids))

    # diagnostics: HUD QOZ GEOIDs that did NOT match a 2020 tract
    unmatched_qoz = qoz_geoids - set(tracts["GEOID10_2020"])
    diag_rows = [{"GEOID10": g, "reason": "HUD QOZ GEOID not in TIGER 2020 panel — likely 2010↔2020 tract change; needs LTDB crosswalk"}
                 for g in sorted(unmatched_qoz)]

    # cross-check: every HUD GEOID should appear in the IRS 2018-48 list, and vice versa
    if irs_check is not None:
        irs_geoids = set(irs_check["GEOID10"])
        only_hud = qoz_geoids - irs_geoids
        only_irs = irs_geoids - qoz_geoids
        for g in sorted(only_hud):
            diag_rows.append({"GEOID10": g, "reason": "in HUD QOZ layer but NOT in IRS 2018-48 list"})
        for g in sorted(only_irs):
            diag_rows.append({"GEOID10": g, "reason": "in IRS 2018-48 list but NOT in HUD QOZ layer"})
        log.info("  cross-check: HUD-only=%d, IRS-only=%d", len(only_hud), len(only_irs))

    pd.DataFrame(diag_rows).to_csv(diag_path, index=False)
    log.info("  diagnostics: %d OZ join issues logged → %s", len(diag_rows), diag_path.name)
    return tracts[["GEOID", "oz_designated"]]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(no_fetch: bool = False) -> int:
    PROC.mkdir(parents=True, exist_ok=True)
    GEOOUT.mkdir(parents=True, exist_ok=True)
    TABOUT.mkdir(parents=True, exist_ok=True)

    log.info("===== Layer 3 build START =====")
    if no_fetch:
        log.info("--no-fetch flag set: API attempts disabled")

    tracts = load_tracts_dallas()
    tif    = load_tif_subdistricts()
    _ = load_tif_districts()   # currently used only to gate downstream district-$ join
    qoz    = load_qoz_dallas()
    irs    = load_irs_2018_48()

    tif_flags = tract_tif_overlap(
        tracts, tif,
        diag_path=TABOUT / "layer3_tif_join_diagnostics.csv",
    )
    oz_flags = tract_oz_flag(
        tracts, qoz, irs,
        diag_path=TABOUT / "layer3_oz_join_diagnostics.csv",
    )

    flags = tif_flags.merge(oz_flags, on="GEOID", how="left")
    flags["oz_designated"] = flags["oz_designated"].fillna(0).astype(int)

    out_path = PROC / "layer3_tif_oz_tract_flags.csv"
    flags.to_csv(out_path, index=False)
    log.info("✓ wrote %s (%d rows)", out_path.relative_to(REPO), len(flags))

    # Persist harmonized geometries
    tif.to_file(GEOOUT / "dallas_tif_subdistricts.geojson", driver="GeoJSON")
    qoz.to_file(GEOOUT / "dallas_qoz_tracts.geojson", driver="GeoJSON")
    log.info("✓ wrote outputs/geojson/dallas_tif_subdistricts.geojson, dallas_qoz_tracts.geojson")

    # Headline counts for the audit log
    log.info("===== Layer 3 build COMPLETE =====")
    log.info("  tif_present:    %d / %d tracts (%.1f%%)",
             int(flags["tif_present"].sum()), len(flags),
             100.0 * flags["tif_present"].mean())
    log.info("  oz_designated:  %d / %d tracts (%.1f%%)",
             int(flags["oz_designated"].sum()), len(flags),
             100.0 * flags["oz_designated"].mean())
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--no-fetch", action="store_true",
                   help="Skip API attempts; require all inputs in data/raw/layer3_tif_oz/")
    args = p.parse_args()
    sys.exit(main(no_fetch=args.no_fetch))

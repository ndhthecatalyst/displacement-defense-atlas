"""
h4_sfr_institutional_flag.py
=============================
Displacement Defense Atlas — Layer 4 Institutional SFR Ownership Pipeline
Dallas County, TX | Thesis: "Below the Line" | Nicholas Donovan Hawkins, TSU

PURPOSE
-------
Build the Layer 4 institutional single-family-residential (SFR) ownership
signal for each census tract in Dallas County (FIPS 48113). This pipeline
downloads the Dallas Central Appraisal District (DCAD) bulk appraisal
export, filters to SFR parcels (SPTD codes A11/A12/A13), flags each parcel
as `institutional`, `small_investor`, or `individual` based on a
regex-driven entity classifier plus a portfolio-size threshold, and
aggregates counts to the 2020 TIGER census tract.

INPUTS (expected / auto-downloaded)
-----------------------------------
    DCAD 2025 Certified data files (ACCOUNT_INFO.CSV, ACCOUNT_APPRL_YEAR.CSV)
        https://www.dallascad.org/DataProducts.aspx
    DCAD 2026 Current Parcel polygons (PARCEL_GEOM.shp)
        https://www.dallascad.org/GISDataProducts.aspx
    2020 TIGER/Line tracts for Texas (tl_2020_48_tract.shp)
        https://www2.census.gov/geo/tiger/TIGER2020/TRACT/tl_2020_48_tract.zip
    data/h4_readiness/h4_tract_readiness_inputs.csv   (existing repo asset)

OUTPUTS
-------
    data/h4_readiness/h4_sfr_institutional_raw.csv
        One row per SFR parcel: geo_id, owner_name,
        owner_mailing_address, land_use_code, GEOID (tract),
        ownership_tier, owner_parcel_count
    data/h4_readiness/h4_tract_readiness_with_sfr.csv
        Tract-level merge of h4_tract_readiness_inputs.csv +
        institutional_parcel_count, small_investor_count,
        total_sfr_parcels, institutional_pct, top_owner_1/2/3

USAGE
-----
    python scripts/analysis/h4_sfr_institutional/h4_sfr_institutional_flag.py

Set DCAD_WORK_DIR env var to reuse an existing download cache (default
/tmp/dcad). Re-runs are idempotent — already-downloaded archives are not
re-fetched.
"""

from __future__ import annotations

import os
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd
import geopandas as gpd
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data" / "h4_readiness"
INPUTS_CSV = DATA_DIR / "h4_tract_readiness_inputs.csv"
OUT_RAW = DATA_DIR / "h4_sfr_institutional_raw.csv"
OUT_MERGED = DATA_DIR / "h4_tract_readiness_with_sfr.csv"

WORK_DIR = Path(os.environ.get("DCAD_WORK_DIR", "/tmp/dcad"))
WORK_DIR.mkdir(parents=True, exist_ok=True)

DCAD_APPRAISAL_ZIP = WORK_DIR / "dcad2025.zip"
DCAD_APPRAISAL_URL = (
    "https://www.dallascad.org/ViewPDFs.aspx?type=3&id="
    r"\\DCAD.ORG\WEB\WEBDATA\WEBFORMS\DATA%20PRODUCTS\DCAD2025_CURRENT.ZIP"
)
DCAD_PARCEL_ZIP = WORK_DIR / "parcel_geom.zip"
DCAD_PARCEL_URL = (
    "https://www.dallascad.org/ViewPDFs.aspx?type=3&id="
    r"\\DCAD.ORG\WEB\WEBDATA\WEBFORMS\GIS%20PRODUCTS\PARCEL_GEOM.zip"
)
TIGER_ZIP = WORK_DIR / "tl_2020_48_tract.zip"
TIGER_URL = (
    "https://www2.census.gov/geo/tiger/TIGER2020/TRACT/tl_2020_48_tract.zip"
)

# DCAD SPTD codes for single-family residential
# (per SPTD_CD_XREF.pdf shipped in DCAD appraisal archive)
#   A11 = Single Family Residences
#   A12 = SFR - Townhouses
#   A13 = SFR - Condominiums
SFR_CODES = {"A11", "A12", "A13"}

# ---------------------------------------------------------------------------
# Institutional-owner regex patterns (expanded from prompt baseline)
# ---------------------------------------------------------------------------

INSTITUTIONAL_PATTERNS = [
    r"\bINVITATION\s+HOMES?\b",
    r"\bPROGRESS\s+RESIDENTIAL\b",
    r"\bAMERICAN\s+RESIDENTIAL\s+PROP\b",
    r"\bVINEBROOK\b",
    r"\bFRONTYARD\b",
    r"\bARK[YI]\b",
    r"\bOPENDOOR\b",
    r"\bOFFERPAD\b",
    r"\bBLACKSTONE\b",
    r"\bTRICON\b",
    r"\bSILVERBAY\b",
    r"\bCERBERUS\b",
    r"\bCOLUMBIA\s+PROPERTY\b",
    r"\bNFR\b",
    r"\bSFR\s*(PROP|LLC|FUND|TRUST|CAPITAL)\b",
    r"\bHAVEN\s+REALTY\b",
    r"\bKATELLA\b",
    r"\bHOMEPARTNERS?\b",
    r"LLC$",
    r"LP$",
    r"TRUST$",
    r"FUND\b",
    r"REIT\b",
    r"\bACQUISITION(S)?\b",
    r"\bHOLDINGS?\b",
    r"\bPROPERTIES\b",
]
# Wrap each pattern in a non-capturing group so pandas str.contains does not
# emit the "has match groups" warning triggered by patterns like \bARK[YI]\b.
INST_REGEX = re.compile(
    "|".join(f"(?:{p})" for p in INSTITUTIONAL_PATTERNS),
    flags=re.IGNORECASE,
)

# Portfolio-size thresholds (parcels owned, dataset-wide)
INSTITUTIONAL_MIN_PARCELS = 10
SMALL_INVESTOR_MIN_PARCELS = 2


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def _download(url: str, dest: Path, label: str) -> None:
    if dest.exists() and dest.stat().st_size > 1024:
        print(f"[cache] {label} already present at {dest} "
              f"({dest.stat().st_size / 1e6:.1f} MB)")
        return
    print(f"[download] {label}: {url}")
    with requests.get(url, stream=True, timeout=600,
                      headers={"User-Agent": "Mozilla/5.0"}) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    print(f"[download] wrote {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def _extract(zip_path: Path, members: list[str], out_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        for m in members:
            if m in names and not (out_dir / m).exists():
                zf.extract(m, out_dir)


# ---------------------------------------------------------------------------
# Step A1 — load & filter DCAD appraisal rolls to SFR parcels
# ---------------------------------------------------------------------------

def load_sfr_parcels(work_dir: Path) -> pd.DataFrame:
    """Returns a DataFrame with:
       geo_id, owner_name, owner_mailing_address, land_use_code
    restricted to SFR parcels (SPTD in SFR_CODES)."""
    _download(DCAD_APPRAISAL_URL, DCAD_APPRAISAL_ZIP, "DCAD 2025 appraisal roll")

    members = ["ACCOUNT_INFO.CSV", "ACCOUNT_APPRL_YEAR.CSV"]
    _extract(DCAD_APPRAISAL_ZIP, members, work_dir)

    appy_path = work_dir / "ACCOUNT_APPRL_YEAR.CSV"
    info_path = work_dir / "ACCOUNT_INFO.CSV"

    print(f"[load] {appy_path.name} (SPTD codes)")
    appy = pd.read_csv(
        appy_path,
        usecols=["ACCOUNT_NUM", "SPTD_CODE", "DIVISION_CD", "GIS_PARCEL_ID"],
        dtype=str,
        low_memory=False,
    )
    sfr = appy[appy["SPTD_CODE"].isin(SFR_CODES)].copy()
    print(f"[filter] {len(sfr):,} SFR parcel rows "
          f"(codes {sorted(SFR_CODES)}) out of {len(appy):,} total accounts")

    print(f"[load] {info_path.name} (owner/address)")
    info = pd.read_csv(
        info_path,
        usecols=[
            "ACCOUNT_NUM", "OWNER_NAME1", "OWNER_NAME2",
            "OWNER_ADDRESS_LINE1", "OWNER_ADDRESS_LINE2",
            "OWNER_CITY", "OWNER_STATE", "OWNER_ZIPCODE",
        ],
        dtype=str,
        low_memory=False,
    )

    merged = sfr.merge(info, on="ACCOUNT_NUM", how="left")

    addr_cols = [
        "OWNER_ADDRESS_LINE1", "OWNER_ADDRESS_LINE2",
        "OWNER_CITY", "OWNER_STATE", "OWNER_ZIPCODE",
    ]
    for c in addr_cols:
        merged[c] = merged[c].fillna("").astype(str).str.strip()
    merged["owner_mailing_address"] = (
        merged[addr_cols]
        .apply(lambda r: ", ".join(v for v in r if v), axis=1)
    )

    owner1 = merged["OWNER_NAME1"].fillna("").astype(str).str.strip()
    owner2 = merged["OWNER_NAME2"].fillna("").astype(str).str.strip()
    merged["owner_name"] = (owner1 + " " + owner2).str.strip()
    # A few accounts have no OWNER_NAME1 but do have a business name — fall
    # through to empty string rather than NaN.
    merged["owner_name"] = merged["owner_name"].replace("", pd.NA)

    merged = merged.rename(
        columns={"SPTD_CODE": "land_use_code", "ACCOUNT_NUM": "geo_id"}
    )
    merged = merged[[
        "geo_id", "GIS_PARCEL_ID",
        "owner_name", "owner_mailing_address", "land_use_code",
    ]].copy()
    return merged


# ---------------------------------------------------------------------------
# Step A2 — classify ownership tier
# ---------------------------------------------------------------------------

def classify_ownership(parcels: pd.DataFrame) -> pd.DataFrame:
    """Adds columns: owner_parcel_count, regex_hit, ownership_tier."""
    names = parcels["owner_name"].fillna("").astype(str)
    parcels["regex_hit"] = names.str.contains(INST_REGEX, regex=True, na=False)

    counts = names.value_counts()
    parcels["owner_parcel_count"] = names.map(counts).fillna(0).astype(int)

    tier = pd.Series("individual", index=parcels.index, dtype=object)

    # Secondary filter — over-broad LLC/LP/TRUST/FUND hits only stick if the
    # entity owns 10+ parcels across Dallas County. Otherwise those names fall
    # back to small_investor (2–9) or individual (1) based on portfolio size.
    inst_mask = (
        parcels["regex_hit"]
        & (parcels["owner_parcel_count"] >= INSTITUTIONAL_MIN_PARCELS)
    )
    tier.loc[inst_mask] = "institutional"

    small_mask = (~inst_mask) & parcels["owner_parcel_count"].between(
        SMALL_INVESTOR_MIN_PARCELS, INSTITUTIONAL_MIN_PARCELS - 1
    )
    tier.loc[small_mask] = "small_investor"

    # Empty owner names default to individual (1-parcel equivalent).
    tier.loc[names == ""] = "individual"

    parcels["ownership_tier"] = tier
    return parcels


# ---------------------------------------------------------------------------
# Step A3 — spatial join to 2020 TIGER tracts
# ---------------------------------------------------------------------------

def load_tracts(work_dir: Path) -> gpd.GeoDataFrame:
    _download(TIGER_URL, TIGER_ZIP, "TIGER 2020 Texas tracts")
    out_dir = work_dir / "tiger_tx_tract"
    out_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(TIGER_ZIP) as zf:
        zf.extractall(out_dir)

    tracts = gpd.read_file(out_dir / "tl_2020_48_tract.shp")
    dallas = tracts[tracts["COUNTYFP"] == "113"].copy()
    # Reproject to EPSG:2276 (Texas North Central, ft) to match DCAD parcels.
    dallas = dallas.to_crs("EPSG:2276")
    return dallas[["GEOID", "geometry"]].reset_index(drop=True)


def load_parcel_polygons(work_dir: Path) -> gpd.GeoDataFrame:
    _download(DCAD_PARCEL_URL, DCAD_PARCEL_ZIP, "DCAD parcel geometry")
    out_dir = work_dir / "PARCEL_GEOM"
    if not (out_dir / "PARCEL_GEOM.shp").exists():
        with zipfile.ZipFile(DCAD_PARCEL_ZIP) as zf:
            zf.extractall(work_dir)
    parcels = gpd.read_file(out_dir / "PARCEL_GEOM.shp")
    parcels = parcels.rename(columns={"Acct": "geo_id"})
    parcels["geo_id"] = parcels["geo_id"].astype(str)
    # Use representative point for robust sjoin (handles slivers/overlaps).
    parcels["geometry"] = parcels.geometry.representative_point()
    return parcels[["geo_id", "geometry"]]


def spatial_join_to_tracts(
    parcels_df: pd.DataFrame,
    work_dir: Path,
) -> pd.DataFrame:
    tracts = load_tracts(work_dir)
    parcels_geom = load_parcel_polygons(work_dir)

    print(f"[sjoin] {len(parcels_geom):,} parcel points "
          f"× {len(tracts):,} Dallas County tracts")
    joined = gpd.sjoin(
        parcels_geom, tracts, how="left", predicate="within"
    )[["geo_id", "GEOID"]]
    # Deduplicate (very rare boundary double-hits).
    joined = joined.drop_duplicates(subset="geo_id", keep="first")

    out = parcels_df.merge(joined, on="geo_id", how="left")
    unmatched = out["GEOID"].isna().sum()
    print(f"[sjoin] matched {len(out) - unmatched:,} / {len(out):,} parcels "
          f"to a tract ({unmatched:,} unmatched)")
    return out


# ---------------------------------------------------------------------------
# Step A4 — aggregate to tract
# ---------------------------------------------------------------------------

def _top_owners(series: pd.Series, n: int = 3) -> list[str | None]:
    names = [s for s in series.dropna().astype(str) if s.strip()]
    if not names:
        return [None] * n
    top = [name for name, _ in Counter(names).most_common(n)]
    while len(top) < n:
        top.append(None)
    return top


def aggregate_to_tract(parcels: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for geoid, grp in parcels.dropna(subset=["GEOID"]).groupby("GEOID"):
        total = len(grp)
        inst = int((grp["ownership_tier"] == "institutional").sum())
        small = int((grp["ownership_tier"] == "small_investor").sum())
        inst_owners = grp.loc[
            grp["ownership_tier"] == "institutional", "owner_name"
        ]
        top1, top2, top3 = _top_owners(inst_owners, 3)
        rows.append({
            "GEOID": geoid,
            "institutional_parcel_count": inst,
            "small_investor_count": small,
            "total_sfr_parcels": total,
            "institutional_pct": round(inst / total * 100, 3)
                if total else 0.0,
            "top_owner_1": top1,
            "top_owner_2": top2,
            "top_owner_3": top3,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"[config] REPO_ROOT      = {REPO_ROOT}")
    print(f"[config] WORK_DIR       = {WORK_DIR}")
    print(f"[config] OUT_RAW        = {OUT_RAW}")
    print(f"[config] OUT_MERGED     = {OUT_MERGED}")

    # A1
    parcels = load_sfr_parcels(WORK_DIR)

    # A2
    parcels = classify_ownership(parcels)

    tier_counts = parcels["ownership_tier"].value_counts().to_dict()
    print(f"[classify] tier counts: {tier_counts}")

    # A3
    parcels = spatial_join_to_tracts(parcels, WORK_DIR)

    # Raw output — normalize column order
    raw = parcels[[
        "geo_id", "owner_name", "owner_mailing_address",
        "land_use_code", "GEOID", "ownership_tier", "owner_parcel_count",
    ]].copy()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw.to_csv(OUT_RAW, index=False)
    print(f"[write] {OUT_RAW}  ({len(raw):,} rows)")

    # A4
    tract_agg = aggregate_to_tract(parcels)
    print(f"[aggregate] {len(tract_agg):,} tracts with SFR parcels")

    base = pd.read_csv(INPUTS_CSV, dtype={"GEOID": str})
    tract_agg["GEOID"] = tract_agg["GEOID"].astype(str)
    merged = base.merge(tract_agg, on="GEOID", how="left")

    for col in ["institutional_parcel_count", "small_investor_count",
                "total_sfr_parcels"]:
        merged[col] = merged[col].fillna(0).astype(int)
    merged["institutional_pct"] = merged["institutional_pct"].fillna(0.0)

    merged.to_csv(OUT_MERGED, index=False)
    print(f"[write] {OUT_MERGED}  ({len(merged):,} tracts)")

    # Console summary
    top_inst = merged.nlargest(5, "institutional_pct")[
        ["GEOID", "NAMELSAD", "institutional_parcel_count",
         "total_sfr_parcels", "institutional_pct", "top_owner_1"]
    ]
    print("\n[summary] top 5 tracts by institutional SFR penetration:")
    print(top_inst.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

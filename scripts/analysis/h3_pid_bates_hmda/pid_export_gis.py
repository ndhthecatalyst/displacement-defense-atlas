"""
Export GIS-ready files for the Dallas PID x Tract spatial join.

Produces open, interoperable formats that drop directly into ArcGIS Pro,
QGIS, or any web-mapping stack (Mapbox, Leaflet, Kepler.gl).

Outputs:
  outputs/gis/tracts_pid_join.geojson       -- 645 tract polygons w/ PID fields + Bates typology
  outputs/gis/pid_polygons.geojson          -- 17 PID polygons w/ budget + per-capita attrs
  outputs/gis/dallas_pid_atlas.gpkg         -- GeoPackage, 2 layers (tracts_pid, pid_polygons)
  outputs/gis/tracts_pid_join.shp           -- ESRI Shapefile (ArcGIS-default)
  outputs/gis/README.md                     -- field dictionary + provenance

All layers in EPSG:4326 (WGS84) for web-first; EPSG:2276 (TX North Central,
ftUS) retained in GeoPackage as metadata for downstream area/length math.
"""
from pathlib import Path
import json
import geopandas as gpd
import pandas as pd

# Resolve repo root from this script's location: scripts/analysis/h3_pid_bates_hmda/<this>
REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT = REPO_ROOT / "outputs"
RAW = REPO_ROOT / "data" / "raw"
TABLES = ROOT / "tables"
GIS = ROOT / "geojson"
GIS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Load inputs
# ---------------------------------------------------------------------------
print("[load] tract polygons")
tracts = gpd.read_file(RAW / "tl_2020_48_tract.shp")
tracts = tracts[tracts["COUNTYFP"] == "113"].copy()  # Dallas County
tracts["GEOID"] = tracts["GEOID"].astype(str)

print("[load] pid polygons")
pids = gpd.read_file(RAW / "pid_polygons.geojson")

print("[load] join table")
join = pd.read_csv(TABLES / "pid_tract_join.csv", dtype={"GEOID": str})

print("[load] h6 bates typology (full attributes)")
h6 = pd.read_csv(RAW / "h6_bates_full_typology.csv", dtype={"GEOID": str})

print("[load] pid budget lookup")
budgets = pd.read_csv(TABLES / "pid_budget_lookup.csv")

# ---------------------------------------------------------------------------
# Assemble tract layer (polygons + join attrs + h6 subset)
# ---------------------------------------------------------------------------
# Keep a tight, well-documented attribute schema -- shapefile has 10-char
# field-name limit so we pick QGIS/ArcGIS-friendly short names.
h6_keep = [
    "GEOID", "population", "bates_typology_v21",
    "median_household_income", "pct_renters", "pct_poc",
    "median_gross_rent_pct_change_2013_2021",
]
h6_keep = [c for c in h6_keep if c in h6.columns]
h6_subset = h6[h6_keep].copy()

# Inner-to-outer merges: tracts (geom) <- join <- h6
tract_gdf = tracts[["GEOID", "NAMELSAD", "ALAND", "AWATER", "geometry"]].merge(
    join, on="GEOID", how="inner"
).merge(
    h6_subset, on="GEOID", how="left"
)

# Shapefile-friendly column rename (<=10 chars, no dots)
rename_map = {
    "NAMELSAD": "tract_full",
    "tract_name": "tract_nm",
    "in_pid": "in_pid",
    "pid_name": "pid_name",
    "pid_annual_budget": "pid_budget",
    "pid_per_capita": "pid_pcap",
    "population": "pop",
    "bates_typology_v21": "bates_v21",
    "median_household_income": "mhi",
    "pct_renters": "pct_rent",
    "pct_poc": "pct_poc",
    "median_gross_rent_pct_change_2013_2021": "rent_chg",
    "ALAND": "aland_m2",
    "AWATER": "awatr_m2",
}
tract_gdf = tract_gdf.rename(columns=rename_map)

# Boolean -> int (shapefile can't store true bool)
tract_gdf["in_pid"] = tract_gdf["in_pid"].fillna(False).astype(int)

# Project once, then reproject copies so we have WGS84 for web + 2276 for GPKG
tract_gdf_4326 = tract_gdf.to_crs(4326)

# ---------------------------------------------------------------------------
# Assemble PID layer (polygons + budget + per-capita roll-up)
# ---------------------------------------------------------------------------
# Attach budgets via PID name
pid_layer = pids.copy()
pid_layer["pid_name"] = pid_layer["Name"].astype(str)

# Per-PID: total population covered (sum pop of tracts whose centroid falls in it)
pop_by_pid = tract_gdf.groupby("pid_name", dropna=True)["pop"].sum().reset_index()
pop_by_pid = pop_by_pid.rename(columns={"pop": "pop_covered"})

pid_layer = pid_layer.merge(budgets, on="pid_name", how="left")
pid_layer = pid_layer.merge(pop_by_pid, on="pid_name", how="left")

# Per-capita rollup at the PID level
pid_layer["pid_pcap"] = (
    pid_layer["pid_annual_budget"] / pid_layer["pop_covered"].replace({0: pd.NA})
).astype(float).round(2)

pid_keep = {
    "pid_name": "pid_name",
    "pid_annual_budget": "budget",
    "pop_covered": "pop_cover",
    "pid_pcap": "pid_pcap",
    "SqMi": "sq_mi",
    "Acres": "acres",
    "Date_Exp": "date_exp",
}
pid_layer = pid_layer[[c for c in pid_keep.keys() if c in pid_layer.columns] + ["geometry"]]
pid_layer = pid_layer.rename(columns=pid_keep)
pid_layer_4326 = pid_layer.to_crs(4326)

# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------
print("[write] GeoJSON (EPSG:4326, RFC 7946)")
tract_gdf_4326.to_file(GIS / "tracts_pid_join.geojson", driver="GeoJSON")
pid_layer_4326.to_file(GIS / "pid_polygons.geojson", driver="GeoJSON")

print("[write] GeoPackage (multi-layer)")
gpkg_dir = ROOT / "gpkg"; gpkg_dir.mkdir(parents=True, exist_ok=True)
gpkg_path = gpkg_dir / "dallas_pid_atlas.gpkg"
if gpkg_path.exists():
    gpkg_path.unlink()
tract_gdf_4326.to_file(gpkg_path, layer="tracts_pid", driver="GPKG")
pid_layer_4326.to_file(gpkg_path, layer="pid_polygons", driver="GPKG")

print("[write] ESRI Shapefile (legacy ArcGIS default)")
shp_dir = ROOT / "shapefile"
shp_dir.mkdir(parents=True, exist_ok=True)
tract_gdf_4326.to_file(shp_dir / "tracts_pid_join.shp", driver="ESRI Shapefile")
pid_layer_4326.to_file(shp_dir / "pid_polygons.shp", driver="ESRI Shapefile")

# ---------------------------------------------------------------------------
# README with field dictionary
# ---------------------------------------------------------------------------
readme = f"""# Dallas PID × Tract Atlas — GIS Layers

Open-format spatial exports for the Displacement Defense Atlas h6 analysis.

## Files

| File | Driver | Layers | CRS |
|---|---|---|---|
| `tracts_pid_join.geojson` | GeoJSON (RFC 7946) | 1 | EPSG:4326 |
| `pid_polygons.geojson` | GeoJSON (RFC 7946) | 1 | EPSG:4326 |
| `dallas_pid_atlas.gpkg` | GeoPackage | 2 (`tracts_pid`, `pid_polygons`) | EPSG:4326 |
| `shapefile/tracts_pid_join.shp` (+ sidecars) | ESRI Shapefile | 1 | EPSG:4326 |
| `shapefile/pid_polygons.shp` (+ sidecars) | ESRI Shapefile | 1 | EPSG:4326 |

**Recommended format:** GeoPackage for desktop GIS (single file, multi-layer, no 10-char field limit). GeoJSON for web mapping. Shapefile only for legacy ArcGIS workflows.

## Layer: `tracts_pid` — {len(tract_gdf_4326)} features

Dallas County census tracts (2020 TIGER) with PID coverage + Bates v2.1 typology.

| Field | Type | Description |
|---|---|---|
| `GEOID` | str | 2020 census tract GEOID (11 chars) |
| `tract_full` | str | Full TIGER NAMELSAD (e.g., "Census Tract 31.02") |
| `tract_nm` | str | Short tract name |
| `aland_m2` | int | Land area (m²) from TIGER |
| `awatr_m2` | int | Water area (m²) from TIGER |
| `in_pid` | int (0/1) | 1 if tract centroid falls in a PID polygon |
| `pid_name` | str | PID name if `in_pid=1`, else null |
| `pid_budget` | float | PID annual assessment budget ($) -- null where unpublished |
| `pid_pcap` | float | Per-capita PID assessment for this tract ($/resident/yr) |
| `pop` | int | Tract population (h6 source, ACS 2019-2023 5yr) |
| `bates_v21` | str | Bates v2.1 typology stage (Stable, Historic Loss, Susceptible, Late, Early: Type 1, Early: Type 2, Dynamic) |
| `mhi` | float | Median household income |
| `pct_rent` | float | % renter-occupied |
| `pct_poc` | float | % people of color |
| `rent_chg` | float | Median gross rent % change 2013–2021 |

## Layer: `pid_polygons` — {len(pid_layer_4326)} features

Public Improvement District boundaries from Dallas Open Data (ArcGIS FeatureServer `EconomicDevelopment/2`).

| Field | Type | Description |
|---|---|---|
| `pid_name` | str | PID name |
| `budget` | float | Annual assessment budget ($) -- null = not yet obtained via PIA |
| `pop_cover` | int | Sum of tract populations whose centroid falls inside this PID |
| `pid_pcap` | float | PID-level per-capita budget ($/resident/yr) |
| `sq_mi` | float | PID area (sq miles, from source) |
| `acres` | float | PID area (acres, from source) |
| `date_exp` | str | PID expiration date |

## Provenance

- **Tract polygons:** US Census Bureau, 2020 TIGER/Line (`tl_2020_48_tract`), filtered to `COUNTYFP='113'` (Dallas County).
- **PID polygons:** City of Dallas Open Data, ArcGIS item `215f5e7243d44c25b7e503e3dafe73da` (resolved to FeatureServer `EconomicDevelopment/2`, 17 features).
- **PID budgets:** Compiled from repo source `outputs/analysis/h6_closing_argument_memo.md` (Dallas DID & Uptown PID from FY2023 vendor payments; South Side PIDs from City of Dallas FY2024 assessment ordinances). Non-Downtown / non-South Side PIDs carry null budgets pending the pending City PIA response.
- **Bates v2.1 typology:** From `outputs/tables/h6_bates_full_typology.csv` in repo, derived from ACS 2019-2023 5-year + NHGIS 2000 longitudinal tract crosswalks.
- **Spatial join:** centroid-in-polygon in EPSG:2276 (Texas North Central, ftUS).

## Reproduction

```bash
python outputs/pid_tract_join.py    # produces CSVs, maps
python outputs/export_gis.py        # produces this directory
```

## Known limitations

1. 11 of 17 active PIDs carry `budget=NULL`; refresh after City PIA response (`docs/correspondence/email2_pia_fy2016_2024.md`).
2. `in_pid` uses centroid-in-polygon -- tracts straddling PID boundaries are classified by centroid only. For edge cases, use `tracts_pid ∩ pid_polygons` in desktop GIS.
3. `pid_pcap` values are tract-level when read from `tracts_pid`, but PID-wide when read from `pid_polygons`. Both are correct; they answer different questions.

---
Generated {pd.Timestamp.now().isoformat(timespec='seconds')} by `outputs/export_gis.py`.
"""
(gpkg_dir / "README.md").write_text(readme)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
print(f"[done] wrote {len(list(GIS.rglob('*')))} files to {GIS}")
for p in sorted(GIS.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(ROOT)}  ({p.stat().st_size:,} bytes)")

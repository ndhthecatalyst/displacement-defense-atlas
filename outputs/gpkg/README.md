# Dallas PID × Tract Atlas — GIS Layers

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

## Layer: `tracts_pid` — 645 features

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

## Layer: `pid_polygons` — 17 features

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
Generated 2026-04-22T04:28:40 by `outputs/export_gis.py`.

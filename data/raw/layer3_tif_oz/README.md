# Layer 3 — TIF / Opportunity Zones (Raw Inputs)

This directory holds the authoritative inputs for the Layer 3 pipeline
(`scripts/pipeline/build_layer3_tif_oz.py`). All files in this directory
must be either (a) auto-fetched from a public endpoint by the pipeline,
or (b) manually deposited and documented in the schema table below.

The pipeline **must not silently fall back to hardcoded geometries or
GEOID lists.** If a required input is missing it must hard-fail with a
message naming the file and the canonical source URL.

---

## Why this directory exists

The previous Layer 3 implementation (`scripts/pipeline/atlas_v0_build.py`,
PHASE 2.5–2.6) used 18 hand-typed bounding-box polygons for TIF districts
and a 30-GEOID hardcoded list for Opportunity Zones. That approach was
silently producing a 90% join collapse on the OZ side (30 hardcoded → 3
matched in the 645-tract panel) and a generous over-inclusion on the TIF
side (~1.5 km² boxes covering far more area than the real subdistricts).

The 2026-04-26 audit (`docs/audit/2026-04-26_layer3_audit.md`) flagged
the "0 TIF / 0 OZ in 54 Susceptible South tracts" claim as technically
true on paper but resting on inputs that cannot survive review. This
directory and the new pipeline are the corrective.

---

## Required input files

| # | File | Source | Vintage | Schema (required cols) |
|---|------|--------|---------|------------------------|
| 1 | `dallas_tif_subdistricts.geojson` | City of Dallas GIS Hub item `867cb869d7764aeda0832f8af3512b02` (Tax Increment Finance Subdistricts) | Current | `subdistrict_name`, `district_name`, `year_created`, `geometry` (polygon, EPSG:4326) |
| 2 | `dallas_tif_districts.geojson` | Same hub or `egis.dallascityhall.com/resources/shapefileDownload.aspx` (TIF Districts master) | Current | `district_name`, `district_id`, `year_created`, `expiration_year`, `geometry` |
| 3 | `dallas_tif_increment_2025.csv` | Hand-extracted from `annual_reports/2025-TIF-Annual-Report.pdf` via `scripts/pipeline/parse_tif_annual_report.py` | FY2025 | `district_name`, `fy`, `base_value`, `current_value`, `increment_captured`, `lifetime_increment`, `source_page` |
| 4 | `annual_reports/*.pdf` | Dallas OED `dallasecodev.org/715/Recent-Annual-Reports` (per-district FY annual reports) | FY22-23, FY23-24 | One PDF per district per FY. Filename pattern: `{district_slug}_FY{yy}-{yy}.pdf` |
| 5 | `qoz_tracts_us.geojson` | HUD Open Data `hudgis-hud.opendata.arcgis.com/datasets/ef143299845841f8abb95969c01f88b5_13` (Opportunity Zones national layer) | 2018 designation, 2010 tract vintage | `GEOID10` (11-char string), `STATE`, `COUNTY`, `TRACT`, `geometry` |
| 6 | `irs_notice_2018_48_qoz.csv` | Treasury / IRS Notice 2018-48 official designation list, filtered to Dallas County (`STATEFP=48 AND COUNTYFP=113`) | 2018 designation | `GEOID10` (11-char string with leading zeros), `state`, `county`, `tract` |
| 7 | `oz_investments_ground_truth.csv` | Manual curation. See "Ground-truth ledger" section below. | Rolling | `project_name`, `address`, `lat`, `lon`, `claimed_oz_geoid`, `qof_name`, `qof_hq_state`, `year_announced`, `dollars_invested`, `asset_type`, `source_url` |

TIGER 2020 Dallas County tracts (the join target) live in the existing
`data/raw/layer0_boundaries/` directory; Layer 3 reuses them rather than
duplicating.

---

## Ground-truth ledger (file #7)

`oz_investments_ground_truth.csv` is the falsification dataset. Its
purpose is to detect a broken QOZ polygon layer or a wrong-vintage
GEOID join: every documented OZ-eligible investment in Dallas County
should geocode to a tract whose GEOID is in our QOZ layer. If more than
5% of ground-truth investments fall outside our QOZ polygons, the
pipeline hard-fails.

Sources for ground-truth project entries (in order of trust):

1. **Dallas Office of Economic Development OZ project announcements**
   `dallasecodev.org/546/Opportunity-Zones` and the OZ 2.0 RFI page.
2. **Dallas Fed *Opportunity Zones in Texas: Promise and Peril* (2020)**
   `dallasfed.org/cd/pubs/opportunity/opportunity2` — case studies + the
   Texas OZ Investment Tracker dataset.
3. **Novogradac Opportunity Zones Investment Tracker** (paywalled;
   hand-extract Dallas-county rows where licensed).
4. **SEC EDGAR Form 8996 filings** — only useful for the ~8 publicly-
   traded QOFs; provides QOF identity and aggregate asset size, not
   project-level location.
5. **Dallas Observer / D Magazine / Dallas Morning News coverage** —
   case-by-case, useful for high-profile mixed-use and hotel projects.

The ledger is **necessarily incomplete**; its label in any downstream
map should read *"documented OZ investments"* rather than *"all OZ
investments"* (per the v0.2 cartography spec).

---

## Pipeline contract

When `scripts/pipeline/build_layer3_tif_oz.py` runs:

1. It first attempts API fetch for files #1, #2, #5.
2. If a file already exists in this directory, it uses the local copy
   (manual upload wins over API to support offline / blocked-egress
   environments).
3. Files #3, #4, #6, #7 must be supplied manually — they originate in
   PDFs or curated CSVs, not in any single API.
4. Outputs land in `data/processed/layer3_tif_oz_tract_flags.csv` and
   `outputs/geojson/dallas_tif_districts.geojson` /
   `outputs/geojson/dallas_qoz_tracts.geojson`.
5. Diagnostics (every dropped or mismatched join row) land in
   `outputs/tables/layer3_join_diagnostics.csv`.

---

## Vintages — important

- **Opportunity Zone designations are anchored to 2010 census tracts**
  (IRS Notice 2018-48 used the 2011-2015 ACS, which used 2010 tracts).
  HUD's QOZ layer carries `GEOID10` for this reason. Joining to a 2020
  TIGER tract panel requires a 2010↔2020 crosswalk — handled inside the
  pipeline via the LTDB crosswalk that H6 already uses.
- **TIF districts use current-year boundaries.** Subdistricts may have
  been added or amended; the GIS Hub layer is the authority.
- **Always join in EPSG:2276** (Texas State Plane North Central, US
  feet) before any area math. Reprojecting back to EPSG:4326 is fine
  for storage and web display.

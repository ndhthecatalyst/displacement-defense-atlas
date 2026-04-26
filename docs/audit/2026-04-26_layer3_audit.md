# Layer 3 (TIF / Opportunity Zones) Provenance Audit

**Date:** 2026-04-26
**Auditor:** Internal pre-fellowship-submission review
**Scope:** All TIF and Opportunity Zone claims in the Displacement Defense Atlas, with emphasis on the load-bearing claim *"54 Susceptible South tracts, 0 with TIF or OZ"* (FACTS.md key `H4_WITH_TIF_OZ`).
**Outcome:** Mixed. Downstream metrics are computed correctly from the inputs they receive. The inputs themselves were hardcoded and one of them (OZ) was silently producing a 90% join collapse.

---

## Executive summary

| Claim | Status | Evidence |
|-------|--------|----------|
| 54 Susceptible South tracts, 0 with TIF or OZ | **Technically true on paper, but the underlying TIF/OZ flags are derived from hardcoded inputs that cannot survive review** | `scripts/pipeline/atlas_v0_build.py:262–325` |
| Downtown TIF $8.83B vs Grand Park South $333M (26:1) | **No traceable lineage in the repo** — only appears in FACTS.md and a map annotation string | `docs/FACTS.md:33–35`, `scripts/analysis/h3_pid_bates_hmda/atlas_v0_map_c.py:325` |
| 44 HIGH_PRESSURE_LOW_READINESS tracts | **Correctly computed** | `scripts/h4_readiness_index.py:82` |
| 14 immediate-priority tracts (readiness ≤ 0.028) | **Correctly computed** | `outputs/tables/h4_priority_54.csv` |

---

## Findings — TIF

### Finding T-1: TIF district geometries are 18 hand-typed bounding boxes, not the official subdistrict polygons

**File:** `scripts/pipeline/atlas_v0_build.py:282–309`

After a Socrata API call (`https://www.dallasopendata.com/resource/vvbn-m6yb.json`) failed or returned empty, the pipeline silently fell through to a hardcoded list of 18 `Polygon([(lon,lat),(lon,lat),(lon,lat),(lon,lat)])` rectangles approximately 1.5 km on a side. These were the geometries used to compute `tif_present` for every tract in the panel.

**Implication:** the "70 TIF-present tracts" reported in `docs/h4_methodology.md:96` is over-inclusive (rectangles cover area outside actual subdistricts) and the "0 in 54 Susceptible South" is correspondingly under-inclusive.

**Resolution:** `scripts/pipeline/build_layer3_tif_oz.py` replaces this with an authoritative spatial join against the City of Dallas GIS Hub TIF Subdistricts FeatureServer. Any tract whose intersected area exceeds the 1% threshold (consistent with the existing NEZ threshold at `h4_spatial_join.py:147`) is flagged.

### Finding T-2: `data/h4_readiness/tif/tif_parcels.geojson` is mislabeled

**File:** `data/h4_readiness/tif/tif_parcels.geojson` (73 features)

This file does not contain TIF district polygons. It contains 73 property-tax parcel records where the string "TIF" happens to appear in the `LEGAL_2` text field (e.g., `"VICKERY MEADOWS #9 TIF"`). There is no district ID column. It cannot support a clean spatial join and was not actually consumed by the H4 pipeline.

**Resolution:** the file is retained for diagnostic use (parcel-count-by-district sanity check) but is no longer load-bearing. The new pipeline uses the official subdistrict polygons.

### Finding T-3: $8.83B / $333M / 26:1 figures lack data lineage

**Files:** `docs/FACTS.md:33–35`, `scripts/analysis/h3_pid_bates_hmda/atlas_v0_map_c.py:18,325`

These dollar figures appear in FACTS.md and in a single map annotation string. **No CSV, JSON, or computed cell** in the repo holds the per-district lifetime-increment values from which they would be derived. They are typed-in.

The Dallas County 2025 TIF Annual Report shows individual districts at $1.1B–$1.9B in lifetime increment captured. There is no single "Downtown Connection TIF" in Dallas's actual 18-district roster — the figure is most likely a sum of 6–8 downtown-area TIFs. Presented as a single district name, the claim is misleading; presented as a cluster sum it is potentially defensible but needs sourcing.

**Resolution:** `scripts/pipeline/parse_tif_annual_report.py` extracts per-district figures from the source PDF and writes them to `data/raw/layer3_tif_oz/dallas_tif_increment_2025.csv`. FACTS.md will be updated in PR-2 once the PDF is uploaded and parsed.

---

## Findings — Opportunity Zones

### Finding O-1: OZ designations are a 30-GEOID hardcoded list with no authoritative source file

**File:** `scripts/pipeline/atlas_v0_build.py:315–325`

The list is annotated as deriving from "irs.gov Notice 2018-48" but no copy of that source list (PDF or CSV) is present in the repo. The 30 GEOIDs cannot be verified against the upstream document without external lookup.

### Finding O-2: 90% join collapse — 30 hardcoded GEOIDs, only 3 matched

**Files:** `scripts/pipeline/atlas_v0_build.py:323` (input), `docs/h4_methodology.md:98` (output)

H4 methodology table reports `OZ designated | 3` tracts in the 645-tract panel. With 30 GEOIDs in the source list, this is a 90% loss in the join. Likely causes: leading-zero loss when the GEOIDs were stored as integers, 2010↔2020 tract vintage mismatch, or string-vs-numeric type coercion during the merge.

This is a silent data bug, not a finding. It directly compromises the "0 OZ in 54 South Susceptible" claim — that claim may be technically true even after fixing the join, but until the join is fixed it cannot be defended.

**Resolution:** `scripts/pipeline/build_layer3_tif_oz.py` joins against the HUD Open Data Opportunity Zones national layer (`hudgis-hud.opendata.arcgis.com/datasets/ef143299845841f8abb95969c01f88b5_13`) on `GEOID10` as a zero-padded 11-character string, with explicit cross-check against the IRS Notice 2018-48 list. Diagnostics for any unmatched GEOIDs are written to `outputs/tables/layer3_oz_join_diagnostics.csv`.

### Finding O-3: City of Dallas alone has 15 OZs; 3 in our panel is not credible

Public city documentation (`dallasecodev.org/546/Opportunity-Zones`) reports 15 OZ tracts within the City of Dallas. Dallas County has more. A 3-tract result is implausible by an order of magnitude and is the strongest single signal that the join is broken.

---

## Findings — Repo hygiene

### Finding H-1: Directory naming drift

`README.md:59` documents `data/raw/layer3_tif_oz/` — the actual directory was `data/raw/layer3_early_warning/` and contained ACS / HMDA / HOLC files. The TIF/OZ inputs lived at `data/h4_readiness/tif/` (the mislabeled parcels file).

**Resolution:** `data/raw/layer3_tif_oz/` is created in this PR. The `layer3_early_warning/` dir is left in place pending a follow-up rename in PR-2 to avoid breaking active scripts during this audit cycle.

### Finding H-2: H4 spatial-join script does not actually compute TIF/OZ flags

**File:** `scripts/h4_spatial_join.py`

The script joins LIHTC, HUD Picture, HCAs, community orgs, and NEZ — and stops. There is no second-pass spatial validation against TIF or OZ inputs. H4 silently inherits whatever H6 (which calls `atlas_v0_build.py`) wrote earlier.

**Resolution:** the new `build_layer3_tif_oz.py` produces `data/processed/layer3_tif_oz_tract_flags.csv`. PR-2 will modify `h4_readiness_index.py` to consume this file directly rather than inheriting from H6.

### Finding H-3: Council-district phrasing in h4_methodology.md is confusing

**File:** `docs/h4_methodology.md:88`

The text reads `"Bazaldua (District 7 overlaps), Atkins (8), Gracey (3), Schultz (4), Resendez (5)"` — the parenthetical "(District 7 overlaps)" reads as a sentence fragment in the methodology memo. Bazaldua represents District 7. Phrasing fix in PR-1.

### Finding H-4: Maps a, b are still synthetic-data-only

**Files:** `scripts/analysis/h1_investment_bias/atlas_v0_map_a.py:436–439`, `scripts/analysis/h2_vendor_residue/atlas_v0_map_b.py`

Both scripts call `make_synthetic_gdf_dallas()` at their entry point and have never been wired to real ACS / HMDA / Bates inputs. No `atlas_v0_map_a_vulnerability.png` or `atlas_v0_map_b_tool_intensity.png` exists in `outputs/figures/`.

**Resolution:** wiring is scheduled for PR-2 once the corrected Layer 3 inputs are merged.

### Finding H-5: Cartography spec only documents three maps (a, b, c)

**File:** `docs/methods/atlas_v0_map_specifications.md`

The atlas has expanded to seven panels (A composite, B CIP vendor gap, C need-vs-investment, D Layer 4 SFR, E PID×SFR overlap, F Bates longitudinal staging, G political recirculation Sankey). Specs for D, E, F, G are added in this PR.

---

## What survives

- **44 HIGH_PRESSURE_LOW_READINESS** count, **14 immediate-priority tract list**, and the priority ordering all reproduce from the readiness-index logic in `scripts/h4_readiness_index.py`. The H4 methodology in sections 1–3 is sound.
- **HMDA disparity (1.19× South/North)**, **vendor residue 12.6× gap**, **PID 33× gap**, **HOLC-D β = +247.6** all have full data lineage and are not implicated by this audit.

---

## Tracking

This audit is the basis for `outputs/tables/layer3_provenance_audit.csv`, generated by `scripts/audit/audit_layer3_provenance.py`. Re-run that script after `build_layer3_tif_oz.py` to see the row-by-row diff between the old hardcoded inputs and the new authoritative ones.

PR sequence:

- **PR-1 (this PR):** scaffold the new pipeline, document the audit, restructure data dirs, append D/E/F/G map specs. No headline numbers move.
- **PR-2:** run pipeline against authoritative inputs (after Notion files are uploaded). Update FACTS.md, README, h4_methodology with re-derived values. Wire maps A, B, F to real data.
- **PR-3:** re-render maps C, D against corrected L3 inputs. Build Figure G.
- **PR-4 (deferred):** Map E if SFR data is sufficient.

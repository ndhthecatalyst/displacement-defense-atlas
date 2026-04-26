# H4: Readiness Layer — Methodology Memo

**Thesis:** "Below the Line" · Nicholas D. Hawkins · TSU Freeman Honors College
**Hypothesis H4:** *Where the most vulnerable Dallas tracts also have the thinnest affordable-housing stock and organized community-defense infrastructure — the risk × readiness "crisis quadrant" — is where displacement is most likely to convert from pressure into loss.*

---

## 1. Scope and Inputs

H4 adds a **readiness dimension** on top of H6's Bates v2.1 typology (645 Dallas County tracts) to complete the risk × readiness grid. The 54 South-of-I-30 Susceptible tracts form the intervention priority list.

| Dataset | Source | Vintage | Rows ingested |
|---|---|---|---|
| HUD LIHTC property database (TX slice) | [HUD User](https://www.huduser.gov/portal/datasets/lihtc/property.html) | 1987–2023 placed in service | 187 Dallas County projects · 25,576 LI units |
| HUD Picture of Subsidized Households (tract-level) | [HUD User](https://www.huduser.gov/portal/datasets/assthsg.html) | 2023 | 646 Dallas tract rows × 7 programs · 31,216 units total |
| HUD Active Housing Counseling Agencies | [HUD ArcGIS](https://services.arcgis.com/VTyQ9soqVukalItT/ArcGIS/rest/services/Active_HCAs/FeatureServer) | Current | 7 Dallas County agencies |
| Curated DFW community orgs (CLT/CDC/tenant/legal-aid) | Manual curation | 2025–2026 | 18 orgs (17 Dallas County) |
| City of Dallas NEZ (Residential) | [Dallas GIS Hub](https://services2.arcgis.com/rwnOSbfKSwyTBcwN/arcgis/rest/services/Residential_NEZ/FeatureServer) | 2020 designation | 7 polygons · 42 tracts with >1% overlap |
| Dallas City Council District Boundaries (2023 redistricting) | [Dallas GIS Hub](https://services2.arcgis.com/rwnOSbfKSwyTBcwN/arcgis/rest/services/CouncilBoundaries/FeatureServer) | Effective May 2023 | 14 districts |
| Census TIGER/Line 2020 tracts | Census TIGER 2020 | 2020 | 645 Dallas County |
| H6 Bates v2.1 typology | `outputs/tables/h6_bates_full_typology.csv` | HEAD commit 0fa0dea | 645 tracts × 64 cols |
| **TIF subdistrict polygons** | [Dallas GIS Hub item `867cb869d7764aeda0832f8af3512b02`](https://gisservices-dallasgis.opendata.arcgis.com/maps/867cb869d7764aeda0832f8af3512b02) — *added in v0.2 to replace the hardcoded bounding boxes flagged by the 2026-04-26 Layer 3 audit* | Current | TBD post-pipeline-run |
| **Opportunity Zone tracts** | [HUD Open Data layer `ef143299845841f8abb95969c01f88b5_13`](https://hudgis-hud.opendata.arcgis.com/datasets/ef143299845841f8abb95969c01f88b5_13) — *added in v0.2 to replace the 30-GEOID hardcoded list flagged by the 2026-04-26 Layer 3 audit* | 2018 designation, 2010 tract vintage | TBD post-pipeline-run |

**NHPD deliberately omitted** — behind a free login wall; the two datasets NHPD de-duplicates (HUD LIHTC + Picture of Subsidized Households) are ingested directly, so NHPD would be marginal enrichment. Flagged for next-session backfill.

**TIF/OZ inputs note (added 2026-04-26):** Earlier H4 runs inherited TIF and OZ flags from `scripts/pipeline/atlas_v0_build.py`, which used 18 hand-typed bounding-box polygons for TIF districts and a 30-GEOID hardcoded list for OZ designations. The OZ join silently collapsed 30 hardcoded GEOIDs to 3 matched tracts (see Section 4 row 3 below) — a 90% loss now traced to a vintage/string-padding mismatch. The new pipeline (`scripts/pipeline/build_layer3_tif_oz.py`) joins against the authoritative City of Dallas GIS Hub and HUD Open Data layers cited above. PR-2 will re-run H4 against the corrected inputs and update the counts in Section 4.

---

## 2. Readiness Index Construction

### 2.1 Components and normalization

Each tract gets a readiness score on [0, 1] computed from three normalized signals:

| Component | Weight | Input | Normalization |
|---|---|---|---|
| **Affordable units** | **50%** | `max(LIHTC low-income units, HUD all-programs subsidized units)` | per-1,000-residents rate → winsorized at 95th percentile → divided by max |
| **Organized community defense** | **30%** | `HCA count + 0.7 × curated-org count` (HUD-certified counseling agencies weighted full; CDC/CLT/tenant/legal-aid orgs weighted 0.7 to reflect ZIP-centroid geocoding imprecision) | divided by max |
| **NEZ overlay** | **20%** | Fraction of tract area overlapping a Neighborhood Empowerment Zone | already [0, 1] |

```
readiness_score = 0.50 · norm_affordable + 0.30 · norm_orgs + 0.20 · norm_nez
```

**Affordable-unit choice:** Taking `max()` of LIHTC LI units and HUD Picture "All Programs" units avoids double-counting LIHTC + Section 8 overlaps at the property level. It intentionally errs on the side of **over-counting** a tract's readiness — a conservative stance for identifying low-readiness priority tracts (a tract that looks thin under this metric is truly thin).

**Weighting rationale:** The 50/30/20 split follows the user's guidance and the scope doc's argument that deed-restricted units are the single most defensible signal (a unit with a deed restriction cannot be displaced). Org presence ranks second because it is the lever for conversion of external capital into community-directed outcomes. NEZ is third because it is a policy tool — necessary but not sufficient for displacement defense.

### 2.2 Risk × readiness classification

- **High pressure** ≡ Bates typology ∈ {Susceptible, Early: Type 1, Early: Type 2, Dynamic, Late}
- **High readiness** ≡ readiness_score ≥ Dallas County median

Distribution across the 645 tracts:

| Cell | Tracts | Interpretation |
|---|---|---|
| HIGH_PRESSURE_LOW_READINESS | 44 | **Crisis quadrant** — thesis intervention priority |
| HIGH_PRESSURE_HIGH_READINESS | 129 | Pressured but defended |
| LOW_PRESSURE_LOW_READINESS | 278 | Thin readiness but stable |
| LOW_PRESSURE_HIGH_READINESS | 194 | Stable and defended |

---

## 3. Priority Ranking — The 54 Susceptible South Tracts

All 54 tracts ranked ascending by `readiness_score` (lowest readiness = highest urgency). **Bottom-quartile** (14 tracts, readiness ≤ 0.028) = thesis policy recommendation target.

Top 14 priority tracts (intervention target):

| Rank | GEOID | Tract | Readiness | Affordable units | Council |
|---|---|---|---|---|---|
| 1 | 48113017009 | 170.09 | 0.001 | 1 | 8 |
| 2 | 48113006402 | 64.02 | 0.001 | 1 | 1 |
| 3 | 48113009103 | 91.03 | 0.010 | 6 | 5 |
| 4 | 48113017007 | 170.07 | 0.011 | 10 | 8 |
| 5 | 48113009202 | 92.02 | 0.011 | 10 | 5 |
| 6 | 48113016001 | 160.01 | 0.012 | 7 | Outside City |
| 7 | 48113016302 | 163.02 | 0.014 | 4 | Outside City |
| 8 | 48113011802 | 118.02 | 0.017 | 11 | 5 |
| 9 | 48113005901 | 59.01 | 0.017 | 15 | 4 |
| 10 | 48113016002 | 160.02 | 0.018 | 11 | Outside City |
| 11 | 48113011103 | 111.03 | 0.020 | 11 | 3 |
| 12 | 48113011104 | 111.04 | 0.027 | 23 | 8 |
| 13 | 48113010809 | 108.09 | 0.027 | 23 | 3 |
| 14 | 48113017101 | 171.01 | 0.027 | 28 | 8 |

Full ranked list: `outputs/tables/h4_priority_54.csv`.

Council-district concentration across all 54: **District 8 (14 tracts), District 3 (14), District 5 (5), District 4 (4), District 1 (3)**, plus 14 tracts outside the City of Dallas limits. The intervention audience for these districts is the council members representing them in the May 2023 redistricting roster: Atkins (D8), Gracey (D3), Resendez (D5), Schultz (D4), and West (D1). District 7 (Bazaldua) overlaps a small share of the priority tract footprint and is included as a secondary audience.

---

## 4. Tool Density × Readiness

| Universe | Subset | n | Mean readiness | Median readiness |
|---|---|---|---|---|
| All 645 tracts | TIF present | 70 | **0.158** | 0.111 |
| All 645 tracts | No TIF | 575 | 0.088 | 0.022 |
| All 645 tracts | OZ designated | 3 | 0.158 | 0.006 |
| All 645 tracts | No OZ | 642 | 0.095 | 0.024 |
| 122 Susceptible tracts | TIF present | **0** | — | — |
| 122 Susceptible tracts | OZ designated | **0** | — | — |
| **54 South Susceptible tracts** | **TIF present** | **0** | — | — |
| **54 South Susceptible tracts** | **OZ designated** | **0** | — | — |

> **Caveat (added 2026-04-26):** The TIF and OZ counts in this table were computed from the hardcoded inputs in `scripts/pipeline/atlas_v0_build.py` (18 bounding-box approximations for TIF; 30-GEOID list for OZ that silently matched only 3 tracts in this panel). The 0/0 result for the 54 South Susceptible tracts may be robust under the corrected pipeline (`scripts/pipeline/build_layer3_tif_oz.py`) but cannot be defended until that pipeline runs against the authoritative City of Dallas TIF Subdistricts layer and HUD Opportunity Zones layer. PR-2 will re-run and update this table with sourced values; the corresponding `H4_WITH_TIF_OZ` key in `docs/FACTS.md` is annotated as `provenance: pending-rerun` until then.

**Key finding:** *Zero* of the 54 South Susceptible tracts have a TIF district or an active Opportunity Zone designation. County-wide, TIF tracts show higher readiness (mean 0.158 vs 0.088) because TIF zones concentrate in already-subsidized downtown/near-core areas. **South Dallas is susceptible to displacement without any current capital-tool scaffolding in place** — the opposite of the hypothesis that tool density without readiness is the crisis configuration. The crisis configuration here is **pressure without tools OR readiness** — a more severe version of the hypothesis.

This flips the policy recommendation: the 54 South tracts need *new* tool designations paired with deed-restricted preservation, not just readiness layered onto existing tools.

---

## 5. Civic Decision-Point Calendar

`outputs/tables/h4_decision_calendar.csv` — 7 recurring cycles mapped for the 54 priority tracts.

| Cycle | Next window | Intervention type |
|---|---|---|
| Dallas CIP (Capital Improvement Program) update | FY27 CIP adopted Sept 2026 | Budget priorities + bond planning |
| TIF District Board Meetings | Recurring monthly-quarterly | TIF project approvals + affordable housing set-asides |
| Dallas City Council Budget Hearings | Budget FY27: Aug–Sept 2026 | Operating + capital budget amendments |
| Bond Election Windows | Next typically 2029–2030 | Infrastructure + housing bond propositions |
| NEZ Designations | Ongoing review | Tax abatement + development incentives |
| Comprehensive Housing Policy Updates | CHP 2.0 expected mid-2026 | Affordable housing strategy + tools |
| South Dallas/Fair Park Area Plan Implementation | Zoning authorized hearing 2026 | Zoning + land-use (displacement mitigation) |

---

## 6. Outputs

| File | Description |
|---|---|
| `outputs/tables/h4_readiness_index.csv` | All 645 tracts with readiness columns + 2×2 cell |
| `outputs/tables/h4_priority_54.csv` | 54 Susceptible South tracts, ranked |
| `outputs/tables/h4_decision_calendar.csv` | Civic decision-point cycles |
| `outputs/geojson/h4_readiness.geojson` | Tract-level GeoJSON for ArcGIS/web mapping |
| `maps/h4/h4_priority_54_readiness.png` | Choropleth of the 54, colored by readiness |
| `maps/h4/h4_risk_readiness_grid.png` | County-wide 2×2 risk × readiness map |

---

## 7. Caveats and Next Steps

1. **ZIP-centroid geocoding** for curated community orgs is coarse (~1 ZIP = ~10 tracts). For thesis rigor, replace with address geocoding via the Census Geocoder API.
2. **NHPD backfill**: register for a free account and pull the Texas "Active and Inconclusive Properties" extract to cross-validate LIHTC + HUD Picture totals and identify expiring affordability.
3. **Legal Aid service area**: current approach places Legal Aid of NorthWest Texas at its HQ ZIP; its actual service footprint is county-wide. Consider a county-level counting alternative.
4. **Dallas County tracts without a council district** (14 of the 54) are in suburban cities (DeSoto, Lancaster, Cedar Hill, Glenn Heights, Balch Springs). These should be joined to their respective city councils for the decision calendar in a follow-up pass.
5. **Readiness score is bounded 0–1** but distribution is highly right-skewed — the bottom quartile cuts at 0.028 while the max is ~0.55. Consider log-transforming for visualizations.

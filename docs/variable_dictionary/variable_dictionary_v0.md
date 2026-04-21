# Variable Dictionary — Atlas v0
**Below the Line: Dallas I-30 Corridor Displacement Risk**  
Nicholas D. Hawkins | TSU Freeman Honors College | Updated: April 2026

---

## Unit of Analysis
Census Tract (2020 TIGER/Line boundaries), Dallas County, TX (FIPS 48113)  
N = 645 tracts | Population: ~2.6M | ACS Vintage: 2023 5-Year

---

## Layer 1: Investment Variables

| Variable | Description | Source | Units | Notes |
|----------|-------------|--------|-------|-------|
| `cip_budget_total` | Total CIP/bond dollars allocated to projects intersecting tract | Dallas CIP FY2025–26 | USD | Point-in-polygon spatial join |
| `cip_project_count` | Count of CIP projects intersecting tract | Dallas CIP | Integer | |
| `cip_per_capita` | CIP budget divided by tract population | Derived | USD/person | Excludes tracts with pop < 100 |
| `tif_present` | Binary: tract intersects ≥1 active TIF district | Dallas OED | 0/1 | 18 active TIF districts |
| `tif_district_name` | Name(s) of intersecting TIF district(s) | Dallas OED | String | |
| `oz_designated` | Binary: tract designated as Opportunity Zone | CDFI Fund / Treasury 2018-48 | 0/1 | Permanent designations |
| `tool_density` | Count of distinct policy tools (TIF + OZ) | Derived | Integer (0–2) | Expandable to include NEZ, PID |

## Layer 2: Demographic / ACS Variables

| Variable | Description | Source | Units | Notes |
|----------|-------------|--------|-------|-------|
| `population` | Total population | ACS 2023 B01003 | Integer | Tract-level |
| `median_income` | Median household income | ACS 2023 B19013 | USD | -666666666 = suppressed (cleaned) |
| `pct_black` | % residents identifying as Black/African American | ACS 2023 B02001 | Percent | |
| `pct_hispanic` | % residents identifying as Hispanic/Latino | ACS 2023 B03002 | Percent | |
| `pct_nonwhite` | pct_black + pct_hispanic (primary race exposure proxy) | Derived | Percent | Capped at 100 |
| `pct_renter` | % housing units that are renter-occupied | ACS 2023 B25003 | Percent | |
| `rent_burden_pct` | % renter HHs paying ≥35% income on rent | ACS 2023 B25070 | Percent | Severe burden threshold |

## Layer 3: Early Warning / Legacy Variables

| Variable | Description | Source | Units | Notes |
|----------|-------------|--------|-------|-------|
| `holc_grade` | 1937 HOLC grade assigned to tract centroid | Mapping Inequality | A/B/C/D | Approximate digitization in v0 |
| `holc_score` | Numeric HOLC grade (A=1, B=2, C=3, D=4) | Derived | Integer 1–4 | Higher = worse legacy |
| `redline_legacy` | Normalized legacy score (0–1) | Derived | Float | D=1.0, C=0.67, B=0.33, A=0 |
| `south_of_i30` | Binary: tract centroid south of I-30 corridor | Derived (spatial) | 0/1 | I-30 centerline from TIGER |

## Composite Variables

| Variable | Description | Formula | Range |
|----------|-------------|---------|-------|
| `demo_vuln` | Demographic vulnerability index | 0.5×norm(pct_nonwhite) + 0.3×norm(rent_burden) + 0.2×norm(-income) | 0–1 |
| `public_invest_conc` | Public investment concentration index | 0.4×tif_present + 0.3×oz_designated + 0.3×norm(cip_budget) | 0–1 |
| `dpi` | Displacement Pressure Index | (0.25×redline_legacy + 0.35×demo_vuln + 0.40×public_invest_conc) × 100 | 0–100 |
| `risk_tier` | DPI quartile tier | Binned: Low/Moderate/High/Critical | Categorical |

---

## H1 Regression Variables

**Dependent variable:** `cip_per_capita` (log-transformed recommended)  
**Primary independent:** `pct_nonwhite`  
**Controls:** `median_income`, `population`, `south_of_i30`  
**Model:** OLS with robust standard errors (HC3)

---

*v0 notes: CIP layer uses representative project data pending full geocoded Dallas OpenData export. HOLC boundaries are approximate. All variables subject to revision in v1.*

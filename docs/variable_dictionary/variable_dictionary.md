# Variable Dictionary

**Thesis:** Below the Line: Development as Governance and the Geography of Displacement Risk in Dallas
**Author:** Nicholas Donovan Hawkins
**Institution:** Texas Southern University, Freeman Honors College
**Date:** April 2026
**Version:** v1.0
**Publication Target:** Urban Affairs Review

---

## How to Use This Dictionary

Each section corresponds to a numbered hypothesis (H1, H2, H3, H6) and contains a full variable-level table followed by a brief analytical description of that variable set. The **Type** column classifies each variable as continuous, binary, categorical, ordinal, or composite. The **Transformation Applied** column records any recoding, scaling, ratio construction, or inflation adjustment performed prior to analysis; where no transformation was applied, the entry reads "None."

---

## H1 — Investment Bias (OLS Regression)

### Analytical Purpose

H1 models spatial variation in municipal capital investment intensity across Dallas census tracts, testing whether tract-level racial composition and poverty rates predict lower per-capita Capital Improvement Program (CIP) expenditure after controlling for income, density, and geography. The unit of analysis is the census tract; inference is cross-sectional using the most recent ACS five-year estimates. Distance to I-30 operationalizes the structural geographic divide that is central to the thesis argument.

### Variable Table

| Variable Name | Type | Description | Source | Unit | Transformation Applied |
|---|---|---|---|---|---|
| CIP expenditure per capita | Continuous | Total Capital Improvement Program spending allocated to a census tract divided by tract population | City of Dallas CIP Open Data | U.S. dollars per person | Tract-level CIP totals divided by ACS 2023 tract population estimate |
| % non-white population | Continuous | Share of tract population identifying as any race or ethnicity other than non-Hispanic white alone | ACS 5-Year 2023 (Table B03002) | Percentage (0–100) | Derived as 100 minus the non-Hispanic white alone share |
| % below poverty line | Continuous | Share of tract population with income below the federal poverty threshold in the prior 12 months | ACS 5-Year 2023 (Table B17001) | Percentage (0–100) | None |
| Population density | Continuous | Total tract population divided by tract land area | ACS 5-Year 2023 population; Census TIGER/Line tract boundaries | Persons per square mile | Tract population divided by land area in square miles derived from TIGER shapefile |
| Distance to I-30 | Continuous | Straight-line (Euclidean) distance from tract centroid to the nearest point on the I-30 corridor | Census TIGER/Line tract boundaries; I-30 alignment from TXDOT | Kilometers | Calculated from projected centroid coordinates using planar distance in a Texas State Plane CRS |
| Median household income | Continuous | Median household income in the prior 12 months (inflation-adjusted to 2023 dollars) | ACS 5-Year 2023 (Table B19013) | U.S. dollars | None (ACS 2023 estimates already in 2023 dollars) |
| Tract area | Continuous | Total land area of the census tract | Census TIGER/Line 2023 tract boundaries | Square kilometers | Derived from TIGER shapefile geometry; water area excluded |

---

## H2 — Redlining Legacy (Vendor Geocode + Spatial Join)

### Analytical Purpose

H2 documents the spatial correspondence between mid-twentieth-century Home Owners' Loan Corporation (HOLC) risk grades and present-day distribution of CIP vendor contract dollars. The analysis geocodes vendor addresses from City of Dallas CIP procurement records and spatially joins each vendor point to its enclosing census tract and HOLC polygon, enabling comparison of capital flow by historical grade and by position relative to I-30. The principal finding—a 12.6× North/South capital gap and a 26:1 TIF increment ratio—is derived from these aggregations.

### Variable Table

| Variable Name | Type | Description | Source | Unit | Transformation Applied |
|---|---|---|---|---|---|
| HOLC grade | Ordinal | Home Owners' Loan Corporation appraisal grade assigned to a neighborhood circa 1935–1940 | Mapping Inequality, University of Richmond (Digital Scholarship Lab) | Categorical ordinal: A (Best), B (Still Desirable), C (Declining), D (Hazardous) | None; original letter grades retained; numeric encoding (1–4) used in rank-order analyses |
| CIP vendor contract amount | Continuous | Dollar value of a single CIP procurement contract as recorded in the vendor payment dataset | City of Dallas CIP vendor data | U.S. dollars | None at record level; aggregated by region and HOLC zone for summary statistics |
| Vendor address geocode — latitude | Continuous | WGS 84 latitude of the geocoded vendor business address | City of Dallas CIP vendor data; geocoded via address matching | Decimal degrees | Geocoded from vendor street address; records with geocode quality below rooftop/parcel level reviewed manually |
| Vendor address geocode — longitude | Continuous | WGS 84 longitude of the geocoded vendor business address | City of Dallas CIP vendor data; geocoded via address matching | Decimal degrees | Geocoded from vendor street address; records with geocode quality below rooftop/parcel level reviewed manually |
| Tract assignment (FIPS code) | Categorical | 11-digit Federal Information Processing Standards tract identifier assigned to vendor via spatial join | Census TIGER/Line 2023 tract boundaries | FIPS code string (e.g., 48113XXXXXXX) | Point-in-polygon spatial join; vendors falling outside tract boundaries excluded |
| North/South of I-30 binary | Binary | Indicator for whether the vendor tract centroid lies north (1) or south (0) of the I-30 corridor | Analyst-derived from Census TIGER/Line tract centroids and I-30 alignment | Binary integer (0 = South, 1 = North) | Derived by comparing projected centroid y-coordinate to I-30 polyline in Texas State Plane CRS |
| Economic residue by geography (total CIP$ per region) | Composite | Sum of CIP vendor contract amounts aggregated to North or South subregion | City of Dallas CIP vendor data; North/South binary indicator | U.S. dollars (aggregated) | Row-level contract amounts summed by North/South binary group |
| North/South capital gap ratio | Composite | Ratio of total North CIP vendor dollars to total South CIP vendor dollars | Derived from economic residue aggregation | Dimensionless ratio | North total divided by South total (documented value: $485M ÷ $38M = 12.6×) |
| TIF increment ratio | Composite | Ratio of total assessed value increment in the Downtown Connection TIF district to that of the Grand Park South TIF district | Dallas OED TIF annual reports | Dimensionless ratio | Downtown Connection increment ($8.83B) divided by Grand Park South increment ($333M) = 26:1 |

---

## H3 — Three Moves Diagnostic (Spatial Join + HMDA Analysis)

### Analytical Purpose

H3 uses Home Mortgage Disclosure Act loan application records to measure racial and geographic disparities in mortgage denial rates across Dallas census tracts, with particular attention to tracts intersecting Property Improvement District boundaries. The spatial join links HMDA applicant records to census tracts and to PID polygons, enabling decomposition of denial rates by race, loan purpose, and North/South geography. The South/North denial rate ratio (1.19×) and Black applicant share of denials (20.7%) are the primary inferential outputs.

### Variable Table

| Variable Name | Type | Description | Source | Unit | Transformation Applied |
|---|---|---|---|---|---|
| PID boundary | Categorical | Polygon delineating a Property Improvement District as established by the Dallas City Council | Dallas County Appraisal District PID boundary files | GIS polygon (no numeric unit) | None; used as spatial join key to assign HMDA records to PID membership (inside/outside) |
| HMDA loan application record | Categorical | Individual mortgage loan application record as reported by covered financial institutions under HMDA | CFPB HMDA 2023 (primary CFPB LAR dataset, not Urban Institute pre-aggregated) | Record/row (N = 12,300 denial records; 625 tracts) | Filtered to Dallas County; records with missing census tract suppressed per CFPB guidelines |
| Denial indicator | Binary | Equals 1 if the loan application resulted in a denial action; equals 0 otherwise | CFPB HMDA 2023 (action_taken field) | Binary integer (0 = not denied, 1 = denied) | Derived by recoding HMDA action_taken code 3 (Denied) to 1; all other terminal action codes to 0 |
| Applicant race | Categorical | Self-reported race of the primary loan applicant as recorded in the HMDA LAR | CFPB HMDA 2023 (applicant_race fields) | Categorical: Black, White, Hispanic, Asian, Other | Recoded from HMDA race code integers to labeled categories; multi-race combinations classified as Other |
| Tract FIPS code | Categorical | 11-digit census tract identifier assigned to each HMDA application record by the reporting institution | CFPB HMDA 2023 (census_tract field) | FIPS code string | None; used as primary spatial join and aggregation key |
| Loan purpose | Categorical | Purpose of the loan application as categorized in the HMDA LAR | CFPB HMDA 2023 (loan_purpose field) | Categorical: Purchase, Refinance, Improvement | Recoded from HMDA integer codes (1 = Purchase, 31/32 = Refinance, 2 = Improvement) to labels |
| Loan amount | Continuous | Dollar amount of the loan applied for, reported in thousands of dollars in the HMDA LAR | CFPB HMDA 2023 (loan_amount field) | U.S. dollars (thousands) | None at record level; used in descriptive comparisons by denial status and race |
| Denial rate by tract | Composite | Share of loan applications in a given census tract that resulted in denial | Derived from denial indicator and tract FIPS code | Percentage (0–100) | Total denials divided by total applications per tract, expressed as a percentage |
| South/North denial rate ratio | Composite | Ratio of the average tract-level denial rate in South Dallas tracts to that in North Dallas tracts | Derived from denial rate by tract and North/South geographic classification | Dimensionless ratio | South mean denial rate divided by North mean denial rate (documented value: 1.19×) |
| Black share of denials | Composite | Share of total denial records in which the primary applicant identified as Black | Derived from denial indicator and applicant race | Percentage (0–100) | Black denial count divided by total denial count (documented value: 20.7%) |

---

## H6 — Bates Typology v2.1 (Longitudinal ACS Panel)

### Analytical Purpose

H6 applies an adaptation of the Bates (2013) neighborhood change typology to Dallas census tracts using a longitudinal panel of ACS five-year estimates from 2013 and 2023. Tracts are classified into four displacement-pressure stages—Early, Dynamic, Late, and Stable—based on composite indices of displacement pressure (income appreciation, rent appreciation) and demographic vulnerability (renter share, non-white share). All dollar-denominated 2013 variables are CPI-adjusted to 2023 dollars using the BLS CPI-U multiplier to ensure temporal comparability. Tract boundaries are harmonized across the two time points using the Brown University Longitudinal Tract Database crosswalk.

### Variable Table

| Variable Name | Type | Description | Source | Unit | Transformation Applied |
|---|---|---|---|---|---|
| Median household income 2013 | Continuous | Median household income in the tract for the 2009–2013 ACS reference period, adjusted to 2023 dollars | ACS 5-Year 2013 (Table B19013); BLS CPI-U | 2023 U.S. dollars | Nominal 2013 value multiplied by BLS CPI-U adjustment factor (base year 2023); tract boundaries harmonized via LTDB crosswalk |
| Median household income 2023 | Continuous | Median household income in the tract for the 2019–2023 ACS reference period | ACS 5-Year 2023 (Table B19013) | 2023 U.S. dollars | None (ACS 2023 estimates in 2023 dollars) |
| % renter-occupied 2013 | Continuous | Share of occupied housing units that are renter-occupied in the tract, 2009–2013 ACS reference period | ACS 5-Year 2013 (Table B25003) | Percentage (0–100) | Derived as renter-occupied units divided by total occupied units; LTDB crosswalk applied |
| % renter-occupied 2023 | Continuous | Share of occupied housing units that are renter-occupied in the tract, 2019–2023 ACS reference period | ACS 5-Year 2023 (Table B25003) | Percentage (0–100) | Derived as renter-occupied units divided by total occupied units |
| % non-white 2013 | Continuous | Share of tract population identifying as any race or ethnicity other than non-Hispanic white alone, 2009–2013 reference period | ACS 5-Year 2013 (Table B03002) | Percentage (0–100) | Derived as 100 minus non-Hispanic white alone share; LTDB crosswalk applied |
| % non-white 2023 | Continuous | Share of tract population identifying as any race or ethnicity other than non-Hispanic white alone, 2019–2023 reference period | ACS 5-Year 2023 (Table B03002) | Percentage (0–100) | Derived as 100 minus non-Hispanic white alone share |
| Median gross rent 2013 | Continuous | Median gross rent (contract rent plus estimated average utility costs) in the tract, 2009–2013 ACS reference period, adjusted to 2023 dollars | ACS 5-Year 2013 (Table B25064); BLS CPI-U | 2023 U.S. dollars per month | Nominal 2013 value multiplied by BLS CPI-U adjustment factor (base year 2023); LTDB crosswalk applied |
| Median gross rent 2023 | Continuous | Median gross rent in the tract, 2019–2023 ACS reference period | ACS 5-Year 2023 (Table B25064) | 2023 U.S. dollars per month | None (ACS 2023 estimates in 2023 dollars) |
| Displacement pressure index | Composite | Composite index summarizing tract-level upward pressure on housing costs, constructed from income appreciation and rent appreciation between 2013 and 2023 | Derived from ACS 5-Year 2013 and 2023; BLS CPI-U adjusted values | Standardized index score (z-score scale) | Component variables (income change, rent change) standardized to z-scores; index is mean of component z-scores; higher values indicate greater pressure |
| Vulnerability index | Composite | Composite index summarizing tract-level population susceptibility to displacement, constructed from renter share and non-white share at baseline (2013) | Derived from ACS 5-Year 2013 | Standardized index score (z-score scale) | Component variables (% renter-occupied 2013, % non-white 2013) standardized to z-scores; index is mean of component z-scores; higher values indicate greater vulnerability |
| Bates stage classification | Categorical | Tract-level neighborhood change stage assigned per the Bates (2013) typology, version 2.1 adaptation | Derived from displacement pressure index and vulnerability index via threshold classification | Categorical: Early, Dynamic, Late, Stable | Quadrant classification applied to pressure × vulnerability scatter: high pressure + high vulnerability = Late; high pressure + low vulnerability = Dynamic; low pressure + high vulnerability = Early; low pressure + low vulnerability = Stable |

---

## Derived Outputs and Key Findings

The following derived outputs are produced from the analyses above and are referenced in the thesis body, tables, and figures. They are documented here for reproducibility and auditability.

| Output | Analysis | Description | Value Documented |
|---|---|---|---|
| North CIP total | H2 | Sum of CIP vendor contract dollars allocated to tracts north of I-30 | $485 million |
| South CIP total | H2 | Sum of CIP vendor contract dollars allocated to tracts south of I-30 | $38 million |
| North/South capital gap ratio | H2 | Ratio of North to South CIP vendor totals | 12.6× |
| Downtown Connection TIF increment | H2 | Total assessed value increment captured in the Downtown Connection TIF district, per Dallas OED annual report | $8.83 billion |
| Grand Park South TIF increment | H2 | Total assessed value increment captured in the Grand Park South TIF district, per Dallas OED annual report | $333 million |
| TIF increment ratio | H2 | Ratio of Downtown Connection increment to Grand Park South increment | 26:1 |
| South/North denial rate ratio | H3 | Ratio of mean tract-level mortgage denial rate in South Dallas tracts to mean rate in North Dallas tracts | 1.19× |
| Black share of denials | H3 | Black applicant share of total HMDA denial records in the Dallas County sample | 20.7% |
| HMDA analysis dataset scale | H3 | Total tracts and denial records included in the H3 analysis | 625 tracts; 12,300 denial records |
| Pressure × Vulnerability scatter (Panel B) | H6 | Bivariate scatter of displacement pressure index (x-axis) against vulnerability index (y-axis) for all Dallas tracts, with Bates stage quadrant overlays | Figure output; all tracts |
| Typology distribution by region (Panel A) | H6 | Bar chart or table showing the count and percentage of tracts in each Bates stage, disaggregated by North/South geography | Figure output |
| Income distribution by Bates stage (Panel C) | H6 | Box plot or violin plot showing the distribution of 2023 median household income by Bates stage classification | Figure output |

---

## Data Sources Reference

| Abbreviation | Full Citation |
|---|---|
| ACS 5-Year 2023 | U.S. Census Bureau. *American Community Survey 5-Year Estimates, 2019–2023.* Washington, DC: U.S. Census Bureau. https://data.census.gov |
| ACS 5-Year 2013 | U.S. Census Bureau. *American Community Survey 5-Year Estimates, 2009–2013.* Washington, DC: U.S. Census Bureau. https://data.census.gov |
| Census TIGER/Line | U.S. Census Bureau. *TIGER/Line Shapefiles 2023: Census Tracts.* Washington, DC: U.S. Census Bureau. https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html |
| City of Dallas CIP Open Data | City of Dallas. *Capital Improvement Program Open Data.* Dallas, TX: City of Dallas Office of Budget. https://www.dallasopendata.com |
| CFPB HMDA 2023 | Consumer Financial Protection Bureau. *Home Mortgage Disclosure Act Loan Application Register, 2023.* Washington, DC: CFPB. https://www.consumerfinance.gov/data-research/hmda/ |
| Dallas OED TIF Reports | City of Dallas Office of Economic Development. *Tax Increment Financing District Annual Reports.* Dallas, TX: City of Dallas OED. https://dallasecodev.org |
| Dallas County Appraisal District | Dallas Central Appraisal District. *Property Improvement District Boundary Files.* Dallas, TX: DCAD. https://www.dallascad.org |
| Mapping Inequality / HOLC | Nelson, R.K., L. Winling, R. Marciano, N. Connolly, et al. *Mapping Inequality: Redlining in New Deal America.* Digital Scholarship Lab, University of Richmond, 2023. https://dsl.richmond.edu/panorama/redlining/ |
| BLS CPI-U | U.S. Bureau of Labor Statistics. *Consumer Price Index for All Urban Consumers (CPI-U), All Items, U.S. City Average.* Washington, DC: BLS. https://www.bls.gov/cpi/ |
| LTDB | Logan, J.R., Z. Xu, and B. Stults. *Longitudinal Tract Database.* Spatial Structures in the Social Sciences, Brown University, 2014. https://s4.ad.brown.edu/projects/diversity/Researcher/LTDB.htm |

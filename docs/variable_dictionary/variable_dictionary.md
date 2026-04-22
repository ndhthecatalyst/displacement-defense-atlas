# Variable Dictionary

**Thesis:** Below the Line: Development as Governance and the Geography of Displacement Risk in Dallas
**Author:** Nicholas Donovan Hawkins
**Institution:** Texas Southern University, Freeman Honors College
**Date:** April 2026
**Version:** v1.1 (V5 Capital Stack reconciliation — April 2026)
**Publication Target:** Urban Affairs Review

---

## How to Use This Dictionary

Each section corresponds to a numbered hypothesis (H1–H6) and contains a full variable-level table followed by a brief analytical description of that variable set. Sections are organized by the Five-Layer Capital Stack framing: Layer 1 (CIP, H1), Layer 5 (Vendor Residue, H2), Layers 2+4 composite (H3), Layer 3 (TIF/OZ readiness gap, H4), Political Recirculation (H5), and Longitudinal Bates staging (H6). A final "Layered Capital Stack Variables" section documents the V5 composite exposure score inputs. The **Type** column classifies each variable as continuous, binary, categorical, ordinal, or composite. The **Transformation Applied** column records any recoding, scaling, ratio construction, or inflation adjustment performed prior to analysis; where no transformation was applied, the entry reads "None."

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

## H2 — Vendor Residue / Layer 5 (Vendor Geocode + Spatial Join)

### Analytical Purpose

H2 operationalizes Layer 5 of the Five-Layer Capital Stack — the *vendor residue* layer, which measures where public contracting dollars ultimately flow. The analysis geocodes vendor addresses from the City of Dallas vendor payment dataset (145,551 payment rows; 8,354 unique vendors geocoded by ZIP5) and spatially joins each vendor to its enclosing census tract and HOLC polygon, enabling comparison of capital flow by historical grade and by position relative to I-30. The V5 top-18 vendor analysis produces the principal finding: $369.2M (25.3%) flows to North Dallas versus $38.3M (2.6%) to South Dallas — a 12.6× ratio. Supplementary findings: 83% of $108.8M in CIP spend originating from South Dallas projects is extracted northward; $58.9M (15¢ of every top-vendor dollar) flows to Texas Materials Group, owned by CRH plc (Irish corporate parent). The 26:1 TIF increment ratio reported here is the Layer 3 anchor retained in this section as the adjacent comparison, with the full Layer 3 analysis living in H4.

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

## H4 — TIF/OZ Readiness Gap / Layer 3 (Readiness Index + Susceptibility Classification)

### Analytical Purpose

H4 operationalizes Layer 3 of the Five-Layer Capital Stack by documenting the inverted spatial gap between displacement pressure and public readiness capacity. The analysis constructs a Readiness Index from tract-level indicators of public investment presence (TIF, OZ, LIHTC, NEZ, HUD-subsidized units) and cross-classifies each tract against a pressure score (housing cost appreciation, income gap, vulnerability). The V5 central finding is that zero of the 54 Susceptible South Dallas tracts contain any TIF or OZ designation, producing 44 *HIGH_PRESSURE_LOW_READINESS* crisis tracts where displacement is rising without a public readiness response. Among these, 14 *immediate priority* tracts (readiness ≤ 0.028) are flagged: the top five are 170.09 (District 8), 64.02 (D1), 91.03 (D5), 170.07 (D8), and 92.02 (D5).

### Variable Table

| Variable Name | Type | Description | Source | Unit | Transformation Applied |
|---|---|---|---|---|---|
| Readiness score | Composite | Tract-level composite measuring public investment and readiness capacity, weighted 50% public investment presence (TIF/OZ), 30% subsidized affordable housing (LIHTC, HUD Picture), 20% targeted redevelopment overlays (NEZ) | Derived from TIF/OZ boundaries, LIHTC projects, HUD Picture of Subsidized Households, Dallas NEZ layer | Standardized index score (0–1 scale) | Components min-max scaled; weighted sum applied; 50/30/20 weighting |
| Pressure score | Composite | Tract-level composite measuring displacement pressure, derived from CPI-adjusted housing-cost appreciation, real-income gap, and baseline vulnerability | Derived from ACS 2013 and 2023 (LTDB crosswalked); BLS CPI-U | Standardized index score (0–1 scale) | Components min-max scaled; mean of component scores |
| Pressure-readiness class | Categorical | Tract-level cross-classification: HIGH_PRESSURE_LOW_READINESS / HIGH_PRESSURE_HIGH_READINESS / LOW_PRESSURE_LOW_READINESS / LOW_PRESSURE_HIGH_READINESS | Derived from pressure score and readiness score | Categorical (4-level) | Median split on each axis; quadrant classification |
| Susceptible South flag | Binary | Indicator of whether a South Dallas tract meets the V5 Susceptibility criteria (baseline vulnerability percentile + non-white share threshold + South of I-30) | Derived from ACS 2013 vulnerability index, I-30 spatial boundary | Binary (0/1) | Tract must be south of I-30 AND in top tercile of baseline vulnerability; 54 tracts identified |
| TIF overlap percentage | Continuous | Share of tract land area contained within any active Dallas TIF district polygon | Dallas OED TIF boundary shapefiles; Census TIGER tracts | Percentage (0–100) | Polygon intersection area ÷ tract area × 100 |
| OZ overlap percentage | Continuous | Share of tract land area designated as an Opportunity Zone | CDFI Fund / Treasury OZ designations; Census TIGER tracts | Percentage (0–100) | Polygon intersection area ÷ tract area × 100 |
| Immediate priority flag | Binary | Indicator of the 14 tracts with readiness score ≤ 0.028 and HIGH_PRESSURE_LOW_READINESS classification | Derived from readiness score + pressure-readiness class | Binary (0/1) | Bottom-decile readiness within HIGH_PRESSURE_LOW_READINESS subset |

---

## H5 — Political Recirculation (Campaign Finance + Corporate Parentage)

### Analytical Purpose

H5 documents the political recirculation loop that closes the capital stack: where vendor revenue recirculates through campaign contributions and board interlocks rather than through direct municipal contributions. The analysis pulls TEC bulk campaign-finance data (state), FEC data (federal), and Dallas CFR records (municipal) for the top-18 vendors and their corporate parents, cross-checking board membership and PAC activity. The V5 central finding is threefold: (a) zero direct corporate contributions to Dallas City Council from top-18 vendors; (b) Tan Parker (TX HD-63) sits on the Board of Southland Holdings, parent of Oscar Renda Contracting ($26.5M in Dallas contracts); (c) $58.9M — 15¢ of every top-vendor dollar — flows to Texas Materials Group, owned by CRH plc (Irish corporate parent).

### Variable Table

| Variable Name | Type | Description | Source | Unit | Transformation Applied |
|---|---|---|---|---|---|
| TEC contribution amount | Continuous | Dollar value of state-level campaign contribution from a vendor-linked entity | Texas Ethics Commission bulk data (TEC_CF_CSV.zip) | U.S. dollars | Filtered to top-18 vendor corporate family; aggregated by recipient |
| FEC contribution amount | Continuous | Dollar value of federal-level campaign contribution from a vendor-linked entity | FEC bulk data | U.S. dollars | Filtered to top-18 vendor corporate family; aggregated by recipient |
| Vendor-to-PAC amount | Continuous | Dollar value of contribution from a vendor-linked entity to a political action committee | TEC + FEC | U.S. dollars | Filtered to PAC recipient type |
| Council direct contribution flag | Binary | Indicator of any direct corporate contribution from a top-18 vendor to a Dallas City Council campaign | Dallas CFR (campfin.dallascityhall.com) | Binary (0/1) | Any match in municipal CFR records; result: 0 of 18 |
| Board interlock flag | Binary | Indicator of any publicly identifiable board or executive role held by a sitting Texas state or federal legislator in a top-18 vendor or its corporate parent | SEC filings, corporate websites, Open Corporates, press releases | Binary (0/1) | Manual verification; documented case: Tan Parker / Southland Holdings |
| Foreign parent flag | Binary | Indicator that a top-18 vendor is owned by a corporate parent headquartered outside the United States | Open Corporates, SEC filings | Binary (0/1) | Documented case: Texas Materials Group / CRH plc (Ireland) |
| Capital-return extraction amount | Continuous | Dollar value of public contract spend flowing to foreign-parented vendors | Derived from vendor payment dataset and parent-company mapping | U.S. dollars | Sum across foreign-parented vendor subset |

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
| North vendor total (top-18) | H2 | Sum of top-18 vendor payment dollars flowing to vendors geocoded north of I-30 | $369.2 million (25.3% of audited spend) |
| South vendor total (top-18) | H2 | Sum of top-18 vendor payment dollars flowing to vendors geocoded south of I-30 | $38.3 million (2.6% of audited spend) |
| North/South vendor residue ratio | H2 | Ratio of North to South top-18 vendor totals | 12.6× |
| Southward spend extracted northward | H2 | Share of $108.8M in CIP spend on South Dallas projects captured by northern-geocoded vendors | 83% |
| CRH plc / Texas Materials Group share | H2 | Share of total top-vendor spend flowing to Texas Materials Group, owned by CRH plc (Ireland) | $58.9 million (≈15¢ per top-vendor dollar) |
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

## Layered Capital Stack Variables (V5 Composite Exposure Score Inputs)

### Analytical Purpose

The V5 framing integrates tract-level indicators from all five layers of the capital stack into a single composite exposure score, enabling a test of whether the composite predicts displacement stage better than any single layer variable (H3 v5). The variables below are the Layer-by-Layer inputs.

### Variable Table

| Variable Name | Layer | Type | Description | Source | Transformation Applied |
|---|---|---|---|---|---|
| `cip_discretionary_share` | L1 | Continuous | Share of tract CIP dollars classified as discretionary (parks, libraries, economic development) vs. mandatory (streets, utilities) | Dallas CIP Open Data; manual project-type coding | Discretionary $ ÷ total CIP $ per tract |
| `pid_present` | L2 | Binary | Indicator that the tract overlaps any active Dallas PID | Dallas GIS Hub PID layers (215f5e7243d44c25b7e503e3dafe73da; 16a1eb7a28f143ffb3714435ffac740a) | Spatial intersection |
| `pid_revenue_per_parcel` | L2 | Continuous | Annual PID assessment revenue divided by parcel count, for tracts within PID boundaries | Dallas OED + individual PID annual reports; DCAD parcel layer | Revenue ÷ parcel count |
| `econ_dev_pid_share` | L2 | Continuous | Share of tract's total economic-development spending that is PID-funded rather than general-fund | Dallas OED budget; PID reports | PID-funded ED $ ÷ total ED $ |
| `tif_increment_share` | L3 | Continuous | Share of tract assessed value captured by an active TIF district | Dallas County 2025 TIF Annual Report; Dallas OED; DCAD | TIF increment $ ÷ total tract assessed value |
| `oz_investment_received` | L3 | Continuous | Documented QOF investment directed into the tract | IRS Form 8996 data (Treasury) | Direct value; missing coded as 0 |
| `sfr_investor_share` | L4 | Continuous | Share of single-family rental parcels in the tract owned by institutional (mega-investor) entities | CoreLogic / ATTOM / PropStream; cross-referenced with Immergluck et al. | Institutional SFR parcels ÷ total SFR parcels |
| `investor_purchase_rate` | L4 | Continuous | Annualized rate of institutional SFR acquisitions per 1,000 tract parcels, 2019–2024 | Derived from deed-transfer records | Institutional acquisitions per 1,000 parcels per year |
| `vendor_residue` | L5 | Continuous | Share of tract-originated CIP spend captured by vendors geocoded within the tract (or within the same quadrant) | Derived from vendor payments + geocoding | Same-tract/quadrant $ ÷ total tract-originated CIP $ |
| `vendor_local_share` | L5 | Continuous | Share of top-vendor payment dollars flowing to Dallas-headquartered vendors | Dallas vendor payments; ZIP5 geocode | Dallas-ZIP $ ÷ total top-vendor $ |
| `vendor_south_share` | L5 | Continuous | Share of top-vendor payment dollars flowing to vendors geocoded south of I-30 | Dallas vendor payments; I-30 spatial boundary | South-of-I-30 $ ÷ total top-vendor $ |
| `mbe_contract_share` | L5 | Continuous | Share of tract-originated capital program spend flowing to certified Minority Business Enterprise vendors (pre-BID suspension baseline) | Dallas BID tracking records (historical); City procurement records | MBE $ ÷ total capital-program $ per tract |
| `appraisal_gap_proxy` | Cross-layer | Continuous | Proxy for the gap between HMDA-documented appraisal value and purchase price in the tract | CFPB HMDA 2023 loan-level file | Median (appraisal − purchase) within tract |
| `capital_stack_score` | Composite | Continuous | V5 integrated exposure score combining standardized L1–L5 inputs | Derived from all variables above | Each input standardized (z-score); weighted mean (equal weights in v0; factor-analysis weights in v1) |

### Notes on the Composite

The `capital_stack_score` is the V5 analytical innovation. It operationalizes the thesis claim that the five layers compound — their presence amplifies returns in wealthy white communities, their absence compounds disinvestment in Black communities. The H3 (v5) hypothesis test regresses Bates displacement stage on the composite score and compares explanatory power against single-layer predictors.

---

## Derived Outputs — V5 Additions

| Output | Analysis | Description | Value Documented |
|---|---|---|---|
| Susceptible South tract count | H4 | Count of South Dallas tracts meeting the V5 Susceptibility criteria | 54 |
| TIF/OZ presence in Susceptible South | H4 | Count of Susceptible South tracts with any TIF or OZ designation | 0 |
| HIGH_PRESSURE_LOW_READINESS tract count | H4 | Count of tracts classified in the crisis-zone quadrant | 44 |
| Immediate priority tract count | H4 | Count of tracts with readiness score ≤ 0.028 in HIGH_PRESSURE_LOW_READINESS | 14 |
| Top-5 immediate priority tracts | H4 | Ranked list by readiness-score ascending | 170.09 (D8); 64.02 (D1); 91.03 (D5); 170.07 (D8); 92.02 (D5) |
| Council direct contributions from top-18 vendors | H5 | Count of direct corporate contributions to Dallas City Council from top-18 vendors | 0 |
| Tan Parker / Southland Holdings interlock | H5 | Documented board interlock case | Tan Parker (TX HD-63) on Board of Southland Holdings (parent of Oscar Renda) |
| CRH plc capital-return extraction | H5 | Annual top-vendor dollars flowing to a foreign (Irish) parent company | $58.9 million (≈15% of top-vendor spend) |
| ACS panel tract match count | H4, H6 | Tracts with complete 2013↔2023 ACS observations via LTDB crosswalk | 385 of 645 Dallas County tracts |
| CPI adjustment factor 2013→2023 | All | BLS CPI-U all-items U.S. city average | 1.36 (36%) |
| South vs. North home-value change 10yr | H6 | ACS 2013→2023 median home-value percent change, CPI-adjusted | +120.5% (South) vs. +111.3% (North) |
| South vs. North real-income change 10yr | H6 | ACS 2013→2023 median household income percent change, CPI-adjusted | +8.6% (South) vs. +17.1% (North) |
| M7 OLS HOLC-D coefficient (H1) | H1 | Coefficient on HOLC-D grade in CIP $/capita regression | β = +247.6 (p<0.001); race coefficient becomes non-significant when controlled |

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
| Dallas PID Boundaries | City of Dallas GIS Hub. *Public Improvement District Boundary Files.* Layer IDs: `215f5e7243d44c25b7e503e3dafe73da`; `16a1eb7a28f143ffb3714435ffac740a`. https://dallasgis.dallascityhall.com |
| Dallas Vendor Payments | City of Dallas. *Vendor Payments for Fiscal Year 2019–Present.* Dallas Open Data. https://www.dallasopendata.com |
| HUD Picture of Subsidized Households | U.S. Department of Housing and Urban Development. *Picture of Subsidized Households.* Washington, DC: HUD. https://www.huduser.gov/portal/datasets/assthsg.html |
| Dallas NEZ | City of Dallas. *Neighborhood Empowerment Zone Designations.* Dallas, TX. https://dallasecodev.org |
| TEC | Texas Ethics Commission. *Campaign Finance Bulk Data (CSV).* https://prd.tecprd.ethicsefile.com/public/cf/public/TEC_CF_CSV.zip |
| FEC | Federal Election Commission. *Bulk Data Downloads.* https://www.fec.gov/data/ |
| Dallas CFR | City of Dallas. *Municipal Campaign Finance Records.* https://campfin.dallascityhall.com |
| IRS Form 8996 | U.S. Internal Revenue Service. *Qualified Opportunity Fund Annual Reporting (Form 8996).* https://www.irs.gov |
| CoreLogic / ATTOM | Institutional SFR ownership acquired via CoreLogic or ATTOM Data Solutions subscription; cross-referenced with Immergluck et al. |
| OpenCorporates | OpenCorporates. *Corporate Registry Data.* https://opencorporates.com (for parent-company verification, e.g., CRH plc) |

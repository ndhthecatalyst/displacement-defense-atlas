# Methods Memo v1 — Displacement Defense Atlas
## "Below the Line: How Dallas's Municipal Investment Architecture Reinforces Displacement Risk South of I-30"

**Author:** Nicholas D. Hawkins  
**Institution:** Texas Southern University, Freeman Honors College  
**Document type:** Undergraduate Honors Thesis — Methods Memo, Version 1  
**Date:** 2025

---

## 1. Overview & Purpose

This memo documents the methodological design for the first empirical chapter of the thesis, which tests whether Dallas's Capital Improvement Program (CIP) investment is distributed in a racially and economically disparate pattern south of Interstate 30. It is intended to serve two functions simultaneously: a working methods guide for the committee and a transparency record that demonstrates the author's methodological reasoning at each design decision point. The memo supersedes the v0 sketch and incorporates committee feedback on geographic scope, variable construction, and statistical treatment.

---

## 2. Research Question & H1 Hypothesis

**Core research question:** Does Dallas's municipal investment architecture — operationalized here through CIP spending from FY2012 through FY2026 — systematically underinvest in the predominantly Black and Hispanic communities located south of Interstate 30, relative to what a needs-proportional allocation formula would predict?

**Hypothesis 1 (H1):** After controlling for tract-level median income and CIP project category, census tracts south of I-30 with higher proportions of Black and Hispanic residents receive statistically significantly less per-capita CIP investment than comparably low-income tracts north of I-30. The investment gap is expected to be largest for discretionary spending categories (parks, libraries, cultural facilities) and smallest for categories driven by objectively measurable need proxies (drainage, flood control).

This hypothesis is the entry point into a broader argument about Dallas's **municipal investment architecture** — the full stack of public and quasi-public capital mechanisms including Tax Increment Financing (TIF) districts, Opportunity Zones, Public Improvement Districts (PIDs), Neighborhood Enterprise Zones (NEZs), and tax abatements. H1 isolates the CIP component because it is the most tractable for quantitative analysis; subsequent chapters extend the framework to the full architecture.

---

## 3. Study Design

### 3.1 Geographic Scope

The unit of analysis is the **census tract within Dallas city limits** (not Dallas County). Approximately 434 tracts fall within the city boundary. County-level analysis would conflate Dallas's historically inequitable investment patterns with those of suburban municipalities operating under entirely different political economies, introducing confounding that would obscure rather than illuminate the core claim.

**The "South of I-30" study zone** is defined operationally as census tracts whose **centroids fall south of the I-30 centerline** AND within the following named geographies: South Dallas, Fair Park, Frazier Courts, Bonton, Ideal, Oak Cliff (North, East, and West), Bishop Arts District, Kessler Park, Cedar Hill boundary tracts, Lancaster corridor, Pleasant Grove, and Rylie. Tracts north of I-30 serve as the comparison group. This definition is deliberate: it avoids the ecological fallacy of treating all southside tracts as equivalent while ensuring that the named communities most associated with displacement pressure are analytically visible.

*Note for v1:* The centroid-in-zone assignment will be validated by a manual spot-check of boundary tracts where the centroid placement might misclassify a tract that is substantively in the study zone. Any reassignments will be logged as a sensitivity table.

### 3.2 Time Window

The analytically meaningful window is **FY2012–FY2026** (14 fiscal years). This span captures three distinct political economy moments in Dallas's capital budgeting history:

- **2012 Bond Program ($642M):** The post-recession rebuilding cycle. Approved by Dallas voters in November 2012.
- **2017 Bond Program ($1.05B):** The full arc of the second bond cycle, including the period of rapid demographic change and rising housing costs across inner Dallas. Approved in November 2017.
- **2024 Bond Program ($1.25B):** Currently in early implementation as of the thesis writing period. Provides a prospective window into whether historic patterns persist under new political conditions.

Cross-sectional **ACS 2023 5-year estimates** will be used as the demographic baseline. This choice is methodologically deliberate: the 2023 ACS reflects the current population *bearing the effects* of cumulative investment decisions made over the prior 14 years. Using a midpoint-year demographic snapshot would introduce a mismatch between the population exposed to disinvestment and the population measured.

*Data acquisition flag for v1:* The analysis requires **actual CIP expenditure data** by project, by fiscal year — not just bond authorization amounts. Allocation authorizations and actual expenditures can diverge substantially; projects may be deferred, descoped, or cancelled after bond approval. The Dallas Office of Financial Services publishes annual CAFR (Comprehensive Annual Financial Report) data, and the Office of Budget publishes CIP project status reports. The author will submit a public records request for project-level expenditure data tagged to fiscal year of disbursement.

### 3.3 Metropolitan Comparison Panel (Planned Extension)

A DFW metroplex comparison panel is planned as a future extension. The analytical purpose is to test whether the I-30 investment gap is a Dallas-specific political economy phenomenon or a regional pattern of metropolitan governance. Candidate comparison cities include Fort Worth, Arlington, Garland, and Irving. This extension is flagged here but will not be executed in v1.

---

## 4. Data Sources & Acquisition

| Data Layer | Source | Format | Status |
|---|---|---|---|
| CIP project locations (point centroids, v0) | Dallas Open Data Portal — Capital Projects | GeoJSON/CSV | Available |
| CIP project line geometries (v1 upgrade) | Dallas Public Works GIS export (records request) | Shapefile | Pending |
| CIP project budgets & expenditures | Dallas OFS / CAFR; City Budget Office CIP Status Report | PDF/Excel | Pending (public records request) |
| Census tract boundaries | TIGER/Line 2023, Dallas city limits clip | Shapefile | Available |
| ACS 2023 5-year estimates | U.S. Census Bureau API (tables B03002, B19013, B01003) | CSV/API | Available |
| AMI reference figure (2023) | HUD FY2023 Income Limits, Dallas-Plano-Irving HUD Metro FMR Area | Published | Available: $89,800 |
| I-30 centerline geometry | TxDOT Roadway Inventory; OpenStreetMap | Shapefile/GeoJSON | Available |
| PID boundaries (future) | City of Dallas OED; Texas Secretary of State (HOA registrations) | Various | Planned Layer 1 |
| TIF district boundaries (future) | Dallas Development Services | Shapefile | Available for future chapter |

---

## 5. Variable Construction

### 5.1 CIP Investment Per Capita (Dependent Variable)

CIP dollars will be allocated to census tracts using a **dual proration method** that reflects the geometry of the underlying infrastructure:

- **Point and polygon projects** (parks, recreation centers, libraries, public safety facilities): Assignment uses **centroid-in-polygon** — the full project budget is credited to the tract containing the project's geographic centroid.
- **Linear infrastructure projects** (roads, drainage corridors, utility lines): Assignment uses **line-length proration** — the project budget is distributed across all intersected tracts proportional to the share of total project line length falling within each tract. Formally: *Allocation_i = Budget × (Length_i / ΣLength_j)*, where *i* indexes the tract and *j* indexes all tracts intersected by the project.

*v0 limitation:* The current version approximates all projects with point centroids. True line proration requires the geocoded line geometry of each CIP project, which is available through the Dallas Public Works GIS export but has not yet been obtained. The v0–v1 upgrade to line proration is expected to shift budget totals materially for drainage and streets projects that span multiple tracts.

The raw CIP dollar amount will be divided by tract population (ACS 2023 total population, Table B01003) to produce the primary dependent variable: **log(CIP per capita)**. The log transformation addresses right-skew in the distribution of investment amounts. For tracts with CIP investment of zero, see the hurdle model treatment in Section 6.

### 5.2 Race and Ethnicity Variables

Three race/ethnicity predictors will be constructed from ACS Table B03002 (Hispanic or Latino origin by race):

- `pct_black`: Non-Hispanic Black alone population as share of total tract population
- `pct_hispanic`: Hispanic or Latino population (any race) as share of total tract population
- `pct_nonwhite`: Combined non-Hispanic Black + Hispanic as share of total tract population

Models will be estimated with each variable separately and jointly. The theoretical motivation for this dual-track approach is that Black and Hispanic communities in Dallas occupy **distinct spatial geographies** and may have experienced different municipal investment histories. South Dallas (Bonton, Frazier Courts, Ideal) is majority Black; Oak Cliff (North, East, and West), Pleasant Grove, and the Lancaster corridor are majority Hispanic. An investment gap that appears only for `pct_black` would suggest different allocation dynamics than one appearing for `pct_hispanic`, and jointly significant coefficients would support a more generalized claim about non-white communities. Running models both ways also reduces the risk that a combined nonwhite measure masks divergent patterns.

### 5.3 Income Controls

No income threshold will be applied to exclude tracts from the sample. Truncating the sample at an income cutoff (e.g., excluding tracts above 120% AMI) would introduce selection bias by removing exactly the high-investment, high-income northern tracts that define the comparison group's upper end. Instead:

- `median_income`: Tract median household income from ACS Table B19013, entered as a continuous predictor. The model includes `log(median_income)` to account for the diminishing-returns relationship between income and CIP investment.
- `ami_ratio`: Tract median income expressed as a percentage of the Dallas-Plano-Irving HUD Metro Area Median Income (2023 AMI = $89,800). This variable contextualizes each tract's income relative to regional affordability norms. Tracts below 80% AMI (~$71,840) will be flagged in descriptive tables as **cost-burdened communities** for narrative purposes, but the 80% threshold is not used as a sample boundary.

### 5.4 CIP Category Fixed Effects

Each CIP project is classified into one of six functional categories:

1. Streets / Transportation
2. Drainage / Flood Control
3. Parks / Recreation
4. Public Safety / Facilities
5. Libraries / Culture
6. Utilities / Water

Category fixed effects are included in the regression models to absorb spending-logic heterogeneity. The reasoning: street investment may plausibly follow traffic volume or pavement condition indices (relatively objective criteria); drainage investment may follow FEMA flood risk maps; parks and libraries investment is most discretionary and most susceptible to political economy dynamics. The theoretical prediction is that the race coefficient will be **largest in magnitude for categories 3–5** (discretionary) and smallest for categories 1–2 (need-driven), providing a within-model test of the structural argument.

---

## 6. Analytical Strategy

### 6.1 Descriptive Analysis

Prior to regression, the memo documents a descriptive comparison of mean per-capita CIP investment across four quadrants defined by the I-30 divide and majority-race classification (majority-white north, majority-white south, majority-Black south, majority-Hispanic south). Maps will visualize the spatial distribution of cumulative investment density across the 14-year window alongside ACS demographic variables.

### 6.2 Spatial Autocorrelation Check (Moran's I)

Census tract data is spatially structured: tracts that are geographically adjacent tend to share similar characteristics. When residuals from a regression are also similar for neighboring tracts — a condition called **spatial autocorrelation** — standard regression assumptions are violated and standard errors may be underestimated.

To test for this, the analysis will compute **Moran's I** on the H1 residuals. Moran's I is a statistic that ranges from −1 (perfect dispersion: every neighbor is different) through 0 (no spatial pattern) to +1 (perfect clustering: every neighbor is similar). In plain language: Moran's I asks, "Do tracts that got more investment tend to be surrounded by other tracts that also got more investment?" If the answer is yes and the statistic is statistically significant (p < 0.05), it means the residuals are spatially clustered rather than randomly distributed, and this needs to be acknowledged.

**Decision rule:** If Moran's I is significant, the analysis will (1) report OLS estimates with **HC3 heteroskedasticity-consistent robust standard errors** as the primary specification, and (2) note spatial autocorrelation as a limitation requiring a spatial lag or spatial error model in v2. A full spatial econometric model (e.g., spatial lag via the `spdep` package in R or `PySAL` in Python) is methodologically appropriate but exceeds the scope of a v0/v1 undergraduate thesis. Reporting OLS with robust SEs and being transparent about the limitation is the correct approach at this stage.

### 6.3 Hurdle Model for Zero-Inflated CIP Investment

A substantial proportion of Dallas census tracts may report zero CIP investment in any given bond cycle — particularly in the study zone. Treating zeros as simply low investment would conflate two qualitatively different conditions: (a) a tract that received no investment and (b) a tract that received some investment but less than the city average. The thesis's theoretical claim is most directly tested by separating these: the argument is not merely that south-of-I-30 tracts get *less*, but that they are systematically *excluded from the allocation pool in the first place*.

To address this, the analysis uses a **two-part hurdle model**:

**Part 1 — Probit (Who gets investment?):** A binary variable coded 1 if the tract received any CIP investment during the study window, 0 if not. Predictors include `pct_nonwhite`, `log(median_income)`, `south_of_i30` (binary indicator), and CIP category fixed effects. In plain language: *first, we ask WHO gets investment at all*.

**Part 2 — OLS among funded tracts (How much?):** Conditional on investment > 0, the dependent variable is `log(CIP per capita)`. Same predictors. In plain language: *then, among those who got something, we ask HOW MUCH they got*.

This structure maps directly onto the thesis's theoretical claim: disinvestment in communities of color operates through both exclusion from the allocation pool and undersizing of awards within the pool. The two-part model makes both mechanisms visible and testable independently.

*Note:* A **Tobit model** is theoretically appropriate for a censored dependent variable (left-censored at zero) and would be a single-equation alternative to the two-part model. However, Tobit requires maximum likelihood estimation and interpreting marginal effects at the censoring boundary, which introduces interpretive complexity at the undergraduate level. The two-part OLS/Probit approach is more transparent, produces directly interpretable coefficients, and is more appropriate for a learning-demonstrating thesis. The Tobit comparison will be flagged as a v2 robustness check.

---

## 7. Theoretical Framework & Mechanistic Claim

The thesis does not claim that Dallas officials intentionally discriminated against Black or Hispanic neighborhoods in CIP allocation. The claim is **structural, not intentional**: CIP investment follows ostensibly neutral administrative criteria — traffic counts, pavement condition indices, council district requests, flood risk scores — but those criteria were themselves produced by decades of racially differential maintenance investment, exclusionary zoning, and redlining. Neutrally applying a degraded infrastructure baseline to degraded infrastructure reproduces the original inequality. This is the mechanism of **structural path dependence**.

The theoretical vocabulary for this claim is "facially neutral, racially disparate in effect" — a standard drawn from disparate impact doctrine in fair housing law. The thesis applies this framework to public investment rather than to discrete housing transactions.

Three anchoring texts inform this argument:

- **Rothstein (2017), *The Color of Law***: Documents the federal and municipal government's affirmative role in constructing residential segregation, providing the historical foundation for why South Dallas neighborhoods arrived at the present moment with degraded infrastructure baselines.
- **Dantzler (2022), investment-displacement paradox**: Establishes that public investment in historically divested communities can accelerate rather than prevent displacement by raising land values without commensurate protections for existing residents — directly relevant to the thesis's subtitle ("reinforces displacement risk").
- **Self (2003), *American Babylon***: Documents infrastructure investment as a mechanism of spatial exclusion in postwar Oakland, providing a comparative urban case that generalizes the Dallas argument and establishes the historiographic tradition within which the thesis sits.

The thesis's contribution is to formalize these theoretical arguments into a testable, spatially explicit empirical model applied to a specific city and a specific investment mechanism.

---

## 8. Comparison Baseline & Investment Gap Metric

A finding that South Dallas received less per-capita CIP investment than North Dallas is necessary but not sufficient to support the thesis. High-income areas often have newer infrastructure requiring less reinvestment; low-income areas with older and more degraded infrastructure have higher marginal need per dollar. The relevant question is whether south-of-I-30 tracts received less than a **needs-proportional allocation** would predict.

**Operational definition of "equitable" baseline:** A tract's fair share of CIP dollars equals its proportional share of total citywide need, where need is **inversely proportional to tract median household income** (lower income = higher need weight). Formally:

> Expected_i = (Need_i / Σ Need_j) × Total_CIP_Budget
>
> where Need_i = 1 / median_income_i

The **investment gap** for each tract is then:

> Gap_i = Actual_i − Expected_i

Negative values indicate underinvestment relative to need; positive values indicate overinvestment. This gap measure becomes the dependent variable for the normative version of H1 alongside the standard per-capita regression.

This baseline is acknowledged as a working operationalization, not a definitive normative standard. Alternative need metrics — infrastructure condition ratings, poverty rates, population density — would each produce a different expected allocation and a different gap estimate. The sensitivity of the gap measure to alternative baseline definitions will be reported in the appendix as a robustness check.

---

## 9. Planned Extensions

### 9.1 DFW Metropolitan Comparison Panel

A metroplex-level comparison panel will test whether the I-30 investment gradient is a Dallas-specific phenomenon or a regional pattern common to major DFW municipalities. Candidate cities: Fort Worth, Arlington, Garland, Irving. The panel would apply the same CIP allocation and gap methodology to each city's bond program during a comparable time window, using ACS demographic data clipped to each city's boundary. The key estimand is whether the race-investment correlation is a feature of Dallas's particular political economy or a broadly reproducible pattern of metropolitan governance. *Status: Planned for v2.*

### 9.2 PID/HOA Private Capital Overlay

Public Improvement Districts (PIDs) represent a mechanism by which property owners in a defined area levy supplemental assessments on themselves to fund enhanced infrastructure and services. In practice, PIDs are concentrated in North Dallas commercial and residential corridors (e.g., Uptown, Knox-Henderson, Midtown) where property values are high enough to sustain the assessment structure. In South Dallas, PIDs are largely absent.

This asymmetry is directly relevant to the thesis's displacement argument: if PIDs effectively **double the public infrastructure budget** in affluent northern corridors while providing no supplemental capital in southern communities, then the true capital allocation gap is substantially larger than CIP spending alone would suggest. The PID overlay will test whether the CIP investment gap identified in H1 is compensated by private capital in white neighborhoods and uncompensated in communities of color — directly addressing the full-stack character of the municipal investment architecture.

Data sources: City of Dallas Office of Economic Development (PID boundary files), Texas Secretary of State HOA registration records. *Status: Planned as Layer 1 of Chapter 2.*

### 9.3 True Line-Length Proration

As noted in Section 5.1, the v0 analysis approximates all CIP projects with point centroids. The v1 upgrade to true line-length proration for roads, drainage corridors, and utility projects requires obtaining the geocoded line geometry of each project from the Dallas Public Works GIS export. This upgrade is material for linear infrastructure, which constitutes a large share of both bond programs by dollar value. *Status: Pending public records request to Dallas Public Works.*

---

## 10. Limitations & Transparency Notes

1. **Expenditure vs. authorization:** Bond authorization amounts and actual CIP expenditures can diverge. The v0 analysis uses allocation/authorization figures. True expenditure data, tagged to fiscal year, is needed for v1 and will be sought via public records request.

2. **Centroid assignment error:** The centroid-in-polygon rule for linear projects introduces systematic measurement error for projects that cross tract boundaries. Tracts at the project origin or terminus receive 100% of the allocation when the true allocation might be shared. Line-length proration (see §9.3) will correct this.

3. **Ecological inference limitation:** The analysis uses tract-level aggregates. Coefficients on `pct_black` or `pct_hispanic` describe associations at the tract level; they do not establish that individual Black or Hispanic households received less investment. Readers should interpret findings as aggregate distributional patterns, not individual-level effects.

4. **AMI baseline sensitivity:** The Dallas MSA AMI figure used here ($89,800, FY2023 HUD) reflects the broader metro area median, which is pulled upward by high-income suburbs. A city-only income baseline would produce a different AMI ratio for each tract and a different set of "cost-burdened" flags. The sensitivity of results to this choice will be documented.

5. **Spatial autocorrelation:** As described in §6.2, if Moran's I is significant on H1 residuals, the OLS standard errors will be downward-biased. HC3 robust SEs provide a partial correction but do not fully address spatial dependence. A spatial lag or spatial error model is the correct long-run solution and is planned for v2.

6. **Council district confounding:** CIP allocation in Dallas is substantially shaped by council district boundaries and individual council member priorities. Council district fixed effects are not included in the primary specification because they partially mediate rather than confound the race-investment relationship (many south-of-I-30 districts are represented by council members of color who have faced structural budget constraints). Sensitivity models with council district FEs will be estimated and reported.

7. **Omitted capital mechanisms:** CIP is one component of Dallas's municipal investment architecture. TIF district subsidies, Opportunity Zone investments, NEZ property tax abatements, and federal Community Development Block Grant (CDBG) allocations are not included in this chapter. The thesis explicitly frames H1 as an entry point, not a complete accounting of capital flows.

---

## 11. Next Steps Before H1 Is Publishable

The following tasks must be completed before the empirical chapter is ready for committee review:

1. **Public records request — CIP expenditures:** Submit formal request to the Dallas Office of Financial Services for project-level CIP expenditure data by fiscal year, FY2012–FY2026. The CAFR alone does not disaggregate spending to individual projects.

2. **Public records request — CIP line geometries:** Submit request to Dallas Public Works GIS division for project-level line geometry files (shapefiles or GeoJSON) to enable line-length proration in v1.

3. **Census tract boundary clipping:** Download TIGER/Line 2023 tract shapefile and clip to Dallas city limits using the city boundary polygon. Identify and resolve any boundary tracts with centroids outside the city that should be included or excluded.

4. **I-30 centerline geometry:** Download the TxDOT roadway inventory or OpenStreetMap centerline for I-30 within Dallas County. Assign the `south_of_i30` binary indicator to each tract based on centroid position relative to the I-30 centerline. Spot-check 10–15 boundary tracts manually.

5. **ACS data pull and cleaning:** Query the Census API for ACS 2023 5-year estimates (Tables B03002, B19013, B01003) for all Dallas tracts. Compute `pct_black`, `pct_hispanic`, `pct_nonwhite`, `median_income`, and `ami_ratio` variables. Document any suppressed cells or margin-of-error issues for small tracts.

6. **CIP project dataset assembly and classification:** Once raw CIP project data is obtained, classify all projects into the six category fixed-effect groups. Resolve ambiguous classifications (e.g., a "multimodal corridor" that includes streets, drainage, and parks elements) by consulting project scope-of-work descriptions.

7. **v0 OLS specification:** Run initial OLS models on the assembled dataset using point-centroid allocation. Report coefficient estimates, HC3 robust standard errors, and Moran's I on residuals. Use this output to finalize the hurdle model specification for v1.

8. **Committee submission:** Circulate revised Methods Memo v2 incorporating v1 data and v0 regression results. Schedule methods review session with thesis advisor.

---

*Methods Memo v1 — Displacement Defense Atlas*  
*Nicholas D. Hawkins | Texas Southern University, Freeman Honors College*  
*Version 1 — drafted 2025*

*References:*  
- Rothstein, R. (2017). *The Color of Law: A Forgotten History of How Our Government Segregated America*. Liveright.  
- Dantzler, P. (2022). The urban process under racial capitalism: Race, anti-Blackness, and capital accumulation. *Journal of Race, Ethnicity and the City*, 2(2), 113–134. https://doi.org/10.1080/26884674.2021.1934201  
- Self, R. O. (2003). *American Babylon: Race and the Struggle for Postwar Oakland*. Princeton University Press.  
- U.S. Census Bureau. (2023). American Community Survey 5-Year Estimates. https://www.census.gov/programs-surveys/acs  
- HUD. (2023). FY2023 Income Limits. https://www.huduser.gov/portal/datasets/il.html  
- City of Dallas. (2024). Capital Improvement Program. https://dallascityhall.com/departments/budget/Pages/capital-improvement-program.aspx

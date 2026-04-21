# Displacement Defense Atlas
## Below the Line: Dallas I-30 Corridor Displacement Risk

**Author:** Nicholas Donovan Hawkins  
**Institution:** Texas Southern University  
**Degree:** B.A. General Studies  
**Advisor:** [TBD]  
**Thesis Due:** December 15, 2027  

---

### Research Question

Does Dallas's municipal investment infrastructure — capital improvement projects, tax increment finance districts, and Opportunity Zones — systematically underserve communities of color south of I-30, and does this pattern reflect the structural legacy of HOLC redlining?

### Hypotheses

| # | Hypothesis Name | Research Claim | Primary Analysis |
|---|----------------|----------------|-----------------|
| H1 | Investment Bias | Public capital investment is systematically skewed away from majority non-white tracts, independent of income and density. | OLS regression: CIP $/capita ~ % non-white, controlling for median income & population density |
| H2 | Redlining Legacy | Contemporary disinvestment patterns in Dallas trace directly to HOLC-era grade designations, with measurable economic residue persisting across generations; speculative investor activity concentrates along TIF/OZ boundaries and reinforces these spatial inequities. | HOLC grade spatial join; vendor geocode analysis quantifying economic residue by geography ($485M North vs. $38M South); t-test comparing Grade A–B vs. C–D tracts; buffer analysis around TIF/OZ boundaries and kernel density estimation of investor purchase clustering |
| H3 | Three Moves Diagnostic | Displacement risk in Dallas follows a three-part structural sequence — property market pressure, credit denial, and neighborhood typology — detectable through integrated parcel, lending, and demographic data. | PID spatial join + Bates typology classification + HMDA denial rates (CFPB 2023 primary data: 625 tracts, 12,300 denials); South/North denial rate ratio 1.19× with Black share decomposition accounting for 20.7% of the gap |
| H4 | Defense Gap | Tracts with high displacement risk and low community defense capacity represent acute crisis zones requiring targeted intervention. | Bivariate scatter: Displacement Risk Index (DRI) × Community Defense Score (CDS); quadrant classification identifying high-risk, low-defense crisis zones |
| H5 | I-30 Divide | The I-30 corridor functions as a hard spatial discontinuity in displacement exposure, producing a measurable treatment effect on outcomes north vs. south of the highway. | Regression discontinuity design (RDD) across the I-30 corridor |
| H6 | Bates Typology v2.1 | Dallas neighborhoods can be classified into discrete displacement stages — Early, Dynamic, and Late — using a decade-long longitudinal panel of pressure and vulnerability indicators, enabling prospective rather than retrospective risk assessment. | ACS 2013→2023 longitudinal panel (CPI-adjusted); Pressure × Vulnerability scatter; displacement stage classification (Early / Dynamic / Late); 4-panel diagnostic output |

> **Numbering note:** H3 was redesignated from *Investor Capture* to *Three Moves Diagnostic* to reflect the operational analytical approach actually implemented — integrating parcel data, Bates typology classification, and HMDA denial-rate decomposition — while the original Investor Capture work (TIF/OZ buffer analysis and investor purchase kernel density) is retained as a supporting component of H2's Redlining Legacy analysis. H6 (*Bates Typology v2.1*) was added as the longitudinal displacement staging component, providing the prospective classification framework that bridges the cross-sectional findings of H1–H5 into a policy-actionable typology.

### Atlas Versions

| Version | Phase | Target Date | Status |
|---------|-------|-------------|--------|
| v0 | Foundation (3-map prototype) | May 2026 | 🟡 In Progress |
| v1 | Full DRI + CDS + 5 hypothesis maps | Aug 2026 | ⬜ Planned |
| v2 | Statistical models + Ch. 4–5 draft | Dec 2026 | ⬜ Planned |
| v3 | Public StoryMap + policy brief | Summer 2027 | ⬜ Planned |

### Repository Structure

```
displacement-defense-atlas/
├── data/
│   ├── raw/
│   │   ├── layer1_investment/      # CIP, TIF, OZ, PID
│   │   ├── layer2_mechanism/       # HMDA, permits, rent burden
│   │   ├── layer3_early_warning/   # HOLC, LTDB, UDP typology
│   │   └── layer4_readiness/       # CLT, LIHTC, CDFI
│   ├── processed/                  # Harmonized GeoJSON & CSVs
│   └── exports/                    # Publication-ready tables
├── scripts/
│   ├── pipeline/                   # Data acquisition & harmonization
│   └── analysis/
│       ├── h1_investment_bias/
│       ├── h2_redline_legacy/
│       ├── h3_investor_capture/
│       ├── h4_defense_gap/
│       └── h5_i30_divide/
├── notebooks/                      # Exploratory analysis
├── maps/
│   ├── v0/                        # Atlas v0 HTML + PNG outputs
│   └── v1/
├── outputs/
│   ├── figures/
│   ├── tables/
│   └── memos/                     # Methods memos, write-ups
├── docs/
│   ├── methods/                   # Methods documentation
│   └── variable_dictionary/
└── storymap/                      # ArcGIS StoryMap assets
```

### Data Sources

| Layer | Dataset | Source |
|-------|---------|--------|
| Investment | ACS 5-Year (2018–2023) | U.S. Census Bureau |
| Investment | Dallas CIP Projects | City of Dallas Open Data |
| Investment | TIF District Boundaries | Dallas OED |
| Investment | Opportunity Zone Designations | CDFI Fund / Treasury |
| Mechanism | HMDA Neighborhood Summary | Urban Institute |
| Mechanism | Dallas Building Permits | Dallas Open Data |
| Early Warning | HOLC Redlining Maps | Mapping Inequality (U. Richmond) |
| Early Warning | Longitudinal Tract Database | Brown University |
| Readiness | LIHTC Project Database | HUD |
| Readiness | CDFI & Nonprofit Locations | CDFI Fund / IRS |

### Citation

Hawkins, N.D. (2027). *Below the Line: How Dallas's Municipal Investment Architecture Reinforces Displacement Risk South of I-30.* Undergraduate Thesis, Texas Southern University.

---

*For academic and research use only. Data pipeline: Python/GeoPandas. Visualization: Folium, Matplotlib, ArcGIS Pro.*

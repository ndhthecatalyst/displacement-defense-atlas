# Displacement Defense Atlas
## Below the Line: Dallas I-30 Corridor Displacement Risk

**Author:** Nicholas Donovan Hawkins  
**Institution:** Texas Southern University — Freeman Honors College  
**Degree:** B.S. Political Science / Economics  
**Advisor:** [Committee TBD]  
**Thesis Due:** December 15, 2027  

---

### Research Question

Does Dallas's municipal investment infrastructure — capital improvement projects, tax increment finance districts, and Opportunity Zones — systematically underserve communities of color south of I-30, and does this pattern reflect the structural legacy of HOLC redlining?

### Hypotheses

| # | Hypothesis | Analysis |
|---|------------|----------|
| H1 | Investment Bias | OLS: CIP$/capita ~ % non-white, controlling for income & density |
| H2 | Redlining Legacy | HOLC grade spatial join; t-test between Grade A–B vs C–D tracts; DRI prototype |
| H3 | Investor Capture | Buffer analysis around TIF/OZ boundaries; kernel density of investor purchases |
| H4 | Defense Gap | Bivariate scatter: DRI × CDS; identifies crisis zones |
| H5 | I-30 Divide | Regression discontinuity design across I-30 corridor |

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

Hawkins, N.D. (2027). *Below the Line: How Dallas's Municipal Investment Architecture Reinforces Displacement Risk South of I-30.* Undergraduate Honors Thesis, Texas Southern University Freeman Honors College.

---

*For academic and research use only. Data pipeline: Python/GeoPandas. Visualization: Folium, Matplotlib, ArcGIS Pro.*

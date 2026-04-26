# Displacement Defense Atlas
## Below the Line: Development as Governance and the Geography of Displacement Risk in Dallas

**Author:** Nicholas Donovan Hawkins
**Institution:** Texas Southern University · Thomas F. Freeman Honors College
**Degree:** B.A. General Studies
**Advisor:** [TBD]
**Thesis Due:** December 15, 2027
**Architecture Version:** v5 (April 2026) — *Five-Layer Capital Stack*

---

### Research Question (v5)

Does Dallas's municipal investment architecture — operationalized as the full capital stack comprising CIP public investment, PID/HOA private supplementation, TIF/OZ financial engineering, institutional investor ownership patterns, and vendor economic residue — systematically direct capital returns away from majority-Black and Hispanic communities south of I-30, reproducing displacement through the racially constructed category of *investability* rather than through any single discriminatory policy?

The original (v0) question asked *who lives near* a road project. The v5 correction is to ask *who captures the economic returns* of public capital. Displacement is treated as the output of a governance design, not a market failure.

### The Five-Layer Capital Stack

| Layer | Mechanism | Headline finding |
|-------|-----------|------------------|
| **1. CIP** (public base) | Capital Improvement Program allocation | $984M FY2012–2026; discretionary categories skewed north |
| **2. PID/HOA** (private supplementation) | Public Improvement Districts + HOA assessments | Downtown $13.5M/yr vs South Side $411K/yr (**33× gap**) |
| **3. TIF/OZ** (financial engineering) | Tax Increment Finance + Opportunity Zones | Downtown TIF $8.83B vs Grand Park South $333M (**26:1**) |
| **4. Institutional SFR** (ownership) | Mega-investor single-family rental capture | 26,961 units in DFW; 3× national avg in Black neighborhoods |
| **5. Vendor Residue** (contracting) | Where public dollars go after they are spent | South 2.6% ($38.3M) vs North 25.3% ($369.2M) = **12.6× gap** |

### Hypotheses (v5)

| # | Layer | Hypothesis | Primary Analysis |
|---|-------|------------|------------------|
| **H1** | Layer 1 (CIP) | CIP investment per capita, after controlling for income and infrastructure need, is significantly lower in majority-Black and Hispanic tracts south of I-30, with the gap largest in discretionary spending categories (parks, libraries, economic development). | OLS: CIP $/capita ~ % non-white + controls; M7 result: HOLC-D β = +247.6 (p<0.001); race becomes insignificant when HOLC grade is controlled. |
| **H2** | Layer 5 (Vendor Residue) | Tracts that lack PID coverage, TIF district inclusion, and institutional investor activity also receive disproportionately low economic residue from public vendor contracting — the absence of all five layers compounds in Black communities while the presence of all five compounds in wealthy white communities. | Vendor geocode of 145,551 payment rows; top-18 vendor analysis: South 2.6% vs North 25.3% ($369.2M / $38.3M = 12.6×); 83% of $108.8M South CIP spend extracted northward. |
| **H3** | Layers 2 + 4 (PID × SFR) | The capital-stack exposure score is a better predictor of displacement stage (Bates/UDP typology) than any single investment variable. The interaction of Layer 2 absence (no PID) and Layer 4 presence (institutional investor activity) predicts the *Dynamic Gentrification* and *Historic Loss* stages with the highest accuracy. | PID spatial join + SFR ownership + Bates typology classification; HMDA 1.19× South/North denial ratio (CFPB 2023, 12,300 denials, 625 tracts). |
| **H4** | Layer 3 (TIF/OZ — inverted gap) | Zero Susceptible South Dallas tracts have received TIF or OZ investment, producing a population of *HIGH_PRESSURE_LOW_READINESS* crisis tracts where displacement pressure is rising without any public readiness response. | Readiness Index (50/30/20 weighting); 385 tracts matched ACS 2013↔2023 (LTDB crosswalk, CPI +36%); **54 Susceptible South tracts, 0 with TIF or OZ; 44 HIGH_PRESSURE_LOW_READINESS**; 14 immediate priority (readiness ≤ 0.028): 170.09 (D8), 64.02 (D1), 91.03 (D5), 170.07 (D8), 92.02 (D5). |
| **H5** | Political recirculation | The capital stack recirculates through political financing at the state and federal level, not through direct municipal contributions — routed via PACs, board interlocks, and foreign parent corporations. | TEC + FEC + Dallas CFR analysis: zero direct corporate contributions to Dallas City Council from top-18 vendors; **Tan Parker (TX HD-63) sits on the Board of Southland Holdings** (parent of Oscar Renda, $26.5M in Dallas contracts); BAR Constructors + Archer Western jointly funded "Texans for Opportunity" PAC (TX Prop 4); **$58.9M — 15¢ of every top-vendor dollar — flows to Texas Materials Group, owned by CRH plc (Irish corp)**. |
| **H6** | Longitudinal staging | Dallas neighborhoods can be classified into discrete displacement stages — Early, Dynamic, and Late — using a decade-long longitudinal panel of pressure and vulnerability indicators, enabling *prospective* rather than retrospective risk assessment. | ACS 2013→2023 longitudinal panel (CPI-adjusted); Pressure × Vulnerability scatter; 4-panel diagnostic; South Dallas home values +120.5% vs North +111.3%; real income +8.6% vs +17.1%. |

> **Numbering note.** H1 carries the v0 question forward in its revised form; H2 reframes v4's "Redlining Legacy" around vendor residue (Layer 5) per v5's capital-return pivot. H3 is the v5 capital-stack composite. H4 (readiness/TIF-OZ gap), H5 (political recirculation), and H6 (Bates longitudinal staging) were added in the April 2026 pre-writing sprint and retained under the v5 architecture. The earlier v4 labels (H3 *Investor Capture*, H4 *Defense Gap*, H5 *I-30 Divide*) are retired; the Investor Capture work is folded into H3 Layer 4, and the I-30 discontinuity test is retained as a robustness check inside H1.

### Atlas Versions

| Version | Phase | Target Date | Status |
|---------|-------|-------------|--------|
| v0 | Foundation (3-map prototype) | May 2026 | 🟡 In Progress |
| v1 | Full capital-stack exposure score + all layer maps | Aug 2026 | ⬜ Planned |
| v2 | Statistical models + Ch. 4–5 draft | Dec 2026 | ⬜ Planned |
| v3 | Public StoryMap + policy brief | Summer 2027 | ⬜ Planned |

### Repository Structure

```
displacement-defense-atlas/
├── data/
│   ├── raw/
│   │   ├── layer0_boundaries/       # Council districts, TIGER tracts
│   │   ├── layer1_investment/       # CIP projects + bond programs + vendor payments
│   │   ├── layer2_mechanism/        # PID boundaries + assessments
│   │   ├── layer3_tif_oz/           # TIF subdistricts + OZ designations + ground-truth ledger
│   │   ├── layer3_early_warning/    # ACS / HMDA / HOLC inputs (legacy name; keeps current scripts working)
│   │   └── layer4_readiness/        # LIHTC, HUD Picture, NEZ, council, HCAs, community orgs
│   ├── processed/                   # Harmonized GeoJSON & CSVs
│   └── exports/                     # Publication-ready tables
├── scripts/
│   ├── pipeline/                    # Data acquisition & harmonization
│   └── analysis/
│       ├── h1_investment_bias/      # Layer 1 — CIP allocation
│       ├── h2_vendor_residue/       # Layer 5 — vendor extraction
│       ├── h3_pid_bates_hmda/       # Layers 2+4 — composite stack
│       ├── h4_readiness/            # Layer 3 — TIF/OZ gap + readiness index
│       ├── h5_political/            # Political recirculation (TEC/FEC)
│       └── h6_bates_longitudinal/   # Displacement staging
├── notebooks/                       # Exploratory analysis
├── maps/
│   ├── v0/                          # Atlas v0 HTML + PNG outputs
│   └── v1/
├── outputs/
│   ├── figures/
│   ├── tables/
│   └── memos/                       # Methods memos, write-ups
├── docs/
│   ├── theory/                      # Theoretical framework
│   │   ├── five_layer_capital_stack.md
│   │   └── theoretical_framework_v1.md
│   ├── methods/                     # Methods documentation
│   ├── variable_dictionary/         # Variable dictionary
│   └── bibliography.bib             # 47-source bibliography
└── storymap/                        # ArcGIS StoryMap assets
```

### Data Sources

| Layer | Dataset | Source |
|-------|---------|--------|
| L1 — CIP | ACS 5-Year (2018–2023, 2013) | U.S. Census Bureau |
| L1 — CIP | Dallas CIP Projects + Bond Programs (2012/2017/2024) | City of Dallas Open Data |
| L2 — PID | Dallas PID Boundaries | Dallas GIS Hub (`215f5e7243d44c25b7e503e3dafe73da`, `16a1eb7a28f143ffb3714435ffac740a`) |
| L2 — PID | PID Annual Assessments | Dallas OED + individual PID reports |
| L3 — TIF/OZ | TIF Subdistrict Boundaries | [Dallas GIS Hub item `867cb869d7764aeda0832f8af3512b02`](https://gisservices-dallasgis.opendata.arcgis.com/maps/867cb869d7764aeda0832f8af3512b02) |
| L3 — TIF/OZ | TIF District Boundaries + Annual Increment | Dallas County 2025 TIF Annual Report; Dallas OED |
| L3 — TIF/OZ | Opportunity Zone Designations | [HUD Open Data layer `ef143299845841f8abb95969c01f88b5_13`](https://hudgis-hud.opendata.arcgis.com/datasets/ef143299845841f8abb95969c01f88b5_13); cross-checked against IRS Notice 2018-48 |
| L3 — TIF/OZ | QOF Investment by Tract | IRS Form 8996; Dallas OED announcements; Novogradac OZ Investment Tracker; SEC EDGAR (publicly-traded QOFs) |
| L3 — TIF/OZ | OZ ground-truth validation ledger | Manual curation — see `data/raw/layer3_tif_oz/README.md` |
| L4 — SFR | Institutional SFR Ownership | CoreLogic / ATTOM / PropStream; Immergluck et al. |
| L5 — Vendor | Dallas Vendor Payments (FY2019–present, 145,551 rows) | Dallas Open Data |
| L5 — Vendor | Vendor Geocoding (ZIP5, 8,354 unique vendors) | Derived — this project |
| Causal warrant | HOLC Redlining Maps | Mapping Inequality (U. Richmond) |
| Longitudinal | Longitudinal Tract Database (2013↔2023 crosswalk) | Brown University |
| Mechanism | HMDA Loan-Level Data | CFPB HMDA Explorer |
| Mechanism | Dallas Building Permits | Dallas Open Data |
| Readiness | LIHTC Project Database | HUD |
| Readiness | HUD Picture of Subsidized Households | HUD |
| Readiness | Neighborhood Empowerment Zones (NEZ) | City of Dallas |
| Political | Campaign Contributions (state) | Texas Ethics Commission bulk data (`https://prd.tecprd.ethicsefile.com/public/cf/public/TEC_CF_CSV.zip`) |
| Political | Campaign Contributions (federal) | FEC |
| Political | Campaign Contributions (municipal) | `campfin.dallascityhall.com` |

### Scholarly Apparatus

Bibliography: `docs/bibliography.bib` (47 sources, Chicago author-date + BibTeX). Six required theoretical anchors are verified:

- **Aaronson, Hartley & Mazumder (2021)** — HOLC redlining causality
- **Fullilove (2004)** *Root Shock* — serial forced displacement
- **Dantzler (2021)** — racial capitalism and urban process
- **Logan & Molotch (1987)** *Urban Fortunes* — growth machine
- **Wyly & Hammel (2004)** — TIF, gentrification, segregation
- **Rothstein (2017)** *The Color of Law* — de jure segregation

11 Dallas-specific sources including Schutze (1987) *The Accommodation*, Dallas City Auditor TIF Audit (2025), and a TWU thesis on Black Dallas displacement 1943–1983.

### Citation

Hawkins, N. D. (2027). *Below the Line: Development as Governance and the Geography of Displacement Risk in Dallas.* Undergraduate Thesis, Texas Southern University, Thomas F. Freeman Honors College.

---

*For academic and research use only. Data pipeline: Python/GeoPandas. Spatial statistics: PySAL / esda. Regression: statsmodels. Visualization: Matplotlib, Folium, Contextily, ArcGIS Pro.*

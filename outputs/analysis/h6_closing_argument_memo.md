# H6: Closing the Argument
## Bates Typology v2.1 (Real 2013→2023) + Vendor-Project Spatial Join
**Below the Line — Nicholas D. Hawkins | TSU Freeman Honors College**
**Commit:** h6-close-the-argument | April 21, 2026

---

## What This Commit Does

Closes two open gaps identified in the H5 self-assessment:

1. **Bates typology v2.1 with real longitudinal ACS data** — replaced proxy `demo_change` flag with actual 10-year change variables (2013→2023 ACS 5-year estimates). 385 of 645 tracts matched across both periods. CPI adjustment: 36% (BLS CPI-U 2013→2023).
2. **Vendor-project spatial join** — matched vendor HQ locations to CIP project sites, measuring the physical distance between where contracts originate and where that economic activity lands.

---

## Finding 1: Bates Typology v2.1 (Real 2013→2023 Change)

### South vs North Distribution

| Stage | South (n=185) | % | North (n=460) | % |
|-------|:---:|:---:|:---:|:---:|
| **Dynamic** | 1 | 1% | 3 | 1% |
| **Late** | 11 | 6% | 8 | 2% |
| Early: Type 1 | 8 | 4% | 5 | 1% |
| Early: Type 2 | 7 | 4% | 8 | 2% |
| **Susceptible** | **54** | **29%** | 68 | 15% |
| **Historic Loss** | 42 | 23% | **193** | **42%** |
| Stable | 62 | 34% | 175 | 38% |

**Matched tracts with real 2013 baseline:** 385 of 645 (60%)

### The Critical Number: 54 Susceptible Tracts in South Dallas

29% of South Dallas tracts are classified Susceptible — high vulnerability, not yet under full market pressure. These are the tracts most at risk of future displacement if investment patterns continue unchanged. North Dallas has already moved through this stage: 42% of North tracts show Historic Loss — displacement that has already completed its cycle.

South Dallas is not a static low-investment zone. It is an active displacement front where the mechanisms are in place but the displacement is still in process.

### Real 10-Year Change Variables (2013→2023, CPI-adjusted)

| Metric | South Dallas | North Dallas | Gap |
|--------|:---:|:---:|:---:|
| Nominal income change (median) | +44.6% | +53.1% | −8.5pp |
| **Real income change (CPI-adj)** | **+8.6%** | **+17.1%** | **−8.5pp real gap** |
| Home value change (median) | +120.5% | +111.3% | South rising faster |
| Demographic change signal | 36% of tracts | 22% of tracts | South more active |
| Renter share change (median) | 0.000 | −0.005 | Renter lock-in South |

The home value data is the most important signal. South Dallas home values rose 120.5% over 10 years — outpacing North Dallas's 111.3% — while real incomes grew at less than half the rate (8.6% vs 17.1%). This is the textbook precondition for displacement: asset values rising faster than resident incomes, compressing affordability before residents can build equity.

36% of South Dallas tracts show a confirmed demographic change signal (vs 22% North), meaning the population transition has already begun in more than a third of South tracts — even as 54 remain in the Susceptible pre-displacement stage.

### The Historic Loss Pattern

Historic Loss tracts show the widest income variance of any stage ($35K–$250K+ median). This is the signature of completed gentrification: formerly vulnerable communities that have been displaced and replaced with higher-income households. That 193 of these tracts (42%) concentrate in North Dallas tells you where the displacement cycle has already run its course.

South Dallas's 42 Historic Loss tracts are not evidence of stability — they are evidence of displacement that already occurred, likely in prior decades (1990s–2000s), before the current capital stack was fully assembled.

---

## Finding 2: Vendor-Project Spatial Mismatch

### Core Result

| Geography | Projects | Total $ Paid | Avg dist to vendor HQ |
|-----------|:---:|:---:|:---:|
| North of I-30 | 334 | $396.1M | 4.0 km |
| South of I-30 | 166 | $108.8M | 6.9 km |
| **North:South Ratio** | — | **3.64×** | **1.74×** |

North projects are served by vendors 4.0 km away. South projects are served by vendors 6.9 km away — **73% farther**. The vendors doing the work are not from the community being worked on.

### The 17% Number

Of the $108.8M paid for South Dallas CIP projects, only **$18.8M (17%)** went to vendors headquartered south of I-30. **$90M (83%) extracted northward** — out of the community being invested in.

This is the mechanism behind the 12.6× vendor residue gap documented in H2. It isn't just that South Dallas gets less investment. It's that even the investment it does receive is extracted by vendors whose economic presence, employment base, and tax nexus sits elsewhere.

### Category Breakdown

The spatial mismatch is worst in discretionary categories:
- **Erosion Control:** 2.9× more North spend than South
- **Aquatics:** 2.6×
- **City Facilities:** 2.3×
- **Economic Development:** 0.0× — no North equivalent (all spend concentrated in South)

Categories closer to parity (Storm Drainage, Fire Facilities) are those where geographic necessity overrides procurement discretion. Where discretion exists, the gap appears.

---

## Theoretical Synthesis: The Argument

The argument can now be stated precisely, with all layers of evidence in place:

Dallas's Capital Improvement Program deploys public bond dollars into South Dallas communities at a **3.64× lower rate** than North Dallas. When those dollars do arrive in South Dallas, **83% are immediately extracted** by vendors headquartered elsewhere — vendors who are 73% farther from the project site, whose employees, subcontractors, and supply chains are not embedded in the community. The remaining 17% that stays local goes largely to two Hispanic-owned firms (BAR Constructors, Camino Construction) that collectively represent less than 14% of top-vendor spend.

The Bates typology v2.1, built on real 2013→2023 change data, shows where this process stands: **54 South Dallas tracts (29%) are in the Susceptible stage** — maximum vulnerability, real incomes growing at half the North rate, home values rising 120% over 10 years, demographic transition already confirmed in 36% of tracts. These 54 tracts are the next displacement front. The pressure is arriving. The tools that could intervene — procurement reform, local vendor preference, community benefit agreements — are not deployed.

This is not market failure. It is governance design. The procurement system, operating without pay-to-play restrictions (Texas has none), has produced a structural outcome in which public investment in South Dallas generates private wealth for North Dallas and suburban firms — while the communities receiving the physical infrastructure capture almost none of the economic multiplier.

The H5 finding completes the circuit: water and school bond contractors fund the ballot measures that authorize their own contracts. Public capital is allocated, vendors are selected, economic residue flows north, political contributions flow back to secure the next cycle of authorization. The loop is closed.

---

## Capital Stack Summary (All Layers)

| Layer | Finding | Ratio |
|-------|---------|:---:|
| L1: CIP investment | $396.1M North vs $108.8M South | 3.64× |
| L2: PID/HOA supplemental | $13.5M/yr Downtown vs $411K/yr South | 33× |
| L3-TIF: Tax capture | $8.83B Downtown TIF vs $333M Grand Park South | 26× |
| L3-HMDA: Credit denial | 35.6% South denial rate vs 29.8% North | 1.19× |
| L4: Institutional SFR | 26,961 mega-investor units DFW-wide | — |
| L5: Vendor residue | 25.3% North economic multiplier vs 2.6% South | 12.6× (H2) / 83% extraction (H6) |
| H5: Political recirculation | Contractors fund ballot measures for own contracts | Loop closed |
| H6: Bates displacement front | 54 Susceptible South tracts, real income gap 8.5pp | Active front |

---

## Data Files

| File | Description |
|------|-------------|
| `outputs/tables/h6_bates_full_typology.csv` | 645 tracts, full v2.1 typology + all real change vars |
| `outputs/tables/h6_vendor_project_spatial_join.csv` | 500 CIP projects with nearest vendor HQ + distance |
| `outputs/tables/h6_vendor_hq_geocoded.csv` | Top 50 vendors with geocoded HQ locations |
| `data/raw/layer1_investment/CIP_Points_All_Bonds.csv` | 1,051 CIP projects with lat/lon (all 4 bond programs) |
| `data/raw/layer3_early_warning/acs5_2013_dallas_tracts.csv` | ACS 2013 5-yr, manually downloaded (Census API outage) |
| `data/raw/layer3_early_warning/acs5_2023_dallas_tracts.csv` | ACS 2023 5-yr, 645 Dallas County tracts |
| `outputs/figures/h6_vendor_spatial_mismatch.png` | 4-panel spatial mismatch diagnostic |
| `outputs/figures/h6_bates_typology_v21.png` | 3-panel real change Bates typology (v2.1) |
| `outputs/analysis/h6_closing_argument_memo.md` | This document |

---

## ACS 2013 Source Note

ACS 2013 data was manually downloaded from data.census.gov by Nicholas D. Hawkins on April 21, 2026 due to a Census API outage. Files: B19013 (median household income), B25077 (median home value), B25003 (tenure/renter share), B03002 (race/ethnicity). 385 of 645 Dallas County tracts matched between 2013 and 2023 vintage GEO_IDs.

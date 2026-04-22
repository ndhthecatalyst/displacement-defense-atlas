# H7 — HMDA Credit-Access Gap (Dallas County, 2022–2023)

## Question
Do the tracts flagged as highest-priority by the H4 readiness index (Susceptible
South, bottom-quartile civic infrastructure) also face elevated mortgage
denial rates — and does the Black/White denial disparity there exceed the
national benchmark?

## Data
- **CFPB HMDA Loan Application Register**, pulled via the Data Browser filtered
  CSV endpoint (`ffiec.cfpb.gov/v2/data-browser-api/view/csv`) for county FIPS
  48113, years 2022 + 2023 → 149,514 LAR records.
- Filtered to **conventional** (`loan_type == 1`) **home-purchase** applications
  (`loan_purpose == 1`) with **decisioned actions** (`action_taken ∈ {1, 2, 3,
  7, 8}`) → 42,111 applications across 622 tracts.
- Denial = `action_taken ∈ {3, 7}` (denied + pre-approval denied).
- Race flags use HMDA single-race coding:
  - Black alone: `applicant_race-1 == 3` with races 2–5 empty
  - White alone: `applicant_race-1 == 5` with races 2–5 empty
- Group-specific rates suppressed when tract n < 10 for stability.
- Tract geometries: TIGER/Line 2023 (`tl_2023_48_tract`).

## Headline results (Dallas County, 2022–2023)

| Metric                               | Value        |
|--------------------------------------|--------------|
| Total conv. home-purchase apps       | 42,111       |
| Overall denial rate                  | **13.28 %**  |
| Median tract denial rate             | 10.96 %      |
| Black denial rate (n = 3,795)        | **22.27 %**  |
| White denial rate (n = 22,545)       | 10.34 %      |
| **Black/White disparity ratio**      | **2.15×**    |

The Dallas County disparity is nearly double the widely-cited 1.19× national
benchmark and sits in line with published HMDA literature (Urban Institute
~2.4×; Structural Racism Index ~2.3×; LendingTree 1.7× in 2024).

## H4 → H7 bridge
Of the 14 highest-priority Susceptible South tracts (H4 readiness rank 1–14):

- **10 of 14 have denial rates above the county median** (10.96 %).
- Highest: tract 170.09 (49.3 %), tract 171.01 (45.5 %), tract 111.03 (38.9 %).
- Tract 59.01 — 58 % Black, 2.70× local Black/White disparity — is the
  cleanest single-tract illustration of the H4 → H6 → H7 displacement front
  (low civic readiness + Bates "Susceptible" + amplified credit-denial gap).

## Reproducibility
- `scripts/h7_hmda/analyze_hmda.py` — pulls CFPB CSVs, filters, aggregates tract
  metrics → `outputs/tables/h7_hmda_tract_denials_2022_2023.csv` and county
  summary.
- `scripts/h7_hmda/build_choropleth.py` — renders the sextile-binned denial-rate
  map with priority-14 overlay → `outputs/figures/h7_hmda_denial_rate_choropleth.png`.

## Outputs
- `outputs/tables/h7_hmda_tract_denials_2022_2023.csv` (622 tracts × 10 metrics)
- `outputs/tables/h7_hmda_county_summary_2022_2023.csv`
- `outputs/tables/h7_priority14_hmda_crossref.csv`
- `outputs/figures/h7_hmda_denial_rate_choropleth.png`

## Caveats
- "Denial rate" here excludes withdrawn and incomplete files; including them
  would lower rates but not materially change the Black/White ratio.
- Race is self-reported at application and missing for ~30 % of applications;
  the single-race "alone" filter is conservative.
- Pooling 2022 + 2023 smooths annual volatility driven by rate shocks but
  masks within-period trends — year-split table available on request.

# Canonical Facts — Displacement Defense Atlas

**Status:** Authoritative. This file is the single source of truth for all numeric claims.
**Owner:** Nicholas D. Hawkins (thesis). Any change requires a PR with cited source.
**Read by:** `.github/workflows/docs-consistency.yml` CI check. Drift in README, variable_dictionary.md, theoretical_framework_v1.md, or five_layer_capital_stack.md vs. values below will fail CI.

## Format

Each fact is `KEY: VALUE  # short source note`. Keep KEY stable; values may only change with a sourced commit.

---

## Five-Layer Capital Stack (V5 canonical)

LAYER_1_NAME: CIP
LAYER_2_NAME: PID/HOA
LAYER_3_NAME: TIF/OZ
LAYER_4_NAME: SFR
LAYER_5_NAME: Vendor Residue

## Layer 1 — CIP (2012–2026)

L1_TOTAL_FY2012_2026: $984M  # Dallas CIP total FY2012-FY2026

## Layer 2 — PID / HOA

L2_DOWNTOWN_ANNUAL: $13.5M/yr  # Downtown PID annual assessments
L2_SOUTH_SIDE_ANNUAL: $411K/yr  # South Side PID annual assessments
L2_GAP_MULTIPLIER: 33×         # Downtown / South Side ratio

## Layer 3 — TIF / OZ

L3_DOWNTOWN_TIF: $8.83B        # Downtown TIF lifetime
L3_GRAND_PARK_SOUTH_TIF: $333M # Grand Park South TIF lifetime
L3_RATIO: 26:1                 # Downtown : Grand Park South

## Layer 4 — SFR

L4_DFW_MEGA_INVESTOR_UNITS: 26,961  # Mega-investor SFR units in DFW

## Layer 5 — Vendor Residue

L5_NORTH_TOTAL: $369.2M        # North vendor residue (absolute)
L5_NORTH_SHARE: 25.3%          # North share
L5_SOUTH_TOTAL: $38.3M         # South vendor residue (absolute)
L5_SOUTH_SHARE: 2.6%           # South share
L5_GAP_MULTIPLIER: 12.6×       # North / South ratio

## H1 — Investment Bias (OLS M7)

H1_HOLC_D_BETA: +247.6         # HOLC-D coefficient
H1_HOLC_D_PVALUE: p<0.001
H1_RACE_CONTROLLED: insignificant  # When HOLC + structural controls included

## H4 — Readiness Dimension

H4_SUSCEPTIBLE_SOUTH_TRACTS: 54
H4_WITH_TIF_OZ: 0
H4_HIGH_PRESSURE_LOW_READINESS: 44
H4_IMMEDIATE_PRIORITY: 14              # readiness ≤ 0.028
H4_IMMEDIATE_READINESS_CUTOFF: 0.028
H4_TOP5_PRIORITY_TRACTS: 170.09, 64.02, 91.03, 170.07, 92.02
H4_TOP5_DISTRICTS: D8, D1, D5, D8, D5

## H5 — Vendor → Political Contributions

H5_DIRECT_COUNCIL_CONTRIBUTIONS_TOP18: 0  # Direct corporate to Dallas Council from top-18 vendors
H5_TAN_PARKER_DISTRICT: TX HD-63
H5_TAN_PARKER_BOARD: Southland Holdings
H5_TEXAS_MATERIALS_GROUP_TOTAL: $58.9M    # CRH plc (Ireland)
H5_PAC_NAME: Texans for Opportunity       # Funded by BAR + Archer Western for TX Prop 4

## H6 — Close the Argument (Bates v2.1, 2013→2023)

H6_SOUTH_HOME_VALUE_CHANGE: +120.5%
H6_NORTH_HOME_VALUE_CHANGE: +111.3%
H6_SOUTH_REAL_INCOME_CHANGE: +8.6%
H6_NORTH_REAL_INCOME_CHANGE: +17.1%

## ACS / Data Panel

ACS_MATCHED_TRACTS: 385        # of 645 total via LTDB crosswalk
ACS_TOTAL_TRACTS: 645
ACS_CPI_ADJUSTMENT_2013_2023: +36%

---

## Change log

- 2026-04-21 — Initial FACTS.md created as part of divergence-controls PR #3.

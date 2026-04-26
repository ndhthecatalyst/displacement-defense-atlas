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

# Provenance status (2026-04-26 audit, docs/audit/2026-04-26_layer3_audit.md):
#   The three keys below have no traceable lineage in the repo. They are
#   typed-in figures that appear only here and a single map annotation
#   string at scripts/analysis/h3_pid_bates_hmda/atlas_v0_map_c.py:325.
#   The Dallas County 2025 TIF Annual Report shows individual districts
#   at $1.1B–$1.9B in lifetime increment captured; "Downtown Connection
#   TIF" is not a single district in Dallas's 18-district roster — it is
#   most likely a sum of 6–8 downtown-area TIFs. PR-2 will re-derive
#   these values from data/raw/layer3_tif_oz/dallas_tif_increment_2025.csv
#   (parsed via scripts/pipeline/parse_tif_annual_report.py) and, if the
#   corrected ratio differs, update FACTS.md, README.md, and theory docs
#   together per SOURCE_OF_TRUTH.md precedence rules.
# provenance: pending-rerun
L3_DOWNTOWN_TIF: $8.83B        # Downtown TIF lifetime — pending re-derivation from 2025 TIF Annual Report PDF
L3_GRAND_PARK_SOUTH_TIF: $333M # Grand Park South TIF lifetime — pending re-derivation from 2025 TIF Annual Report PDF
L3_RATIO: 26:1                 # Downtown : Grand Park South — pending re-derivation

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
# H4_WITH_TIF_OZ provenance status (2026-04-26 audit):
#   This count was computed from hardcoded TIF bounding boxes (18) and
#   hardcoded OZ GEOIDs (30, of which only 3 actually matched the 645-tract
#   panel — a 90% join collapse) in scripts/pipeline/atlas_v0_build.py.
#   The 0 result may survive the corrected pipeline
#   (scripts/pipeline/build_layer3_tif_oz.py) but cannot be defended until
#   that pipeline runs against the authoritative City of Dallas TIF
#   Subdistricts and HUD QOZ layers.
# provenance: pending-rerun
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
- 2026-04-26 — Layer 3 audit (`docs/audit/2026-04-26_layer3_audit.md`) flagged `L3_DOWNTOWN_TIF`, `L3_GRAND_PARK_SOUTH_TIF`, `L3_RATIO`, and `H4_WITH_TIF_OZ` as `provenance: pending-rerun`. Values are unchanged in this PR (CI parity preserved); PR-2 will re-derive against the authoritative TIF Annual Report PDF and HUD QOZ layer and update both the values and the dependent docs in a single propagation PR.

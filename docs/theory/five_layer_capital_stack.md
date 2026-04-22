# The Five-Layer Capital Stack

**Canonical framing document · V5 Architecture · April 2026**
**Thesis:** *Below the Line: Development as Governance and the Geography of Displacement Risk in Dallas*
**Companion documents:** `theoretical_framework_v1.md` (Chapter 2 spine); `variable_dictionary.md` (operational definitions); `v5_atlas_reframe_capital_stack_theory.pdf` (original reframe memo).

---

## The Argument in One Sentence

Dallas's public finance architecture — CIP allocation, PID supplementation, TIF/OZ capture, institutional ownership, and vendor extraction — constitutes a **governance design** that produces displacement, not a market failure.

## What the Stack Corrects

V0–V4 of this project asked *who lives near* a road project. V5 asks *who captures the economic returns* of public capital. The capital stack is the instrument by which that second question becomes measurable. Each layer is a distinct mechanism by which public capital is allocated, supplemented, captured, owned, or extracted. The five layers are vertically integrated: their joint presence amplifies exchange value in wealthy white communities; their joint absence compounds disinvestment in Black and Hispanic communities south of I-30.

---

## Layer 1 — CIP (Public Base)

**Mechanism:** Capital Improvement Program allocation — the public base of the stack.
**Scale:** $984M FY2012–FY2026 across bond programs and general capital funds.
**Headline finding:** After controlling for income and infrastructure need, CIP per-capita allocation is significantly lower in majority-Black and Hispanic tracts south of I-30, with the largest gap in *discretionary* categories (parks, libraries, economic development). The M7 OLS regression finds HOLC-D grade β = +247.6 (p<0.001); the race coefficient becomes statistically insignificant once HOLC grade is controlled, reproducing Aaronson, Hartley & Mazumder (2021) in a new outcome variable.
**Primary variables:** `cip_per_capita`, `cip_discretionary_share`, `holc_grade`, `% non_white`, `pop_density`, `distance_to_i30`.
**Hypothesis:** H1.
**Data sources:** Dallas CIP Open Data; Bond Programs 2012 / 2017 / 2024; ACS 5-Year; Mapping Inequality (HOLC); Census TIGER.
**Key citations:** Aaronson, Hartley & Mazumder (2021); Rothstein (2017); Logan & Molotch (1987).

---

## Layer 2 — PID/HOA (Private Supplementation)

**Mechanism:** Public Improvement Districts and Homeowners' Associations — privately funded, publicly administered supplementation of the CIP base.
**Scale:** Downtown Dallas PID $13.5M/yr vs. South Side PID $411K/yr = **33× gap**.
**Headline finding:** PID revenue is not neutral supplemental funding; it is a private amplifier of public investment that requires an assessable tax base to initiate. Communities whose exchange value has been suppressed by prior policy (Layer 1 underinvestment + HOLC legacy) cannot meet the threshold to form a PID, and so cannot privately amplify their own investment — even as wealthy downtown areas stack PID spending on top of already-favorable CIP allocation. This is Wyly & Hammel's (2004) argument extended into the private-supplementation layer.
**Primary variables:** `pid_present`, `pid_revenue_per_parcel`, `econ_dev_pid_share`.
**Hypothesis:** H3 (Layer 2 component).
**Data sources:** Dallas GIS Hub PID boundaries (layer IDs `215f5e7243d44c25b7e503e3dafe73da` and `16a1eb7a28f143ffb3714435ffac740a`); Dallas OED; individual PID annual reports.
**Key citations:** Wyly & Hammel (2004); Briffault (1999) on BID/PID governance.

---

## Layer 3 — TIF/OZ (Financial Engineering)

**Mechanism:** Tax Increment Finance districts + federal Opportunity Zones — financial engineering that redirects future public tax revenues and federal capital-gains incentives to designated geographies.
**Scale:** Downtown Connection TIF $8.83B assessed increment vs. Grand Park South $333M = **26:1 gap**.
**Inverted gap finding (V5):** *Zero* of 54 Susceptible South Dallas tracts have received TIF or OZ designation, producing **44 HIGH_PRESSURE_LOW_READINESS** crisis tracts. 14 of these meet the *immediate priority* threshold (readiness ≤ 0.028): top five are 170.09 (D8), 64.02 (D1), 91.03 (D5), 170.07 (D8), 92.02 (D5).
**Headline claim:** TIF and OZ do not reach the communities whose displacement pressure is rising fastest. The spatial targeting of these instruments expresses the growth machine's exchange-value logic, not need-based allocation. Weber (2002): the "but for" standard is political, not empirical.
**Primary variables:** `tif_overlap_pct`, `oz_overlap_pct`, `tif_increment_share`, `oz_investment_received`, `readiness_score`, `pressure_readiness_class`, `susceptible_south_flag`.
**Hypothesis:** H4.
**Data sources:** Dallas County 2025 TIF Annual Report; Dallas OED; CDFI Fund / Treasury OZ designations; IRS Form 8996; LIHTC; HUD Picture; Dallas NEZ.
**Key citations:** Weber (2002); Wyly & Hammel (2004); Theodos, Hangen, González-Hermoso & Meixell (2020).

---

## Layer 4 — Institutional SFR (Ownership)

**Mechanism:** Mega-investor single-family rental capture — institutional ownership of residential parcels, displacing local homeownership and rental markets.
**Scale:** 26,961 mega-investor SFR units in DFW; concentrated in majority-Black neighborhoods at ~3× the national average.
**Headline finding:** Institutional SFR ownership is the ownership-side expression of racial capitalism (Dantzler 2021): Black-occupied neighborhoods are identified as undervalued acquisition targets precisely because prior layers of the stack have suppressed their exchange value. Purchase pressure converts homeownership opportunity into extractive rental income flowing to distant REITs and private-equity funds.
**Primary variables:** `sfr_investor_share`, `investor_purchase_rate`.
**Hypothesis:** H3 (Layer 4 component); interaction of L2 absence × L4 presence predicts *Dynamic Gentrification* and *Historic Loss* Bates stages.
**Data sources:** CoreLogic / ATTOM / PropStream; Immergluck et al. academic datasets.
**Key citations:** Immergluck (2018); Fields (2022); Dantzler (2021); Ananya Roy (2017) on racial banishment.

---

## Layer 5 — Vendor Residue (Contracting / Return)

**Mechanism:** Where public contracting dollars ultimately flow — the *return* on public capital.
**Scale:** Top-18 vendor analysis: North $369.2M (25.3%) vs. South $38.3M (2.6%) = **12.6× gap**. 83% of $108.8M South-originated CIP spend is extracted northward. **$58.9M (15¢ of every top-vendor dollar) flows to Texas Materials Group, owned by CRH plc (Ireland)**.
**Political recirculation loop (H5):**
1. Zero direct corporate contributions to Dallas City Council from top-18 vendors identified in municipal CFR data.
2. **Tan Parker (TX HD-63) sits on the Board of Southland Holdings**, parent of Oscar Renda Contracting ($26.5M in active Dallas contracts) — a documented board interlock.
3. BAR Constructors and Archer Western jointly funded "Texans for Opportunity" PAC (TX Proposition 4).
**Headline claim:** Layer 5 is the layer V4 could not see. It is the measurable signature of extractive urbanism: public dollars enter South Dallas as CIP allocation, exit northward as vendor payments, and recirculate through state/federal political channels that loop back into the policy environment governing the next cycle of allocation. The race-neutral surface of municipal contracting is preserved while the extractive circuit operates in the jurisdictions above it.
**Primary variables:** `vendor_residue`, `vendor_local_share`, `vendor_south_share`, `mbe_contract_share`, `foreign_parent_flag`, `board_interlock_flag`, `tec_contribution_amount`, `fec_contribution_amount`.
**Hypothesis:** H2, H5.
**Data sources:** Dallas Vendor Payments (FY2019–present, 145,551 rows; 8,354 unique vendors geocoded by ZIP5); TEC bulk data; FEC; Dallas CFR; OpenCorporates for parent verification.
**Key citations:** Robinson (1983); Dantzler (2021); Pulido (2017); Ananya Roy (2017); Mehrotra & Vera (2020).

---

## How the Layers Compound

The theoretical contribution of this thesis is not the identification of any single layer. Each has been studied before, though rarely in Dallas and almost never together. The contribution is the demonstration that **the five layers are vertically integrated**: their joint presence is the architecture of racially structured investability.

- In majority-white North Dallas tracts: Layer 1 favors the tract (higher discretionary CIP); Layer 2 supplements it privately (active PID); Layer 3 captures its appreciation (TIF increment flowing to adjacent reinvestment); Layer 4 has little pressure because homeownership is protected; Layer 5 returns public contracting dollars to local vendors located in the same geography.
- In majority-Black South Dallas tracts: Layer 1 underserves it; Layer 2 is structurally unavailable (no PID assessable base); Layer 3 is entirely absent (0 of 54 Susceptible tracts); Layer 4 extracts ownership through institutional SFR purchases; Layer 5 extracts return through vendor contracts that flow northward and, via CRH plc, internationally.

The compounding is not coincidence. It is the governance design. The V5 `capital_stack_score` operationalizes the compounding at the tract level by integrating standardized inputs from all five layers into a single composite; H3 (V5) tests whether the composite predicts displacement stage better than any single-layer predictor.

---

## Relationship to Bates Typology (H6)

The Five-Layer Capital Stack is a spatial-political-economic diagnosis. The Bates Typology v2.1 is its longitudinal corollary. Bates classifies tracts into Early, Dynamic, and Late displacement stages using a decade-long ACS panel (2013→2023, CPI-adjusted, 385 of 645 Dallas County tracts matched via LTDB crosswalk). The V5 thesis claim is that capital stack configuration *predicts* Bates stage: specifically, the interaction of Layer 2 absence and Layer 4 presence predicts *Dynamic Gentrification* and *Historic Loss* stages with the highest accuracy. This is the operational coupling between the diagnostic (which communities are being displaced) and the prognostic (which communities are staged to be displaced next).

---

## Version Note

This document is the canonical framing artifact for V5. When the thesis language, variable dictionary, theoretical memo, and repository structure disagree, this document governs. Updates to the five-layer framing must be made here first and propagated outward.

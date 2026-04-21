# METHODS MEMO

**Memo Title:** Analytical Methods and Methodological Justification  
**Thesis Title:** Below the Line: Development as Governance and the Geography of Displacement Risk in Dallas  
**Author:** Nicholas Donovan Hawkins  
**Institution:** Texas Southern University, Freeman Honors College  
**Date:** April 21, 2026  
**Version:** v1.0  
**Intended Audience:** Thesis Committee  

---

## 1. HMDA Data Choice: Primary CFPB Data Over UI Pre-Aggregated Summaries

I use CFPB HMDA 2023 primary data — encompassing 625 census tracts and 12,300 denial records — rather than the Urban Institute's pre-aggregated neighborhood summaries because the analytic objectives of this thesis require tract-level granularity that pre-aggregation methodologically forecloses. The Urban Institute summaries impose a fixed aggregation schema designed for portfolio-level equity monitoring; when applied to a fine-grained spatial analysis of a single metropolitan area, that schema obscures precisely the within-city variation I seek to explain. Aggregation collapses denial rates to neighborhood-type averages, masking the intra-category heterogeneity that is theoretically significant when testing whether investment infrastructure systematically underserves communities of color south of I-30.

More specifically, the Urban Institute data do not support original racial decomposition at the tract level. My analysis requires the ability to compute the Black share of mortgage denials independently — a figure I calculate at 20.7 percent of all denial records — and to cross-tabulate that figure against CIP expenditure geography, TIF district boundaries, and Opportunity Zone designations. This decomposition cannot be reverse-engineered from pre-aggregated summaries without strong and unverifiable assumptions about the underlying microdata. By retaining the full CFPB loan-level records and aggregating upward myself to the census tract, I preserve the audit trail and ensure that every intermediate calculation is reproducible and transparent. Reproducibility is a non-trivial concern in housing discrimination research: the evidentiary record must be capable of withstanding methodological scrutiny in both academic peer review and, potentially, public-interest contexts. Working from primary data aligns this project with the reproducibility standards called for in the emerging open-science literature on urban inequality (Aaronson and Mazumder 2021).

---

## 2. ACS CPI Adjustment: Longitudinal Comparability in the Bates Typology v2.1 Analysis

I compare American Community Survey data across the 2013 and 2023 five-year estimates to operationalize the Bates Typology v2.1 displacement risk classification. Because both waves are expressed in the nominal dollars of their respective survey years, a direct comparison of median household income or median gross rent across this ten-year span would be methodologically invalid: it would conflate real changes in economic conditions with changes in the price level, biasing the typology classifications in ways that systematically misidentify tracts undergoing accelerated rent burden.

To correct for this, I apply the Bureau of Labor Statistics CPI-U (All Urban Consumers, All Items) price deflator, using 2023 as the base year. All 2013 dollar-denominated variables are inflated to 2023 equivalents using the ratio of the relevant annual CPI-U indices, sourced from the BLS published series (U.S. Bureau of Labor Statistics, Consumer Price Index for All Urban Consumers [CPI-U], Series ID CUUR0000SA0). The variables adjusted in this procedure are median household income and median gross rent — both of which enter the Bates Typology as threshold-crossing classifiers. Variables that are dimensionless or ratio-scaled — including racial and ethnic composition shares, educational attainment rates, and owner-occupancy rates — are left in their nominal (percentage) form, because applying a price deflator to shares would be arithmetically nonsensical and would introduce rather than remove measurement error. The CPI adjustment procedure is documented in the project's analytical pipeline at the GitHub repository (https://github.com/ndhthecatalyst/displacement-defense-atlas) and is fully reproducible from the BLS public API.

---

## 3. OLS for H1: Rationale and Spatial Limitations

For the H1 investment bias regression — modeled as CIP dollars per capita as a function of percent non-white population plus socioeconomic controls — I use Ordinary Least Squares estimation as the primary analytical model. OLS is appropriate for an initial test of the directional hypothesis for several reasons. First, the dependent variable (per-capita CIP expenditure) is continuous and approximately normally distributed after log-transformation, satisfying the basic distributional requirements for linear regression. Second, OLS produces coefficient estimates that are directly interpretable in substantive terms: a one-unit increase in the non-white share of a tract's population is associated with a specific dollar-denominated change in per-capita capital investment, a relationship that is legible to both academic audiences and public stakeholders. Third, given that this is a first-pass analysis at an early project stage, OLS provides a transparent and methodologically conservative benchmark against which more complex spatial models can be compared.

I acknowledge, however, that OLS rests on the assumption of independently and identically distributed errors — an assumption that is routinely violated in census tract data because of spatial autocorrelation. Adjacent tracts share physical infrastructure, housing markets, and administrative boundaries, which means that the residuals of a tract-level regression are almost certain to exhibit positive spatial dependence. I will diagnose this directly by computing Moran's I on the OLS residuals; if the statistic is statistically significant (p < 0.05), spatial autocorrelation is confirmed. For the v1 version of the analytical pipeline, the plan is to estimate both a spatial lag model — which treats the dependent variable in neighboring tracts as an additional regressor — and a spatial error model — which models spatial dependence as a nuisance structure in the error term — as robustness checks. The spatial models will be estimated using queen contiguity weights derived from the 2023 Dallas County census tract shapefile. Comparisons between the OLS and spatial regression coefficients on the percent non-white variable will be reported; if the direction and approximate magnitude of that coefficient is stable across specifications, the substantive conclusion is robust to spatial misspecification.

---

## 4. CIP/TIF/OZ as Governance Mechanisms: Framing and Theoretical Stakes

I frame the Capital Improvement Program, Tax Increment Financing districts, and Opportunity Zone designations as governance mechanisms rather than as policy instruments, and this distinction carries significant theoretical weight for the argument the thesis advances. A policy instrument, in the conventional public administration literature, is a tool deployed within an assumed-neutral institutional framework to achieve a specified public objective: it is chosen for its technical efficiency and evaluated on whether it achieves its target outcome. The neutral-instrument framing presupposes that the framework within which tools are deployed is itself uncontested and structurally inert. That presupposition is precisely what this thesis contests.

A governance mechanism, by contrast, is an institutional arrangement that does not merely operate within a distribution of power but actively constitutes and reproduces it. CIP allocations, TIF district boundaries, and Opportunity Zone designations each embed spatial priorities — which neighborhoods receive capital, which can leverage private investment through tax increment, which qualify for preferential federal treatment — and those priorities are not technocratically derived but politically negotiated through processes in which resource-rich actors are systematically advantaged. This framing connects directly to the growth machine literature: Logan and Molotch (1987) argue that urban land use is organized around exchange value rather than use value, and that local governing coalitions — alliances of real estate interests, financial institutions, and municipal officials — deploy public authority to channel investment toward areas where value capture is possible. CIP, TIF, and OZ are precisely the institutional levers through which a Dallas-style growth machine operates. Treating them as neutral instruments would render invisible the structural mechanism the thesis is designed to expose: the possibility that these arrangements are not merely failing to serve communities of color south of I-30, but are constitutively organized around their exclusion, a pattern that the historical geography of HOLC redlining established as a durable baseline (Aaronson and Mazumder 2021).

Collapsing governance mechanisms into policy instruments would therefore not merely be an analytical imprecision — it would foreclose the central structural argument before the empirical analysis begins.

---

*This memo will be updated as the analytical pipeline develops, including upon completion of the spatial robustness checks described in Section 3 and following any revisions to the Bates Typology operationalization.*

---

**References**

Aaronson, Daniel, and Bhashkar Mazumder. 2021. "The Effects of the 1930s HOLC 'Redlining' Maps." *American Economic Review: Insights* 3 (3): 327–44.

Logan, John R., and Harvey L. Molotch. 1987. *Urban Fortunes: The Political Economy of Place.* Berkeley: University of California Press.

U.S. Bureau of Labor Statistics. n.d. "Consumer Price Index for All Urban Consumers (CPI-U), Series ID CUUR0000SA0." Accessed April 2026. https://www.bls.gov/cpi/.

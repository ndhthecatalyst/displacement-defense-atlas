"""
H1 Analysis — Investment Bias
Below the Line: Dallas I-30 Corridor Displacement Risk Atlas
Nicholas D. Hawkins | TSU Freeman Honors College

Hypothesis H1:
  Municipal CIP investment dollars per capita are systematically lower
  in census tracts with higher proportions of non-white residents,
  controlling for median household income and population density.

Model:
  log(CIP_per_capita + 1) ~ pct_nonwhite + log(median_income) + log(population) + south_of_i30

Output:
  - OLS regression table (outputs/tables/h1_ols_results.csv)
  - Regression diagnostic plots (outputs/figures/h1_*)
  - Spatial residuals GeoJSON (data/processed/h1_residuals.geojson)
  - Methods memo section (outputs/memos/h1_findings.md)
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

BASE = "/home/user/workspace/dda_repo"
DATA = f"{BASE}/data"

# ─── Load Data ────────────────────────────────────────────────────────────────
print("Loading harmonized atlas data...")
df = pd.read_csv(f"{DATA}/exports/atlas_v1_tract_data.csv")

# ─── Clean & Transform ────────────────────────────────────────────────────────
# Fix census suppression codes
for col in ['median_income', 'population', 'pct_black', 'pct_hispanic',
            'pct_renter', 'rent_burden_pct']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
    df[col] = df[col].where(df[col] > -9999, np.nan)

# Drop tracts with missing key variables or tiny population (< 100)
df_model = df[
    df['population'].notna() & (df['population'] >= 100) &
    df['median_income'].notna() & (df['median_income'] > 0) &
    df['pct_nonwhite'].notna()
].copy()

# Transformations
df_model['log_cip_pc']     = np.log1p(df_model['cip_per_capita'])   # log(x+1) handles zeros
df_model['log_income']     = np.log(df_model['median_income'])
df_model['log_population'] = np.log(df_model['population'])
df_model['pct_nonwhite_c'] = df_model['pct_nonwhite'] / 100         # scale 0–1

print(f"Modeling sample: {len(df_model)} tracts (of {len(df)} total)")
print(f"  Tracts with CIP investment: {(df_model['cip_per_capita']>0).sum()}")
print(f"  Mean pct_nonwhite: {df_model['pct_nonwhite'].mean():.1f}%")
print(f"  Mean CIP per capita: ${df_model['cip_per_capita'].mean():.2f}")

# ─── Model 1: Bivariate ───────────────────────────────────────────────────────
print("\n--- MODEL 1: Bivariate OLS ---")
X1 = sm.add_constant(df_model['pct_nonwhite_c'])
y  = df_model['log_cip_pc']
m1 = sm.OLS(y, X1).fit(cov_type='HC3')
print(m1.summary())

# ─── Model 2: Full specification ──────────────────────────────────────────────
print("\n--- MODEL 2: Full OLS (HC3 robust SEs) ---")
formula = "log_cip_pc ~ pct_nonwhite_c + log_income + log_population + south_of_i30"
m2 = smf.ols(formula, data=df_model).fit(cov_type='HC3')
print(m2.summary())

# ─── Model 3: South-only subsample ───────────────────────────────────────────
print("\n--- MODEL 3: South of I-30 Only ---")
df_south = df_model[df_model['south_of_i30'] == 1]
m3 = smf.ols(formula, data=df_south).fit(cov_type='HC3')
print(m3.summary())

# ─── VIF Check ────────────────────────────────────────────────────────────────
X_vif = df_model[['pct_nonwhite_c','log_income','log_population','south_of_i30']].dropna()
X_vif_c = sm.add_constant(X_vif)
vif_df = pd.DataFrame({
    'Variable': X_vif_c.columns,
    'VIF': [variance_inflation_factor(X_vif_c.values, i) for i in range(X_vif_c.shape[1])]
})
print("\nVariance Inflation Factors:")
print(vif_df.to_string(index=False))

# ─── Breusch-Pagan Heteroskedasticity Test ────────────────────────────────────
bp_stat, bp_pval, _, _ = het_breuschpagan(m2.resid, m2.model.exog)
print(f"\nBreusch-Pagan test: stat={bp_stat:.3f}, p={bp_pval:.4f}")
print(f"  → {'Heteroskedasticity present (HC3 SEs appropriate)' if bp_pval < 0.05 else 'No significant heteroskedasticity'}")

# ─── Export Results Table ─────────────────────────────────────────────────────
results = {
    'Variable': ['Intercept', '% Non-White (0–1)', 'log(Median Income)',
                 'log(Population)', 'South of I-30'],
    'Model 1 Bivariate': [
        f"{m1.params.get('const', np.nan):.4f} ({m1.pvalues.get('const',1):.3f})",
        f"{m1.params.get('pct_nonwhite_c', np.nan):.4f} ({m1.pvalues.get('pct_nonwhite_c',1):.3f})",
        '—', '—', '—'
    ],
    'Model 2 Full': [
        f"{m2.params['Intercept']:.4f} ({m2.pvalues['Intercept']:.3f})",
        f"{m2.params['pct_nonwhite_c']:.4f} ({m2.pvalues['pct_nonwhite_c']:.3f})",
        f"{m2.params['log_income']:.4f} ({m2.pvalues['log_income']:.3f})",
        f"{m2.params['log_population']:.4f} ({m2.pvalues['log_population']:.3f})",
        f"{m2.params['south_of_i30']:.4f} ({m2.pvalues['south_of_i30']:.3f})",
    ],
    'Model 3 South-Only': [
        f"{m3.params['Intercept']:.4f} ({m3.pvalues['Intercept']:.3f})",
        f"{m3.params['pct_nonwhite_c']:.4f} ({m3.pvalues['pct_nonwhite_c']:.3f})",
        f"{m3.params['log_income']:.4f} ({m3.pvalues['log_income']:.3f})",
        f"{m3.params['log_population']:.4f} ({m3.pvalues['log_population']:.3f})",
        f"{m3.params['south_of_i30']:.4f} ({m3.pvalues['south_of_i30']:.3f})" if 'south_of_i30' in m3.params else '(omitted)',
    ],
}
results_df = pd.DataFrame(results)

# Add model-level stats
stats_rows = pd.DataFrame({
    'Variable': ['N', 'R²', 'Adj. R²', 'F-stat (p-value)'],
    'Model 1 Bivariate': [
        str(int(m1.nobs)), f"{m1.rsquared:.4f}", f"{m1.rsquared_adj:.4f}",
        f"{m1.fvalue:.3f} ({m1.f_pvalue:.4f})"
    ],
    'Model 2 Full': [
        str(int(m2.nobs)), f"{m2.rsquared:.4f}", f"{m2.rsquared_adj:.4f}",
        f"{m2.fvalue:.3f} ({m2.f_pvalue:.4f})"
    ],
    'Model 3 South-Only': [
        str(int(m3.nobs)), f"{m3.rsquared:.4f}", f"{m3.rsquared_adj:.4f}",
        f"{m3.fvalue:.3f} ({m3.f_pvalue:.4f})"
    ],
})
results_df = pd.concat([results_df, stats_rows], ignore_index=True)
results_df.to_csv(f"{BASE}/outputs/tables/h1_ols_results.csv", index=False)
print(f"\nResults table saved.")

# ─── Diagnostic Plots ─────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 12))
fig.patch.set_facecolor('#fafafa')
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

# 1. Scatter: pct_nonwhite vs log(CIP per capita) with regression line
ax1 = fig.add_subplot(gs[0, 0])
x_plot = df_model['pct_nonwhite']
y_plot = df_model['log_cip_pc']
ax1.scatter(x_plot, y_plot, alpha=0.4, s=18, color='#4393c3',
            label='Census tract')
# Fitted line
xr = np.linspace(x_plot.min(), x_plot.max(), 100)
yr = m1.params['const'] + m1.params['pct_nonwhite_c'] * (xr / 100)
ax1.plot(xr, yr, color='#d73027', linewidth=2, label=f'OLS fit (β={m1.params["pct_nonwhite_c"]:.3f})')
ax1.set_xlabel('% Non-White Residents', fontsize=10)
ax1.set_ylabel('log(CIP $ per capita + 1)', fontsize=10)
ax1.set_title('H1: CIP Investment vs. Race\n(Bivariate)', fontsize=10, fontweight='bold')
ax1.legend(fontsize=8)
ax1.spines[['top','right']].set_visible(False)

# 2. Partial regression plot: pct_nonwhite controlling for others
ax2 = fig.add_subplot(gs[0, 1])
fig_pr = sm.graphics.plot_partregress(
    'log_cip_pc', 'pct_nonwhite_c',
    ['log_income','log_population','south_of_i30'],
    data=df_model, ax=ax2, obs_labels=False
)
ax2.set_title('H1: Partial Regression\n(Controlled for income, pop, I-30)', fontsize=10, fontweight='bold')
ax2.set_xlabel('% Non-White (residualized)', fontsize=9)
ax2.set_ylabel('log(CIP per capita) (residualized)', fontsize=9)
ax2.spines[['top','right']].set_visible(False)

# 3. Residuals vs fitted
ax3 = fig.add_subplot(gs[0, 2])
fitted = m2.fittedvalues
resids = m2.resid
ax3.scatter(fitted, resids, alpha=0.4, s=18, color='#4393c3')
ax3.axhline(0, color='#d73027', linewidth=1.5, linestyle='--')
ax3.set_xlabel('Fitted values', fontsize=10)
ax3.set_ylabel('Residuals', fontsize=10)
ax3.set_title('Residuals vs Fitted\n(Model 2)', fontsize=10, fontweight='bold')
ax3.spines[['top','right']].set_visible(False)

# 4. Q-Q plot
ax4 = fig.add_subplot(gs[1, 0])
(osm, osr), (slope, intercept, r) = stats.probplot(resids, dist='norm')
ax4.plot(osm, osr, 'o', alpha=0.4, ms=4, color='#4393c3')
ax4.plot(osm, slope*np.array(osm)+intercept, color='#d73027', linewidth=1.5)
ax4.set_xlabel('Theoretical quantiles', fontsize=10)
ax4.set_ylabel('Sample quantiles', fontsize=10)
ax4.set_title('Normal Q-Q Plot\n(Model 2 residuals)', fontsize=10, fontweight='bold')
ax4.spines[['top','right']].set_visible(False)

# 5. Coefficient plot (Model 2 with CI)
ax5 = fig.add_subplot(gs[1, 1])
coef_vars = ['pct_nonwhite_c', 'log_income', 'log_population', 'south_of_i30']
coef_labels = ['% Non-White', 'log(Income)', 'log(Population)', 'South of I-30']
coefs  = [m2.params[v] for v in coef_vars]
ci_low = [m2.conf_int().loc[v, 0] for v in coef_vars]
ci_hi  = [m2.conf_int().loc[v, 1] for v in coef_vars]
colors = ['#d73027' if c < 0 else '#4393c3' for c in coefs]
y_pos = range(len(coef_vars))
ax5.barh(y_pos, coefs, xerr=[np.array(coefs)-np.array(ci_low), np.array(ci_hi)-np.array(coefs)],
         color=colors, alpha=0.8, capsize=4)
ax5.axvline(0, color='black', linewidth=1)
ax5.set_yticks(list(y_pos))
ax5.set_yticklabels(coef_labels, fontsize=9)
ax5.set_xlabel('Coefficient (log CIP per capita)', fontsize=9)
ax5.set_title('Model 2 Coefficients\n(95% CI, HC3 SEs)', fontsize=10, fontweight='bold')
ax5.spines[['top','right']].set_visible(False)

# 6. North vs South box plot
ax6 = fig.add_subplot(gs[1, 2])
ns_data = [
    df_model[df_model['south_of_i30']==0]['log_cip_pc'].dropna(),
    df_model[df_model['south_of_i30']==1]['log_cip_pc'].dropna()
]
bp = ax6.boxplot(ns_data, labels=['North of I-30','South of I-30'],
                  patch_artist=True,
                  boxprops=dict(facecolor='#4393c3', alpha=0.7),
                  medianprops=dict(color='#d73027', linewidth=2))
bp['boxes'][1].set_facecolor('#d73027')
ax6.set_ylabel('log(CIP $ per capita + 1)', fontsize=10)
ax6.set_title('CIP Investment Distribution\nNorth vs South of I-30', fontsize=10, fontweight='bold')
ax6.spines[['top','right']].set_visible(False)

plt.suptitle(
    'H1 Analysis — Investment Bias | Displacement Defense Atlas v0\n'
    'Below the Line: Dallas I-30 Corridor | Nicholas D. Hawkins | TSU',
    fontsize=12, fontweight='bold', y=1.01
)

plt.savefig(f"{BASE}/outputs/figures/h1_diagnostic_plots.png",
            dpi=200, bbox_inches='tight', facecolor='#fafafa')
plt.close()
print("Diagnostic plots saved.")

# ─── Spatial Residuals ────────────────────────────────────────────────────────
try:
    gdf = gpd.read_file("/home/user/workspace/atlas_v1/processed_data/atlas_with_dpi.geojson")
    gdf['GEOID'] = gdf['GEOID'].astype(str)
    resid_df = df_model[['GEOID']].copy()
    resid_df['h1_residual']  = m2.resid.values
    resid_df['h1_fitted']    = m2.fittedvalues.values
    resid_df['h1_studentized'] = m2.get_influence().resid_studentized_internal
    gdf_resid = gdf[['GEOID','geometry']].merge(resid_df, on='GEOID', how='left')
    gdf_resid.to_file(f"{DATA}/processed/h1_spatial_residuals.geojson", driver='GeoJSON')
    print("Spatial residuals GeoJSON saved.")
except Exception as e:
    print(f"Spatial residuals: {e}")

# ─── Summary for Memo ─────────────────────────────────────────────────────────
coef_nw  = m2.params['pct_nonwhite_c']
pval_nw  = m2.pvalues['pct_nonwhite_c']
ci_nw    = m2.conf_int().loc['pct_nonwhite_c']
r2_full  = m2.rsquared_adj
n_full   = int(m2.nobs)
sig_flag = "statistically significant" if pval_nw < 0.05 else "not statistically significant"
dir_flag = "negatively" if coef_nw < 0 else "positively"

summary = f"""
H1 FINDINGS SUMMARY
===================
Model: log(CIP per capita + 1) ~ pct_nonwhite + log(income) + log(population) + south_of_i30
N = {n_full} | Adj. R² = {r2_full:.4f} | HC3 robust standard errors

Key result:
  β(pct_nonwhite) = {coef_nw:.4f} (p={pval_nw:.4f}, 95% CI: [{ci_nw[0]:.4f}, {ci_nw[1]:.4f}])
  → % non-white is {dir_flag} associated with CIP per capita ({sig_flag})

North/South:
  β(south_of_i30) = {m2.params['south_of_i30']:.4f} (p={m2.pvalues['south_of_i30']:.4f})

Breusch-Pagan: stat={bp_stat:.3f}, p={bp_pval:.4f}
VIF max: {vif_df[vif_df['Variable']!='const']['VIF'].max():.2f}
"""
print(summary)

with open(f"{BASE}/outputs/memos/h1_findings_summary.txt", 'w') as f:
    f.write(summary)

print("\nH1 analysis complete.")
print(f"  Table: outputs/tables/h1_ols_results.csv")
print(f"  Plots: outputs/figures/h1_diagnostic_plots.png")
print(f"  Memo:  outputs/memos/h1_findings_summary.txt")

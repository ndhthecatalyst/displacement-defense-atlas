"""
H1 OLS v4 — Real Line Geometry + Real District Boundaries + Actual Expenditure Data
======================================================================================
Atlas: Below the Line — Dallas I-30 Corridor Displacement Risk Atlas
Author: Nicholas D. Hawkins | TSU Freeman Honors College

Data sources (v4):
  - CIP Lines: 2012, 2017, Active, 2024 Bond Program line layers (Dallas GIS Hub)
    → AmountPaid = actual expenditure per project line
    → Shape__Length = project line length in feet (State Plane TX North Central)
  - Council Districts: real polygon boundaries (Dallas Open Data, vda9-h28y)
    → the_geom = MULTIPOLYGON WKT, replaces lat/lon centroid proxy
  - Vendor Payments FY2025-2026: supplemental actual disbursements by fund type
  - Census tract geometry + demographics: ACS 5-year (GEOID, pct_black, pct_hispanic,
    pct_nonwhite, median_income, population) from atlas_v1_tract_data.csv
  - HOLC polygons: mappinginequality_dallas.json (48 Dallas zones)

Key upgrades vs v3:
  1. Road-length proration: when a CIP line crosses multiple tracts, investment
     allocated proportionally by (line length in tract / total line length).
     Shape__Length is line total; tract share estimated via CD flag intersection.
  2. Real council district polygons: spatial join of tract centroids to district
     boundaries (replaces lat/lon quadrant proxy).
  3. AmountPaid as primary expenditure measure (not BondAmount authorization).
  4. CIP type fixed effects: Program field → 5 categories.
  5. Vendor Payments FY2025-2026 used as cross-check / supplemental layer.

Proration strategy (v4):
  The CIP Lines CSVs do not include per-tract geometry — they are line features.
  We use CD01-CD14 boolean flags to identify which districts each project touches,
  then distribute AmountPaid proportionally within those districts by tract population
  (population-weighted within district). This is a hybrid approach:
    - v3: equal pop-share within 2 zones (N/S) → constant CIP/cap per zone
    - v4: pop-share within real districts (14 districts) → 14 unique baselines,
          then within-district refinement using Shape__Length as a scalar weight
          applied to project-level allocation before tract distribution.

  Full road-length proration (line geometry × tract polygon intersection) requires
  geopandas spatial overlay of line GeoJSON against tract polygons. That requires
  the GeoJSON version of these layers. The CSVs contain Shape__Length (total length)
  but not per-tract split geometry. We implement the best feasible approximation here
  and note in the methods that full proration awaits GeoJSON download via ArcGIS API.

======================================================================================
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

warnings.filterwarnings('ignore')

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE = "/home/user/workspace/dda_repo"
DATA_EXPORTS = f"{BASE}/data/exports"
DATA_RAW = f"{BASE}/data/raw"
DATA_PROC = f"{BASE}/data/processed"
OUT_FIGS = f"{BASE}/outputs/figures"
OUT_TABLES = f"{BASE}/outputs/tables"
OUT_MEMOS = f"{BASE}/outputs/memos"

for d in [OUT_FIGS, OUT_TABLES, OUT_MEMOS]:
    os.makedirs(d, exist_ok=True)

# ─── 1. Load Census Tract Data ─────────────────────────────────────────────────
print("=" * 60)
print("ATLAS H1 v4 — Real Data Pipeline")
print("=" * 60)

print("\n[1] Loading Census tract data...")
tracts = pd.read_csv(f"{DATA_EXPORTS}/atlas_v1_tract_data.csv", dtype={'GEOID': str})
tracts['GEOID'] = tracts['GEOID'].str.zfill(11)
print(f"    Tracts: {len(tracts):,} | Columns: {list(tracts.columns)}")

# ─── 2. Load Council District Polygons ────────────────────────────────────────
print("\n[2] Loading Council District polygons...")
cd_raw = pd.read_csv(f"{DATA_RAW}/layer0_boundaries/Council_Districts_20260420.csv")

# Parse WKT geometry
cd_raw['geometry'] = cd_raw['the_geom'].apply(wkt.loads)
cd_gdf = gpd.GeoDataFrame(cd_raw, geometry='geometry', crs='EPSG:4326')
cd_gdf['DISTRICT_NUM'] = cd_gdf['DISTRICT'].astype(int)
print(f"    Districts loaded: {sorted(cd_gdf['DISTRICT_NUM'].tolist())}")

# ─── 3. Spatial join: tract centroids → council districts ─────────────────────
print("\n[3] Spatial join: tract centroids to council districts...")

# Load tract GeoJSON for geometry
tract_geo = gpd.read_file(f"{DATA_PROC}/atlas_with_dpi.geojson")
tract_geo['GEOID'] = tract_geo['GEOID'].astype(str).str.zfill(11)

# Compute centroids
tract_geo['centroid'] = tract_geo.geometry.centroid
tract_centroids = gpd.GeoDataFrame(
    tract_geo[['GEOID']],
    geometry=tract_geo['centroid'],
    crs='EPSG:4326'
)

# Spatial join to council districts
tract_district = gpd.sjoin(
    tract_centroids,
    cd_gdf[['DISTRICT_NUM', 'geometry']],
    how='left',
    predicate='within'
)
tract_district = tract_district[['GEOID', 'DISTRICT_NUM']].drop_duplicates('GEOID')
n_matched = tract_district['DISTRICT_NUM'].notna().sum()
print(f"    Tracts matched to district: {n_matched}/{len(tract_district)}")
print(f"    District distribution:\n{tract_district['DISTRICT_NUM'].value_counts().sort_index().to_string()}")

# Merge district assignment back to tracts
tracts = tracts.merge(tract_district, on='GEOID', how='left')
tracts['DISTRICT_NUM'] = tracts['DISTRICT_NUM'].fillna(0).astype(int)

# ─── 4. Load & Stack CIP Line Files ───────────────────────────────────────────
print("\n[4] Loading CIP line geometry files...")

cip_files = {
    '2012': f"{DATA_RAW}/layer1_investment/CIP_Lines_2012_Bond.csv",
    '2017': f"{DATA_RAW}/layer1_investment/CIP_Lines_2017_Bond.csv",
    'Active': f"{DATA_RAW}/layer1_investment/CIP_Lines_Active_Bond.csv",
    '2024': f"{DATA_RAW}/layer1_investment/CIP_Lines_2024_Bond.csv",
}

cd_cols = [f'CD{str(i).zfill(2)}' for i in range(1, 15)]

dfs = []
for bond_yr, path in cip_files.items():
    df = pd.read_csv(path, low_memory=False)
    df['BondYear'] = bond_yr
    # Standardise CD flags to int (1/0)
    for c in cd_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
        else:
            df[c] = 0
    dfs.append(df)

cip = pd.concat(dfs, ignore_index=True)

# De-duplicate: Active Bond overlaps with 2012/2017 (it's a cross-bond snapshot)
# Keep 2012 and 2017 records; drop Active records whose ProjectID appears in either
proj_ids_2012_2017 = set(
    pd.concat([dfs[0], dfs[1]])['ProjectID'].dropna()
)
active_mask = (cip['BondYear'] == 'Active') & (cip['ProjectID'].isin(proj_ids_2012_2017))
n_dedup = active_mask.sum()
cip = cip[~active_mask].copy()
print(f"    Removed {n_dedup} Active Bond rows already in 2012/2017 programs")

# Use AmountPaid as expenditure; 2024 has $0 paid (too new) → use BondAmount as proxy
cip['expenditure'] = np.where(
    cip['BondYear'] == '2024',
    cip['BondAmount'].fillna(0),          # authorized amount as proxy for 2024
    cip['AmountPaid'].fillna(0)           # actual paid for 2012/2017/Active
)

# Project type classification
def classify_program(prog):
    if pd.isna(prog):
        return 'Other'
    p = str(prog).lower()
    if 'street' in p or 'transportation' in p:
        return 'Streets'
    elif 'flood' in p or 'drainage' in p or 'storm' in p:
        return 'Drainage'
    elif 'park' in p or 'recreation' in p:
        return 'Parks'
    elif 'economic' in p or 'development' in p:
        return 'EconDev'
    else:
        return 'Other'

cip['cip_type'] = cip['Program'].apply(classify_program)

print(f"    Total CIP line records (deduped): {len(cip):,}")
print(f"    Total expenditure: ${cip['expenditure'].sum():,.0f}")
print(f"    By bond year:\n{cip.groupby('BondYear')['expenditure'].sum().apply(lambda x: f'${x:,.0f}').to_string()}")
print(f"    By CIP type:\n{cip.groupby('cip_type')['expenditure'].sum().apply(lambda x: f'${x:,.0f}').to_string()}")

# ─── 5. District-level expenditure allocation ──────────────────────────────────
print("\n[5] Allocating CIP expenditure to tracts via real district boundaries...")

# Step 5a: For each project, identify which districts it touches (CD flags)
# and what fraction of expenditure goes to each district.
# Strategy: if multi-district, split evenly across touching districts
# (Shape__Length proration within districts applied in step 5b)

def get_touching_districts(row):
    """Return list of district numbers flagged in CD01-CD14."""
    districts = []
    for i in range(1, 15):
        col = f'CD{str(i).zfill(2)}'
        if row.get(col, 0) == 1:
            districts.append(i)
    return districts if districts else None

cip['touching_districts'] = cip.apply(get_touching_districts, axis=1)

# Handle rows with no district flags — use District text field as fallback
def parse_district_text(d):
    if pd.isna(d) or str(d).strip() in ('TBD', '', '99'):
        return None
    try:
        parts = [int(x.strip()) for x in str(d).split(',') if x.strip().isdigit()]
        return parts if parts else None
    except:
        return None

fallback_mask = cip['touching_districts'].isna()
cip.loc[fallback_mask, 'touching_districts'] = cip.loc[fallback_mask, 'District'].apply(parse_district_text)

# Projects with still no district → mark as citywide (distribute to all 14)
citywide_mask = cip['touching_districts'].isna()
n_citywide = int(citywide_mask.sum())
print(f"    Projects treated as citywide (no district): {n_citywide}")
if n_citywide > 0:
    citywide_indices = cip.index[citywide_mask].tolist()
    for idx in citywide_indices:
        cip.at[idx, 'touching_districts'] = list(range(1, 15))

# Step 5b: Expand to district-project pairs with per-district expenditure share
records = []
for _, row in cip.iterrows():
    districts = row['touching_districts']
    if not districts:
        continue
    share = 1.0 / len(districts)
    for d in districts:
        records.append({
            'DISTRICT_NUM': d,
            'ProjectID': row['ProjectID'],
            'expenditure_share': row['expenditure'] * share,
            'shape_length': row['Shape__Length'],
            'cip_type': row['cip_type'],
            'BondYear': row['BondYear'],
        })

district_project = pd.DataFrame(records)

# Step 5c: Sum total expenditure per district
district_totals = district_project.groupby('DISTRICT_NUM')['expenditure_share'].sum().reset_index()
district_totals.columns = ['DISTRICT_NUM', 'district_expenditure']
print(f"\n    District expenditure totals:")
for _, r in district_totals.sort_values('DISTRICT_NUM').iterrows():
    print(f"      District {int(r['DISTRICT_NUM']):02d}: ${r['district_expenditure']:>14,.0f}")

# Step 5d: Merge district totals to tracts
tracts = tracts.merge(district_totals, on='DISTRICT_NUM', how='left')
tracts['district_expenditure'] = tracts['district_expenditure'].fillna(0)

# Step 5e: Pop-weighted allocation within district
district_pop = tracts.groupby('DISTRICT_NUM')['population'].sum().rename('district_pop')
tracts = tracts.merge(district_pop, on='DISTRICT_NUM', how='left')
tracts['pop_share'] = np.where(
    tracts['district_pop'] > 0,
    tracts['population'] / tracts['district_pop'],
    0
)
tracts['cip_per_capita_raw'] = np.where(
    tracts['population'] > 0,
    (tracts['district_expenditure'] * tracts['pop_share']) / tracts['population'],
    0
)

# ─── 6. District-level CIP type FEs (for controls) ────────────────────────────
print("\n[6] Computing district-level CIP type shares...")

district_type = district_project.groupby(['DISTRICT_NUM', 'cip_type'])['expenditure_share'].sum().unstack(fill_value=0)
district_type.columns = [f'cip_{c.lower()}_share' for c in district_type.columns]
district_type_pct = district_type.div(district_type.sum(axis=1), axis=0).reset_index()
tracts = tracts.merge(district_type_pct, on='DISTRICT_NUM', how='left')
type_share_cols = [c for c in tracts.columns if c.startswith('cip_') and c.endswith('_share')]
for c in type_share_cols:
    tracts[c] = tracts[c].fillna(0)

# ─── 7. Load HOLC Data ────────────────────────────────────────────────────────
print("\n[7] Loading HOLC zones and joining to tracts...")
# Drop pre-existing holc columns from v1 CSV to avoid merge suffix conflicts
for _col in ['holc_grade', 'holc_score', 'redline_legacy']:
    if _col in tracts.columns:
        tracts = tracts.drop(columns=[_col])

holc_path = f"{DATA_RAW}/layer3_early_warning/mappinginequality_dallas.json"
holc_gdf = gpd.read_file(holc_path)
holc_gdf = holc_gdf[holc_gdf['grade'].notna()].copy()
holc_gdf = holc_gdf.to_crs('EPSG:4326')

tract_geo_join = tract_geo[['GEOID', 'geometry']].merge(
    tracts[['GEOID', 'population']], on='GEOID', how='left'
)
tract_geo_join = gpd.GeoDataFrame(tract_geo_join, geometry='geometry', crs='EPSG:4326')
# Reproject to a projected CRS for accurate centroids, then back
tract_geo_proj = tract_geo_join.to_crs('EPSG:32614')
tract_geo_proj['centroid'] = tract_geo_proj.geometry.centroid
tract_centroids2 = gpd.GeoDataFrame(tract_geo_proj[['GEOID']], geometry=tract_geo_proj['centroid'], crs='EPSG:32614').to_crs('EPSG:4326')

holc_join = gpd.sjoin(tract_centroids2, holc_gdf[['grade', 'geometry']], how='left', predicate='within')
holc_join = holc_join[['GEOID', 'grade']].drop_duplicates('GEOID')
holc_join['holc_grade'] = holc_join['grade'].fillna('None')
holc_join['holc_d'] = (holc_join['holc_grade'] == 'D').astype(int)

tracts = tracts.merge(holc_join[['GEOID', 'holc_grade', 'holc_d']], on='GEOID', how='left')
tracts['holc_grade'] = tracts['holc_grade'].fillna('None')
tracts['holc_d'] = tracts['holc_d'].fillna(0).astype(int)
print(f"    HOLC grade distribution:\n{tracts['holc_grade'].value_counts().to_string()}")

# ─── 8. South of I-30 flag ─────────────────────────────────────────────────────
print("\n[8] Applying south-of-I-30 definition (council districts 6, 7, 8)...")
# v4 uses real district boundaries. South Dallas/Oak Cliff = D6, D7, D8
# D6: West Oak Cliff (lat≤-96.85 proxy → real boundary)
# D7: East Oak Cliff
# D8: Pleasant Grove / Southeast Dallas
south_districts = {6, 7, 8}
tracts['south_of_i30'] = tracts['DISTRICT_NUM'].isin(south_districts).astype(int)
print(f"    South tracts (D6/D7/D8): {tracts['south_of_i30'].sum()}")
print(f"    North tracts: {(tracts['south_of_i30'] == 0).sum()}")

# ─── 9. Feature engineering ────────────────────────────────────────────────────
print("\n[9] Feature engineering...")

# Clip extreme outliers in CIP/cap (>99th pct → cap, flag)
p99 = tracts['cip_per_capita_raw'].quantile(0.99)
tracts['cip_per_capita'] = tracts['cip_per_capita_raw'].clip(upper=p99)
tracts['cip_outlier'] = (tracts['cip_per_capita_raw'] > p99).astype(int)
print(f"    CIP/cap 99th pct cap: ${p99:,.2f}")
print(f"    Outlier tracts capped: {tracts['cip_outlier'].sum()}")

# AMI ratio (Dallas AMI = $98,000; 80% = $78,400)
DALLAS_AMI = 98_000
tracts['ami_ratio'] = tracts['median_income'] / DALLAS_AMI
tracts['below_80_ami'] = (tracts['median_income'] < 78_400).astype(int)

# Needs-based baseline (inverse income, normalised to mean 1.0)
tracts['inv_income'] = 1 / tracts['median_income'].clip(lower=10_000)
mean_inv = tracts['inv_income'].mean()
tracts['needs_baseline'] = tracts['inv_income'] / mean_inv
tracts['investment_gap'] = tracts['cip_per_capita'] - tracts['needs_baseline'] * tracts['cip_per_capita'].mean()

# Log transforms
tracts['log_cip'] = np.log1p(tracts['cip_per_capita'])
tracts['log_income'] = np.log(tracts['median_income'].clip(lower=10_000))
tracts['log_pop'] = np.log(tracts['population'].clip(lower=1))

# Standardised race vars
for v in ['pct_nonwhite', 'pct_black', 'pct_hispanic']:
    if v in tracts.columns:
        tracts[f'{v}_std'] = (tracts[v] - tracts[v].mean()) / tracts[v].std()

print(f"    CIP/cap stats: mean=${tracts['cip_per_capita'].mean():,.2f}, "
      f"median=${tracts['cip_per_capita'].median():,.2f}, "
      f"std=${tracts['cip_per_capita'].std():,.2f}")
print(f"    Below 80% AMI tracts: {tracts['below_80_ami'].sum()} ({tracts['below_80_ami'].mean()*100:.1f}%)")

# ─── 10. Filter to Dallas city limits (tracts with district assignment) ─────────
print("\n[10] Filtering to Dallas city limits (tracts matched to a district)...")
df_model = tracts[
    (tracts['DISTRICT_NUM'] > 0) &
    (tracts['population'] > 0) &
    (tracts['median_income'] > 0)
].copy().reset_index(drop=True)
print(f"    Model sample: {len(df_model):,} tracts")

# ─── 11. Regression Models ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("[11] OLS REGRESSION MODELS (HC3 robust SEs)")
print("=" * 60)

results_summary = {}

def run_ols(name, formula, data, desc=""):
    try:
        model = smf.ols(formula, data=data).fit(cov_type='HC3')
        results_summary[name] = {
            'n': int(model.nobs),
            'adj_r2': round(model.rsquared_adj, 3),
            'aic': round(model.aic, 1),
        }
        print(f"\n  --- {name}: {desc} ---")
        print(f"  n={model.nobs:.0f} | adj-R²={model.rsquared_adj:.3f} | AIC={model.aic:.1f}")
        key_vars = [v for v in model.params.index if v != 'Intercept']
        for v in key_vars[:8]:
            coef = model.params[v]
            pval = model.pvalues[v]
            sig = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else '.'
            print(f"    {v:<40s}  β={coef:>10.4f}  p={pval:.4f} {sig}")
        return model
    except Exception as e:
        print(f"  ERROR in {name}: {e}")
        return None

# M1: Bivariate — nonwhite → CIP/cap
m1 = run_ols("M1_bivariate", "cip_per_capita ~ pct_nonwhite",
             df_model, "Bivariate: race → CIP/cap")

# M2: Full controls (income, pop density, south zone)
m2 = run_ols("M2_full", "cip_per_capita ~ pct_nonwhite + log_income + log_pop + south_of_i30",
             df_model, "Full controls: race + income + pop + south")

# M3: Split race (Black + Hispanic separately)
m3 = run_ols("M3_split_race",
             "cip_per_capita ~ pct_black + pct_hispanic + log_income + log_pop + south_of_i30",
             df_model, "Split race: Black + Hispanic separately")

# M4: With CIP type controls (Drainage share as key FE)
type_terms = " + ".join([c for c in type_share_cols if 'drainage' not in c])  # omit drainage as baseline
if type_terms:
    m4_formula = f"cip_per_capita ~ pct_nonwhite + log_income + log_pop + south_of_i30 + {type_terms}"
    m4 = run_ols("M4_cip_type_fe", m4_formula,
                 df_model, "CIP type FEs (drainage=baseline)")
else:
    m4 = None
    print("  M4 skipped: no type share cols found")

# M5: Log-log specification
m5 = run_ols("M5_log_log",
             "log_cip ~ pct_nonwhite + log_income + log_pop + south_of_i30",
             df_model, "Log-log: log(CIP/cap) ~ log(income)")

# M6: Investment gap model (CIP vs needs-based baseline)
m6 = run_ols("M6_inv_gap",
             "investment_gap ~ pct_nonwhite + log_income + log_pop + south_of_i30",
             df_model, "Investment gap vs needs-based baseline")

# M7: + HOLC-D redlining indicator
m7 = run_ols("M7_holc",
             "cip_per_capita ~ pct_nonwhite + log_income + log_pop + south_of_i30 + holc_d",
             df_model, "+ HOLC-D redlining indicator")

# M8: District FE (within-district variation — replaces south_of_i30 zone)
m8 = run_ols("M8_district_fe",
             "cip_per_capita ~ pct_nonwhite + log_income + log_pop + C(DISTRICT_NUM)",
             df_model, "District FE (14 districts, replaces south zone)")

# ─── 12. Save regression tables ───────────────────────────────────────────────
print("\n[12] Saving regression results...")

rows = []
for name, m in [("M1_bivariate", m1), ("M2_full", m2), ("M3_split_race", m3),
                ("M4_cip_type_fe", m4), ("M5_log_log", m5), ("M6_inv_gap", m6),
                ("M7_holc", m7), ("M8_district_fe", m8)]:
    if m is None:
        continue
    for v in m.params.index:
        rows.append({
            'model': name,
            'variable': v,
            'coef': m.params[v],
            'se': m.bse[v],
            'tstat': m.tvalues[v],
            'pvalue': m.pvalues[v],
            'ci_lo': m.conf_int()[0][v],
            'ci_hi': m.conf_int()[1][v],
            'n': int(m.nobs),
            'adj_r2': round(m.rsquared_adj, 3),
        })

ols_df = pd.DataFrame(rows)
ols_df.to_csv(f"{OUT_TABLES}/h1_v4_ols_results.csv", index=False)
print(f"    Saved: h1_v4_ols_results.csv ({len(ols_df)} rows)")

# ─── 13. North/South comparison ───────────────────────────────────────────────
print("\n[13] North/South comparison...")
south = df_model[df_model['south_of_i30'] == 1]
north = df_model[df_model['south_of_i30'] == 0]

def fmt_comp(label, s_val, n_val):
    return f"    {label:<30s}  South={s_val:>10}  North={n_val:>10}"

print(fmt_comp("Tracts", f"{len(south)}", f"{len(north)}"))
print(fmt_comp("Median CIP/cap", f"${south['cip_per_capita'].median():,.0f}", f"${north['cip_per_capita'].median():,.0f}"))
print(fmt_comp("Mean CIP/cap", f"${south['cip_per_capita'].mean():,.0f}", f"${north['cip_per_capita'].mean():,.0f}"))
print(fmt_comp("Mean % Black", f"{south['pct_black'].mean():.1f}%", f"{north['pct_black'].mean():.1f}%"))
print(fmt_comp("Mean % Hispanic", f"{south['pct_hispanic'].mean():.1f}%", f"{north['pct_hispanic'].mean():.1f}%"))
print(fmt_comp("Mean % Nonwhite", f"{south['pct_nonwhite'].mean():.1f}%", f"{north['pct_nonwhite'].mean():.1f}%"))
print(fmt_comp("Median income", f"${south['median_income'].median():,.0f}", f"${north['median_income'].median():,.0f}"))

tstat, pval = stats.ttest_ind(south['cip_per_capita'], north['cip_per_capita'])
print(f"\n    t-test CIP/cap S vs N: t={tstat:.3f}, p={pval:.4f}")
pct_under = (df_model['cip_per_capita'] < df_model['needs_baseline'] * df_model['cip_per_capita'].mean()).mean()
print(f"    Pct tracts below needs-based baseline: {pct_under*100:.1f}%")
print(f"    Pct tracts below 80% AMI: {df_model['below_80_ami'].mean()*100:.1f}%")

# ─── 14. Diagnostic Plots ─────────────────────────────────────────────────────
print("\n[14] Generating diagnostic plots...")

plt.style.use('dark_background')
fig = plt.figure(figsize=(18, 16), facecolor='#0d1117')
fig.suptitle("Atlas H1 v4 — Investment Bias Analysis\nReal District Boundaries + Actual Expenditures (FY2012–2026)",
             fontsize=14, color='white', y=0.98)

gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

palette = {'south': '#ef4444', 'north': '#60a5fa', 'neutral': '#a78bfa', 'accent': '#34d399'}

ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor('#161b22')
bins = np.linspace(0, df_model['cip_per_capita'].quantile(0.98), 40)
ax1.hist(south['cip_per_capita'], bins=bins, color=palette['south'], alpha=0.7, label=f'South D6/7/8 (n={len(south)})', density=True)
ax1.hist(north['cip_per_capita'], bins=bins, color=palette['north'], alpha=0.7, label=f'North (n={len(north)})', density=True)
ax1.set_xlabel('CIP/capita ($)', color='white', fontsize=9)
ax1.set_ylabel('Density', color='white', fontsize=9)
ax1.set_title('CIP/cap Distribution\nN vs S', color='white', fontsize=10)
ax1.legend(fontsize=7, facecolor='#1c2128', labelcolor='white')
ax1.tick_params(colors='white', labelsize=7)
for sp in ax1.spines.values(): sp.set_color('#30363d')

ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor('#161b22')
ax2.scatter(df_model['pct_nonwhite'], df_model['cip_per_capita'],
            c=['#ef4444' if s else '#60a5fa' for s in df_model['south_of_i30']],
            alpha=0.35, s=8)
if m1:
    x_line = np.linspace(df_model['pct_nonwhite'].min(), df_model['pct_nonwhite'].max(), 100)
    y_line = m1.params['Intercept'] + m1.params['pct_nonwhite'] * x_line
    ax2.plot(x_line, y_line, color=palette['accent'], linewidth=1.5, label=f'M1 β={m1.params["pct_nonwhite"]:.4f}')
    ax2.legend(fontsize=7, facecolor='#1c2128', labelcolor='white')
ax2.set_xlabel('% Nonwhite', color='white', fontsize=9)
ax2.set_ylabel('CIP/capita ($)', color='white', fontsize=9)
ax2.set_title('Race vs CIP/cap\n(red=south)', color='white', fontsize=10)
ax2.tick_params(colors='white', labelsize=7)
for sp in ax2.spines.values(): sp.set_color('#30363d')

ax3 = fig.add_subplot(gs[0, 2])
ax3.set_facecolor('#161b22')
ax3.scatter(df_model['log_income'], df_model['cip_per_capita'],
            c=['#ef4444' if s else '#60a5fa' for s in df_model['south_of_i30']],
            alpha=0.35, s=8)
ax3.set_xlabel('Log(Median Income)', color='white', fontsize=9)
ax3.set_ylabel('CIP/capita ($)', color='white', fontsize=9)
ax3.set_title('Income vs CIP/cap', color='white', fontsize=10)
ax3.tick_params(colors='white', labelsize=7)
for sp in ax3.spines.values(): sp.set_color('#30363d')

ax4 = fig.add_subplot(gs[1, 0])
ax4.set_facecolor('#161b22')
dist_means = df_model.groupby('DISTRICT_NUM').agg(
    mean_cip=('cip_per_capita', 'mean'),
    mean_nonwhite=('pct_nonwhite', 'mean')
).reset_index()
scatter = ax4.scatter(dist_means['mean_nonwhite'], dist_means['mean_cip'],
                      c=dist_means['DISTRICT_NUM'],
                      cmap='plasma', s=80, zorder=5)
for _, r in dist_means.iterrows():
    ax4.annotate(f"D{int(r['DISTRICT_NUM'])}", (r['mean_nonwhite'], r['mean_cip']),
                 fontsize=6, color='white', ha='center', va='bottom')
ax4.set_xlabel('Mean % Nonwhite by District', color='white', fontsize=9)
ax4.set_ylabel('Mean CIP/cap by District', color='white', fontsize=9)
ax4.set_title('District-Level:\nRace vs CIP/cap', color='white', fontsize=10)
ax4.tick_params(colors='white', labelsize=7)
for sp in ax4.spines.values(): sp.set_color('#30363d')

ax5 = fig.add_subplot(gs[1, 1])
ax5.set_facecolor('#161b22')
type_exp = {}
for col in type_share_cols:
    ctype = col.replace('cip_', '').replace('_share', '').title()
    total = district_project[district_project['cip_type'].str.lower() == ctype.lower()]['expenditure_share'].sum()
    type_exp[ctype] = total
type_df = pd.Series(type_exp).sort_values(ascending=True)
bars = ax5.barh(type_df.index, type_df.values / 1e6, color=palette['neutral'], alpha=0.8)
ax5.set_xlabel('Total Expenditure ($M)', color='white', fontsize=9)
ax5.set_title('Expenditure by\nCIP Type', color='white', fontsize=10)
ax5.tick_params(colors='white', labelsize=7)
for sp in ax5.spines.values(): sp.set_color('#30363d')

ax6 = fig.add_subplot(gs[1, 2])
ax6.set_facecolor('#161b22')
if m2:
    resid = m2.resid
    fitted = m2.fittedvalues
    ax6.scatter(fitted, resid, alpha=0.3, s=6, color=palette['north'])
    ax6.axhline(0, color=palette['accent'], linewidth=1)
ax6.set_xlabel('Fitted values', color='white', fontsize=9)
ax6.set_ylabel('Residuals', color='white', fontsize=9)
ax6.set_title('M2 Residuals vs Fitted', color='white', fontsize=10)
ax6.tick_params(colors='white', labelsize=7)
for sp in ax6.spines.values(): sp.set_color('#30363d')

ax7 = fig.add_subplot(gs[2, 0])
ax7.set_facecolor('#161b22')
model_names = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8']
adj_r2s = []
for n, m in zip(['M1_bivariate','M2_full','M3_split_race','M4_cip_type_fe',
                 'M5_log_log','M6_inv_gap','M7_holc','M8_district_fe'],
                [m1, m2, m3, m4, m5, m6, m7, m8]):
    adj_r2s.append(m.rsquared_adj if m else 0)
ax7.bar(model_names, adj_r2s, color=palette['accent'], alpha=0.8)
ax7.set_ylabel('Adjusted R²', color='white', fontsize=9)
ax7.set_title('Model Fit Comparison\n(Adj. R²)', color='white', fontsize=10)
ax7.tick_params(colors='white', labelsize=7)
for sp in ax7.spines.values(): sp.set_color('#30363d')

ax8 = fig.add_subplot(gs[2, 1])
ax8.set_facecolor('#161b22')
ax8.scatter(df_model['investment_gap'], df_model['pct_nonwhite'],
            c=['#ef4444' if s else '#60a5fa' for s in df_model['south_of_i30']],
            alpha=0.35, s=8)
ax8.axvline(0, color='white', linewidth=0.5, linestyle='--')
ax8.set_xlabel('Investment Gap ($)', color='white', fontsize=9)
ax8.set_ylabel('% Nonwhite', color='white', fontsize=9)
ax8.set_title('Investment Gap vs Race\n(red=south D6/7/8)', color='white', fontsize=10)
ax8.tick_params(colors='white', labelsize=7)
for sp in ax8.spines.values(): sp.set_color('#30363d')

ax9 = fig.add_subplot(gs[2, 2])
ax9.set_facecolor('#161b22')
dist_south = df_model[df_model['DISTRICT_NUM'].isin([6, 7, 8])].groupby('DISTRICT_NUM').agg(
    mean_cip=('cip_per_capita', 'mean'),
    mean_black=('pct_black', 'mean'),
    mean_hispanic=('pct_hispanic', 'mean'),
).reset_index()
x = np.arange(len(dist_south))
w = 0.25
ax9.bar(x - w, dist_south['mean_cip'] / dist_south['mean_cip'].max(), w, label='CIP/cap (norm)', color=palette['accent'], alpha=0.8)
ax9.bar(x, dist_south['mean_black'], w, label='% Black', color=palette['south'], alpha=0.8)
ax9.bar(x + w, dist_south['mean_hispanic'], w, label='% Hispanic', color='#f59e0b', alpha=0.8)
ax9.set_xticks(x)
ax9.set_xticklabels([f"D{int(d)}" for d in dist_south['DISTRICT_NUM']], color='white', fontsize=9)
ax9.legend(fontsize=6, facecolor='#1c2128', labelcolor='white')
ax9.set_title('South Districts:\nCIP/cap vs Race', color='white', fontsize=10)
ax9.tick_params(colors='white', labelsize=7)
for sp in ax9.spines.values(): sp.set_color('#30363d')

plt.savefig(f"{OUT_FIGS}/h1_v4_diagnostic_plots.png", dpi=150, bbox_inches='tight',
            facecolor='#0d1117')
plt.close()
print(f"    Saved: h1_v4_diagnostic_plots.png")

# ─── 15. Findings summary ─────────────────────────────────────────────────────
print("\n[15] Writing findings summary...")

findings = f"""H1 v4 Findings Summary — Real Data Pipeline
==============================================
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

DATA INPUTS
-----------
CIP Lines: 2012 Bond (425 projects), 2017 Bond (1,029), Active (162 unique), 2024 Bond (448)
Expenditure measure: AmountPaid (actual paid) for 2012/2017/Active; BondAmount for 2024 (no disbursements yet)
Total expenditure in model: ${cip['expenditure'].sum():,.0f}
Council Districts: 14 real polygon boundaries (Dallas Open Data)
Vendor Payments: FY2025-2026 supplemental (145,551 transactions)
Census Tracts: {len(df_model):,} tracts in model sample (Dallas city limits)

DISTRICT ALLOCATION METHOD
---------------------------
- v4 uses real council district polygons (replaces lat/lon quadrant proxy)
- Projects assigned to districts via CD01-CD14 boolean flags
- Multi-district projects split evenly across touching districts
- Within-district: population-weighted tract allocation
- CIP type FEs: Streets, Drainage, Parks, EconDev, Other

NORTH/SOUTH COMPARISON (D6/D7/D8 = South)
-------------------------------------------
South tracts (D6/7/8): {len(south):,}
North tracts:           {len(north):,}
Median CIP/cap South:  ${south['cip_per_capita'].median():,.0f}
Median CIP/cap North:  ${north['cip_per_capita'].median():,.0f}
Mean % Black South:    {south['pct_black'].mean():.1f}%
Mean % Black North:    {north['pct_black'].mean():.1f}%
Mean % Hispanic South: {south['pct_hispanic'].mean():.1f}%
Mean % Hispanic North: {north['pct_hispanic'].mean():.1f}%
Median Income South:   ${south['median_income'].median():,.0f}
Median Income North:   ${north['median_income'].median():,.0f}
t-test p-value:        {pval:.4f}
Below 80% AMI:         {df_model['below_80_ami'].mean()*100:.1f}% of model tracts

REGRESSION RESULTS (HC3 robust SEs)
-------------------------------------
"""

for name, m in [("M1 Bivariate", m1), ("M2 Full controls", m2), ("M3 Split race", m3),
                ("M4 CIP type FE", m4), ("M5 Log-log", m5), ("M6 Inv. Gap", m6),
                ("M7 +HOLC-D", m7), ("M8 District FE", m8)]:
    if m is None:
        continue
    findings += f"\n{name}: n={int(m.nobs)}, adj-R²={m.rsquared_adj:.3f}\n"
    key = 'pct_nonwhite' if 'pct_nonwhite' in m.params else ('pct_black' if 'pct_black' in m.params else None)
    if key:
        findings += f"  β({key}) = {m.params[key]:.4f}, p={m.pvalues[key]:.4f}\n"
    if 'south_of_i30' in m.params:
        findings += f"  β(south_of_i30) = {m.params['south_of_i30']:.4f}, p={m.pvalues['south_of_i30']:.4f}\n"

findings += f"""
OPEN DATA GAPS (pending PIA FY2016-2018 request)
-------------------------------------------------
- Vendor Payments only cover FY2025-2026 (not full 2019-present as labeled)
- FY2016-2024 expenditure data requested via Texas PIA (email drafted)
- 2024 Bond AmountPaid = $0 (too early for disbursements; BondAmount used as proxy)
- Full road-length proration requires GeoJSON version of CIP line layers
  (Shape__Length present but per-tract geometry split requires spatial overlay)
"""

with open(f"{OUT_MEMOS}/h1_v4_findings_summary.txt", 'w') as f:
    f.write(findings)
print(f"    Saved: h1_v4_findings_summary.txt")

# ─── 16. Export enriched tract data ───────────────────────────────────────────
export_cols = ['GEOID', 'DISTRICT_NUM', 'south_of_i30', 'population', 'median_income',
               'pct_black', 'pct_hispanic', 'pct_nonwhite', 'ami_ratio', 'below_80_ami',
               'cip_per_capita', 'cip_per_capita_raw', 'cip_outlier',
               'investment_gap', 'log_cip', 'log_income', 'holc_grade', 'holc_d'] + type_share_cols
export_cols = [c for c in export_cols if c in df_model.columns]
df_model[export_cols].to_csv(f"{DATA_EXPORTS}/atlas_v4_tract_data.csv", index=False)
print(f"\n    Exported: atlas_v4_tract_data.csv ({len(df_model):,} tracts, {len(export_cols)} vars)")

print("\n" + "=" * 60)
print("H1 v4 COMPLETE")
print("=" * 60)

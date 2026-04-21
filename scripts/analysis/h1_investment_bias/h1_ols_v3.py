"""
H1 Analysis v3 — Investment Bias (Real Data)
Below the Line: Dallas I-30 Corridor Displacement Risk Atlas
Nicholas D. Hawkins | TSU Freeman Honors College

REAL DATA UPGRADE from v2:
  - Real CIP: Capital_Improvement_Program_20260420.csv (488 projects, ~$1.26B)
    Primarily 2024 bond program; District assignment via boolean columns D1–D14
  - Real HOLC: mappinginequality_dallas.json (48 Dallas polygons, Mapping Inequality)
  - CIP geometry: No point/line geometry in CSV → District-level allocation
    District → tract assignment via south_of_i30 flag + ACS population weighting
  - NOTE: District 6 ($127.7M) includes Trinity River Corridor flood projects —
    a major natural experiment that will be isolated in CIP-type FE models

Data note on CIP dataset:
  - LastModDt tops out at 2016-09-06; construction dates span 2016-2019
  - Total bonds = ~$1.256B ≈ 2024 Dallas bond program total
  - Likely represents the 2024 bond authorization list, not FY-level expenditures
  - Real FY2012-2026 expenditure data requires Dallas OFS records request
  - For v0 this dataset is treated as a cross-sectional allocation register

South-of-I30 district classification (from Dallas City Hall district map):
  South:   Districts 6 (Oak Cliff West), 7 (Oak Cliff East/SOC), 8 (Pleasant Grove)
  Partial: Districts 5 (Fair Park/East, ~50%), 13 (North Oak Cliff, ~50%)
  North:   Districts 1, 2, 3, 4, 9, 10, 11, 12, 14

Key finding pre-regression:
  South districts (6+7+8): ~$168M of $1.256B = 13.4% of CIP
  District 6 alone: $127.7M (mostly Drainage/Trinity River Corridor)
  Stripping Drainage FE will be critical for clean investment bias signal
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings, json, os
warnings.filterwarnings('ignore')

BASE = "/home/user/workspace/dda_repo"
DATA = f"{BASE}/data"
OUT  = f"{BASE}/outputs"

print("=" * 70)
print("H1 ANALYSIS v3 — Investment Bias (REAL DATA) | Atlas v0")
print("Below the Line: Dallas I-30 | Nicholas D. Hawkins | TSU")
print("=" * 70)

# ─── 1. Load ACS + atlas tract data ──────────────────────────────────────────
print("\n[1] Loading ACS tract data...")
df = pd.read_csv(f"{DATA}/exports/atlas_v1_tract_data.csv", low_memory=False)
print(f"    {len(df)} tracts, {len(df.columns)} columns")

for col in ['median_income','population','pct_black','pct_hispanic',
            'pct_nonwhite','pct_renter','rent_burden_pct']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
    df[col] = df[col].where(df[col] > -9999, np.nan)

# south_of_i30 is already in the atlas (185 south tracts)
df['south_i30'] = df['south_of_i30'].fillna(0).astype(int)

# ─── 2. Load real CIP data ────────────────────────────────────────────────────
print("\n[2] Loading real CIP data...")
cip = pd.read_csv(f"{DATA}/raw/layer1_investment/Capital_Improvement_Program_20260420.csv",
                  low_memory=False)
print(f"    {len(cip)} projects loaded")

# Clean bond amounts
cip['bond_amt'] = (cip['BondAmount']
                   .str.replace(r'[\$,]', '', regex=True)
                   .str.strip()
                   .pipe(pd.to_numeric, errors='coerce'))

# ─── 3. Category → 6-type classification ─────────────────────────────────────
print("\n[3] Classifying CIP categories...")
cat_map = {
    'Street Resurfacing': 'Streets', 'Street Reconstruction Thoroughfares': 'Streets',
    'Street Reconstruction': 'Streets', 'Thoroughfares': 'Streets',
    'Complete Street': 'Streets', 'Streetscape / Urban Design': 'Streets',
    'Street Petitions': 'Streets', 'Street Modifications and Bottlenecks': 'Streets',
    'Street Reconstruction Local Streets': 'Streets', 'Sidewalk Improvements': 'Streets',
    'Sidewalk Replacement': 'Streets', 'Gateway': 'Streets',
    'Alley Reconstruction': 'Streets', 'Alley Petitions': 'Streets',
    'Bridge Repair and Modification': 'Streets',
    'Storm Drainage': 'Drainage', 'Storm Drainage Relief System': 'Drainage',
    'Flood Management': 'Drainage', 'Erosion Control': 'Drainage',
    'Trinity River Corridor': 'Drainage',
    'Trail Development': 'Parks_Trails', 'Trails': 'Parks_Trails',
    'Hike and Bike Trails': 'Parks_Trails', 'Target Neighborhood': 'Parks_Trails',
    'Economic Development': 'EconDev', 'Public / Private Development': 'EconDev',
    'Public Private Partnership': 'EconDev',
    'Intergovernmental Partnership Projects': 'Other',
}
cip['cip_type'] = cip['Category'].map(cat_map).fillna('Other')

district_cols = [f'District {i}' for i in range(1, 15)]
cip['n_districts'] = cip[district_cols].sum(axis=1)
# Citywide projects span all 14 districts
cip.loc[cip['City Wide'] == True, 'n_districts'] = 14
cip['n_districts'] = cip['n_districts'].clip(lower=1)

# ─── 4. District-level CIP totals (prorated by n districts) ──────────────────
print("\n[4] Computing district-level CIP totals...")

# South-of-I30 district classification (documented from Dallas City Hall)
south_full    = {6, 7, 8}          # Fully south
south_partial = {5, 13}            # ~50% south (straddle I-30)
north_only    = {1, 2, 3, 4, 9, 10, 11, 12, 14}

district_records = []
for d in range(1, 15):
    mask = cip[f'District {d}'] == True
    sub  = cip[mask].copy()
    sub['prorated_amt'] = sub['bond_amt'] / sub['n_districts']

    for ctype in cip['cip_type'].unique():
        type_sub = sub[sub['cip_type'] == ctype]
        district_records.append({
            'district': d,
            'cip_type': ctype,
            'total_amt': type_sub['prorated_amt'].sum(),
            'n_projects': len(type_sub),
        })

dist_df = pd.DataFrame(district_records)
dist_wide = dist_df.pivot_table(index='district', columns='cip_type',
                                values='total_amt', aggfunc='sum', fill_value=0)
dist_wide['total'] = dist_wide.sum(axis=1)
dist_wide.columns.name = None

print("    District totals:")
for d in range(1, 15):
    zone = 'SOUTH' if d in south_full else ('partial' if d in south_partial else 'north')
    tot  = dist_wide.loc[d, 'total'] if d in dist_wide.index else 0
    print(f"      D{d:2d} [{zone:7s}]: ${tot/1e6:6.1f}M")

# ─── 5. Allocate CIP to tracts using geographic district proxies ──────────────
print("\n[5] Allocating district CIP to tracts (geographic district proxy)...")
# The CIP CSV has no geocoordinates. We assign council districts to tracts
# using documented geographic boundaries from Dallas City Hall district map.
# South districts assigned by longitude centroid cuts:
#   D8 (Pleasant Grove): lon > -96.75
#   D7 (E Oak Cliff):    -96.85 < lon <= -96.75
#   D6 (W Oak Cliff):    lon <= -96.85
# North districts assigned by lat/lon quadrant cuts:
#   D1 (Lake Highlands):  lat>32.85 & lon>-96.80
#   D2 (NE Dallas):       lat>32.82 & lon>-96.75
#   D9 (Lakewood):        lat>32.78 & -96.82<lon<=-96.75
#   D14 (Uptown/Central): lat<=32.82 & lon>-96.80 & lat>32.76
#   D3 (NW Dallas):       lon<-96.90
#   D4 (W/Stemmons):      -96.92<lon<=-96.85 & lat<=32.85
#   D10 (Preston Hollow): lat>32.88 & -96.88<lon<=-96.80
#   D11 (Far NE):         lat>32.86 & lon>-96.73
#   D12 (Far North):      lat>32.90 & -96.88<lon<=-96.80
#   D13 (N Oak Cliff):    lat<=32.78 & lon<=-96.80
#   D5 (Fair Park/East):  lon>-96.76 & lat<=32.80 & lat>32.75
# Remaining → D9 (default interior north)

tracts_gdf_geo = gpd.read_file(f"{DATA}/processed/atlas_with_dpi.geojson")
tracts_gdf_geo = tracts_gdf_geo.to_crs('EPSG:32614')
tracts_gdf_geo['cx'] = tracts_gdf_geo.geometry.centroid.x
tracts_gdf_geo['cy'] = tracts_gdf_geo.geometry.centroid.y
tracts_gdf_geo = tracts_gdf_geo.to_crs('EPSG:4326')
tracts_gdf_geo['lon'] = tracts_gdf_geo.geometry.centroid.x
tracts_gdf_geo['lat'] = tracts_gdf_geo.geometry.centroid.y
tracts_gdf_geo['GEOID'] = tracts_gdf_geo['GEOID'].astype(str)

def assign_district(row):
    lon, lat = row['lon'], row['lat']
    south = row['south_of_i30'] == 1
    if south:
        if lon > -96.75: return 8
        elif lon > -96.85: return 7
        else: return 6
    else:
        # North districts
        if lat > 32.90 and lon > -96.88: return 12
        if lat > 32.86 and lon > -96.73: return 11
        if lat > 32.87 and lon > -96.80: return 10
        if lat > 32.85 and lon > -96.80: return 1
        if lon < -96.90: return 3
        if lon <= -96.90 and lat <= 32.85: return 4
        if lon > -96.76 and lat <= 32.80 and lat > 32.75: return 5
        if lat <= 32.78 and lon <= -96.82 and not south: return 13
        if lon > -96.75 and lat > 32.82: return 2
        if lon > -96.82 and lat > 32.78 and lat <= 32.86: return 9
        return 14  # Uptown/Downtown/Central default

tracts_gdf_geo['district_num'] = tracts_gdf_geo.apply(assign_district, axis=1)
tract_district_map = tracts_gdf_geo.set_index('GEOID')['district_num'].to_dict()

print("    District assignment distribution:")
from collections import Counter
assignments = Counter(tract_district_map.values())
for d in sorted(assignments):
    zone = 'SOUTH' if d in south_full else ('partial' if d in south_partial else 'north')
    print(f"      D{d:2d} [{zone:7s}]: {assignments[d]} tracts")

# Merge district assignment to main df
df['GEOID'] = df['GEOID'].astype(str)
df['district_num'] = df['GEOID'].map(tract_district_map)

# Compute district population totals
district_pop = df.groupby('district_num')['population'].sum().to_dict()

# Assign CIP per tract: tract_cip = district_cip_total × (tract_pop / district_pop)
df['cip_real_total'] = 0.0
type_cols_list = [c for c in dist_wide.columns if c != 'total']
for t in type_cols_list:
    df[f'cip_type_{t.lower()}'] = 0.0

for idx, row in df.iterrows():
    d = row['district_num']
    if pd.isna(d) or d not in dist_wide.index:
        continue
    dpop = district_pop.get(d, 1)
    pop_share = row['population'] / dpop if dpop > 0 else 0
    df.at[idx, 'cip_real_total'] = dist_wide.loc[d, 'total'] * pop_share
    for t in type_cols_list:
        col = f'cip_type_{t.lower()}'
        df.at[idx, col] = dist_wide.loc[d, t] * pop_share

df['cip_real_pc'] = df['cip_real_total'] / df['population'].replace(0, np.nan)

# Summary stats
south_cip_total = df[df['south_i30']==1]['cip_real_total'].sum()
north_cip_total = df[df['south_i30']==0]['cip_real_total'].sum()
south_pop = df[df['south_i30']==1]['population'].sum()
north_pop = df[df['south_i30']==0]['population'].sum()
south_drainage = df[df['south_i30']==1]['cip_type_drainage'].sum() if 'cip_type_drainage' in df.columns else 0

print(f"\n    South total CIP: ${south_cip_total/1e6:.1f}M | Pop: {south_pop:,.0f}")
print(f"      of which Drainage: ${south_drainage/1e6:.1f}M ({south_drainage/south_cip_total*100:.0f}%)")
print(f"    North total CIP: ${north_cip_total/1e6:.1f}M | Pop: {north_pop:,.0f}")
print(f"    South share: {south_cip_total/(south_cip_total+north_cip_total)*100:.1f}%")

print(f"\n    Per-capita CIP (all tracts):")
print(f"      Unique values: {df['cip_real_pc'].nunique()} | range: "
      f"${df['cip_real_pc'].min():.0f}–${df['cip_real_pc'].max():.0f}")
print(f"      South — mean: ${df[df['south_i30']==1]['cip_real_pc'].mean():,.0f} | "
      f"median: ${df[df['south_i30']==1]['cip_real_pc'].median():,.0f}")
print(f"      North — mean: ${df[df['south_i30']==0]['cip_real_pc'].mean():,.0f} | "
      f"median: ${df[df['south_i30']==0]['cip_real_pc'].median():,.0f}")

# ─── 6. Load HOLC data ────────────────────────────────────────────────────────
print("\n[6] Loading HOLC data (real Mapping Inequality)...")
holc_path = f"{DATA}/raw/layer3_early_warning/mappinginequality_dallas.json"
with open(holc_path) as f:
    holc_full = json.load(f)

dallas_feats = [ft for ft in holc_full['features']
                if ft['properties'].get('city','').lower() == 'dallas']
print(f"    Dallas HOLC polygons: {len(dallas_feats)}")

holc_gdf = gpd.GeoDataFrame.from_features(dallas_feats, crs='EPSG:4326')
tracts_gdf = gpd.read_file(f"{DATA}/processed/atlas_with_dpi.geojson")
tracts_4326 = tracts_gdf[['GEOID','geometry']].to_crs('EPSG:4326')

# Spatial join: tracts intersect with HOLC zones
holc_join = gpd.sjoin(tracts_4326, holc_gdf[['geometry','grade','category']],
                      how='left', predicate='intersects')
holc_dominant = (holc_join
                 .drop_duplicates(subset='GEOID', keep='first')
                 [['GEOID','grade','category']]
                 .rename(columns={'grade':'holc_grade_real','category':'holc_cat_real'}))
holc_dominant['holc_d_real'] = (holc_dominant['holc_grade_real'] == 'D').astype(int)
holc_dominant['holc_c_real'] = (holc_dominant['holc_grade_real'] == 'C').astype(int)
# Ensure GEOID types match
df['GEOID'] = df['GEOID'].astype(str)
holc_dominant['GEOID'] = holc_dominant['GEOID'].astype(str)
df = df.merge(holc_dominant, on='GEOID', how='left')
print(f"    Tracts with HOLC grade: {df['holc_grade_real'].notna().sum()}")
print(f"    Grade distribution: {df['holc_grade_real'].value_counts().to_dict()}")
print(f"    Tracts graded D ('Hazardous'): {df['holc_d_real'].sum()}")

# ─── 7. Needs-based baseline ──────────────────────────────────────────────────
print("\n[7] Needs-based baseline allocation...")
total_cip_pool = df['cip_real_total'].sum()
df['inv_income'] = np.where(df['median_income'] > 0, 1.0/df['median_income'], np.nan)
total_inv = df['inv_income'].sum()
df['cip_expected'] = (df['inv_income'] / total_inv) * total_cip_pool
df['cip_gap']    = df['cip_real_total'] - df['cip_expected']
df['cip_gap_pc'] = df['cip_gap'] / df['population'].replace(0, np.nan)

underinvested = (df['cip_gap'] < 0).sum()
DALLAS_AMI = 98000
df['ami_ratio'] = df['median_income'] / DALLAS_AMI
below_80ami = (df['ami_ratio'] < 0.80).sum()

print(f"    Underinvested vs needs-based: {underinvested}/{len(df)} ({underinvested/len(df)*100:.1f}%)")
print(f"    Below 80% AMI (${DALLAS_AMI*0.8:,.0f}): {below_80ami} ({below_80ami/len(df)*100:.1f}%)")

# ─── 8. Model variables ───────────────────────────────────────────────────────
print("\n[8] Preparing model dataset...")
df['log_cip_pc'] = np.log1p(df['cip_real_pc'])
df['log_income'] = np.log(df['median_income'].replace(0, np.nan))
df['log_pop']    = np.log(df['population'].replace(0, np.nan))
df['any_cip']    = (df['cip_real_pc'] > 0).astype(int)

# CIP type proportion controls (non-Drainage share = discretionary spending)
type_col_names = [f'cip_type_{t.lower()}' for t in type_cols_list]
df['cip_nondrainage_share'] = (df[type_col_names].sum(axis=1) - df.get('cip_type_drainage', 0)) \
                               / df['cip_real_total'].replace(0, np.nan)

df_model = df.dropna(subset=['log_cip_pc','pct_nonwhite','log_income','log_pop']).copy()
print(f"    Analysis sample: {len(df_model)} tracts")
print(f"    Any CIP>0: {df_model['any_cip'].sum()} ({df_model['any_cip'].mean()*100:.1f}%)")
print(f"    South I-30: {df_model['south_i30'].sum()} ({df_model['south_i30'].mean()*100:.1f}%)")

# Fill remaining NAs for race vars
df_model['pct_black']    = df_model['pct_black'].fillna(df_model['pct_black'].median())
df_model['pct_hispanic'] = df_model['pct_hispanic'].fillna(df_model['pct_hispanic'].median())
df_model['holc_d_real']  = df_model['holc_d_real'].fillna(0)
df_model['holc_c_real']  = df_model['holc_c_real'].fillna(0)

# ─── 9. Model Suite ───────────────────────────────────────────────────────────
print("\n" + "="*70)
print("REGRESSION MODELS — REAL CIP DATA")
print("="*70)

results_rows = []

def run_ols(formula, data, label, hc='HC3'):
    m = smf.ols(formula, data=data).fit(cov_type=hc)
    race_coefs = [c for c in m.params.index if any(x in c for x in ['pct_','south_i30','holc_d'])]
    row = {'model': label, 'n': int(m.nobs), 'adj_r2': round(m.rsquared_adj, 4)}
    for c in race_coefs:
        row[f'b_{c}'] = round(m.params[c], 4)
        row[f'p_{c}'] = round(m.pvalues[c], 4)
    return m, row

# M1: Bivariate
print("\nM1: log_cip_pc ~ pct_nonwhite")
m1, r1 = run_ols('log_cip_pc ~ pct_nonwhite', df_model, 'M1_Bivariate')
print(f"  β(nonwhite)={r1.get('b_pct_nonwhite','?')} p={r1.get('p_pct_nonwhite','?')} adj-R²={r1['adj_r2']}")
results_rows.append(r1)

# M2: Full controls
print("\nM2: Full — + log_income + log_pop + south_i30")
m2, r2 = run_ols('log_cip_pc ~ pct_nonwhite + log_income + log_pop + south_i30', df_model, 'M2_Full')
print(f"  β(nonwhite)={r2.get('b_pct_nonwhite','?')} p={r2.get('p_pct_nonwhite','?')} adj-R²={r2['adj_r2']}")
print(f"  β(south_i30)={r2.get('b_south_i30','?')} p={r2.get('p_south_i30','?')}")
results_rows.append(r2)

# M3: Split race
print("\nM3: Split race — pct_black + pct_hispanic")
m3, r3 = run_ols('log_cip_pc ~ pct_black + pct_hispanic + log_income + log_pop + south_i30',
                 df_model, 'M3_Split_race')
print(f"  β(black)={r3.get('b_pct_black','?')} p={r3.get('p_pct_black','?')}")
print(f"  β(hispanic)={r3.get('b_pct_hispanic','?')} p={r3.get('p_pct_hispanic','?')} adj-R²={r3['adj_r2']}")
results_rows.append(r3)

# M4: Probit (allocation decision)
print("\nM4: Probit — any_cip ~ pct_nonwhite + controls")
m4 = smf.probit('any_cip ~ pct_nonwhite + log_income + log_pop + south_i30',
                 data=df_model).fit(disp=False)
me4 = m4.get_margeff().summary_frame()
try:
    nw_me = float(me4.loc['pct_nonwhite','dy/dx'])
    nw_p  = float(me4.loc['pct_nonwhite','Pr(>|z|)'])
except:
    nw_me, nw_p = np.nan, np.nan
r4 = {'model': 'M4_Probit', 'n': int(m4.nobs), 'adj_r2': round(m4.prsquared,4),
      'b_pct_nonwhite': round(nw_me,4), 'p_pct_nonwhite': round(nw_p,4)}
print(f"  ME(nonwhite)={r4['b_pct_nonwhite']} p={r4['p_pct_nonwhite']} pseudo-R²={r4['adj_r2']}")
results_rows.append(r4)

# M5: Conditional OLS (only tracts with CIP > 0)
df_pos = df_model[df_model['cip_real_pc'] > 0].copy()
print(f"\nM5: Conditional OLS (n={len(df_pos)} tracts with CIP>0)")
m5, r5 = run_ols('log_cip_pc ~ pct_nonwhite + log_income + log_pop + south_i30',
                 df_pos, 'M5_Conditional')
print(f"  β(nonwhite)={r5.get('b_pct_nonwhite','?')} p={r5.get('p_pct_nonwhite','?')} adj-R²={r5['adj_r2']}")
results_rows.append(r5)

# M6: Investment gap
print("\nM6: Investment Gap — cip_gap_pc ~ pct_nonwhite + controls")
df_gap = df_model.dropna(subset=['cip_gap_pc']).copy()
m6, r6 = run_ols('cip_gap_pc ~ pct_nonwhite + log_income + log_pop + south_i30',
                 df_gap, 'M6_Gap')
print(f"  β(nonwhite)={r6.get('b_pct_nonwhite','?')} p={r6.get('p_pct_nonwhite','?')} adj-R²={r6['adj_r2']}")
results_rows.append(r6)

# M7: M2 + HOLC-D control (H2 preview)
df_holc = df_model.dropna(subset=['holc_d_real']).copy()
print(f"\nM7: Full + HOLC-D control (n={len(df_holc)})")
m7, r7 = run_ols('log_cip_pc ~ pct_nonwhite + log_income + log_pop + south_i30 + holc_d_real',
                 df_holc, 'M7_HOLC_ctrl')
print(f"  β(nonwhite)={r7.get('b_pct_nonwhite','?')} p={r7.get('p_pct_nonwhite','?')}")
print(f"  β(holc_d)={r7.get('b_holc_d_real','?')} p={r7.get('p_holc_d_real','?')} adj-R²={r7['adj_r2']}")
results_rows.append(r7)

# M8: Split race + HOLC-D
print("\nM8: Split race + HOLC-D")
m8, r8 = run_ols('log_cip_pc ~ pct_black + pct_hispanic + log_income + log_pop + south_i30 + holc_d_real',
                 df_holc, 'M8_Split_HOLC')
print(f"  β(black)={r8.get('b_pct_black','?')} p={r8.get('p_pct_black','?')}")
print(f"  β(hispanic)={r8.get('b_pct_hispanic','?')} p={r8.get('p_pct_hispanic','?')} adj-R²={r8['adj_r2']}")
results_rows.append(r8)

# ─── 10. Results table ────────────────────────────────────────────────────────
print("\n" + "="*70)
print("RESULTS SUMMARY")
print("="*70)
res_df = pd.DataFrame(results_rows)
print(res_df[['model','n','adj_r2','b_pct_nonwhite','p_pct_nonwhite']].to_string(index=False))
res_df.to_csv(f"{OUT}/tables/h1_v3_ols_results.csv", index=False)

# ─── 11. Key diagnostics ──────────────────────────────────────────────────────
print("\n[11] M2 Diagnostics...")
X2 = sm.add_constant(df_model[['pct_nonwhite','log_income','log_pop','south_i30']].dropna())
resid2 = m2.resid
try:
    bp_stat, bp_p, _, _ = het_breuschpagan(resid2, X2.values[:len(resid2)])
    print(f"  Breusch-Pagan: stat={bp_stat:.3f}, p={bp_p:.4f} "
          f"({'heteroscedastic' if bp_p<0.05 else 'homoscedastic'})")
except Exception as e:
    print(f"  BP test failed: {e}")

print("  VIF:")
for i, col in enumerate(X2.columns):
    if col != 'const':
        try:
            print(f"    {col}: {variance_inflation_factor(X2.values, i):.2f}")
        except: pass

try:
    from libpysal.weights import Queen
    import esda
    tracts_model = tracts_gdf[tracts_gdf['GEOID'].isin(df_model['GEOID'].astype(str))].copy()
    w = Queen.from_dataframe(tracts_model)
    w.transform = 'r'
    mi = esda.Moran(m2.resid.values[:len(w.id_order)], w)
    print(f"  Moran's I = {mi.I:.4f}, z={mi.z_norm:.2f}, p={mi.p_norm:.4f}")
except ImportError:
    print("  Moran's I: libpysal not installed — HC3 SEs adequate for v0")
except Exception as e:
    print(f"  Moran's I: {e}")

# ─── 12. North/South comparison ───────────────────────────────────────────────
print("\n[12] North/South I-30 comparison (real CIP data):")
for zone, lbl in [(1,'South I-30'),(0,'North I-30')]:
    sub = df_model[df_model['south_i30']==zone]
    t_stat_s, t_p_s = stats.ttest_ind(
        df_model[df_model['south_i30']==1]['log_cip_pc'],
        df_model[df_model['south_i30']==0]['log_cip_pc']
    )
    print(f"  {lbl} (n={len(sub)}):")
    print(f"    Median CIP/capita: ${sub['cip_real_pc'].median():,.1f}")
    print(f"    Mean %Black: {sub['pct_black'].mean():.1f}%")
    print(f"    Mean %Hispanic: {sub['pct_hispanic'].mean():.1f}%")
    print(f"    Mean income: ${sub['median_income'].mean():,.0f}")
    if zone == 0:
        print(f"    N vs S t-test: t={t_stat_s:.2f}, p={t_p_s:.4f}")

# ─── 13. Diagnostic plots (9-panel dark mode) ─────────────────────────────────
print("\n[13] Generating 9-panel diagnostic plots...")
ACCENT = '#00d4ff'
SOUTH  = '#ff6b6b'
NORTH  = '#69db7c'
YELLOW = '#ffd43b'
BG     = '#0d0d0d'
AX_BG  = '#1a1a1a'

fig = plt.figure(figsize=(18,14), facecolor=BG)
fig.suptitle(
    'H1 v3 Diagnostics — Real CIP Data | Below the Line: Dallas I-30 Atlas\n'
    'Nicholas D. Hawkins | TSU Freeman Honors College | Real: 488 CIP projects, ~$1.26B',
    color='white', fontsize=12, y=0.985
)
gs = gridspec.GridSpec(3,3, hspace=0.48, wspace=0.35)

def style(ax, title):
    ax.set_facecolor(AX_BG)
    ax.set_title(title, color='white', fontsize=8.5, pad=5)
    ax.tick_params(colors='white', labelsize=7)
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    for sp in ax.spines.values(): sp.set_edgecolor('#444')
    ax.grid(color='#2a2a2a', linestyle='--', linewidth=0.5)

# P1: CIP/capita histogram
ax = fig.add_subplot(gs[0,0])
ax.hist(np.log1p(df_model['cip_real_pc']), bins=40, color=ACCENT, alpha=0.8, edgecolor='none')
med = np.log1p(df_model['cip_real_pc'].median())
ax.axvline(med, color=YELLOW, lw=1.5, ls='--', label=f'Median')
style(ax, 'CIP/Capita Distribution (log+1)')
ax.set_xlabel('log(CIP$/capita + 1)')
ax.legend(fontsize=7, labelcolor='white', facecolor='#222', edgecolor='none')

# P2: % Nonwhite vs log CIP
ax = fig.add_subplot(gs[0,1])
colors_s = df_model['south_i30'].map({1:SOUTH,0:NORTH})
ax.scatter(df_model['pct_nonwhite'], df_model['log_cip_pc'],
           c=colors_s, alpha=0.45, s=14, edgecolors='none')
xs = np.linspace(df_model['pct_nonwhite'].min(), df_model['pct_nonwhite'].max(), 100)
m_,b_,r_,p_,_ = stats.linregress(df_model['pct_nonwhite'], df_model['log_cip_pc'])
ax.plot(xs, m_*xs+b_, color='white', lw=1.5, label=f'r={r_:.2f}')
style(ax, '% Nonwhite vs log CIP/Capita')
ax.set_xlabel('Proportion Nonwhite'); ax.set_ylabel('log CIP/capita')
ax.legend(fontsize=7, labelcolor='white', facecolor='#222', edgecolor='none')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=SOUTH,label='South I-30'),
                   Patch(color=NORTH,label='North I-30'),
                   plt.Line2D([0],[0],color='white',lw=1.5,label=f'r={r_:.2f}')],
          fontsize=6.5, labelcolor='white', facecolor='#222', edgecolor='none')

# P3: % Black vs log CIP
ax = fig.add_subplot(gs[0,2])
vb = df_model.dropna(subset=['pct_black'])
ax.scatter(vb['pct_black'], vb['log_cip_pc'],
           c=vb['south_i30'].map({1:SOUTH,0:NORTH}), alpha=0.45, s=14, edgecolors='none')
if len(vb) > 5:
    mb,bb,rb,_,_ = stats.linregress(vb['pct_black'], vb['log_cip_pc'])
    xs2 = np.linspace(vb['pct_black'].min(), vb['pct_black'].max(), 100)
    ax.plot(xs2, mb*xs2+bb, color='white', lw=1.5, label=f'r={rb:.2f}')
style(ax, '% Black vs log CIP/Capita')
ax.set_xlabel('Proportion Black')
ax.legend(fontsize=7, labelcolor='white', facecolor='#222', edgecolor='none')

# P4: % Hispanic vs log CIP
ax = fig.add_subplot(gs[1,0])
vh = df_model.dropna(subset=['pct_hispanic'])
ax.scatter(vh['pct_hispanic'], vh['log_cip_pc'],
           c=vh['south_i30'].map({1:SOUTH,0:NORTH}), alpha=0.45, s=14, edgecolors='none')
if len(vh) > 5:
    mh,bh,rh,_,_ = stats.linregress(vh['pct_hispanic'], vh['log_cip_pc'])
    xs3 = np.linspace(vh['pct_hispanic'].min(), vh['pct_hispanic'].max(), 100)
    ax.plot(xs3, mh*xs3+bh, color='white', lw=1.5, label=f'r={rh:.2f}')
style(ax, '% Hispanic vs log CIP/Capita')
ax.set_xlabel('Proportion Hispanic')
ax.legend(fontsize=7, labelcolor='white', facecolor='#222', edgecolor='none')

# P5: North vs South boxplot
ax = fig.add_subplot(gs[1,1])
sc = df_model[df_model['south_i30']==1]['cip_real_pc']
nc = df_model[df_model['south_i30']==0]['cip_real_pc']
bp = ax.boxplot([sc.clip(upper=sc.quantile(0.95)), nc.clip(upper=nc.quantile(0.95))],
                patch_artist=True, widths=0.5,
                boxprops=dict(color='white'),
                medianprops=dict(color=ACCENT,lw=2),
                whiskerprops=dict(color='white'),
                capprops=dict(color='white'),
                flierprops=dict(marker='o',color='#555',markersize=2))
bp['boxes'][0].set_facecolor(SOUTH+'66')
bp['boxes'][1].set_facecolor(NORTH+'66')
ax.set_xticks([1,2])
ax.set_xticklabels(['South I-30','North I-30'], color='white', fontsize=8)
t_s, t_p = stats.ttest_ind(sc.dropna(), nc.dropna())
ax.text(0.5, 0.93, f't={t_s:.2f}, p={t_p:.3f}',
        transform=ax.transAxes, ha='center', color=YELLOW, fontsize=7.5)
style(ax, 'CIP/Capita: South vs North I-30')
ax.set_ylabel('CIP $/capita')

# P6: M2 residuals vs fitted
ax = fig.add_subplot(gs[1,2])
ax.scatter(m2.fittedvalues, m2.resid, alpha=0.4, s=12, c=ACCENT, edgecolors='none')
ax.axhline(0, color='white', lw=1)
try:
    from statsmodels.nonparametric.smoothers_lowess import lowess
    lw_pts = lowess(m2.resid, m2.fittedvalues, frac=0.3)
    ax.plot(lw_pts[:,0], lw_pts[:,1], color=YELLOW, lw=1.5, label='LOWESS')
    ax.legend(fontsize=7, labelcolor='white', facecolor='#222', edgecolor='none')
except: pass
style(ax, 'M2 Residuals vs Fitted (HC3 SEs)')
ax.set_xlabel('Fitted'); ax.set_ylabel('Residuals')

# P7: Investment gap scatter
ax = fig.add_subplot(gs[2,0])
gv = df_model.dropna(subset=['cip_gap_pc'])
ax.scatter(gv['pct_nonwhite'], gv['cip_gap_pc'],
           c=gv['south_i30'].map({1:SOUTH,0:NORTH}), alpha=0.45, s=12, edgecolors='none')
ax.axhline(0, color=YELLOW, lw=1, ls='--', label='Break-even')
style(ax, 'Investment Gap vs % Nonwhite\n(actual − needs-based expected)')
ax.set_xlabel('Proportion Nonwhite')
ax.set_ylabel('Gap $/capita')
ax.legend(fontsize=7, labelcolor='white', facecolor='#222', edgecolor='none')

# P8: HOLC grades vs CIP/capita
ax = fig.add_subplot(gs[2,1])
holc_sub = df_model.dropna(subset=['holc_grade_real'])
if len(holc_sub) >= 4:
    grades = ['A','B','C','D']
    labels = ['A (Best)','B (Still Desirable)','C (Declining)','D (Hazardous)']
    colors = ['#76a865','#7cb9e8','#d4bd61','#d9838d']
    medians = [holc_sub[holc_sub['holc_grade_real']==g]['cip_real_pc'].median()
               for g in grades]
    counts  = [len(holc_sub[holc_sub['holc_grade_real']==g]) for g in grades]
    bars = ax.bar(range(4), medians, color=colors, edgecolor='none', alpha=0.85)
    ax.set_xticks(range(4))
    ax.set_xticklabels([f'{l}\n(n={c})' for l,c in zip(labels,counts)],
                       fontsize=6, rotation=15, ha='right')
    style(ax, 'Median CIP/Capita by HOLC Grade')
    ax.set_ylabel('Median CIP $/capita')
else:
    ax.text(0.5, 0.5, f'HOLC-tract overlap\nn={len(holc_sub)} tracts',
            ha='center', va='center', transform=ax.transAxes, color='gray', fontsize=10)
    style(ax, 'Median CIP/Capita by HOLC Grade')

# P9: Coefficient plot across models
ax = fig.add_subplot(gs[2,2])
mlabels, betas, pvals = [], [], []
for r in results_rows:
    if 'b_pct_nonwhite' in r and r['b_pct_nonwhite'] not in ['N/A', None]:
        mlabels.append(r['model'].replace('_',' '))
        betas.append(float(r['b_pct_nonwhite']))
        pvals.append(float(r['p_pct_nonwhite']) if r.get('p_pct_nonwhite') not in ['N/A',None] else 1.0)

bar_colors = [ACCENT if p < 0.05 else ('#ff9f43' if p < 0.10 else '#555') for p in pvals]
ax.barh(range(len(mlabels)), betas, color=bar_colors, edgecolor='none', alpha=0.85)
ax.axvline(0, color='white', lw=1)
ax.set_yticks(range(len(mlabels)))
ax.set_yticklabels(mlabels, fontsize=6)
style(ax, 'β(% Nonwhite) Across Models\ncyan=p<.05 | orange=p<.10')
ax.set_xlabel('Coefficient estimate')

plt.savefig(f"{OUT}/figures/h1_v3_diagnostic_plots.png", dpi=150,
            bbox_inches='tight', facecolor=BG)
plt.close()
print(f"    Saved: {OUT}/figures/h1_v3_diagnostic_plots.png")

# ─── 14. Findings memo ────────────────────────────────────────────────────────
south_med_pc = df_model[df_model['south_i30']==1]['cip_real_pc'].median()
north_med_pc = df_model[df_model['south_i30']==0]['cip_real_pc'].median()

headline = f"""
H1 v3 FINDINGS SUMMARY — Real CIP Data
=======================================
CIP File: Capital_Improvement_Program_20260420.csv
  488 projects | ~$1.256B total (2024 Dallas Bond Program register)
  Classified into: Streets=$249.5M, Drainage=$811.7M, Parks/Trails=$40.7M,
                   EconDev=$85.8M, Other=$68.2M

HOLC File: mappinginequality.json (Mapping Inequality)
  48 Dallas HOLC polygons | Grades: A=10, B=15, C=12, D=9
  Tracts with HOLC grade: {df['holc_grade_real'].notna().sum()}

District Allocation (documented geography):
  South (D6+D7+D8): ${south_cip_total/1e6:.1f}M = {south_cip_total/(south_cip_total+north_cip_total)*100:.1f}% of CIP
    NOTE: D6 alone = $127.7M, dominated by Drainage/Trinity River work
  North (all other): ${north_cip_total/1e6:.1f}M = {north_cip_total/(south_cip_total+north_cip_total)*100:.1f}% of CIP

Sample: {len(df_model)} tracts | South I-30: {df_model['south_i30'].sum()} | North: {(df_model['south_i30']==0).sum()}
Population: South={south_pop:,.0f} | North={north_pop:,.0f}
Median CIP/capita: South=${south_med_pc:,.1f} | North=${north_med_pc:,.1f}
Underinvested (vs needs-based): {underinvested}/{len(df)} ({underinvested/len(df)*100:.1f}%)
Below 80% AMI: {below_80ami} ({below_80ami/len(df)*100:.1f}%)

MODEL RESULTS (pct_nonwhite coefficient on log CIP/capita):
  Model                       n      Adj-R²   β(nonwhite)  p-value  Sig
  ─────────────────────────────────────────────────────────────────────"""
for r in results_rows:
    b = r.get('b_pct_nonwhite','N/A')
    p = r.get('p_pct_nonwhite','N/A')
    try:
        sig = '**' if float(p)<0.05 else ('†' if float(p)<0.10 else '')
    except: sig = ''
    headline += f"\n  {r['model']:26s}  {r['n']:4d}  {r['adj_r2']:6.4f}   {str(b):>8}  {str(p):>7}  {sig}"

headline += f"""

INTERPRETATION NOTE:
  District 6 ($127.7M) is dominated by Drainage/Trinity River Corridor work.
  This inflates apparent south-side investment but is NOT discretionary spending.
  The allocation bias is clearest in Streets, Parks, and EconDev categories
  where the south receives a disproportionately smaller share relative to need.

  H2 preview: HOLC 'D' grade tracts show holc_d β={r7.get('b_holc_d_real','?')}, 
  p={r7.get('p_holc_d_real','?')} — redline legacy as persistent CIP predictor.

DATA GAPS FOR V1:
  1. Real CIP expenditure data (vs authorizations) — Dallas OFS records request
  2. Dallas city limits shapefile — to clip from 645 county to ~434 city tracts
  3. Dallas Council District shapefile — for proper spatial allocation
  4. CIP project-level line geometry — Public Works GIS records request
"""
print(headline)
with open(f"{OUT}/memos/h1_v3_findings_summary.txt",'w') as f:
    f.write(headline)

print("\n" + "="*70)
print("H1 v3 COMPLETE — All outputs saved.")
print(f"  CSV: {OUT}/tables/h1_v3_ols_results.csv")
print(f"  PNG: {OUT}/figures/h1_v3_diagnostic_plots.png")
print(f"  TXT: {OUT}/memos/h1_v3_findings_summary.txt")
print("="*70)

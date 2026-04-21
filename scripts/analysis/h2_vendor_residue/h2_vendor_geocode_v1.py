"""
H2 Vendor Geocoding + Local Economic Residue Analysis — v1
============================================================
Atlas: Below the Line — Dallas I-30 Corridor Displacement Risk Atlas
Author: Nicholas D. Hawkins | TSU Freeman Honors College

Purpose:
  Tests H2: CIP spend in South Dallas tracts produces disproportionately less
  local economic residue than identical spend in North Dallas tracts.

  "Economic residue" = vendor dollars that stay within the community —
  operationalized as the share of CIP/capital vendor spend going to firms
  headquartered within defined geographic radii of the tract.

Method:
  1. Load vendor payments, filter to capital program fund types
  2. Geocode all unique vendors by ZIP5 to lat/lon centroid
  3. For each Dallas census tract, compute:
     - vendor_local_share_5mi:  % of CIP spend to vendors within 5-mile radius
     - vendor_local_share_15mi: % of CIP spend to vendors within 15-mile radius
     - vendor_south_share:      % of CIP spend to vendors in South Dallas ZIPs
     - vendor_dallas_share:     % of CIP spend to Dallas-based vendors (752xx)
  4. Join to tract-level demographic data
  5. Run OLS: vendor_local_share ~ pct_nonwhite + south_of_i30 + log(median_income)
  6. Run OLS: vendor_south_share ~ pct_nonwhite + south_of_i30 + controls
  7. Produce diagnostic plots

Data Sources:
  - Vendor_Payments_FY2019_present.csv (145,551 transactions, $3.1B)
  - Capital fund type filter (17 fund types identified in v4 analysis)
  - ZIP5 → lat/lon: uszipcode library (offline, no API needed)
  - Census tract centroids: atlas_with_dpi.geojson
  - Demographics: atlas_v1_tract_data.csv

============================================================
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
warnings.filterwarnings('ignore')

# ─── Paths ────────────────────────────────────────────────────────────────────
# Repo root is 4 levels up from this script: scripts/analysis/h2_vendor_residue/<file>
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_RAW   = os.path.join(BASE, "data", "raw")
DATA_EXP   = os.path.join(BASE, "data", "exports")
DATA_PROC  = os.path.join(BASE, "data", "processed")
OUT_FIGS   = os.path.join(BASE, "outputs", "figures")
OUT_TABLES = os.path.join(BASE, "outputs", "tables")
OUT_MEMOS  = os.path.join(BASE, "outputs", "memos")

for d in [OUT_FIGS, OUT_TABLES, OUT_MEMOS]:
    os.makedirs(d, exist_ok=True)

print("=" * 65)
print("ATLAS H2 v1 — Vendor Geocoding + Local Economic Residue")
print("=" * 65)

# ─── 1. Load vendor payments ──────────────────────────────────────────────────
print("\n[1] Loading vendor payments...")
vp = pd.read_csv(
    os.path.join(DATA_RAW, "layer1_investment", "Vendor_Payments_FY2019_present.csv"),
    low_memory=False
)
vp['amount'] = pd.to_numeric(
    vp['CHKSUBTOT'].astype(str).str.replace(',', '').str.strip(),
    errors='coerce'
)
print(f"    Total transactions: {len(vp):,}")
print(f"    Total spend: ${vp['amount'].sum():,.0f}")

# ─── 2. Filter to capital program fund types ──────────────────────────────────
print("\n[2] Filtering to capital program fund types...")
CAP_KEYWORDS = ['Bond', 'CIP', 'Capital', 'capital']
cap_mask = vp['FUNDTYPE'].apply(lambda x: any(k in str(x) for k in CAP_KEYWORDS))
vp_cap = vp[cap_mask].copy()
print(f"    Capital transactions: {len(vp_cap):,}")
print(f"    Capital spend: ${vp_cap['amount'].sum():,.0f}")

# ─── 3. Build vendor ZIP5 → geography lookup ─────────────────────────────────
print("\n[3] Building vendor geography from ZIP5...")

# Use pgeocode for ZIP → lat/lon lookup (US only, offline after first download)
try:
    import pgeocode
    nomi = pgeocode.Nominatim('us')
    USE_PGEOCODE = True
    print("    pgeocode library available.")
except Exception:
    USE_PGEOCODE = False
    print("    pgeocode unavailable — using fallback coords.")

# Unique vendors with ZIP5
vendors = vp_cap[vp_cap['ZIP5'].notna()][['VENDOR', 'ZIP5']].drop_duplicates('VENDOR')
vendors = vendors.copy()
vendors['ZIP5'] = vendors['ZIP5'].astype(str).str.strip().str.zfill(5)

# Geocode
if USE_PGEOCODE:
    unique_zips = vendors['ZIP5'].unique()
    zip_results = nomi.query_postal_code(list(unique_zips))
    zip_coords = dict(zip(unique_zips,
                         zip(zip_results['latitude'].fillna(np.nan),
                             zip_results['longitude'].fillna(np.nan))))
    vendors['lat'] = vendors['ZIP5'].map(lambda z: zip_coords.get(z, (np.nan, np.nan))[0])
    vendors['lon'] = vendors['ZIP5'].map(lambda z: zip_coords.get(z, (np.nan, np.nan))[1])
    print(f"    Geocoded: {vendors['lat'].notna().sum():,} / {len(vendors):,} vendors via pgeocode")
else:
    # Fallback: approximate ZIP prefix to centroid
    # Dallas ZIPs (752xx) → approx city center; use prefix logic
    def zip_to_approx_coords(z):
        z = str(z)[:5]
        # Dallas city area ZIPs
        dallas_zip_coords = {
            '75201': (32.7874, -96.7979), '75202': (32.7803, -96.7988),
            '75203': (32.7421, -96.8079), '75204': (32.7976, -96.7840),
            '75205': (32.8292, -96.7874), '75206': (32.8196, -96.7660),
            '75207': (32.7839, -96.8264), '75208': (32.7520, -96.8385),
            '75209': (32.8404, -96.8264), '75210': (32.7534, -96.7452),
            '75211': (32.7369, -96.8777), '75212': (32.7688, -96.8727),
            '75214': (32.8224, -96.7344), '75215': (32.7452, -96.7532),
            '75216': (32.7127, -96.7913), '75217': (32.7125, -96.7164),
            '75218': (32.8388, -96.7049), '75219': (32.8108, -96.8110),
            '75220': (32.8729, -96.8703), '75223': (32.7974, -96.7434),
            '75224': (32.7219, -96.8385), '75225': (32.8584, -96.7875),
            '75226': (32.7831, -96.7752), '75227': (32.7697, -96.6913),
            '75228': (32.8063, -96.6694), '75229': (32.8939, -96.8668),
            '75230': (32.9057, -96.7984), '75231': (32.8683, -96.7527),
            '75232': (32.6863, -96.8307), '75233': (32.6979, -96.8666),
            '75234': (32.9116, -96.9001), '75235': (32.8266, -96.8468),
            '75238': (32.8629, -96.7161), '75240': (32.9330, -96.7975),
            '75241': (32.6651, -96.7755), '75243': (32.9031, -96.7439),
            '75244': (32.9349, -96.8356), '75247': (32.8335, -96.8777),
            '75248': (32.9656, -96.7980), '75249': (32.6714, -96.8999),
            '75251': (32.9018, -96.7574), '75252': (32.9847, -96.7786),
            '75253': (32.7095, -96.6366), '75254': (32.9501, -96.8165),
        }
        if z in dallas_zip_coords:
            return dallas_zip_coords[z]
        # Non-Dallas: rough TX center or national
        if z[:3] in [str(x) for x in range(750, 800)]:
            return (31.9686, -99.9018)  # TX center
        return (39.5, -98.35)  # US center
    
    coords = vendors['ZIP5'].apply(zip_to_approx_coords)
    vendors['lat'] = coords.apply(lambda x: x[0])
    vendors['lon'] = coords.apply(lambda x: x[1])
    print(f"    Approx coords assigned: {len(vendors):,} vendors (fallback mode)")

# ─── 4. Build vendor GeoDataFrame ─────────────────────────────────────────────
print("\n[4] Building vendor GeoDataFrame...")
vendors_geo = vendors.dropna(subset=['lat', 'lon']).copy()
vendors_geo['geometry'] = [
    Point(row['lon'], row['lat'])
    for _, row in vendors_geo.iterrows()
]
vendors_gdf = gpd.GeoDataFrame(vendors_geo, geometry='geometry', crs='EPSG:4326')
print(f"    Vendor points: {len(vendors_gdf):,}")

# ─── 5. Load tract centroids ──────────────────────────────────────────────────
print("\n[5] Loading census tract centroids...")
tract_geo = gpd.read_file(os.path.join(DATA_PROC, "atlas_with_dpi.geojson"))
tract_geo['GEOID'] = tract_geo['GEOID'].astype(str).str.zfill(11)
tract_geo = tract_geo.to_crs('EPSG:4326')
tract_geo['centroid'] = tract_geo.geometry.centroid
tract_geo['centroid_lon'] = tract_geo['centroid'].x
tract_geo['centroid_lat'] = tract_geo['centroid'].y
print(f"    Tracts loaded: {len(tract_geo):,}")

# ─── 6. Project to meters for distance calculation ────────────────────────────
print("\n[6] Projecting to Texas State Plane (EPSG:2276) for distance calc...")
# EPSG:2276 = NAD83 / Texas North Central — units in US survey feet
vendors_proj = vendors_gdf.to_crs('EPSG:2276')
tract_proj = tract_geo.copy()
tract_proj['centroid_geom'] = tract_geo['centroid']
tract_proj_gdf = gpd.GeoDataFrame(tract_proj, geometry='centroid_geom', crs='EPSG:4326')
tract_proj_gdf = tract_proj_gdf.to_crs('EPSG:2276')

# Convert mile radii to feet
MILES_5  = 5  * 5280   # 26,400 ft
MILES_15 = 15 * 5280   # 79,200 ft

print(f"    5-mile radius:  {MILES_5:,} ft")
print(f"    15-mile radius: {MILES_15:,} ft")

# ─── 7. Merge vendor amounts back ─────────────────────────────────────────────
print("\n[7] Aggregating capital spend by vendor...")
vendor_spend = (
    vp_cap
    .groupby('VENDOR')['amount']
    .sum()
    .reset_index()
    .rename(columns={'amount': 'total_cap_spend'})
)
vendors_proj = vendors_proj.merge(vendor_spend, on='VENDOR', how='left')
vendors_proj['total_cap_spend'] = vendors_proj['total_cap_spend'].fillna(0)
total_cap = vendors_proj['total_cap_spend'].sum()
print(f"    Total capital spend in geocoded vendors: ${total_cap:,.0f}")

# ─── 8. Compute local residue per tract ───────────────────────────────────────
print("\n[8] Computing vendor local residue per census tract...")
print("    (This may take 1-2 minutes for 300+ tracts × 8,000+ vendors)")

results = []
tracts_list = tract_proj_gdf[['GEOID']].copy()
tracts_list['centroid_geom'] = tract_proj_gdf.geometry

vendor_points = vendors_proj.copy()
total_cap_all = vendor_spend['total_cap_spend'].sum()  # denominator = all cap spend

for idx, tract_row in tracts_list.iterrows():
    geoid = tract_row['GEOID']
    centroid = tract_row['centroid_geom']
    
    if centroid is None or centroid.is_empty:
        continue
    
    # Distance from tract centroid to each vendor
    dists = vendor_points.geometry.distance(centroid)
    
    # Spend within each radius
    spend_5mi  = vendor_points.loc[dists <= MILES_5,  'total_cap_spend'].sum()
    spend_15mi = vendor_points.loc[dists <= MILES_15, 'total_cap_spend'].sum()
    
    # Share of total capital spend
    share_5mi  = spend_5mi  / total_cap_all if total_cap_all > 0 else 0
    share_15mi = spend_15mi / total_cap_all if total_cap_all > 0 else 0
    
    results.append({
        'GEOID': geoid,
        'vendor_cap_5mi':      spend_5mi,
        'vendor_cap_15mi':     spend_15mi,
        'vendor_share_5mi':    share_5mi,
        'vendor_share_15mi':   share_15mi,
    })

residue_df = pd.DataFrame(results)
print(f"    Computed residue for {len(residue_df):,} tracts")

# ─── 9. Add South Dallas ZIP flag per vendor ──────────────────────────────────
print("\n[9] Computing South Dallas vendor share metrics...")

SOUTH_ZIPS = {'75203','75210','75211','75212','75215','75216','75217',
              '75224','75232','75233','75241','75249'}

# Re-aggregate by south ZIP
vp_cap2 = vp_cap.copy()
vp_cap2['ZIP5_clean'] = vp_cap2['ZIP5'].astype(str).str.strip().str.zfill(5)
vp_cap2['is_south_vendor'] = vp_cap2['ZIP5_clean'].isin(SOUTH_ZIPS)
vp_cap2['is_dallas_vendor'] = vp_cap2['ZIP5_clean'].str.startswith('752')

south_spend = vp_cap2[vp_cap2['is_south_vendor']]['amount'].sum()
dallas_spend = vp_cap2[vp_cap2['is_dallas_vendor']]['amount'].sum()
total_cap_spend = vp_cap2['amount'].sum()

print(f"    South Dallas vendor spend: ${south_spend:,.0f} ({100*south_spend/total_cap_spend:.1f}%)")
print(f"    Dallas-area vendor spend:  ${dallas_spend:,.0f} ({100*dallas_spend/total_cap_spend:.1f}%)")

# ─── 10. Join to demographics ─────────────────────────────────────────────────
print("\n[10] Joining to tract demographics...")
tracts = pd.read_csv(
    os.path.join(DATA_EXP, "atlas_v1_tract_data.csv"),
    dtype={'GEOID': str}
)
tracts['GEOID'] = tracts['GEOID'].str.zfill(11)

merged = tracts.merge(residue_df, on='GEOID', how='left')
print(f"    Merged: {len(merged):,} tracts | residue matched: {merged['vendor_cap_5mi'].notna().sum():,}")

# ─── 11. Summary statistics by north/south ────────────────────────────────────
print("\n" + "=" * 65)
print("RESULTS: VENDOR LOCAL RESIDUE BY NORTH/SOUTH")
print("=" * 65)

if 'south_of_i30' in merged.columns:
    south = merged[merged['south_of_i30'] == 1]
    north = merged[merged['south_of_i30'] == 0]
    
    print(f"\n{'Metric':<35} {'South':>12} {'North':>12} {'Gap':>10}")
    print("-" * 72)
    
    metrics = [
        ('vendor_cap_5mi',  'Mean vendor spend within 5mi ($)'),
        ('vendor_cap_15mi', 'Mean vendor spend within 15mi ($)'),
        ('vendor_share_5mi', 'Mean share of total cap spend 5mi'),
        ('vendor_share_15mi','Mean share of total cap spend 15mi'),
    ]
    
    for col, label in metrics:
        if col in merged.columns:
            s_mean = south[col].mean()
            n_mean = north[col].mean()
            gap = n_mean - s_mean if n_mean > s_mean else s_mean - n_mean
            direction = "N>S" if n_mean > s_mean else "S>N"
            if 'share' in col:
                print(f"  {label:<33} {s_mean:>12.4f} {n_mean:>12.4f} {direction:>10}")
            else:
                print(f"  {label:<33} {s_mean:>12,.0f} {n_mean:>12,.0f} {direction:>10}")

# ─── 12. OLS regression: vendor residue ~ race + geography ───────────────────
print("\n" + "=" * 65)
print("OLS REGRESSION: VENDOR LOCAL RESIDUE ~ RACE + GEOGRAPHY")
print("=" * 65)

reg_df = merged.dropna(subset=['pct_nonwhite', 'south_of_i30', 'median_income', 'vendor_cap_15mi']).copy()
reg_df = reg_df[reg_df['median_income'] > 0]
reg_df['log_income'] = np.log(reg_df['median_income'])
reg_df['log_vendor_15mi'] = np.log1p(reg_df['vendor_cap_15mi'])

formula = "log_vendor_15mi ~ pct_nonwhite + south_of_i30 + log_income + population"
try:
    model = smf.ols(formula, data=reg_df).fit(cov_type='HC3')
    print(f"\n  Formula: {formula}")
    print(f"  N={model.nobs:.0f}  Adj-R²={model.rsquared_adj:.3f}")
    print()
    for var in model.params.index:
        coef = model.params[var]
        pval = model.pvalues[var]
        stars = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else ''
        print(f"    β({var:25}) = {coef:>9.4f}  p={pval:.4f} {stars}")
except Exception as e:
    print(f"  Regression error: {e}")

# ─── 13. Export results table ─────────────────────────────────────────────────
print("\n[13] Exporting vendor residue table...")
export_cols = ['GEOID'] + [c for c in merged.columns if 'vendor' in c.lower() or c in
               ['pct_nonwhite','pct_black','pct_hispanic','median_income','south_of_i30','population']]
export_df = merged[[c for c in export_cols if c in merged.columns]]
out_path = os.path.join(OUT_TABLES, "h2_vendor_residue_by_tract.csv")
export_df.to_csv(out_path, index=False)
print(f"    Saved: {out_path}")

# ─── 14. Summary statistics table ────────────────────────────────────────────
summary = {
    'total_vendor_payments':    int(len(vp)),
    'total_spend_all_funds':    float(vp['amount'].sum()),
    'capital_transactions':     int(len(vp_cap)),
    'capital_spend_total':      float(vp_cap['amount'].sum()),
    'unique_vendors':           int(vp['VENDOR'].nunique()),
    'south_dallas_vendor_spend': float(south_spend),
    'south_dallas_vendor_pct':  float(100*south_spend/total_cap_spend),
    'dallas_vendor_spend':      float(dallas_spend),
    'dallas_vendor_pct':        float(100*dallas_spend/total_cap_spend),
    'top_vendor':               str(vendor_spend.nlargest(1, 'total_cap_spend').iloc[0]['VENDOR']),
    'top_vendor_spend':         float(vendor_spend.nlargest(1, 'total_cap_spend').iloc[0]['total_cap_spend']),
}

summary_df = pd.DataFrame([summary]).T.reset_index()
summary_df.columns = ['metric', 'value']
summary_path = os.path.join(OUT_TABLES, "h2_vendor_summary_stats.csv")
summary_df.to_csv(summary_path, index=False)
print(f"    Summary stats saved: {summary_path}")

# ─── 15. Diagnostic plot ──────────────────────────────────────────────────────
print("\n[14] Generating diagnostic plot...")

fig = plt.figure(figsize=(16, 10), facecolor='#0d1117')
fig.suptitle(
    'Atlas H2 v1 — Vendor Local Residue Analysis\nWho Captures the Economic Return of Public Capital?',
    color='white', fontsize=14, fontweight='bold', y=0.98
)
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[0, 2])
ax4 = fig.add_subplot(gs[1, 0])
ax5 = fig.add_subplot(gs[1, 1])
ax6 = fig.add_subplot(gs[1, 2])

plot_style = {'facecolor': '#161b22', 'labelcolor': 'white'}
for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
    ax.set_facecolor('#161b22')
    ax.tick_params(colors='white', labelsize=8)
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    for spine in ax.spines.values():
        spine.set_edgecolor('#30363d')

# Plot 1: North vs South vendor geography bar
categories = ['South Dallas\nVendors', 'North Dallas\nVendors', 'Other TX\nVendors', 'Out of State']
values_all = [south_spend/1e6, dallas_spend/1e6 - south_spend/1e6,
              (vp_cap2[vp_cap2['ZIP5_clean'].str.match(r'^7[5-9]', na=False)]['amount'].sum() - dallas_spend)/1e6,
              vp_cap2[~vp_cap2['ZIP5_clean'].str.match(r'^7[5-9]', na=False) & vp_cap2['ZIP5_clean'].notna()]['amount'].sum()/1e6]
colors_bar = ['#e05c2a', '#4a9edd', '#a8c4d4', '#6e7681']
bars = ax1.bar(categories, values_all, color=colors_bar, width=0.6)
ax1.set_title('Capital Spend by\nVendor Geography ($M)', fontsize=9, fontweight='bold')
ax1.set_ylabel('$ Millions', fontsize=8)
for bar, val in zip(bars, values_all):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
             f'${val:.0f}M', ha='center', va='bottom', color='white', fontsize=7)

# Plot 2: Vendor spend scatter — % nonwhite vs vendor_cap_15mi
if 'vendor_cap_15mi' in merged.columns and 'pct_nonwhite' in merged.columns:
    plot_df = merged.dropna(subset=['vendor_cap_15mi', 'pct_nonwhite', 'south_of_i30'])
    colors_scatter = ['#e05c2a' if s == 1 else '#4a9edd' for s in plot_df['south_of_i30']]
    ax2.scatter(plot_df['pct_nonwhite'], plot_df['vendor_cap_15mi']/1e6,
                c=colors_scatter, alpha=0.5, s=15)
    ax2.set_title('% Nonwhite vs\nVendor Spend 15mi ($M)', fontsize=9, fontweight='bold')
    ax2.set_xlabel('% Nonwhite', fontsize=8)
    ax2.set_ylabel('Vendor Spend 15mi ($M)', fontsize=8)
    from matplotlib.lines import Line2D
    legend_els = [Line2D([0],[0], marker='o', color='w', markerfacecolor='#e05c2a', label='South', markersize=6),
                  Line2D([0],[0], marker='o', color='w', markerfacecolor='#4a9edd', label='North', markersize=6)]
    ax2.legend(handles=legend_els, fontsize=7, facecolor='#161b22', labelcolor='white')

# Plot 3: Top 15 vendors by capital spend
top15 = vendor_spend.nlargest(15, 'total_cap_spend')
y_pos = range(len(top15))
vendor_labels = [v[:28] + '..' if len(v) > 28 else v for v in top15['VENDOR']]
ax3.barh(list(y_pos), top15['total_cap_spend']/1e6, color='#4a9edd', height=0.7)
ax3.set_yticks(list(y_pos))
ax3.set_yticklabels(vendor_labels, fontsize=6)
ax3.invert_yaxis()
ax3.set_title('Top 15 Capital Vendors ($M)', fontsize=9, fontweight='bold')
ax3.set_xlabel('$ Millions', fontsize=8)

# Plot 4: Economic Development Fund vendors
econ_dev_vendors = vp[vp['FUNDTYPE'] == 'Other-Economic Development']
ed_top = econ_dev_vendors.groupby('VENDOR')['amount'].sum().nlargest(10)
y_pos4 = range(len(ed_top))
ed_labels = [v[:30] + '..' if len(v) > 30 else v for v in ed_top.index]
ed_colors = ['#e05c2a' if any(k in v for k in ['Tourism PID','Downtown','Uptown','Klyde','Knox','Lake High','Midtown','Prestonwood','Oak Lawn'])
             else '#4a9edd' for v in ed_top.index]
ax4.barh(list(y_pos4), ed_top.values/1e6, color=ed_colors, height=0.7)
ax4.set_yticks(list(y_pos4))
ax4.set_yticklabels(ed_labels, fontsize=6.5)
ax4.invert_yaxis()
ax4.set_title('Econ Dev Fund: PID Corps\nvs Community Orgs ($M)', fontsize=9, fontweight='bold')
ax4.set_xlabel('$ Millions', fontsize=8)
from matplotlib.lines import Line2D
leg_els = [Line2D([0],[0], marker='s', color='w', markerfacecolor='#e05c2a', label='PID/BID Mgmt Corps', markersize=7),
           Line2D([0],[0], marker='s', color='w', markerfacecolor='#4a9edd', label='Other/Community', markersize=7)]
ax4.legend(handles=leg_els, fontsize=7, facecolor='#161b22', labelcolor='white')

# Plot 5: 2017 Bond vendor geography
b17 = vp[vp['FUNDTYPE'] == '2017 General Obligation Bond Program'].copy()
b17['ZIP5_clean'] = b17['ZIP5'].astype(str).str.strip().str.zfill(5)
b17['geo_cat'] = 'Other TX'
b17.loc[b17['ZIP5_clean'].isin(SOUTH_ZIPS), 'geo_cat'] = 'South Dallas'
b17.loc[b17['ZIP5_clean'].str.startswith('752') & ~b17['ZIP5_clean'].isin(SOUTH_ZIPS), 'geo_cat'] = 'North/Central Dallas'
b17.loc[~b17['ZIP5_clean'].str.match(r'^7[5-9]', na=False), 'geo_cat'] = 'Out of State'
b17_geo = b17.groupby('geo_cat')['amount'].sum().sort_values(ascending=False)
colors_pie = ['#e05c2a', '#4a9edd', '#a8c4d4', '#6e7681']
wedges, texts, autotexts = ax5.pie(
    b17_geo.values, labels=b17_geo.index,
    autopct='%1.1f%%', colors=colors_pie[:len(b17_geo)],
    textprops={'color': 'white', 'fontsize': 7},
    pctdistance=0.75
)
for t in texts: t.set_fontsize(7)
ax5.set_title(f'2017 Bond Program\nVendor Geography (${b17["amount"].sum()/1e6:.0f}M total)', fontsize=9, fontweight='bold')

# Plot 6: Vendor count N/S by ZIP range
south_vendor_count = vp_cap2[vp_cap2['is_south_vendor']]['VENDOR'].nunique()
dallas_non_south_count = vp_cap2[vp_cap2['is_dallas_vendor'] & ~vp_cap2['is_south_vendor']]['VENDOR'].nunique()
other_tx_count = vp_cap2[~vp_cap2['is_dallas_vendor'] & vp_cap2['ZIP5_clean'].str.match(r'^7[5-9]', na=False)]['VENDOR'].nunique()
out_of_state_count = vp_cap2[~vp_cap2['ZIP5_clean'].str.match(r'^7[5-9]', na=False) & vp_cap2['ZIP5_clean'].notna()]['VENDOR'].nunique()

cats = ['South\nDallas\nVendors', 'North/Central\nDallas\nVendors', 'Other\nTX\nVendors', 'Out of\nState']
counts = [south_vendor_count, dallas_non_south_count, other_tx_count, out_of_state_count]
spends_norm = [south_spend/1e6, (dallas_spend - south_spend)/1e6,
               vp_cap2[~vp_cap2['is_dallas_vendor'] & vp_cap2['ZIP5_clean'].str.match(r'^7[5-9]', na=False)]['amount'].sum()/1e6,
               vp_cap2[~vp_cap2['ZIP5_clean'].str.match(r'^7[5-9]', na=False) & vp_cap2['ZIP5_clean'].notna()]['amount'].sum()/1e6]

x = np.arange(len(cats))
w = 0.35
ax6.bar(x - w/2, counts, width=w, color='#4a9edd', label='Unique Vendors')
ax6_r = ax6.twinx()
ax6_r.bar(x + w/2, spends_norm, width=w, color='#e05c2a', label='Total Spend ($M)', alpha=0.8)
ax6.set_xticks(x)
ax6.set_xticklabels(cats, fontsize=7, color='white')
ax6.set_ylabel('Unique Vendor Count', fontsize=8, color='#4a9edd')
ax6_r.set_ylabel('Total Spend ($M)', fontsize=8, color='#e05c2a')
ax6_r.tick_params(colors='#e05c2a', labelsize=7)
ax6.set_facecolor('#161b22')
ax6_r.set_facecolor('#161b22')
ax6.set_title('Vendor Count vs Spend\nby Geography', fontsize=9, fontweight='bold')
ax6.tick_params(colors='white', labelsize=7)
for spine in ax6_r.spines.values():
    spine.set_edgecolor('#30363d')

fig.tight_layout(rect=[0, 0, 1, 0.95])
plot_path = os.path.join(OUT_FIGS, "h2_v1_vendor_residue_diagnostic.png")
fig.savefig(plot_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
plt.close()
print(f"    Plot saved: {plot_path}")

print("\n" + "=" * 65)
print("H2 v1 COMPLETE")
print("=" * 65)
print(f"\n  Key finding:")
print(f"  South Dallas vendor share of capital spend: {100*south_spend/total_cap_spend:.1f}%")
print(f"  North/Central Dallas vendor share:          {100*(dallas_spend-south_spend)/total_cap_spend:.1f}%")
print(f"  Gap: {(dallas_spend-south_spend)/south_spend:.1f}x more capital residue in North Dallas")
print(f"\n  Outputs:")
print(f"  - {out_path}")
print(f"  - {summary_path}")
print(f"  - {plot_path}")

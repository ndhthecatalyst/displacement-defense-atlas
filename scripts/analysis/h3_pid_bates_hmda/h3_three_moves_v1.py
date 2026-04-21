"""
Atlas H3 — Three Moves Integration Script
Nicholas D. Hawkins | Below the Line: Development as Governance
Texas Southern University Freeman Honors College
April 21, 2026

Inputs:
  - data/processed/atlas_with_dpi.geojson (645 tracts)
  - data/raw/layer2_mechanism/dallas_pid_boundaries.geojson (16 active PIDs)
  - data/raw/layer3_early_warning/hmda_2023_dallas_denials.csv (12,086 denied apps)
  - data/raw/layer3_early_warning/hmda_2023_dallas_originated.csv (28,511 orig.)
  - outputs/tables/h2_vendor_residue_by_tract.csv

Outputs:
  - outputs/tables/atlas_three_moves_tract_data.csv
  - outputs/figures/atlas_three_moves_diagnostic.png

Move 1: PID Spatial Join — which census tracts fall within a Dallas PID boundary
Move 2: Bates/BOH Displacement Typology — reconstructed from ACS vulnerability, 
         market pressure, demographic change proxy (Builders of Hope / Lisa Bates method)
Move 3: HMDA 2023 Denial Rates — real CFPB data, tract-level denial rate + racial breakdown

Key findings:
  - North PID tracts: 26  |  South PID tracts: 2  |  Ratio 13:1
  - 107 vulnerable tracts (17%), 15 in Late stage, 19 Historic Loss
  - South of I-30 avg mortgage denial rate: 35.6% vs 29.8% North (1.19x)
  - South of I-30 = 39% of total denials despite ~29% of total apps
  - Black share of denied applications: 20.7%
"""
"""
Atlas — Three Moves Final Integration
Nicholas D. Hawkins | Below the Line
April 21, 2026
"""
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import BoundaryNorm
import warnings
warnings.filterwarnings('ignore')

BASE = '/tmp/atlas_review'

# ================================================================
# LOAD BASE DATA
# ================================================================
atlas = gpd.read_file(f'{BASE}/data/processed/atlas_with_dpi.geojson')
pid_gdf = gpd.read_file(f'{BASE}/data/raw/layer2_mechanism/dallas_pid_boundaries.geojson')
h2 = pd.read_csv(f'{BASE}/outputs/tables/h2_vendor_residue_by_tract.csv')
hmda_raw = pd.read_csv(f'{BASE}/data/raw/layer3_early_warning/hmda_2023_dallas_denials.csv', low_memory=False)

atlas.loc[atlas['median_income'] < 0, 'median_income'] = np.nan
atlas.loc[atlas['median_income'] > 250000, 'median_income'] = np.nan
atlas['GEOID'] = atlas['GEOID'].astype(str)
h2['GEOID'] = h2['GEOID'].astype(str)
atlas = atlas.merge(h2[['GEOID','vendor_cap_5mi','vendor_share_5mi']], on='GEOID', how='left')
print(f"Base atlas: {len(atlas)} tracts")

# ================================================================
# MOVE 1: PID SPATIAL JOIN
# ================================================================
print("\n=== MOVE 1: PID SPATIAL JOIN ===")
pid_active = pid_gdf[pid_gdf['Name'] != 'South Dallas-Fair Park (Expired 12/2023)'].copy()
pid_active = pid_active.to_crs(atlas.crs)

atlas_cents = atlas.copy()
atlas_cents['geometry'] = atlas.centroid
joined = gpd.sjoin(atlas_cents, pid_active[['Name','SqMi','geometry']], how='left', predicate='within')
joined_deduped = joined.groupby('GEOID').first().reset_index()

atlas['pid_name'] = joined_deduped.set_index('GEOID')['Name'].reindex(atlas['GEOID']).values
atlas['in_pid'] = (~atlas['pid_name'].isna()).astype(int)

south_pids = ['South Side PID - Premium','South Side PID - Standard',
              'RedBird PID','University Crossing PID']
north_pid_names = [n for n in pid_active['Name'].tolist() if n not in south_pids]
atlas['pid_north'] = atlas['pid_name'].isin(north_pid_names).astype(int)
atlas['pid_south'] = atlas['pid_name'].isin(south_pids).astype(int)

north_tracts = int(atlas['pid_north'].sum())
south_tracts = int(atlas['pid_south'].sum())
inc_north_pid = atlas[atlas['pid_north']==1]['median_income'].median()
inc_south_pid = atlas[atlas['pid_south']==1]['median_income'].median()
inc_no_pid    = atlas[atlas['in_pid']==0]['median_income'].median()

print(f"  Tracts in PIDs: {int(atlas['in_pid'].sum())} total")
print(f"  North PID tracts: {north_tracts} | South PID tracts: {south_tracts} | Ratio: {north_tracts}:{south_tracts}")
print(f"  Median income — North PIDs: ${inc_north_pid:,.0f} | South PIDs: ${inc_south_pid:,.0f}")

# PID names list for reference
print(f"\n  North PIDs ({len(north_pid_names)}): {', '.join(north_pid_names)}")
print(f"  South PIDs ({len(south_pids)}): {', '.join(south_pids)}")

# ================================================================
# MOVE 2: BATES DISPLACEMENT TYPOLOGY
# ================================================================
print("\n=== MOVE 2: BATES DISPLACEMENT TYPOLOGY ===")
av = atlas.copy()

# -- Vulnerability dimension --
for v in ['pct_nonwhite','pct_renter','rent_burden_pct']:
    av[v] = av[v].fillna(av[v].median())

# Low income: < 80% of Dallas MSA median (use our sample median as proxy)
dallas_med = av['median_income'].median()
av['low_income'] = (av['median_income'].fillna(dallas_med * 0.5) < 0.8 * dallas_med).astype(float)

# Z-scores computed only on valid rows
def safe_zscore(s):
    s = s.copy().fillna(s.median())
    mu, std = s.mean(), s.std()
    if std == 0: return pd.Series(0, index=s.index)
    return (s - mu) / std

vuln_vars = ['pct_nonwhite','pct_renter','rent_burden_pct','low_income']
zdf = pd.concat([safe_zscore(av[v]).rename(f'z_{v}') for v in vuln_vars], axis=1)
av['bates_vuln_zscore'] = zdf.mean(axis=1)
av['bates_vulnerable'] = ((zdf > 0.5).sum(axis=1) >= 3).astype(int)
vuln_n = int(av['bates_vulnerable'].sum())
print(f"  Vulnerable tracts: {vuln_n} ({vuln_n/len(av)*100:.1f}%)")

# -- Housing market dimension --
# Income rank, TIF, OZ, tool_density as market pressure indicators
inc_rank = av['median_income'].rank(pct=True, na_option='keep').fillna(0.5)
market_raw = (
    safe_zscore(inc_rank) * 0.4 +
    safe_zscore(av['tif_present'].astype(float)) * 0.25 +
    safe_zscore(av['oz_designated'].astype(float)) * 0.15 +
    safe_zscore(av['tool_density'].astype(float)) * 0.2
)
av['market_score'] = market_raw

# Quintile-based market categories matching Bates
q20 = av['market_score'].quantile(0.20)
q40 = av['market_score'].quantile(0.40)
q60 = av['market_score'].quantile(0.60)
q80 = av['market_score'].quantile(0.80)

# High market = top 40% (Sustained + Accelerating)
# Low market but adjacent = Adjacent
# Bottom 60% non-adjacent = low/moderate
av['market_high'] = (av['market_score'] >= q60).astype(int)

# Spatial adjacency to high-market tracts (project to meters for buffer)
av_proj = av.copy()
av_proj = av_proj.to_crs('EPSG:32614')  # UTM Zone 14N (Dallas)
high_market_geoids = set(av[av['market_high']==1]['GEOID'])
high_gdf = av_proj[av_proj['GEOID'].isin(high_market_geoids)][['GEOID','geometry']].copy()
low_gdf  = av_proj[~av_proj['GEOID'].isin(high_market_geoids)][['GEOID','geometry']].copy()

# Buffer high-market tracts by 100m to catch shared boundary tracts
high_buf = high_gdf.copy()
high_buf['geometry'] = high_gdf['geometry'].buffer(100)
adj_result = gpd.sjoin(
    low_gdf.reset_index(drop=True),
    high_buf.reset_index(drop=True)[['GEOID','geometry']],
    how='inner',
    predicate='intersects'
)
adj_result.columns = [c.replace('_left','').replace('_right','_high') for c in adj_result.columns]
adjacent_geoids = set(adj_result['GEOID'].unique())
print(f"  Adjacent tracts (near high-market): {len(adjacent_geoids)}")

av['market_cat'] = 'Low'
av.loc[av['market_score'] >= q80, 'market_cat'] = 'Sustained'
av.loc[(av['market_score'] >= q60) & (av['market_score'] < q80), 'market_cat'] = 'Accelerating'
av.loc[av['GEOID'].isin(adjacent_geoids) & (av['market_cat'] == 'Low'), 'market_cat'] = 'Adjacent'
print(f"\n  Market categories:")
print(av['market_cat'].value_counts().to_string())

# -- Demographic change dimension --
# Proxy for 10-yr change: redline legacy tracts under investment pressure
# = historically marginalized community now experiencing capital inflow
av['demo_change'] = 0
# Track 1: Redlined + TIF = active displacement corridor
av.loc[(av['redline_legacy']==1) & (av['tif_present']==1), 'demo_change'] = 1
# Track 2: High vulnerability + Sustained/Accelerating market
av.loc[(av['bates_vulnerable']==1) & (av['market_cat'].isin(['Sustained','Accelerating'])), 'demo_change'] = 1
# Track 3: OZ overlap with vulnerable tracts = capital incursion
av.loc[(av['bates_vulnerable']==1) & (av['oz_designated']==1), 'demo_change'] = 1
print(f"\n  Demo change proxy tracts: {int(av['demo_change'].sum())}")

# -- Assign typology --
def bates_type(row):
    v   = row['bates_vulnerable']
    m   = row['market_cat']
    d   = row['demo_change']
    if not v:
        if d and m in ['Sustained']:
            return 'Historic Loss'
        return 'Stable'
    if m == 'Sustained' and d:
        return 'Late'
    elif m == 'Accelerating' and d:
        return 'Dynamic'
    elif m == 'Accelerating' and not d:
        return 'Early: Type 1'
    elif m == 'Adjacent' and d:
        return 'Early: Type 2'
    elif m == 'Adjacent' and not d:
        return 'Susceptible'
    else:
        return 'Stable'

av['bates_typology'] = av.apply(bates_type, axis=1)
typo_counts = av['bates_typology'].value_counts()
print(f"\n  Bates typology distribution:")
print(typo_counts.to_string())
print(f"\n  Typology x South of I-30:")
print(pd.crosstab(av['bates_typology'], av['south_of_i30']).to_string())

# ================================================================
# MOVE 3: HMDA REAL DENIAL RATES BY TRACT
# ================================================================
print("\n=== MOVE 3: HMDA 2023 DENIAL RATES BY TRACT ===")

hmda = hmda_raw.copy()
hmda['census_tract'] = pd.to_numeric(hmda['census_tract'], errors='coerce')
hmda['tract_str'] = hmda['census_tract'].dropna().apply(
    lambda x: str(int(x)).ljust(11,'0')[:11]).reindex(hmda.index)
# Also try as-is
hmda['tract_11'] = hmda['census_tract'].apply(
    lambda x: f"{int(x):011d}" if pd.notna(x) else np.nan)

print(f"  HMDA records: {len(hmda):,} (all action=3, denied)")
print(f"  Tracts covered: {hmda['tract_11'].nunique()}")

# We need total apps (not just denials) to compute denial RATE
# Download originations (action=1) for denominator
# For now: compute denial count + Black denial count per tract
# Denial rate proxy = denials/(denials + will add orig later)

# Group by tract
def denial_stats(df):
    tot = len(df)
    black = (df['derived_race'] == 'Black or African American').sum()
    white = (df['derived_race'] == 'White').sum()
    hisp  = (df['derived_ethnicity'].str.contains('Hispanic', na=False)).sum()
    return pd.Series({
        'hmda_denials_total': tot,
        'hmda_denials_black': black,
        'hmda_denials_white': white,
        'hmda_denials_hispanic': hisp,
        'hmda_denial_pct_black': black/tot if tot>0 else 0
    })

tract_hmda = hmda.groupby('tract_11').apply(denial_stats).reset_index()
tract_hmda.rename(columns={'tract_11':'GEOID'}, inplace=True)
print(f"\n  Aggregated to {len(tract_hmda)} unique tracts")
print(f"  Total denials: {tract_hmda['hmda_denials_total'].sum():,}")
print(f"  Black denials: {tract_hmda['hmda_denials_black'].sum():,} ({tract_hmda['hmda_denials_black'].sum()/tract_hmda['hmda_denials_total'].sum()*100:.1f}%)")

# Merge into atlas
av['GEOID'] = av['GEOID'].astype(str)
tract_hmda['GEOID'] = tract_hmda['GEOID'].astype(str)
av = av.merge(tract_hmda, on='GEOID', how='left')
print(f"\n  Tracts with HMDA denial data: {av['hmda_denials_total'].notna().sum()} / {len(av)}")

# Download originations for denominator
print("\n  [Downloading HMDA originations for denial rate denominator...]")
import subprocess
result = subprocess.run([
    'curl','-s','-L',
    'https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?years=2023&counties=48113&actions_taken=1',
    '-o', f'{BASE}/data/raw/layer3_early_warning/hmda_2023_dallas_originated.csv',
    '--max-time','120'
], capture_output=True, text=True)
orig_path = f'{BASE}/data/raw/layer3_early_warning/hmda_2023_dallas_originated.csv'

try:
    hmda_orig = pd.read_csv(orig_path, low_memory=False)
    hmda_orig['tract_11'] = hmda_orig['census_tract'].apply(
        lambda x: f"{int(x):011d}" if pd.notna(x) else np.nan)
    
    tract_orig = hmda_orig.groupby('tract_11').size().reset_index(name='hmda_orig_total')
    tract_orig.rename(columns={'tract_11':'GEOID'}, inplace=True)
    tract_orig['GEOID'] = tract_orig['GEOID'].astype(str)
    
    print(f"  Originations downloaded: {len(hmda_orig):,} records, {tract_orig['GEOID'].nunique()} tracts")
    
    av = av.merge(tract_orig, on='GEOID', how='left')
    av['hmda_total_apps'] = av['hmda_denials_total'].fillna(0) + av['hmda_orig_total'].fillna(0)
    av['hmda_denial_rate'] = av['hmda_denials_total'] / av['hmda_total_apps'].replace(0, np.nan)
    av['hmda_black_denial_share'] = av['hmda_denials_black'] / av['hmda_denials_total'].replace(0, np.nan)
    
    print(f"  Tracts with denial rate: {av['hmda_denial_rate'].notna().sum()}")
    print(f"  Mean denial rate: {av['hmda_denial_rate'].mean():.3f}")
    print(f"  South of I-30 mean denial rate: {av[av['south_of_i30']==1]['hmda_denial_rate'].mean():.3f}")
    print(f"  North of I-30 mean denial rate: {av[av['south_of_i30']==0]['hmda_denial_rate'].mean():.3f}")
    
    high_risk_south = int(((av['hmda_denial_rate'] > av['hmda_denial_rate'].quantile(0.75)) & 
                            (av['south_of_i30']==1)).sum())
    total_south = int((av['south_of_i30']==1).sum())
    use_real_hmda = True
    hmda_note = "Real HMDA 2023 data"
    
except Exception as e:
    print(f"  Originations download failed: {e} — using proxy")
    av['hmda_denial_rate'] = np.nan
    av['hmda_black_denial_share'] = np.nan
    high_risk_south = 0
    total_south = int((av['south_of_i30']==1).sum())
    use_real_hmda = False
    hmda_note = "Proxy (originations pending)"

# ================================================================
# SAVE CSV OUTPUT
# ================================================================
print("\n=== SAVING OUTPUTS ===")
out_cols = [
    'GEOID','NAMELSAD','population','median_income','pct_black','pct_hispanic',
    'pct_nonwhite','pct_renter','rent_burden_pct','south_of_i30',
    'tif_present','oz_designated','redline_legacy',
    'in_pid','pid_name','pid_north','pid_south',
    'bates_typology','bates_vulnerable','bates_vuln_zscore','market_cat','demo_change',
    'hmda_denials_total','hmda_denials_black','hmda_denial_rate','hmda_black_denial_share',
    'dpi','risk_tier','vendor_share_5mi'
]
out_cols = [c for c in out_cols if c in av.columns]
av[out_cols].to_csv(f'{BASE}/outputs/tables/atlas_three_moves_tract_data.csv', index=False)
print(f"  Saved: atlas_three_moves_tract_data.csv ({len(av)} rows, {len(out_cols)} cols)")

# ================================================================
# DIAGNOSTIC VISUALIZATION
# ================================================================
print("\n=== BUILDING DIAGNOSTIC CHART ===")
typology_colors = {
    'Historic Loss': '#67001f',
    'Late':          '#d73027',
    'Dynamic':       '#f46d43',
    'Early: Type 1': '#fdae61',
    'Early: Type 2': '#fee090',
    'Susceptible':   '#abd9e9',
    'Stable':        '#ececec'
}
typo_order = list(typology_colors.keys())

fig = plt.figure(figsize=(21, 13))
fig.patch.set_facecolor('white')

# Title
fig.suptitle(
    "Below the Line — Atlas Three Moves Diagnostic\n"
    "Dallas Displacement Risk: PID Boundaries · Bates Typology · HMDA Denial Rates",
    fontsize=14, fontweight='bold', y=0.99
)

gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3)
axes = [[fig.add_subplot(gs[r, c]) for c in range(3)] for r in range(2)]

# --- P1: PID BOUNDARY MAP ---
ax = axes[0][0]
av_plot = av.copy()
av_plot[av_plot['in_pid']==0].plot(ax=ax, color='#d9ead3', edgecolor='#bbbbbb', linewidth=0.2)
av_plot[av_plot['pid_north']==1].plot(ax=ax, color='#1565c0', edgecolor='none', alpha=0.85)
av_plot[av_plot['pid_south']==1].plot(ax=ax, color='#c62828', edgecolor='none', alpha=0.85)
pid_active.plot(ax=ax, facecolor='none', edgecolor='#212121', linewidth=1.2)
ax.set_title(f'Move 1: PID Coverage\n'
             f'North PIDs: {north_tracts} tracts  ·  South PIDs: {south_tracts} tracts  ·  Ratio {north_tracts}:{south_tracts}',
             fontsize=9.5, fontweight='bold')
ax.set_axis_off()
ax.legend(handles=[
    mpatches.Patch(color='#1565c0', label=f'North PIDs ({north_tracts} tracts)'),
    mpatches.Patch(color='#c62828', label=f'South PIDs ({south_tracts} tracts)'),
    mpatches.Patch(color='#d9ead3', label='No PID coverage'),
], loc='lower right', fontsize=7.5, framealpha=0.85)

# --- P2: INCOME BY PID STATUS ---
ax = axes[0][1]
grps = [
    av[av['pid_north']==1]['median_income'].dropna(),
    av[av['pid_south']==1]['median_income'].dropna(),
    av[av['in_pid']==0]['median_income'].dropna(),
]
bp = ax.boxplot(grps, patch_artist=True,
                labels=['North PIDs','South PIDs','No PID'],
                medianprops=dict(color='white', linewidth=2.5),
                whiskerprops=dict(linewidth=1.2),
                capprops=dict(linewidth=1.2))
for patch, c in zip(bp['boxes'], ['#1565c0','#c62828','#9e9e9e']):
    patch.set_facecolor(c); patch.set_alpha(0.75)
ax.set_title(f'PID Income Gap (Layer 2)\n'
             f'North ${inc_north_pid/1000:.0f}K  ·  South ${inc_south_pid/1000:.0f}K  ·  No PID ${inc_no_pid/1000:.0f}K',
             fontsize=9.5, fontweight='bold')
ax.set_ylabel('Median Household Income', fontsize=8.5)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x/1000:.0f}K'))
ax.grid(axis='y', alpha=0.25); ax.set_facecolor('#fafafa')

# --- P3: BATES TYPOLOGY MAP ---
ax = axes[0][2]
for typo, color in typology_colors.items():
    sub = av[av['bates_typology'] == typo]
    if len(sub): sub.plot(ax=ax, color=color, edgecolor='none', alpha=0.92)
av.plot(ax=ax, facecolor='none', edgecolor='#aaaaaa', linewidth=0.1)
ax.set_title('Move 2: Bates/BOH Displacement Typology\n(Reconstructed via ACS vulnerability + market proxy)',
             fontsize=9.5, fontweight='bold')
ax.set_axis_off()
legend_patches = [
    mpatches.Patch(color=typology_colors[t], 
                   label=f'{t}  ({typo_counts.get(t,0)})')
    for t in typo_order if typo_counts.get(t, 0) > 0
]
ax.legend(handles=legend_patches, loc='lower right', fontsize=7, 
          framealpha=0.9, edgecolor='#cccccc')

# --- P4: TYPOLOGY x I-30 ---
ax = axes[1][0]
order_present = [t for t in typo_order if typo_counts.get(t,0) > 0]
cross = pd.crosstab(av['bates_typology'], av['south_of_i30'], normalize='index') * 100
cross_o = cross.reindex(order_present).fillna(0)
y = list(range(len(cross_o)))
south_vals = cross_o.get(1, pd.Series(0, index=cross_o.index))
north_vals = cross_o.get(0, pd.Series(0, index=cross_o.index))
ax.barh(y, south_vals.values, color='#c62828', alpha=0.75, label='South of I-30')
ax.barh(y, north_vals.values, left=south_vals.values, color='#1565c0', alpha=0.75, label='North of I-30')
ax.set_yticks(y); ax.set_yticklabels(cross_o.index, fontsize=9)
ax.set_xlabel('% of tracts in stage', fontsize=8.5)
ax.set_xlim(0, 108)
ax.set_title('Typology Stage by I-30 Geography\n(Concentration of displacement pressure)',
             fontsize=9.5, fontweight='bold')
ax.legend(fontsize=8, loc='lower right')
ax.grid(axis='x', alpha=0.25); ax.set_facecolor('#fafafa')
# Add n labels
for i, (s, n) in enumerate(zip(south_vals.values, north_vals.values)):
    tot = typo_counts.get(cross_o.index[i], 0)
    ax.text(102, i, f'n={tot}', va='center', fontsize=7.5, color='#444444')

# --- P5: HMDA DENIAL RATE MAP ---
ax = axes[1][1]
if av['hmda_denial_rate'].notna().sum() > 10:
    col_field = 'hmda_denial_rate'
    col_label = 'Denial Rate (applications denied / total)'
    cmap_use = 'RdYlGn_r'
    note_text = f'Real HMDA 2023 data\n{av["hmda_denial_rate"].notna().sum()} tracts with data'
    av.plot(column=col_field, ax=ax, cmap=cmap_use,
            legend=True, legend_kwds={'label': col_label, 'shrink': 0.7, 'format': '%.1%'},
            missing_kwds={'color': '#cccccc', 'label': 'No data'})
elif av['hmda_denials_total'].notna().sum() > 10:
    col_field = 'hmda_denials_total'
    av[col_field] = av[col_field].fillna(0)
    av.plot(column=col_field, ax=ax, cmap='YlOrRd',
            legend=True, legend_kwds={'label': 'Denial Count (2023)','shrink':0.7},
            missing_kwds={'color':'#cccccc'})
    note_text = f'Real HMDA denials 2023\n(Rate pending origination data)'
else:
    note_text = 'HMDA data pending'
    av.plot(ax=ax, color='#cccccc')
ax.set_title('Move 3: HMDA Mortgage Denial\n2023 Dallas County — Denied Applications',
             fontsize=9.5, fontweight='bold')
ax.set_axis_off()
ax.text(0.02, 0.04, note_text, transform=ax.transAxes, fontsize=7.5,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffde7', alpha=0.9, edgecolor='#cccc00'))

# --- P6: SUMMARY STATS ---
ax = axes[1][2]
ax.set_axis_off()

# HMDA stats
denial_south = av[av['south_of_i30']==1]['hmda_denials_total'].sum()
denial_north = av[av['south_of_i30']==0]['hmda_denials_total'].sum()
denial_total = av['hmda_denials_total'].sum()
black_denial_pct = av['hmda_denials_black'].sum() / max(denial_total, 1) * 100

late_dynamic = int((av['bates_typology'].isin(['Late','Dynamic'])).sum())
hist_loss = int((av['bates_typology'] == 'Historic Loss').sum())
susceptible = int((av['bates_typology'] == 'Susceptible').sum())

lines = [
    "THREE MOVES — KEY STATISTICS",
    "━" * 34,
    "",
    "MOVE 1  |  PID SPATIAL JOIN",
    f"  Active PIDs:            16",
    f"  North PID tracts:       {north_tracts}",
    f"  South PID tracts:       {south_tracts}",
    f"  Tract ratio (N:S):      {north_tracts}:{south_tracts}",
    f"  Median income N PIDs:   ${inc_north_pid/1000:.0f}K",
    f"  Median income S PIDs:   ${inc_south_pid/1000:.0f}K",
    "",
    "MOVE 2  |  BATES TYPOLOGY",
    f"  Vulnerable tracts:      {vuln_n} / 645",
] + [
    f"  {t:<20}  {typo_counts.get(t,0):>4}" for t in typo_order if typo_counts.get(t,0) > 0
] + [
    f"  Dynamic+Late tracts:    {late_dynamic}",
    f"  Historic Loss:          {hist_loss}",
    f"  Susceptible:            {susceptible}",
    "",
    "MOVE 3  |  HMDA DENIALS 2023",
    f"  Total denials:          {int(denial_total):,}",
    f"  South of I-30:          {int(denial_south):,}  ({int(denial_south)/max(int(denial_total),1)*100:.0f}%)",
    f"  Black share of denials: {black_denial_pct:.1f}%",
]

ax.text(0.04, 0.97, "\n".join(lines), transform=ax.transAxes,
        fontsize=8.5, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f8f8', 
                  alpha=0.95, edgecolor='#cccccc'))

plt.savefig(f'{BASE}/outputs/figures/atlas_three_moves_diagnostic.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Diagnostic chart saved.")

# Also save PID script
print("\n=== DONE ===")
print(f"Outputs:")
print(f"  outputs/tables/atlas_three_moves_tract_data.csv")
print(f"  outputs/figures/atlas_three_moves_diagnostic.png")
print(f"  data/raw/layer3_early_warning/hmda_2023_dallas_denials.csv ({len(hmda_raw):,} records)")

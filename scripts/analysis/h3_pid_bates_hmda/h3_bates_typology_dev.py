"""
Fixed Bates typology with proper spatial adjacency detection
and corrected summary panel
"""
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

BASE = '/tmp/atlas_review'

# Load
atlas = gpd.read_file(f'{BASE}/data/processed/atlas_with_dpi.geojson')
pid_gdf = gpd.read_file(f'{BASE}/data/raw/layer2_mechanism/dallas_pid_boundaries.geojson')
h2 = pd.read_csv(f'{BASE}/outputs/tables/h2_vendor_residue_by_tract.csv')

atlas.loc[atlas['median_income'] < 0, 'median_income'] = np.nan
atlas.loc[atlas['median_income'] > 250000, 'median_income'] = np.nan
atlas['GEOID'] = atlas['GEOID'].astype(str)
h2['GEOID'] = h2['GEOID'].astype(str)
atlas = atlas.merge(h2[['GEOID','vendor_cap_5mi','vendor_share_5mi']], on='GEOID', how='left')

# ---- MOVE 1: PID JOIN ----
pid_active = pid_gdf[pid_gdf['Name'] != 'South Dallas-Fair Park (Expired 12/2023)'].copy()
pid_active = pid_active.to_crs(atlas.crs)
atlas_cents = atlas.copy()
atlas_cents['geometry'] = atlas.centroid
joined = gpd.sjoin(atlas_cents, pid_active[['Name','geometry']], how='left', predicate='within')
joined = joined.groupby('GEOID').first().reset_index()
atlas['pid_name'] = joined.set_index('GEOID')['Name'].reindex(atlas['GEOID']).values
atlas['in_pid'] = (~atlas['pid_name'].isna()).astype(int)
south_pids = ['South Side PID - Premium','South Side PID - Standard','RedBird PID','University Crossing PID']
atlas['pid_north'] = atlas['pid_name'].isin([n for n in pid_active['Name'] if n not in south_pids]).astype(int)
atlas['pid_south'] = atlas['pid_name'].isin(south_pids).astype(int)
north_tracts = int(atlas['pid_north'].sum())
south_tracts = int(atlas['pid_south'].sum())

# ---- MOVE 2: BATES TYPOLOGY WITH PROPER ADJACENCY ----
av = atlas.copy()

# Vulnerability z-scores
for v in ['pct_nonwhite','pct_renter','rent_burden_pct']:
    av[v] = av[v].fillna(av[v].median())
av['low_income_flag'] = (av['median_income'].fillna(0) < 0.8 * av['median_income'].median()).astype(float)
vuln_vars = ['pct_nonwhite','pct_renter','rent_burden_pct','low_income_flag']
zdf = pd.DataFrame({f'z_{v}': stats.zscore(av[v]) for v in vuln_vars})
av['bates_vuln_zscore'] = zdf.mean(axis=1)
av['bates_vulnerable'] = ((zdf > 0.5).sum(axis=1) >= 3).astype(int)

# Housing market: use home value proxy from tool_density + TIF + OZ + inverse income rank
inc_rank = av['median_income'].rank(pct=True)
av['market_raw'] = (
    av['tif_present'] * 2.0 +
    av['oz_designated'] * 1.0 +
    av['tool_density'] * 1.5 +
    inc_rank * 1.5
)
av['market_z'] = stats.zscore(av['market_raw'])

# Market categories
av['market_cat'] = 'Stable'
av.loc[av['market_z'] > 1.2, 'market_cat'] = 'Sustained'
av.loc[(av['market_z'] > 0.4) & (av['market_z'] <= 1.2), 'market_cat'] = 'Accelerating'
av.loc[(av['market_z'] > -0.2) & (av['market_z'] <= 0.4), 'market_cat'] = 'Appreciated'

# Spatial adjacency: build neighbor list using GeoPandas sjoin touches
print("Building spatial neighbor index...")
atlas_indexed = av.set_index('GEOID')[['geometry']].copy()
atlas_indexed = gpd.GeoDataFrame(atlas_indexed)

# Find tracts adjacent to Accelerating/Sustained/Appreciated
high_market_geoids = set(av[av['market_cat'].isin(['Sustained','Accelerating','Appreciated'])]['GEOID'])
high_market_gdf = av[av['GEOID'].isin(high_market_geoids)][['GEOID','geometry']].copy()

# Spatial join: which low-market tracts are adjacent to high-market tracts?
low_market = av[~av['GEOID'].isin(high_market_geoids)][['GEOID','geometry']].copy()
low_market_indexed = gpd.GeoDataFrame(low_market).set_index('GEOID')

adj_join = gpd.sjoin(
    gpd.GeoDataFrame(low_market, geometry='geometry'),
    gpd.GeoDataFrame(high_market_gdf, geometry='geometry'),
    how='inner',
    predicate='touches'
)
adjacent_geoids = set(adj_join.index.unique())
print(f"  Adjacent tracts (neighboring high-market): {len(adjacent_geoids)}")

# Update market_cat for adjacent low-value tracts
av.loc[av['GEOID'].isin(adjacent_geoids), 'market_cat'] = 'Adjacent'

print("Market categories:")
print(av['market_cat'].value_counts().to_string())

# Demographic change: use redline_legacy + TIF overlap + south_of_i30 inversion
# Tracts where non-white pop declining AND income rising = demographic change
# Proxy: tracts with holc_score 3-4 (C/D redlined) that now have tool_density > 0 OR tif
av['demo_change'] = 0
# High-vulnerability tracts near investment pressure show change
av.loc[
    (av['bates_vulnerable'] == 1) & 
    (av['market_cat'].isin(['Accelerating','Sustained','Appreciated'])), 
    'demo_change'] = 1
# Redlined tracts with TIF = displacement corridor
av.loc[
    (av['redline_legacy'] == 1) & (av['tif_present'] == 1),
    'demo_change'] = 1

print(f"\nDemo change tracts: {av['demo_change'].sum()}")

# Assign typology
def bates_type(row):
    v = row['bates_vulnerable']
    m = row['market_cat']
    d = row['demo_change']
    if not v:
        if d and m in ['Sustained','Appreciated']:
            return 'Historic Loss'
        return 'Stable'
    if m == 'Sustained' and d:
        return 'Late'
    elif m in ['Accelerating','Appreciated'] and d:
        return 'Dynamic'
    elif m in ['Accelerating','Appreciated'] and not d:
        return 'Early: Type 1'
    elif m == 'Adjacent' and d:
        return 'Early: Type 2'
    elif m == 'Adjacent' and not d:
        return 'Susceptible'
    else:
        return 'Stable'

av['bates_typology'] = av.apply(bates_type, axis=1)
print("\nBates typology:")
print(av['bates_typology'].value_counts().to_string())
print("\nTypology x South of I-30:")
print(pd.crosstab(av['bates_typology'], av['south_of_i30']).to_string())

# ---- MOVE 3: HMDA PROXY ----
av['hmda_denial_risk'] = (
    stats.zscore(av['pct_black'].fillna(0)) * 0.5 +
    stats.zscore(av['rent_burden_pct'].fillna(0)) * 0.3 +
    stats.zscore(-(av['median_income'].fillna(av['median_income'].median()))) * 0.2
)

high_risk_south = int(((av['hmda_denial_risk'] > av['hmda_denial_risk'].quantile(0.9)) & (av['south_of_i30']==1)).sum())
total_south = int((av['south_of_i30']==1).sum())

# ---- INCOME BY PID ----
inc_north_pid = av[av['pid_north']==1]['median_income'].median()
inc_south_pid = av[av['pid_south']==1]['median_income'].median()
inc_no_pid    = av[av['in_pid']==0]['median_income'].median()

# ---- SAVE CSV ----
output_cols = [
    'GEOID','NAMELSAD','population','median_income','pct_black','pct_hispanic',
    'pct_nonwhite','pct_renter','rent_burden_pct','south_of_i30',
    'tif_present','oz_designated','redline_legacy',
    'in_pid','pid_name','pid_north','pid_south',
    'bates_typology','bates_vulnerable','bates_vuln_zscore',
    'market_cat','demo_change','hmda_denial_risk',
    'dpi','risk_tier','vendor_share_5mi'
]
av[output_cols].to_csv(f'{BASE}/outputs/tables/atlas_three_moves_tract_data.csv', index=False)
print(f"\nSaved CSV: {len(av)} rows")

# ---- PLOTS ----
fig, axes = plt.subplots(2, 3, figsize=(20, 13))
fig.suptitle("Atlas — Three Moves Diagnostic\nBelow the Line: Dallas Displacement Risk", 
             fontsize=15, fontweight='bold', y=0.99)

typology_colors = {
    'Historic Loss': '#67001f',
    'Late':          '#d73027',
    'Dynamic':       '#f46d43',
    'Early: Type 1': '#fdae61',
    'Early: Type 2': '#fee090',
    'Susceptible':   '#abd9e9',
    'Stable':        '#e8e8e8'
}

# P1: PID map
ax = axes[0,0]
av.plot(ax=ax, color='#e8e8e8', edgecolor='#cccccc', linewidth=0.2)
av[av['in_pid']==0].plot(ax=ax, color='#d4e8d4', edgecolor='none')
av[av['pid_north']==1].plot(ax=ax, color='#2166ac', edgecolor='none', alpha=0.85)
av[av['pid_south']==1].plot(ax=ax, color='#d73027', edgecolor='none', alpha=0.85)
pid_active.plot(ax=ax, facecolor='none', edgecolor='#111111', linewidth=1.3)
ax.set_title(f'Move 1: PID Boundaries\nNorth PIDs: {north_tracts} tracts | South PIDs: {south_tracts} tracts | Ratio {north_tracts}:{south_tracts}',
             fontsize=10, fontweight='bold')
ax.set_axis_off()
ax.legend(handles=[
    mpatches.Patch(color='#2166ac', label=f'North PIDs ({north_tracts} tracts)'),
    mpatches.Patch(color='#d73027', label=f'South PIDs ({south_tracts} tracts)'),
    mpatches.Patch(color='#d4e8d4', label='No PID coverage')
], loc='lower right', fontsize=8)

# P2: Income boxplot by PID
ax = axes[0,1]
inc_data = [
    av[av['pid_north']==1]['median_income'].dropna(),
    av[av['pid_south']==1]['median_income'].dropna(),
    av[av['in_pid']==0]['median_income'].dropna(),
]
bp = ax.boxplot(inc_data, patch_artist=True, labels=['North PIDs','South PIDs','No PID'],
                medianprops=dict(color='white', linewidth=2))
for patch, color in zip(bp['boxes'], ['#2166ac','#d73027','#aaaaaa']):
    patch.set_facecolor(color); patch.set_alpha(0.7)
ax.set_title(f'Median Income by PID Status\nNorth PID median: ${inc_north_pid:,.0f} | South PID: ${inc_south_pid:,.0f}',
             fontsize=10, fontweight='bold')
ax.set_ylabel('Median Household Income ($)', fontsize=9)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x/1000:.0f}K'))
ax.grid(axis='y', alpha=0.3)

# P3: Bates typology map
ax = axes[0,2]
for typo, color in typology_colors.items():
    subset = av[av['bates_typology'] == typo]
    if len(subset) > 0:
        subset.plot(ax=ax, color=color, edgecolor='none', alpha=0.9)
av.plot(ax=ax, facecolor='none', edgecolor='#aaaaaa', linewidth=0.15)
ax.set_title('Move 2: Bates/BOH Displacement Typology\n(Reconstructed — vulnerability + market + demo change)',
             fontsize=10, fontweight='bold')
ax.set_axis_off()
legend_patches = [mpatches.Patch(color=c, label=f'{t} ({(av["bates_typology"]==t).sum()})')
                  for t, c in typology_colors.items() if (av['bates_typology']==t).sum() > 0]
ax.legend(handles=legend_patches, loc='lower right', fontsize=7.5)

# P4: Typology x I-30
ax = axes[1,0]
order = ['Historic Loss','Late','Dynamic','Early: Type 1','Early: Type 2','Susceptible','Stable']
order = [o for o in order if o in av['bates_typology'].values]
cross = pd.crosstab(av['bates_typology'], av['south_of_i30'], normalize='index') * 100
cross_o = cross.reindex(order).fillna(0)
y = range(len(cross_o))
ax.barh(y, cross_o.get(1, pd.Series(0, index=cross_o.index)),
        color='#d73027', alpha=0.75, label='South of I-30')
ax.barh(y, cross_o.get(0, pd.Series(0, index=cross_o.index)),
        left=cross_o.get(1, pd.Series(0, index=cross_o.index)),
        color='#2166ac', alpha=0.75, label='North of I-30')
ax.set_yticks(list(y)); ax.set_yticklabels(list(cross_o.index), fontsize=9)
ax.set_xlabel('% of Tracts in Stage', fontsize=9)
ax.set_title('Typology Stage by I-30 Geography', fontsize=10, fontweight='bold')
ax.legend(fontsize=8); ax.grid(axis='x', alpha=0.3)
ax.set_xlim(0, 105)

# P5: HMDA denial risk map
ax = axes[1,1]
av['hmda_clipped'] = av['hmda_denial_risk'].clip(-2.5, 2.5)
av.plot(column='hmda_clipped', ax=ax, cmap='RdYlGn_r',
        legend=True, legend_kwds={'label':'Structural Denial Risk (Z)','shrink':0.75})
ax.set_title('Move 3: HMDA Structural Denial Risk\n(Proxy: Black%, rent burden, inverse income)',
             fontsize=10, fontweight='bold')
ax.set_axis_off()
ax.text(0.02, 0.02, 'Proxy variable\nReal HMDA pending API fix',
        transform=ax.transAxes, fontsize=7.5, color='#cc0000',
        bbox=dict(boxstyle='round', facecolor='#fffde7', alpha=0.85))

# P6: Summary stats (clean, no repeating)
ax = axes[1,2]
ax.set_axis_off()
typo_counts = av['bates_typology'].value_counts()
lines = [
    "THREE MOVES  —  SUMMARY",
    "",
    "MOVE 1 | PID SPATIAL JOIN",
    f"  Active PIDs (excl expired):  16",
    f"  Tracts in North PIDs:  {north_tracts}",
    f"  Tracts in South PIDs:  {south_tracts}",
    f"  North / South ratio:  {north_tracts}:{south_tracts}",
    f"  Median income North PIDs:  ${inc_north_pid:,.0f}",
    f"  Median income South PIDs:  ${inc_south_pid:,.0f}",
    "",
    "MOVE 2 | BATES TYPOLOGY",
    f"  Vulnerable tracts:  {int(av['bates_vulnerable'].sum())} / 645",
]
for t in order:
    n = typo_counts.get(t, 0)
    lines.append(f"  {t:<18} {n:>4}")
lines += [
    "",
    "MOVE 3 | HMDA DENIAL RISK",
    f"  High-risk tracts (top 10%):  65",
    f"  S. Dallas high-risk:  {high_risk_south}/{total_south} ({high_risk_south/total_south*100:.0f}%)",
    "",
    "  [!] HMDA proxy only — real data",
    "      pending CFPB API resolution"
]
txt = "\n".join(lines)
ax.text(0.05, 0.97, txt, transform=ax.transAxes,
        fontsize=9, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#f5f5f5', alpha=0.9))

plt.tight_layout(rect=[0,0,1,0.97])
plt.savefig(f'{BASE}/outputs/figures/atlas_three_moves_diagnostic.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Diagnostic saved.")

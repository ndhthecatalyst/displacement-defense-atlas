"""Static choropleth: 54 Susceptible South tracts colored by readiness score."""
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

ROOT = Path('/tmp/atlas_review')
geo = gpd.read_file(ROOT / 'outputs/geojson/h4_readiness.geojson')
# All Dallas County tracts as context, 54 priority tracts highlighted
fig, ax = plt.subplots(figsize=(11, 13))
geo.plot(ax=ax, color='#eeeeee', edgecolor='white', linewidth=0.3)

# All Susceptible tracts
susc = geo[geo['bates_typology_v21'] == 'Susceptible']
susc.plot(ax=ax, color='#fde0dc', edgecolor='#aaaaaa', linewidth=0.3, alpha=0.6)

# South + Susceptible = priority 54
pri = geo[(geo['bates_typology_v21'] == 'Susceptible') & (geo['south_of_i30'] == True)].copy()
pri.plot(ax=ax, column='readiness_score', cmap='RdYlGn', vmin=0, vmax=pri['readiness_score'].max() if len(pri) else 1,
         legend=True, legend_kwds={'label': 'Readiness Score (lower = higher urgency)', 'shrink': 0.5, 'orientation':'horizontal'},
         edgecolor='#222222', linewidth=0.5)

# I-30 reference line (approximate)
ax.axhline(y=32.745, color='#333', linestyle='--', linewidth=1, alpha=0.4)
ax.text(-97.10, 32.748, 'I-30 (north/south divide)', fontsize=8, color='#333', alpha=0.6)

ax.set_title('H4: The 54 — Susceptible South Dallas Tracts Ranked by Readiness\n'
             'Red = low readiness (highest intervention priority); Green = higher readiness',
             fontsize=13, fontweight='bold')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')

# Legend patches
p1 = mpatches.Patch(color='#fde0dc', label='Susceptible tracts (North of I-30)')
p2 = mpatches.Patch(color='#eeeeee', label='Other Dallas County tracts')
ax.legend(handles=[p1, p2], loc='lower left', fontsize=9)

plt.tight_layout()
out = ROOT / 'maps/h4/h4_priority_54_readiness.png'
out.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f"Saved {out}")

# Second map: 2x2 risk x readiness cell coloring
fig2, ax2 = plt.subplots(figsize=(11, 13))
cell_colors = {
    'HIGH_PRESSURE_LOW_READINESS':  '#d62728',  # crisis red
    'HIGH_PRESSURE_HIGH_READINESS': '#ff9f40',  # defended
    'LOW_PRESSURE_LOW_READINESS':   '#bbbbbb',  # low priority
    'LOW_PRESSURE_HIGH_READINESS':  '#4caf50',  # stable
}
for cell, color in cell_colors.items():
    sub = geo[geo['risk_readiness_cell'] == cell]
    sub.plot(ax=ax2, color=color, edgecolor='white', linewidth=0.3, label=cell.replace('_', ' ').title())

ax2.axhline(y=32.745, color='#333', linestyle='--', linewidth=1, alpha=0.4)
ax2.text(-97.10, 32.748, 'I-30', fontsize=9, color='#333', alpha=0.6)
ax2.set_title('H4: Risk × Readiness — Dallas County Census Tracts',
              fontsize=13, fontweight='bold')
ax2.legend(loc='lower left', fontsize=9, title='Cell')
plt.tight_layout()
out2 = ROOT / 'maps/h4/h4_risk_readiness_grid.png'
plt.savefig(out2, dpi=150, bbox_inches='tight')
print(f"Saved {out2}")

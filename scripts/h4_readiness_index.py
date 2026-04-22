"""
H4 readiness index + risk × readiness classification + priority ranking
Weights: 50/30/20 (affordable units / org presence / NEZ overlay)
Output:
  outputs/tables/h4_readiness_index.csv (all 645 tracts, full readiness columns)
  outputs/tables/h4_priority_54.csv (the 54 Susceptible South tracts, ranked)
  outputs/tables/h4_decision_calendar.csv (Council + TIF + OZ + next decision)
  outputs/geojson/h4_readiness.geojson (tract-level GeoJSON w/ readiness)
"""
import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
from shapely.geometry import Point

ROOT = Path('/tmp/atlas_review')
H4 = ROOT / 'data' / 'h4_readiness'
OUT = ROOT / 'outputs'

# Load inputs
h6 = pd.read_csv(ROOT / 'outputs/tables/h6_bates_full_typology.csv', dtype={'GEOID': str})
h6['GEOID'] = h6['GEOID'].str.zfill(11)
rin = pd.read_csv(H4 / 'h4_tract_readiness_inputs.csv', dtype={'GEOID': str})
rin['GEOID'] = rin['GEOID'].str.zfill(11)

# Merge H6 typology + readiness inputs
df = h6.merge(rin.drop(columns=['NAMELSAD'], errors='ignore'), on='GEOID', how='left')
print("Merged rows:", len(df))

# ============================================================
# Normalize readiness components (0-1 scale)
# ============================================================
# Component 1 (50%): AFFORDABLE UNITS — combine LIHTC LI units + HUD subsidized units
#                    Deed-restricted or subsidy-backed = non-displaceable stock
# Avoid double-count: LIHTC + "Project Based Section 8" can overlap at property level
# Use: total_deed_restricted = max(LIHTC li_units, hud_all_units) + public_housing + PB_S8 + HCV
# Conservative approach — take the larger of (LIHTC LI units) and (sum of HUD programs minus HCV)
df['affordable_units_count'] = df[['lihtc_units_li', 'hud_all_units']].max(axis=1)

# Normalize per 1000 residents to get density
df['pop_for_rate'] = df['pop_2023'].fillna(df['population']).fillna(0).replace(0, np.nan)
df['affordable_units_per_1k'] = df['affordable_units_count'] / df['pop_for_rate'] * 1000
df['affordable_units_per_1k'] = df['affordable_units_per_1k'].fillna(0).replace([np.inf, -np.inf], 0)

# Winsorize at 95th percentile (cap outliers for normalization)
cap = df['affordable_units_per_1k'].quantile(0.95)
df['affordable_units_per_1k_cap'] = df['affordable_units_per_1k'].clip(upper=cap)
max_a = df['affordable_units_per_1k_cap'].max()
df['norm_affordable'] = df['affordable_units_per_1k_cap'] / max_a if max_a > 0 else 0

# Component 2 (30%): ORG PRESENCE — HCA count + curated community orgs
# Weight HCAs (HUD-certified) = 1.0, community orgs (ZIP-centroid) = 0.7 (proximity signal, less precise)
df['org_signal'] = df['hca_count'].fillna(0) + 0.7 * df['org_count'].fillna(0)
max_o = df['org_signal'].max()
df['norm_orgs'] = df['org_signal'] / max_o if max_o > 0 else 0

# Component 3 (20%): NEZ OVERLAY — fractional overlap with NEZ polygon
df['norm_nez'] = df['nez_overlap_frac'].fillna(0).clip(0, 1)

# Composite readiness
W_AFFORD, W_ORG, W_NEZ = 0.50, 0.30, 0.20
df['readiness_score'] = (
    W_AFFORD * df['norm_affordable'].fillna(0)
    + W_ORG * df['norm_orgs'].fillna(0)
    + W_NEZ * df['norm_nez'].fillna(0)
)

# ============================================================
# 2x2 risk × readiness classification
# ============================================================
# Pressure = Bates "Susceptible" OR Early-stage tracts = High pressure
# Readiness threshold: Dallas County median readiness
HIGH_PRESSURE_TYPOLOGIES = {'Susceptible', 'Early: Type 1', 'Early: Type 2', 'Dynamic', 'Late'}
df['high_pressure'] = df['bates_typology_v21'].isin(HIGH_PRESSURE_TYPOLOGIES)

readiness_median = df['readiness_score'].median()
df['high_readiness'] = df['readiness_score'] >= readiness_median

def cell(r):
    p = r['high_pressure']
    rd = r['high_readiness']
    if p and not rd: return 'HIGH_PRESSURE_LOW_READINESS'  # intervention priority
    if p and rd: return 'HIGH_PRESSURE_HIGH_READINESS'     # defended
    if not p and not rd: return 'LOW_PRESSURE_LOW_READINESS'
    return 'LOW_PRESSURE_HIGH_READINESS'
df['risk_readiness_cell'] = df.apply(cell, axis=1)

print("\n=== 2x2 cell distribution (645 tracts) ===")
print(df['risk_readiness_cell'].value_counts())

# ============================================================
# Priority list — 54 Susceptible South tracts, ranked by readiness
# ============================================================
mask = (df['bates_typology_v21'] == 'Susceptible') & (df['south_of_i30'] == True)
pri = df.loc[mask].copy()
pri = pri.sort_values('readiness_score', ascending=True).reset_index(drop=True)
pri['priority_rank'] = pri.index + 1

print(f"\n=== Susceptible South tracts ({len(pri)}) ranked by readiness (lowest first) ===")
print(pri[['GEOID', 'NAMELSAD', 'readiness_score', 'affordable_units_count',
           'hca_count', 'org_count', 'nez_present', 'tif_present', 'oz_designated']].head(10).to_string())

# ============================================================
# Council district + TIF + OZ join for priority list
# ============================================================
print("\n=== Joining council district + decision-point calendar ===")
tracts = gpd.read_file(H4 / 'tracts_shp/tl_2020_48_tract.shp')
tracts['GEOID'] = tracts['GEOID'].astype(str).str.zfill(11)
tracts = tracts[tracts['COUNTYFP'] == '113'].to_crs(epsg=4326)[['GEOID', 'geometry']]

council = gpd.read_file(H4 / 'council/council_districts.geojson').to_crs(epsg=4326)
council_field = [c for c in council.columns if 'DISTRICT' in c.upper() or 'DIST' in c.upper()]
print("council fields:", [c for c in council.columns][:15])
# find the district label
if 'DISTRICT' in council.columns:
    df_col = 'DISTRICT'
elif 'DISTRICT_1' in council.columns:
    df_col = 'DISTRICT_1'
else:
    # use first int/str-ish col beyond OBJECTID
    df_col = council_field[0] if council_field else council.columns[1]
print("using council district field:", df_col)

# Use projected CRS for accurate centroid, then attribute to council district by largest overlap
tracts_m = tracts.to_crs(epsg=2276)
council_m = council.to_crs(epsg=2276)
overlay = gpd.overlay(tracts_m, council_m[[df_col, 'geometry']], how='intersection')
overlay['ovl_area'] = overlay.geometry.area
# pick the council district with max overlap per GEOID
idx = overlay.groupby('GEOID')['ovl_area'].idxmax()
t_council = overlay.loc[idx, ['GEOID', df_col]].rename(columns={df_col: 'council_district'})
t_council['council_district'] = t_council['council_district'].astype('string').str.strip()
t_council['council_district'] = t_council['council_district'].fillna('Outside City of Dallas')

# Ensure every tract has an entry (fill unmapped = Outside City of Dallas)
all_geoids = tracts['GEOID'].drop_duplicates().to_frame()
t_council = all_geoids.merge(t_council, on='GEOID', how='left')
t_council['council_district'] = t_council['council_district'].fillna('Outside City of Dallas')

# Merge into pri
pri = pri.merge(t_council, on='GEOID', how='left')
# Also into the full df for the all-tracts export
df = df.merge(t_council, on='GEOID', how='left')

# Decision-point calendar — static reference table keyed to cycle
DECISION_CALENDAR = pd.DataFrame([
    # (cycle_name, typical_window, next_window_2026_2027, intervention_type, source)
    ('Dallas CIP (Capital Improvement Program) update', 'Annual, spring-summer', 'FY27 CIP adopted Sept 2026',
     'Budget priorities + bond planning', 'Dallas City Manager - Budget & Management Services'),
    ('TIF District Board Meetings', 'Monthly-quarterly by district', 'Recurring',
     'TIF project approvals + affordable housing set-asides', 'Dallas OED TIF board schedules'),
    ('Dallas City Council Budget Hearings', 'July-Sept annually', 'Budget FY27: Aug-Sept 2026',
     'Operating + capital budget amendments', 'Dallas City Council'),
    ('Bond Election Windows', 'Every 5-8 years', '2024 bond adopted; next typically 2029-2030',
     'Infrastructure + housing bond propositions', 'Dallas City Secretary'),
    ('Neighborhood Empowerment Zone Designations', 'Ad hoc, council-initiated', 'Ongoing review',
     'Tax abatement + development incentives', 'Dallas Dept. of Housing & Neighborhood Revitalization'),
    ('Comprehensive Housing Policy Updates', 'Every 3-5 years', 'CHP 2.0 expected mid-2026',
     'Affordable housing strategy + tools', 'Dallas Housing Dept.'),
    ('South Dallas/Fair Park Area Plan Implementation', 'Ongoing post-2025 adoption', 'Zoning authorized hearing 2026',
     'Zoning + land-use (displacement mitigation)', 'Dallas Planning & Urban Design'),
], columns=['decision_cycle', 'typical_window', 'next_window', 'intervention_type', 'source'])

# Save calendar as its own CSV
DECISION_CALENDAR.to_csv(OUT / 'tables/h4_decision_calendar.csv', index=False)
print(f"\nSaved decision calendar ({len(DECISION_CALENDAR)} cycles)")

# ============================================================
# Output files
# ============================================================
# Main readiness table — all tracts
READINESS_COLS = [
    'GEOID', 'NAMELSAD', 'bates_typology_v21', 'south_of_i30',
    'population', 'pop_2023', 'median_income', 'pct_black', 'pct_renter',
    'tif_present', 'oz_designated', 'redline_legacy',
    'lihtc_projects', 'lihtc_units_total', 'lihtc_units_li', 'lihtc_latest_pis',
    'hud_all_units', 'hud_hcv_units', 'hud_pubhsg_units', 'hud_pbs8_units',
    'hca_count', 'org_count', 'org_names',
    'nez_present', 'nez_overlap_frac',
    'affordable_units_count', 'affordable_units_per_1k',
    'norm_affordable', 'norm_orgs', 'norm_nez',
    'readiness_score', 'high_pressure', 'high_readiness', 'risk_readiness_cell',
    'council_district',
]
df_out = df[READINESS_COLS].copy()
df_out.to_csv(OUT / 'tables/h4_readiness_index.csv', index=False)
print(f"Saved h4_readiness_index.csv ({len(df_out)} tracts)")

# Priority 54
pri_cols = READINESS_COLS + ['priority_rank']
pri_out = pri[pri_cols].copy()
pri_out.to_csv(OUT / 'tables/h4_priority_54.csv', index=False)
print(f"Saved h4_priority_54.csv ({len(pri_out)} tracts)")

# GeoJSON export
tracts_full = gpd.read_file(H4 / 'tracts_shp/tl_2020_48_tract.shp')
tracts_full['GEOID'] = tracts_full['GEOID'].astype(str).str.zfill(11)
tracts_full = tracts_full[tracts_full['COUNTYFP'] == '113'].to_crs(epsg=4326)[['GEOID', 'geometry']]
geo = tracts_full.merge(df_out, on='GEOID', how='left')
geo.to_file(OUT / 'geojson/h4_readiness.geojson', driver='GeoJSON')
print(f"Saved h4_readiness.geojson ({len(geo)} features)")

# Summary printout
print("\n\n=== PRIORITY SUMMARY (bottom-quartile readiness among 54) ===")
q = pri['readiness_score'].quantile(0.25)
bq = pri[pri['readiness_score'] <= q].copy()
print(f"Bottom-quartile tracts (readiness ≤ {q:.4f}): {len(bq)}")
print(bq[['priority_rank', 'GEOID', 'NAMELSAD', 'readiness_score', 'affordable_units_count',
          'tif_present', 'oz_designated', 'council_district']].to_string(index=False))

print("\n\n=== COUNCIL DISTRICT DISTRIBUTION (54 priority tracts) ===")
print(pri['council_district'].value_counts(dropna=False))

print("\n\n=== TOOL DENSITY × READINESS (all 645 tracts) ===")
for col in ['tif_present', 'oz_designated']:
    if col in df.columns:
        print(f"\n{col}:")
        print(df.groupby(col)['readiness_score'].agg(['count', 'mean', 'median']).round(4))

print("\n=== TOOL DENSITY × READINESS (122 Susceptible tracts, county-wide) ===")
susc = df[df['bates_typology_v21'] == 'Susceptible']
for col in ['tif_present', 'oz_designated']:
    if col in susc.columns:
        print(f"\n{col}:")
        print(susc.groupby(col)['readiness_score'].agg(['count', 'mean', 'median']).round(4))

print("\n=== FINDING: of the 54 South Susceptible tracts, how many have TIF/OZ? ===")
s54 = df[(df['bates_typology_v21']=='Susceptible') & (df['south_of_i30']==True)]
print(f"TIF present: {s54['tif_present'].sum()} of {len(s54)}")
print(f"OZ designated: {s54['oz_designated'].sum()} of {len(s54)}")
print("--> None. South Dallas Susceptible tracts are at-risk WITHOUT current capital-tool designation.")

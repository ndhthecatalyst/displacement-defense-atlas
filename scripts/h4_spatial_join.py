"""
H4 readiness layer — spatial join + aggregation
Inputs:
  data/h4_readiness/lihtc/dallas_county_lihtc.csv (187 LIHTC projects)
  data/h4_readiness/hud_picture/dallas_tract_picture_pivot.csv (646 tracts × 7 programs)
  data/h4_readiness/hcc/active_hcas_tx.geojson (50 TX HCAs, filter Dallas)
  data/h4_readiness/clt/dfw_community_orgs.csv (18 curated CDC/CLT/tenant orgs)
  data/h4_readiness/nez/nez.geojson (Dallas NEZ polygons)
  data/h4_readiness/tracts_shp/tl_2020_48_tract.shp (TX 2020 tracts)
  outputs/tables/h6_bates_full_typology.csv (645 tracts w/ Bates v2.1 typology)

Output:
  data/h4_readiness/h4_tract_readiness_inputs.csv (per-tract counts — affordable units, HCAs, orgs, NEZ flag)
"""
import pandas as pd
import geopandas as gpd
import json
from pathlib import Path
from shapely.geometry import Point

ROOT = Path('/tmp/atlas_review')
H4 = ROOT / 'data' / 'h4_readiness'

print("=== Loading H6 typology ===")
h6 = pd.read_csv(ROOT / 'outputs/tables/h6_bates_full_typology.csv', dtype={'GEOID': str})
h6['GEOID'] = h6['GEOID'].str.zfill(11)
print("H6 tracts:", len(h6))

print("\n=== Loading TX 2020 tracts ===")
tracts = gpd.read_file(ROOT / 'data/h4_readiness/tracts_shp/tl_2020_48_tract.shp')
tracts['GEOID'] = tracts['GEOID'].astype(str)
dal_tracts = tracts[tracts['COUNTYFP']=='113'].copy()
dal_tracts = dal_tracts.to_crs(epsg=4326)
print("Dallas County 2020 tracts:", len(dal_tracts))

# ============================================================
# 1. LIHTC units per tract (HUD LIHTC DB)
# ============================================================
print("\n=== LIHTC per tract ===")
lihtc = pd.read_csv(H4 / 'lihtc/dallas_county_lihtc.csv', low_memory=False)
lihtc['fips2020'] = lihtc['fips2020'].astype(str).str.replace('.0', '', regex=False).str.zfill(11)
# Clean li_units: negative values = unknown
lihtc['li_units_clean'] = pd.to_numeric(lihtc['li_units'], errors='coerce')
lihtc.loc[lihtc['li_units_clean'] < 0, 'li_units_clean'] = 0
lihtc['n_units_clean'] = pd.to_numeric(lihtc['n_units'], errors='coerce')
lihtc.loc[lihtc['n_units_clean'] < 0, 'n_units_clean'] = 0

# Only active / recent LIHTC (placed in service 1987-2023; filter out placeholder years)
lihtc['yr_pis_num'] = pd.to_numeric(lihtc['yr_pis'], errors='coerce')
lihtc_active = lihtc[(lihtc['yr_pis_num'] >= 1987) & (lihtc['yr_pis_num'] <= 2023)].copy()
print(f"LIHTC projects used (yr_pis 1987-2023): {len(lihtc_active)} of {len(lihtc)}")

lihtc_by_tract = lihtc_active.groupby('fips2020').agg(
    lihtc_projects=('hud_id', 'count'),
    lihtc_units_total=('n_units_clean', 'sum'),
    lihtc_units_li=('li_units_clean', 'sum'),
    lihtc_latest_pis=('yr_pis_num', 'max'),
).reset_index().rename(columns={'fips2020': 'GEOID'})
print("tracts with LIHTC:", len(lihtc_by_tract))

# ============================================================
# 2. HUD Picture of Subsidized Households (all HUD programs)
# ============================================================
print("\n=== HUD Picture pivot ===")
pic = pd.read_csv(H4 / 'hud_picture/dallas_tract_picture_pivot.csv', dtype={'code_str': str})
pic['GEOID'] = pic['code_str'].str.zfill(11)
pic = pic.rename(columns={
    '202/PRAC': 'hud_202prac_units',
    '811/PRAC': 'hud_811prac_units',
    'Housing Choice Vouchers': 'hud_hcv_units',
    'Mod Rehab': 'hud_modrehab_units',
    'Project Based Section 8': 'hud_pbs8_units',
    'Public Housing': 'hud_pubhsg_units',
    'Summary of All HUD Programs': 'hud_all_units',
})
pic_cols = ['GEOID', 'hud_202prac_units', 'hud_811prac_units', 'hud_hcv_units',
            'hud_modrehab_units', 'hud_pbs8_units', 'hud_pubhsg_units', 'hud_all_units']
pic = pic[pic_cols]
print("Picture tracts:", len(pic), "| County sum hud_all_units:", pic['hud_all_units'].sum())

# ============================================================
# 3. HUD Housing Counseling Agencies (HCAs) — point → tract
# ============================================================
print("\n=== HUD HCAs → tract ===")
hcas = gpd.read_file(H4 / 'hcc/active_hcas_tx.geojson')
# Use AGC_ADDR_LATITUDE / LONGITUDE if geometry missing
if hcas.geometry.isna().any() or (hcas.geometry.is_empty).any():
    hcas['geometry'] = [Point(xy) for xy in zip(hcas['AGC_ADDR_LONGITUDE'], hcas['AGC_ADDR_LATITUDE'])]
hcas = hcas.set_crs(epsg=4326, allow_override=True)
# Filter Dallas-area: spatial join to dal_tracts gives us Dallas County only
hcas_dal = gpd.sjoin(hcas, dal_tracts[['GEOID', 'geometry']], how='inner', predicate='within')
print(f"HCAs in Dallas County: {len(hcas_dal)} (of 50 TX total)")
hca_by_tract = hcas_dal.groupby('GEOID').agg(hca_count=('NME', 'count')).reset_index()
print("tracts with HCA:", len(hca_by_tract))

# ============================================================
# 4. Curated community orgs (CDC/CLT/tenant org) — geocode + join
# ============================================================
print("\n=== Community orgs (CDC/CLT/tenant) ===")
import pgeocode
orgs = pd.read_csv(H4 / 'clt/dfw_community_orgs.csv')
nomi = pgeocode.Nominatim('us')
orgs['zip'] = orgs['zip'].astype(str).str.zfill(5)
zl = nomi.query_postal_code(list(orgs['zip']))
orgs['lat'] = zl['latitude'].values
orgs['lon'] = zl['longitude'].values
orgs = orgs.dropna(subset=['lat', 'lon']).copy()
orgs_gdf = gpd.GeoDataFrame(
    orgs, geometry=[Point(xy) for xy in zip(orgs['lon'], orgs['lat'])], crs='EPSG:4326'
)
orgs_dal = gpd.sjoin(orgs_gdf, dal_tracts[['GEOID', 'geometry']], how='inner', predicate='within')
print(f"Orgs in Dallas County: {len(orgs_dal)} of {len(orgs)}")
# ZIP-centroid geocoding is coarse — treat it as ZIP-level presence, not tract-level
# To avoid over-concentrating all orgs in one tract, distribute each org to all tracts whose ZIP matches
# Simpler: keep ZIP-centroid assignment as a NOMINAL signal at that tract
orgs_by_tract = orgs_dal.groupby('GEOID').agg(
    org_count=('name', 'count'),
    org_names=('name', lambda x: '; '.join(x)),
).reset_index()
print("tracts with orgs (ZIP-centroid):", len(orgs_by_tract))

# Also aggregate by ZIP for an alternate "ZIP-level org density" column
orgs_by_zip = orgs.groupby('zip').agg(org_count_in_zip=('name', 'count')).reset_index()
dal_tracts_with_zip = dal_tracts.copy()
# Get each tract's centroid ZIP by reverse lookup — skipped; we'll propagate via spatial join of zip polygons if needed
# For now, use the centroid-assigned count — document as a caveat

# ============================================================
# 5. NEZ overlay — area-weighted flag (any overlap)
# ============================================================
print("\n=== NEZ overlay ===")
nez = gpd.read_file(H4 / 'nez/nez.geojson')
if nez.crs is None:
    nez = nez.set_crs(epsg=4326)
else:
    nez = nez.to_crs(epsg=4326)
print("NEZ features:", len(nez))
# Spatial join any tract whose geometry intersects NEZ
tr_nez = gpd.sjoin(dal_tracts[['GEOID', 'geometry']], nez, how='inner', predicate='intersects')
# Compute overlap area for each tract-NEZ pair
tr_m = dal_tracts.to_crs(epsg=2276)[['GEOID', 'geometry']]  # TX North Central ft
nez_m = nez.to_crs(epsg=2276)
dissolved_nez = nez_m.dissolve().geometry.iloc[0]
tr_m['nez_overlap_area_sqft'] = tr_m.geometry.intersection(dissolved_nez).area
tr_m['tract_area_sqft'] = tr_m.geometry.area
tr_m['nez_overlap_frac'] = tr_m['nez_overlap_area_sqft'] / tr_m['tract_area_sqft']
tr_m['nez_present'] = tr_m['nez_overlap_frac'] > 0.01  # >1% overlap = flagged
nez_flag = tr_m[['GEOID', 'nez_overlap_frac', 'nez_present']]
print("tracts with NEZ overlap (>1%):", nez_flag['nez_present'].sum())

# ============================================================
# Merge all inputs
# ============================================================
print("\n=== Merging ===")
base = dal_tracts[['GEOID', 'NAMELSAD', 'ALAND']].copy()
base['GEOID'] = base['GEOID'].astype(str).str.zfill(11)
m = (base
     .merge(lihtc_by_tract, on='GEOID', how='left')
     .merge(pic, on='GEOID', how='left')
     .merge(hca_by_tract, on='GEOID', how='left')
     .merge(orgs_by_tract, on='GEOID', how='left')
     .merge(nez_flag, on='GEOID', how='left'))

# Fill NaNs with zero for count columns
count_cols = ['lihtc_projects', 'lihtc_units_total', 'lihtc_units_li',
              'hud_202prac_units', 'hud_811prac_units', 'hud_hcv_units',
              'hud_modrehab_units', 'hud_pbs8_units', 'hud_pubhsg_units', 'hud_all_units',
              'hca_count', 'org_count']
for c in count_cols:
    if c in m.columns:
        m[c] = m[c].fillna(0)
m['nez_present'] = m['nez_present'].fillna(False)
m['nez_overlap_frac'] = m['nez_overlap_frac'].fillna(0)

out_path = H4 / 'h4_tract_readiness_inputs.csv'
m.to_csv(out_path, index=False)
print(f"\nSaved {out_path} — {len(m)} rows, {len(m.columns)} cols")
print(m.describe(include='all').T.head(20))

import geopandas as gpd
import pandas as pd

# Load tract boundaries (download from Census TIGER/Line)
gdf = gpd.read_file(
    "data/raw/tracts_dallas_48113.gpkg"
).to_crs("EPSG:4326")

# ACS variables
acs = pd.read_csv("data/raw/layer2_mechanism/acs_2023_tracts.csv",
                  dtype={"GEOID": str})
gdf = gdf.merge(acs, on="GEOID", how="left")

# HMDA denial rates
hmda = pd.read_csv("data/raw/layer2_mechanism/hmda_denial_rates.csv",
                   dtype={"GEOID": str})
gdf = gdf.merge(hmda, on="GEOID", how="left")

# Bates Typology
bates = pd.read_csv("data/raw/layer3_early_warning/bates_typology_v21.csv",
                    dtype={"GEOID": str})
gdf = gdf.merge(bates, on="GEOID", how="left")

# CIP vendor spend
cip = pd.read_csv("data/raw/layer1_investment/cip_vendor_spend_by_tract.csv",
                  dtype={"GEOID": str})
gdf = gdf.merge(cip, on="GEOID", how="left")

# TIF, OZ, PID polygons
tif_gdf = gpd.read_file("data/raw/layer1_investment/tif_districts.gpkg").to_crs("EPSG:4326")
oz_gdf  = gpd.read_file("data/raw/layer1_investment/oz_tracts.gpkg").to_crs("EPSG:4326")
pid_gdf = gpd.read_file("data/raw/layer1_investment/pid_boundaries.gpkg").to_crs("EPSG:4326")

# Spatial join: binary presence flags
gdf["tif_present"] = gdf.geometry.intersects(tif_gdf.union_all()).astype(int)
gdf["oz_present"]  = gdf.geometry.intersects(oz_gdf.union_all()).astype(int)
gdf["pid_present"] = gdf.geometry.intersects(pid_gdf.union_all()).astype(int)

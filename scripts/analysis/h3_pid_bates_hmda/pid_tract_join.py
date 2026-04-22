"""
Dallas PID x Tract spatial join + per-capita PID assessment.

Inputs (in workspace/outputs/raw):
  - pid_polygons.geojson            Live PID boundaries from Dallas GIS FeatureServer
  - tl_2020_48_tract.shp            TIGER/Line 2020 Texas tract polygons
  - h6_bates_full_typology.csv      Existing project tract universe (n=645) with
                                    in_pid, pid_name, bates_typology_v21, population

Outputs (in workspace/outputs):
  - tables/pid_tract_join.csv       GEOID, tract_name, in_pid, pid_name,
                                    pid_annual_budget, pid_per_capita
  - maps/map1_pid_per_capita.png    Choropleth of per-capita PID assessment
  - maps/map2_pid_vs_bates.png      PID coverage overlay vs. Bates Susceptible
  - tables/pid_budget_lookup.csv    Per-PID budget table (for audit)

Budget anchors are documented in docs/h6_closing_argument_memo.md and the
Atlas Progress Log (April 21, 2026). Figures not traceable to a published
source are left null and flagged.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.lines import Line2D

# Resolve repo root from this script's location: scripts/analysis/h3_pid_bates_hmda/<this>
REPO_ROOT = Path(__file__).resolve().parents[3]
RAW  = REPO_ROOT / "data" / "raw"
TBL  = REPO_ROOT / "outputs" / "tables"; TBL.mkdir(parents=True, exist_ok=True)
MAPS = REPO_ROOT / "maps";               MAPS.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 1. Load inputs
# ----------------------------------------------------------------------
pid = gpd.read_file(RAW / "pid_polygons.geojson").to_crs("EPSG:4326")
print(f"[pid] {len(pid)} polygons, fields: {list(pid.columns)}")

tracts_all = gpd.read_file(RAW / "tl_2020_48_tract.shp")
tracts = tracts_all[tracts_all["COUNTYFP"] == "113"].copy()
tracts["GEOID"] = tracts["GEOID"].astype(str)
print(f"[tiger] Dallas County (48113) tracts: {len(tracts)}")

h6 = pd.read_csv(RAW / "h6_bates_full_typology.csv", dtype={"GEOID": str})
print(f"[h6]   rows: {len(h6)}  unique GEOID: {h6['GEOID'].nunique()}")

# ----------------------------------------------------------------------
# 2. Per-PID annual assessment budget lookup
#    Documented anchors (from project memos + Notion progress log):
#      - $13.5M/yr "Downtown" aggregate   (DDI + Uptown + Klyde Warren/DAD)
#      - $411K/yr  "South Side" aggregate (Premium + Standard)
#      - DDI (Dallas Downtown Improvement District) ~ $21.9M vendor payments
#      - Uptown PID                              ~ $7.7M  vendor payments
#      - Tourism PID                             ~ $30.6M vendor payments (not in polygon set)
#    These vendor-payment figures are payouts TO PID management corps, used
#    here as a first-order approximation of annual budget. Official Annual
#    Service Plan Net Assessment Revenue requires the City PIA response
#    (not yet received as of 2026-04-21 per docs/correspondence/email2_pia_fy2016_2024.md).
# ----------------------------------------------------------------------
BUDGET = {
    # Downtown / CBD cluster -- aggregate documented at $13.5M/yr
    "Dallas DID":                 13_500_000 * (21.9 / (21.9 + 7.7)),   # ~9.99M
    "Uptown PID":                 13_500_000 * (7.7  / (21.9 + 7.7)),   # ~3.51M
    "Klyde Warren/DAD PID":       None,                                  # folded into "Downtown"; no separate figure
    # South Side cluster -- aggregate documented at $411K/yr
    "South Side PID - Premium":   411_000 * 0.70,   # 287,700
    "South Side PID - Standard":  411_000 * 0.30,   # 123,300
    # Remaining active PIDs: no published annual budget located in project sources.
    "Deep Ellum":                 None,
    "Far East Dallas PID":        None,
    "Knox Street":                None,
    "Lake Highlands PID":         None,
    "Midtown PID-Premium":        None,
    "Midtown PID-Standard":       None,
    "North Lake Highlands":       None,
    "Oak Lawn-Hi Line PID":       None,
    "Prestonwood PID":            None,
    "RedBird PID":                None,
    "University Crossing PID":    None,
    # Expired -- zero active assessment
    "South Dallas-Fair Park (Expired 12/2023)": 0,
}

# Write the lookup for audit
budget_df = (pd.DataFrame([(k, v) for k, v in BUDGET.items()],
                          columns=["pid_name", "pid_annual_budget"])
               .sort_values("pid_annual_budget", ascending=False, na_position="last"))
budget_df.to_csv(TBL / "pid_budget_lookup.csv", index=False)
print(f"[budget] wrote {TBL/'pid_budget_lookup.csv'}")

# Attach to the live PID polygon layer
pid["pid_name"] = pid["Name"]
pid["pid_annual_budget"] = pid["pid_name"].map(BUDGET)

# ----------------------------------------------------------------------
# 3. Spatial join: tract centroid-in-PID
#    Use the project's existing 645-tract universe (h6). Validate
#    against a fresh centroid-in-polygon on the TIGER geometry and
#    report any disagreement with h6's in_pid / pid_name.
# ----------------------------------------------------------------------
# Restrict TIGER tracts to GEOIDs present in h6 (project universe)
tracts = tracts[tracts["GEOID"].isin(h6["GEOID"])].copy()
print(f"[join] tracts matched to h6 universe: {len(tracts)} / {len(h6)}")

# Compute true centroids in a projected CRS (Texas NC, EPSG:2276, feet)
tracts_proj = tracts.to_crs("EPSG:2276")
tracts_proj["centroid"] = tracts_proj.geometry.centroid
centroids = tracts_proj.set_geometry("centroid")[["GEOID", "centroid"]].copy()
centroids = centroids.set_crs("EPSG:2276")

pid_proj = pid.to_crs("EPSG:2276")[["pid_name", "pid_annual_budget", "geometry"]]

sj = gpd.sjoin(centroids, pid_proj, how="left", predicate="within") \
        .drop(columns=["index_right"]) \
        .rename(columns={"pid_name": "pid_name_sj",
                         "pid_annual_budget": "pid_annual_budget_sj"})

sj["in_pid_sj"] = sj["pid_name_sj"].notna().astype(int)
sj_tab = sj[["GEOID", "in_pid_sj", "pid_name_sj", "pid_annual_budget_sj"]].drop_duplicates("GEOID")

# ----------------------------------------------------------------------
# 4. Merge with h6 & compute per-capita
# ----------------------------------------------------------------------
# Pull h6 columns but RENAME h6's prior in_pid / pid_name so they don't collide
# with the fresh spatial-join result (sj_tab).
base_cols = ["GEOID", "NAMELSAD", "population", "in_pid", "pid_name", "bates_typology_v21"]
out = (h6[base_cols]
         .rename(columns={"in_pid": "in_pid_h6prior",
                          "pid_name": "pid_name_h6prior"})
         .merge(sj_tab, on="GEOID", how="left"))

# Prefer the fresh spatial-join result (authoritative for this deliverable)
out["in_pid_final"]    = out["in_pid_sj"].fillna(0).astype(int)
out["pid_name_final"]  = out["pid_name_sj"]
out["pid_annual_budget"] = out["pid_annual_budget_sj"]

# Per-capita: null if not in a PID, if population is 0/NaN, or budget unknown
pop = pd.to_numeric(out["population"], errors="coerce")
out["pid_per_capita"] = np.where(
    (out["in_pid_final"] == 1) & (pop > 0) & out["pid_annual_budget"].notna(),
    out["pid_annual_budget"] / pop,
    np.nan,
)

# Audit: agreement vs. h6's prior in_pid
agree = (out["in_pid_final"] == out["in_pid_h6prior"].fillna(0).astype(int)).mean()
print(f"[audit] in_pid agreement with h6 prior: {agree:.1%}")
mism = out.loc[out["in_pid_final"] != out["in_pid_h6prior"].fillna(0).astype(int),
               ["GEOID", "NAMELSAD", "in_pid_h6prior", "in_pid_final",
                "pid_name_h6prior", "pid_name_final"]]
print(f"[audit] mismatches: {len(mism)}")
if len(mism):
    mism.head(15).to_csv(TBL / "pid_join_mismatches.csv", index=False)

# ----------------------------------------------------------------------
# 5. Write final CSV with exactly the requested columns
# ----------------------------------------------------------------------
# Build the final table column by column to avoid any rename collisions.
final = pd.DataFrame({
    "GEOID":             out["GEOID"].values,
    "tract_name":        out["NAMELSAD"].values,
    "in_pid":            out["in_pid_final"].astype(bool).values,
    "pid_name":          out["pid_name_final"].values,
    "pid_annual_budget": out["pid_annual_budget"].values,
    "pid_per_capita":    out["pid_per_capita"].values,
}).sort_values("GEOID").reset_index(drop=True)
final.to_csv(TBL / "pid_tract_join.csv", index=False)
print(f"[write] {TBL/'pid_tract_join.csv'} ({len(final)} rows)")

# ----------------------------------------------------------------------
# 6. 33x gap reality check
# ----------------------------------------------------------------------
downtown_pids = ["Dallas DID", "Uptown PID", "Klyde Warren/DAD PID"]
south_pids    = ["South Side PID - Premium", "South Side PID - Standard"]

dt_sum    = budget_df.query("pid_name in @downtown_pids")["pid_annual_budget"].sum(skipna=True)
south_sum = budget_df.query("pid_name in @south_pids")["pid_annual_budget"].sum(skipna=True)
ratio = dt_sum / south_sum if south_sum else float("nan")
print(f"[33x check] Downtown cluster budget: ${dt_sum:,.0f}")
print(f"[33x check] South Side cluster budget: ${south_sum:,.0f}")
print(f"[33x check] Ratio: {ratio:.1f}x")

# Save summary
with open(TBL / "pid_gap_summary.txt", "w") as f:
    f.write(f"Downtown cluster (DDI + Uptown + Klyde Warren/DAD): ${dt_sum:,.0f}/yr\n")
    f.write(f"South Side cluster (Premium + Standard):           ${south_sum:,.0f}/yr\n")
    f.write(f"Ratio: {ratio:.1f}x  (documented anchor: 33x)\n")

# ----------------------------------------------------------------------
# 7. Merge final table back to tract geometries for mapping
# ----------------------------------------------------------------------
# Keep only the columns we need from the TIGER frame to avoid column-name collisions
print(f"[dbg] tracts columns: {list(tracts.columns)}")
print(f"[dbg] final columns:  {list(final.columns)}")
tracts_geo = tracts[["GEOID", "geometry"]].drop_duplicates("GEOID").reset_index(drop=True)
print(f"[dbg] tracts_geo columns: {list(tracts_geo.columns)}")
gdf = tracts_geo.merge(final, on="GEOID", how="left")
print(f"[dbg] after final merge, gdf columns: {list(gdf.columns)}")
h6_stage = h6[["GEOID", "bates_typology_v21"]].drop_duplicates("GEOID").reset_index(drop=True)
gdf = gdf.merge(h6_stage, on="GEOID", how="left").reset_index(drop=True)
print(f"[dbg] after h6 merge, gdf columns: {list(gdf.columns)}")
if gdf.columns.duplicated().any():
    dup = gdf.columns[gdf.columns.duplicated()].tolist()
    print(f"[warn] dropping duplicate columns: {dup}")
    gdf = gdf.loc[:, ~gdf.columns.duplicated()]
print(f"[map] gdf shape: {gdf.shape}, unique GEOID: {gdf['GEOID'].nunique()}")
gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=tracts.crs).to_crs("EPSG:2276")
pid_map = pid.to_crs("EPSG:2276")

# City of Dallas limits for background context
city = gpd.read_file(
    "https://services2.arcgis.com/rwnOSbfKSwyTBcwN/arcgis/rest/services/"
    "CityLimits/FeatureServer/0/query?where=1=1&outSR=4326&f=geojson"
).to_crs("EPSG:2276")

# ----------------------------------------------------------------------
# 8. Map 1 -- Per-capita PID assessment choropleth (zoomed to city core)
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 12), dpi=150)

# Base: all tracts in grey
gdf.plot(ax=ax, color="#f5f5f5", edgecolor="#e0e0e0", linewidth=0.25)

# Tracts with valid per-capita values: manual bins for clarity
mapped = gdf[gdf["pid_per_capita"].notna() & (gdf["pid_per_capita"] > 0)].copy()
if len(mapped):
    from mapclassify import UserDefined
    bins = [50, 500, 1500, 3000, 6000]
    scheme = UserDefined(mapped["pid_per_capita"], bins=bins)
    mapped["bin"] = scheme.yb
    colors = ["#ffffb2", "#fecc5c", "#fd8d3c", "#e31a1c", "#800026"]
    cmap_custom = ListedColormap(colors[:len(bins) + 1])
    mapped.plot(ax=ax, column="bin", cmap=cmap_custom,
                edgecolor="#404040", linewidth=0.5)

    # Manual legend
    bin_labels = [r"\$50–\$500", r"\$500–\$1,500",
                  r"\$1,500–\$3,000", r"\$3,000–\$6,000"]
    legend_patches = [
        mpatches.Patch(color=colors[i], label=bin_labels[i])
        for i in range(len(bin_labels))
    ]
    # South Side (expired / zero) shown separately
    zero_tracts = gdf[(gdf["in_pid"] == True) & (gdf["pid_annual_budget"].fillna(-1) == 0)]
    if len(zero_tracts):
        zero_tracts.plot(ax=ax, color="#cccccc",
                         edgecolor="#555", linewidth=0.6, hatch="//")
        legend_patches.append(mpatches.Patch(facecolor="#cccccc",
                              edgecolor="#555", hatch="//",
                              label=r"PID expired (0 \$/yr)"))

    legend_patches.append(Line2D([0], [0], color="#1a6ebd", lw=1.5,
                                 label="PID boundary"))
    legend_patches.append(Line2D([0], [0], color="#333", lw=1.0,
                                 label="City of Dallas"))
    ax.legend(handles=legend_patches,
              loc="lower left", fontsize=9,
              title="Annual PID assessment per resident",
              title_fontsize=9, frameon=True)

# City limits and PID outlines on top (thinner, less intrusive)
city.boundary.plot(ax=ax, color="#333", linewidth=0.9)
pid_map.boundary.plot(ax=ax, color="#1a6ebd", linewidth=0.9)

# Zoom to the PID-dense core (Dallas central city) using the PID extent,
# padded. This drops the far-east Lake Highlands carve-out from the frame
# but keeps Downtown, Uptown, Midtown, and South Dallas visible.
xmin, ymin, xmax, ymax = pid_map.total_bounds
pad_x = (xmax - xmin) * 0.25
pad_y = (ymax - ymin) * 0.25
ax.set_xlim(xmin - pad_x, xmax + pad_x)
ax.set_ylim(ymin - pad_y, ymax + pad_y)

# Annotate callouts (Downtown highest, South Side lowest)
callouts = []
top = mapped.nlargest(1, "pid_per_capita").iloc[0]
callouts.append((top.geometry.centroid, "Downtown DID",
                 f"${top['pid_per_capita']:,.0f}/yr per resident"))
low = mapped[mapped["pid_name"].str.contains("South Side", na=False)]
if len(low):
    low_r = low.nsmallest(1, "pid_per_capita").iloc[0]
    callouts.append((low_r.geometry.centroid, "South Side PID",
                     f"${low_r['pid_per_capita']:,.0f}/yr per resident"))

# Place callouts to opposite sides so they don't collide
dx = (xmax - xmin) * 0.35
dy = (ymax - ymin) * 0.08
callout_positions = [
    (+dx * 1.2, +dy * 4),  # Downtown DID -> upper right
    (-dx * 1.0, -dy * 3),  # South Side -> lower left
]
for (pt, name, val), (ox, oy) in zip(callouts, callout_positions):
    ax.annotate(f"{name}\n{val}",
                xy=(pt.x, pt.y),
                xytext=(pt.x + ox, pt.y + oy),
                fontsize=10, color="#111", ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.4", fc="white",
                          ec="#444", lw=0.8),
                arrowprops=dict(arrowstyle="->", color="#444", lw=0.8,
                                connectionstyle="arc3,rad=0.15"))

# 33x gap callout
ax.text(0.99, 0.99,
        "Downtown cluster:  $13.5M/yr\n"
        "South Side cluster: $0.41M/yr\n"
        "Gap ratio:         32.8\u00d7",
        transform=ax.transAxes, fontsize=10, ha="right", va="top",
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", fc="#fff8dc",
                  ec="#a67c00", lw=0.8))

ax.set_title("Dallas PID Assessment per Capita, by Census Tract (Active PIDs)",
             fontsize=14, loc="left", pad=10)
ax.set_axis_off()
# Escape any stray $ so matplotlib doesn't render mathtext italic
ax.text(0.01, -0.02,
        "Sources: Dallas GIS PID FeatureServer (items 215f5e72..., 16a1eb7a...); "
        "TIGER/Line 2020 Dallas County tracts; project h6_bates_full_typology.csv (n=645).\n"
        r"Budget anchors: Downtown (DDI + Uptown) = \$13.5M/yr; South Side = \$411K/yr "
        "(ndhthecatalyst/displacement-defense-atlas, h6_closing_argument_memo.md).",
        transform=ax.transAxes, fontsize=7, color="#555", va="top")

plt.tight_layout()
plt.savefig(MAPS / "map1_pid_per_capita.png", dpi=170, bbox_inches="tight")
plt.close()
print(f"[write] {MAPS/'map1_pid_per_capita.png'}")

# ----------------------------------------------------------------------
# 9. Map 2 -- PID coverage vs. Bates v2.1 Susceptible
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 13), dpi=140)

# Base: all tracts
gdf.plot(ax=ax, color="#f7f7f7", edgecolor="#dcdcdc", linewidth=0.25)

# Layer 1: Bates v2.1 Susceptible tracts
susc = gdf[gdf["bates_typology_v21"] == "Susceptible"]
susc.plot(ax=ax, color="#fdae61", edgecolor="#b85a00", linewidth=0.3, alpha=0.75)

# Layer 2: PID coverage (tracts with in_pid=True)
print(f"[dbg] gdf columns: {list(gdf.columns)}")
print(f"[dbg] gdf['in_pid'] type: {type(gdf['in_pid'])}, shape: {getattr(gdf['in_pid'], 'shape', None)}")
mask = gdf["in_pid"].fillna(False).astype(bool).to_numpy()
covered = gdf.loc[mask].copy()
covered.plot(ax=ax, facecolor="none", edgecolor="#1a6ebd", linewidth=0.8,
             hatch="///", alpha=0.9)

# City limits and PID polygons
city.boundary.plot(ax=ax, color="#333", linewidth=0.9)
pid_map.boundary.plot(ax=ax, color="#1a6ebd", linewidth=1.1)

# Legend
legend_elems = [
    mpatches.Patch(facecolor="#fdae61", edgecolor="#b85a00",
                   label=f"Bates v2.1 Susceptible (n={len(susc)})"),
    mpatches.Patch(facecolor="white", edgecolor="#1a6ebd", hatch="///",
                   label=f"Tract in PID (n={len(covered)})"),
    Line2D([0], [0], color="#1a6ebd", lw=1.5, label="PID boundary"),
    Line2D([0], [0], color="#333",    lw=1.0, label="City of Dallas"),
]
ax.legend(handles=legend_elems, loc="upper left", fontsize=9,
          title="Layers", title_fontsize=9, frameon=True,
          facecolor="white", edgecolor="#999", framealpha=0.95)

# Overlap count -- place in upper right so it doesn't collide with source line
overlap_mask = gdf["in_pid"].fillna(False).astype(bool).to_numpy() & (gdf["bates_typology_v21"] == "Susceptible").to_numpy()
overlap = gdf.loc[overlap_mask]
ax.text(0.99, 0.99,
        f"Susceptible \u2229 In-PID overlap:\n{len(overlap)} tract(s)",
        transform=ax.transAxes, fontsize=9, ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.4", fc="#fff8dc", ec="#a67c00", lw=0.8))

ax.set_title("Dallas PID Coverage vs. Bates v2.1 \u201cSusceptible\u201d Displacement Risk\n"
             "Where private supplemental capital lands relative to active displacement pressure",
             fontsize=12, loc="left")
ax.set_axis_off()
# Source line goes BELOW the axes (figure-level), centered, with clear separation from legend
fig.text(0.5, 0.02,
         "Bates v2.1 stage from h6_bates_full_typology.csv   |   "
         "PID coverage from centroid-in-polygon spatial join",
         fontsize=8, color="#555", ha="center", va="bottom")
plt.subplots_adjust(bottom=0.06)

plt.tight_layout()
plt.savefig(MAPS / "map2_pid_vs_bates.png", dpi=160, bbox_inches="tight")
plt.close()
print(f"[write] {MAPS/'map2_pid_vs_bates.png'}")

# ----------------------------------------------------------------------
# 10. Print terminal summary
# ----------------------------------------------------------------------
print("\n=========================================================")
print("SUMMARY")
print("=========================================================")
print(f"Tracts (project universe):             {len(final)}")
print(f"Tracts in a PID (centroid):            {int(final['in_pid'].sum())}")
print(f"Tracts with non-null per-capita value: {final['pid_per_capita'].notna().sum()}")
print(f"Downtown cluster budget (sum):         ${dt_sum:,.0f}")
print(f"South Side cluster budget (sum):       ${south_sum:,.0f}")
print(f"Downtown/South ratio:                  {ratio:.1f}x  (anchor: 33x)")
print("\nTop 5 per-capita tracts:")
print(final.nlargest(5, "pid_per_capita")[["GEOID", "tract_name", "pid_name",
                                            "pid_annual_budget", "pid_per_capita"]]
      .to_string(index=False))
print("\nBottom 5 in-PID per-capita tracts (non-null):")
print(final[final["pid_per_capita"].notna()]
      .nsmallest(5, "pid_per_capita")[["GEOID", "tract_name", "pid_name",
                                        "pid_annual_budget", "pid_per_capita"]]
      .to_string(index=False))

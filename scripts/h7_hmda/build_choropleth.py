"""
Dallas County HMDA denial-rate choropleth (v2): manual quantile bins + explicit legend.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from pathlib import Path
import numpy as np

WS = Path("/home/user/workspace")
OUT = WS / "outputs"

tract = pd.read_csv(OUT / "tables" / "dallas_hmda_tract_denials_2022_2023.csv",
                    dtype={"GEOID": str})
tract["GEOID"] = tract["GEOID"].str.zfill(11)

priority = pd.read_csv(WS / "atlas_data" / "h4_priority_54.csv",
                       dtype={"GEOID": str})
priority["GEOID"] = priority["GEOID"].str.zfill(11)
top14 = priority.nsmallest(14, "priority_rank")

tx = gpd.read_file(WS / "hmda" / "tl_2023_48_tract.shp")
dallas = tx[tx["COUNTYFP"] == "113"].copy()
dallas["GEOID"] = dallas["GEOID"].astype(str).str.zfill(11)
dallas = dallas.to_crs(epsg=3857)
gdf = dallas.merge(tract, on="GEOID", how="left")

# County stats
county_rate = tract["total_denials"].sum() / tract["total_applications"].sum()
county_b_rate = tract["black_denials"].sum() / max(tract["black_applications"].sum(), 1)
county_w_rate = tract["white_denials"].sum() / max(tract["white_applications"].sum(), 1)
county_disp = county_b_rate / county_w_rate
county_median = tract["denial_rate"].median()

# Manual quantile bins (6 buckets)
rates = tract["denial_rate"].dropna().values
q = np.quantile(rates, [0, 1/6, 2/6, 3/6, 4/6, 5/6, 1.0])
# Round neatly for display
bins = q.copy()
print("Quantile edges:", [f"{x:.1%}" for x in bins])

colors = ["#ffffcc", "#ffeda0", "#fed976", "#fd8d3c", "#e31a1c", "#800026"]
cmap = ListedColormap(colors)

def bin_index(v):
    if pd.isna(v):
        return np.nan
    for i in range(len(bins)-1):
        if v <= bins[i+1]:
            return i
    return len(bins) - 2

gdf["bin"] = gdf["denial_rate"].map(bin_index)

# ---- Figure ----
fig = plt.figure(figsize=(14, 16), facecolor="white")
gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[0.12, 1.0], hspace=0.01)
ax_head = fig.add_subplot(gs[0]); ax_head.axis("off")
ax = fig.add_subplot(gs[1])

ax_head.text(0.0, 0.90,
             "Dallas County — Conventional Home-Purchase Denial Rate by Tract",
             fontsize=20, fontweight="bold", va="top", ha="left")
subtitle = (
    f"HMDA 2022–2023  ·  42,111 decisioned applications  ·  "
    f"County denial rate {county_rate:.1%}  ·  Median tract rate {county_median:.1%}\n"
    f"County Black/White disparity: {county_disp:.2f}×  "
    f"(Black {county_b_rate:.1%}, White {county_w_rate:.1%})   —   "
    f"National average Black/White disparity benchmark: 1.19×\n"
    f"Navy outlines = 14 highest-priority Susceptible South tracts "
    f"(Displacement Defense Atlas H4, bottom readiness quartile)"
)
ax_head.text(0.0, 0.58, subtitle, fontsize=12, va="top", ha="left",
             color="#333", linespacing=1.5)

# No-data tracts
no_data = gdf[gdf["denial_rate"].isna()]
no_data.plot(ax=ax, color="#e8e8e8", edgecolor="white", linewidth=0.2)

# Plot with explicit categorical bins
has_data = gdf[gdf["denial_rate"].notna()].copy()
for i, c in enumerate(colors):
    sub = has_data[has_data["bin"] == i]
    if len(sub):
        sub.plot(ax=ax, color=c, edgecolor="white", linewidth=0.15)

# Priority outlines
pri_geo = dallas[dallas["GEOID"].isin(top14["GEOID"])]
pri_geo.boundary.plot(ax=ax, color="#0a3d62", linewidth=2.5, zorder=5)

ax.set_axis_off()

# --- Legend: quantile swatches + priority ---
handles = []
for i, c in enumerate(colors):
    label = f"{bins[i]:.1%} – {bins[i+1]:.1%}"
    handles.append(Patch(facecolor=c, edgecolor="#888", linewidth=0.4, label=label))
handles.append(Patch(facecolor="white", edgecolor="white", label=""))  # spacer
handles.append(Line2D([0], [0], color="#0a3d62", lw=2.8, label="Priority-14 tract"))
handles.append(Patch(facecolor="#e8e8e8", edgecolor="#888", linewidth=0.4,
                     label="No HMDA applications"))

leg = ax.legend(
    handles=handles,
    loc="upper left",
    bbox_to_anchor=(0.01, 0.99),
    title="Denial rate (sextile bins)",
    title_fontsize=12,
    fontsize=11,
    frameon=True,
    framealpha=0.95,
    edgecolor="#999",
)
leg.get_title().set_fontweight("bold")

fig.text(
    0.02, 0.012,
    "Source: CFPB HMDA Loan Application Register (county FIPS 48113). Conventional home purchase, decisioned actions only "
    "(originated / approved-not-accepted / denied, incl. pre-approval denials 7–8). "
    "Priority tracts: Displacement Defense Atlas — ndhthecatalyst/displacement-defense-atlas, outputs/tables/h4_priority_54.csv (ranks 1–14).",
    fontsize=9, color="#666", ha="left", va="bottom",
)

fig_path = OUT / "figures" / "dallas_hmda_denial_rate_choropleth.png"
plt.savefig(fig_path, dpi=180, bbox_inches="tight", facecolor="white", pad_inches=0.3)
print(f"Wrote {fig_path}")
plt.close()

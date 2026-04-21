"""
atlas_map_b_tool_intensity.py
==============================
Displacement Defense Atlas v0 — Map (b): Tool Intensity Overlay Map
Dallas County, TX | Thesis: "Below the Line" | Nicholas Donovan Hawkins, TSU

ANALYTICAL PURPOSE:
    This map documents the spatial logic of policy-enabled displacement by
    plotting the co-presence and density of four displacement-enabling
    mechanisms — CIP capital investment, TIF districts, Opportunity Zones,
    and Public Improvement Districts — across Dallas County census tracts.
    The integer tool score (0–4) per tract makes visible the systematic
    concentration of tools in North Dallas and their near-absence in South
    Dallas. TIF district outlines and OZ hatching allow the viewer to
    distinguish district-level boundaries from the tract-level composite
    score. The stark North/South contrast (12.6× CIP vendor residue gap;
    TIF increment 26:1) is the map's primary visual argument.

REQUIRED DATA FILES:
    - gdf (GeoDataFrame): Dallas County census tracts, EPSG:4326
      Must contain columns:
        cip_present  — int, 0/1, tract has CIP vendor spend > $0
        tif_present  — int, 0/1, tract intersects a TIF district
        oz_present   — int, 0/1, tract is an Opportunity Zone
        pid_present  — int, 0/1, tract intersects a PID boundary
      Source: data/raw/layer1_investment/ (CIP, TIF, OZ, PID files)
    - tif_gdf (GeoDataFrame): TIF district polygons, any CRS
      Source: data/raw/layer1_investment/tif_*.gpkg
    - oz_gdf  (GeoDataFrame): Opportunity Zone tract polygons, any CRS
      Source: data/raw/layer1_investment/oz_*.gpkg

OUTPUTS:
    outputs/figures/atlas_v0_map_b_tool_intensity.png  (300 DPI)
"""

import os
import warnings
import numpy as np
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.patheffects as pe
import contextily as ctx
from shapely.geometry import LineString

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_PATH = "outputs/figures/atlas_v0_map_b_tool_intensity.png"
FIG_WIDTH   = 10
FIG_HEIGHT  = 10
DPI         = 300

# ColorBrewer BuGn 5-class — colorblind-safe sequential (blue-green)
BUGN_5 = ["#edf8fb", "#b2e2e2", "#66c2a4", "#2ca25f", "#006d2c"]

# Tool score labels
TOOL_LABELS = [
    "0 tools (no coverage)",
    "1 tool",
    "2 tools",
    "3 tools",
    "4 tools (full coverage)",
]

# I-30 corridor (WGS84)
I30_COORDS_WGS84 = [(-97.10, 32.75), (-96.55, 32.75)]

TITLE = "Displacement Defense Atlas v0 | Policy Tool Intensity Overlay | Dallas County, TX"
FOOTNOTE = (
    "Sources: City of Dallas CIP FY2019–2024; Dallas TIF District records; "
    "HUD Opportunity Zone designations 2018; Dallas PID records; Dallas County FIPS 48113  |  "
    "Hawkins (2027), Below the Line, TSU"
)


# ---------------------------------------------------------------------------
# Shared helpers (same as map_a — include in a shared utils module in production)
# ---------------------------------------------------------------------------

def add_north_arrow(ax, x=0.93, y=0.93, fontsize=11):
    ax.annotate(
        "N\n▲",
        xy=(x, y), xycoords="axes fraction",
        ha="center", va="center",
        fontsize=fontsize, fontweight="bold",
        fontfamily="DejaVu Sans",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                  edgecolor="#444444", linewidth=0.8, alpha=0.9),
    )


def add_scalebar(ax, length_m=8047, label="5 mi", x0_frac=0.05, y0_frac=0.06):
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    map_width_m  = xlim[1] - xlim[0]
    map_height_m = ylim[1] - ylim[0]
    x0 = xlim[0] + x0_frac * map_width_m
    y0 = ylim[0] + y0_frac * map_height_m
    ax.plot([x0, x0 + length_m], [y0, y0],
            color="black", linewidth=2, solid_capstyle="butt", zorder=7)
    ax.plot([x0, x0], [y0 - map_height_m * 0.005, y0 + map_height_m * 0.005],
            color="black", linewidth=1.5, zorder=7)
    ax.plot([x0 + length_m, x0 + length_m],
            [y0 - map_height_m * 0.005, y0 + map_height_m * 0.005],
            color="black", linewidth=1.5, zorder=7)
    ax.text(x0 + length_m / 2, y0 + map_height_m * 0.015,
            label, ha="center", va="bottom",
            fontsize=8, fontfamily="DejaVu Sans", zorder=7)


# ---------------------------------------------------------------------------
# Main map function
# ---------------------------------------------------------------------------

def make_map_b_tool_intensity(
    gdf: gpd.GeoDataFrame,
    tif_gdf: gpd.GeoDataFrame,
    oz_gdf: gpd.GeoDataFrame,
) -> None:
    """
    Render Displacement Defense Atlas v0 — Map (b): Tool Intensity Overlay.

    Parameters
    ----------
    gdf : GeoDataFrame
        Dallas County census tracts in EPSG:4326.
        Must contain: cip_present, tif_present, oz_present, pid_present
        (each a 0/1 integer flag).
    tif_gdf : GeoDataFrame
        TIF district polygons (any CRS; will be reprojected).
    oz_gdf : GeoDataFrame
        Opportunity Zone tract polygons (any CRS; will be reprojected).
    """
    os.makedirs("outputs/figures", exist_ok=True)

    # --- 1. Compute tool score -----------------------------------------------
    gdf = gdf.copy()
    gdf["tool_score"] = (
        gdf["cip_present"].clip(0, 1) +
        gdf["tif_present"].clip(0, 1) +
        gdf["oz_present"].clip(0, 1) +
        gdf["pid_present"].clip(0, 1)
    ).astype(int)

    # --- 2. Reproject to Web Mercator ----------------------------------------
    gdf_wm  = gdf.to_crs(epsg=3857)
    tif_wm  = tif_gdf.to_crs(epsg=3857)
    oz_wm   = oz_gdf.to_crs(epsg=3857)

    # --- 3. I-30 geometry -----------------------------------------------------
    i30_wm = gpd.GeoDataFrame(
        geometry=[LineString(I30_COORDS_WGS84)], crs="EPSG:4326"
    ).to_crs(epsg=3857)

    # --- 4. County boundary ---------------------------------------------------
    county_boundary = gdf_wm.dissolve()

    # --- 5. Create figure ----------------------------------------------------
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    ax.set_aspect("equal")

    # --- 6. Choropleth by tool score (0–4) -----------------------------------
    for score in range(5):
        mask = gdf_wm["tool_score"] == score
        if mask.sum() == 0:
            continue
        gdf_wm[mask].plot(
            ax=ax,
            facecolor=BUGN_5[score],
            edgecolor="#cccccc",
            linewidth=0.3,
            zorder=2,
        )

    # --- 7. County boundary --------------------------------------------------
    county_boundary.plot(
        ax=ax, facecolor="none", edgecolor="#444444", linewidth=1.2, zorder=3
    )

    # --- 8. TIF district outlines --------------------------------------------
    if len(tif_wm) > 0:
        tif_wm.plot(
            ax=ax,
            facecolor="none",
            edgecolor="#1a237e",
            linewidth=1.2,
            linestyle="-",
            zorder=4,
        )

    # --- 9. OZ hatching -------------------------------------------------------
    if len(oz_wm) > 0:
        oz_wm.plot(
            ax=ax,
            facecolor="none",
            edgecolor="#e65100",
            linewidth=0.7,
            hatch="//",
            alpha=0.85,
            zorder=5,
        )

    # --- 10. I-30 corridor line -----------------------------------------------
    i30_wm.plot(
        ax=ax, color="black", linestyle="--", linewidth=1.5, zorder=6
    )
    # I-30 label
    i30_geom = i30_wm.geometry.iloc[0]
    mid_x = (i30_geom.bounds[0] + i30_geom.bounds[2]) / 2
    mid_y = i30_geom.bounds[1]
    ax.annotate(
        "I-30 Corridor",
        xy=(mid_x, mid_y),
        xytext=(mid_x, mid_y - (gdf_wm.total_bounds[3] - gdf_wm.total_bounds[1]) * 0.04),
        fontsize=7.5, fontstyle="italic", fontfamily="DejaVu Sans",
        ha="center", va="top", color="#222222", zorder=7,
    )

    # --- 11. Basemap ----------------------------------------------------------
    try:
        ctx.add_basemap(
            ax, crs=gdf_wm.crs,
            source=ctx.providers.CartoDB.Positron,
            zoom="auto", alpha=0.4, zorder=1,
        )
    except Exception as e:
        print(f"[WARNING] Basemap unavailable: {e}")

    # --- 12. Map extent -------------------------------------------------------
    bounds = gdf_wm.total_bounds
    pad_x  = (bounds[2] - bounds[0]) * 0.05
    pad_y  = (bounds[3] - bounds[1]) * 0.05
    ax.set_xlim(bounds[0] - pad_x, bounds[2] + pad_x)
    ax.set_ylim(bounds[1] - pad_y, bounds[3] + pad_y)
    ax.set_axis_off()

    # --- 13. Title ------------------------------------------------------------
    ax.set_title(TITLE, fontsize=14, fontweight="bold",
                 fontfamily="DejaVu Sans", pad=10)

    # --- 14. Legend -----------------------------------------------------------
    # BuGn tool score patches
    score_patches = [
        mpatches.Patch(facecolor=BUGN_5[i], edgecolor="#888888",
                       linewidth=0.5, label=TOOL_LABELS[i])
        for i in range(5)
    ]
    # TIF district outline swatch
    tif_patch = mpatches.Patch(
        facecolor="none", edgecolor="#1a237e", linewidth=1.5,
        label="TIF District Boundary"
    )
    # OZ hatch swatch
    oz_patch = mpatches.Patch(
        facecolor="none", edgecolor="#e65100", linewidth=0.8,
        hatch="//", label="Opportunity Zone (OZ)"
    )
    # I-30 line handle
    i30_handle = mlines.Line2D(
        [], [], color="black", linestyle="--", linewidth=1.5,
        label="I-30 Corridor"
    )

    all_handles = score_patches + [tif_patch, oz_patch, i30_handle]
    legend = ax.legend(
        handles=all_handles,
        title="Tool Intensity Score\n(CIP + TIF + OZ + PID)",
        title_fontsize=9,
        fontsize=9,
        loc="lower right",
        frameon=True,
        framealpha=0.92,
        edgecolor="#aaaaaa",
        fancybox=False,
    )
    legend.get_title().set_fontfamily("DejaVu Sans")
    legend.get_title().set_fontweight("bold")

    # --- 15. Map furniture ---------------------------------------------------
    add_north_arrow(ax, x=0.93, y=0.93)
    add_scalebar(ax, length_m=8047, label="5 mi")

    # --- 16. Source footnote -------------------------------------------------
    fig.text(
        0.01, 0.005, FOOTNOTE,
        fontsize=7, fontfamily="DejaVu Sans",
        color="#555555", ha="left", va="bottom",
    )

    # --- 17. Save ------------------------------------------------------------
    fig.savefig(OUTPUT_PATH, dpi=DPI, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"[Map B] Saved → {OUTPUT_PATH}")


# ---------------------------------------------------------------------------
# Synthetic data generator
# ---------------------------------------------------------------------------

def make_synthetic_tool_data(gdf: gpd.GeoDataFrame):
    """
    Generate synthetic tool presence flags and TIF/OZ GeoDataFrames for testing.
    North Dallas (lat > 32.75) is tool-dense; South Dallas is tool-sparse.

    In production replace with:
        gdf = gdf.merge(cip_df, on="GEOID")   # from data/raw/layer1_investment/
        # Spatial join for TIF, OZ, PID presence
        gdf["tif_present"] = gdf.geometry.intersects(tif_gdf.unary_union).astype(int)
    """
    import numpy as np
    from shapely.geometry import box

    rng = np.random.default_rng(42)
    gdf = gdf.copy()

    centroids_lat = gdf.geometry.centroid.y
    north_mask    = centroids_lat > 32.75

    n = len(gdf)
    # North: higher probability of each tool; South: low probability
    gdf["cip_present"] = np.where(north_mask,
                                   rng.binomial(1, 0.75, n),
                                   rng.binomial(1, 0.15, n))
    gdf["tif_present"] = np.where(north_mask,
                                   rng.binomial(1, 0.60, n),
                                   rng.binomial(1, 0.08, n))
    gdf["oz_present"]  = np.where(north_mask,
                                   rng.binomial(1, 0.30, n),
                                   rng.binomial(1, 0.35, n))
    gdf["pid_present"] = np.where(north_mask,
                                   rng.binomial(1, 0.50, n),
                                   rng.binomial(1, 0.05, n))

    # Synthetic TIF districts: 3 rectangles in North Dallas
    tif_geoms = [
        box(-96.85, 32.80, -96.75, 32.90),
        box(-96.80, 32.78, -96.70, 32.88),
        box(-96.90, 32.82, -96.82, 32.92),
    ]
    tif_gdf = gpd.GeoDataFrame(
        {"name": ["Downtown Connection", "Uptown", "Cedars"]},
        geometry=tif_geoms, crs="EPSG:4326"
    )

    # Synthetic OZ tracts: subset of South Dallas tracts
    oz_mask = (~north_mask) & (rng.binomial(1, 0.4, n).astype(bool))
    oz_gdf  = gdf[oz_mask][["geometry"]].copy().reset_index(drop=True)

    return gdf, tif_gdf, oz_gdf


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- Load real data ---
    # gdf = gpd.read_file("data/raw/tracts_dallas_48113.gpkg")
    # gdf = gdf.merge(cip_df[["GEOID","cip_present"]], on="GEOID")
    # gdf["tif_present"] = gdf.geometry.intersects(tif_gdf.unary_union).astype(int)
    # gdf["oz_present"]  = gdf.geometry.intersects(oz_gdf.unary_union).astype(int)
    # gdf["pid_present"] = gdf.geometry.intersects(pid_gdf.unary_union).astype(int)
    # tif_gdf = gpd.read_file("data/raw/layer1_investment/tif_districts.gpkg")
    # oz_gdf  = gpd.read_file("data/raw/layer1_investment/oz_tracts.gpkg")

    # --- For testing with synthetic data ---
    from atlas_map_a_vulnerability import make_synthetic_gdf_dallas
    gdf_base = make_synthetic_gdf_dallas()
    gdf, tif_gdf, oz_gdf = make_synthetic_tool_data(gdf_base)

    make_map_b_tool_intensity(gdf, tif_gdf, oz_gdf)

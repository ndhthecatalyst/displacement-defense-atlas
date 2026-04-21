"""
atlas_map_a_vulnerability.py
============================
Displacement Defense Atlas v0 — Map (a): Baseline Vulnerability Map
Dallas County, TX | Thesis: "Below the Line" | Nicholas Donovan Hawkins, TSU

ANALYTICAL PURPOSE:
    This map operationalizes the thesis's foundational claim that displacement
    risk is structurally pre-patterned along racial and economic lines before
    any policy intervention. The composite vulnerability index (renter burden,
    racial composition, income, HMDA denial rates, Bates stage) is mapped by
    census tract with Jenks Natural Breaks classification to reveal clusters
    of concentrated vulnerability. The I-30 corridor divides the frame,
    making the North/South gradient visually explicit. This map anchors the
    three-map analytical sequence: vulnerability → tool deployment → gap.

REQUIRED DATA FILES:
    - gdf (GeoDataFrame): Dallas County census tracts, EPSG:4326
      Must contain columns:
        pct_renter     — float, 0–100, % renter-occupied housing units
        pct_nonwhite   — float, 0–100, % non-white population
        med_hhinc      — float, median household income in dollars
        hmda_denial_rt — float, 0–1, HMDA denial rate
        bates_stage    — int, 0=Stable, 1=Early, 2=Dynamic, 3=Late
      Source: ACS 2023 (B25003, B03002, B19013), FFIEC HMDA 2022–23,
              LTDB/UDP Bates Typology v2.1
    - Dallas County FIPS prefix: 48113

OUTPUTS:
    outputs/figures/atlas_v0_map_a_vulnerability.png  (300 DPI)
"""

import os
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.patches import FancyArrow
import contextily as ctx
from shapely.geometry import LineString
import mapclassify

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_PATH = "outputs/figures/atlas_v0_map_a_vulnerability.png"
FIG_WIDTH   = 10        # inches
FIG_HEIGHT  = 10        # inches
DPI         = 300

# ColorBrewer OrRd 5-class — colorblind-safe sequential (orange → red)
ORRD_5 = ["#fef0d9", "#fdcc8a", "#fc8d59", "#e34a33", "#b30000"]

# I-30 corridor approximate geometry (WGS84 decimal degrees)
I30_COORDS_WGS84 = [(-97.10, 32.75), (-96.55, 32.75)]

TITLE = "Displacement Defense Atlas v0 | Baseline Vulnerability Index | Dallas County, TX"
FOOTNOTE = (
    "Sources: ACS 2023 (B25003, B03002, B19013); FFIEC HMDA 2022–23; "
    "LTDB/UDP Bates Typology v2.1; Dallas County FIPS 48113  |  "
    "Hawkins (2027), Below the Line, TSU"
)


# ---------------------------------------------------------------------------
# Helper: min-max normalization
# ---------------------------------------------------------------------------

def minmax_norm(series: pd.Series, invert: bool = False) -> pd.Series:
    """Normalize a series to [0, 1]; invert=True flips the scale."""
    mn, mx = series.min(), series.max()
    normed = (series - mn) / (mx - mn) if mx > mn else pd.Series(0.0, index=series.index)
    return 1.0 - normed if invert else normed


# ---------------------------------------------------------------------------
# Helper: build composite vulnerability index
# ---------------------------------------------------------------------------

def build_vulnerability_index(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Construct the five-variable composite displacement vulnerability index.

    Each variable is min-max normalized to [0, 1] and averaged.
    Income is inverted so that lower income = higher vulnerability.
    Bates stage is normalized on its 0–3 integer scale.
    """
    gdf = gdf.copy()
    gdf["v_renter"]     = minmax_norm(gdf["pct_renter"])
    gdf["v_nonwhite"]   = minmax_norm(gdf["pct_nonwhite"])
    gdf["v_income"]     = minmax_norm(gdf["med_hhinc"], invert=True)
    gdf["v_hmda"]       = minmax_norm(gdf["hmda_denial_rt"])
    gdf["v_bates"]      = minmax_norm(gdf["bates_stage"].astype(float))

    gdf["vulnerability_index"] = gdf[
        ["v_renter", "v_nonwhite", "v_income", "v_hmda", "v_bates"]
    ].mean(axis=1)

    return gdf


# ---------------------------------------------------------------------------
# Helper: add north arrow
# ---------------------------------------------------------------------------

def add_north_arrow(ax, x=0.93, y=0.93, fontsize=11):
    """Add a simple 'N ▲' north arrow annotation to the axes."""
    ax.annotate(
        "N\n▲",
        xy=(x, y), xycoords="axes fraction",
        ha="center", va="center",
        fontsize=fontsize, fontweight="bold",
        fontfamily="DejaVu Sans",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                  edgecolor="#444444", linewidth=0.8, alpha=0.9),
    )


# ---------------------------------------------------------------------------
# Helper: add scale bar (approximate, Web Mercator)
# ---------------------------------------------------------------------------

def add_scalebar(ax, length_m=8047, label="5 mi", x0_frac=0.05, y0_frac=0.06):
    """
    Add a simple scale bar.
    length_m: bar length in meters (8047 m ≈ 5 miles).
    Uses axes data coordinates via ax.transData.
    """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    map_width_m  = xlim[1] - xlim[0]
    map_height_m = ylim[1] - ylim[0]

    x0 = xlim[0] + x0_frac * map_width_m
    y0 = ylim[0] + y0_frac * map_height_m

    ax.plot([x0, x0 + length_m], [y0, y0],
            color="black", linewidth=2, solid_capstyle="butt", zorder=6)
    ax.plot([x0, x0], [y0 - map_height_m * 0.005, y0 + map_height_m * 0.005],
            color="black", linewidth=1.5, zorder=6)
    ax.plot([x0 + length_m, x0 + length_m],
            [y0 - map_height_m * 0.005, y0 + map_height_m * 0.005],
            color="black", linewidth=1.5, zorder=6)
    ax.text(x0 + length_m / 2, y0 + map_height_m * 0.015,
            label, ha="center", va="bottom",
            fontsize=8, fontfamily="DejaVu Sans", zorder=6)


# ---------------------------------------------------------------------------
# Main map function
# ---------------------------------------------------------------------------

def make_map_a_vulnerability(gdf: gpd.GeoDataFrame) -> None:
    """
    Render Displacement Defense Atlas v0 — Map (a): Baseline Vulnerability.

    Parameters
    ----------
    gdf : GeoDataFrame
        Dallas County census tracts in EPSG:4326.
        Must contain: pct_renter, pct_nonwhite, med_hhinc,
                      hmda_denial_rt, bates_stage.
    """
    os.makedirs("outputs/figures", exist_ok=True)

    # --- 1. Build vulnerability index ----------------------------------------
    gdf = build_vulnerability_index(gdf)

    # --- 2. Reproject to Web Mercator for basemap tiles ----------------------
    gdf_wm = gdf.to_crs(epsg=3857)

    # --- 3. Jenks Natural Breaks classification (5 classes) ------------------
    classifier = mapclassify.NaturalBreaks(gdf_wm["vulnerability_index"], k=5)
    gdf_wm["jenks_class"] = classifier.yb  # 0-indexed bin assignments

    bins   = classifier.bins          # upper bounds of each class
    breaks = np.concatenate([[gdf_wm["vulnerability_index"].min()], bins])
    labels = [
        f"{breaks[i]:.2f} – {breaks[i+1]:.2f}"
        for i in range(len(breaks) - 1)
    ]

    # --- 4. Build I-30 geometry in Web Mercator ------------------------------
    i30_wgs84 = gpd.GeoDataFrame(
        geometry=[LineString(I30_COORDS_WGS84)],
        crs="EPSG:4326"
    ).to_crs(epsg=3857)

    # --- 5. Dallas County boundary outline -----------------------------------
    county_boundary = gdf_wm.dissolve()

    # --- 6. Create figure ----------------------------------------------------
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    ax.set_aspect("equal")

    # --- 7. Draw choropleth --------------------------------------------------
    for class_idx, (color, label) in enumerate(zip(ORRD_5, labels)):
        mask = gdf_wm["jenks_class"] == class_idx
        if mask.sum() == 0:
            continue
        gdf_wm[mask].plot(
            ax=ax,
            facecolor=color,
            edgecolor="#cccccc",
            linewidth=0.3,
            zorder=2,
        )

    # --- 8. County boundary outline ------------------------------------------
    county_boundary.plot(
        ax=ax,
        facecolor="none",
        edgecolor="#444444",
        linewidth=1.2,
        zorder=3,
    )

    # --- 9. I-30 corridor line ------------------------------------------------
    i30_wgs84.plot(
        ax=ax,
        color="black",
        linestyle="--",
        linewidth=1.5,
        zorder=4,
        label="I-30 Corridor",
    )
    # Label the I-30 line
    i30_geom = i30_wgs84.geometry.iloc[0]
    mid_x = (i30_geom.bounds[0] + i30_geom.bounds[2]) / 2
    mid_y = i30_geom.bounds[1]
    xlim_temp = ax.get_xlim()
    ylim_temp = ax.get_ylim()
    ax.annotate(
        "I-30 Corridor",
        xy=(mid_x, mid_y),
        xytext=(mid_x, mid_y - (gdf_wm.total_bounds[3] - gdf_wm.total_bounds[1]) * 0.04),
        fontsize=7.5, fontstyle="italic", fontfamily="DejaVu Sans",
        ha="center", va="top",
        color="#222222",
        arrowprops=None,
        zorder=5,
    )

    # --- 10. Add CartoDB Positron basemap ------------------------------------
    try:
        ctx.add_basemap(
            ax,
            crs=gdf_wm.crs,
            source=ctx.providers.CartoDB.Positron,
            zoom="auto",
            alpha=0.4,
            zorder=1,
        )
    except Exception as e:
        print(f"[WARNING] Basemap could not be loaded: {e}. Proceeding without basemap.")

    # --- 11. Map extent: clip to Dallas County bounding box with 5% padding -
    bounds = gdf_wm.total_bounds  # [minx, miny, maxx, maxy]
    pad_x  = (bounds[2] - bounds[0]) * 0.05
    pad_y  = (bounds[3] - bounds[1]) * 0.05
    ax.set_xlim(bounds[0] - pad_x, bounds[2] + pad_x)
    ax.set_ylim(bounds[1] - pad_y, bounds[3] + pad_y)

    ax.set_axis_off()

    # --- 12. Title -----------------------------------------------------------
    ax.set_title(
        TITLE,
        fontsize=14, fontweight="bold", fontfamily="DejaVu Sans",
        pad=10,
    )

    # --- 13. Legend (inset axes, lower right) --------------------------------
    legend_patches = [
        mpatches.Patch(facecolor=ORRD_5[i], edgecolor="#888888",
                       linewidth=0.5, label=labels[i])
        for i in range(5)
    ]
    legend = ax.legend(
        handles=legend_patches,
        title="Vulnerability Index\n(Jenks, 5 class)",
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

    # Add I-30 line to legend
    i30_handle = mlines.Line2D(
        [], [], color="black", linestyle="--", linewidth=1.5, label="I-30 Corridor"
    )
    ax.add_artist(legend)  # keep existing legend
    ax.legend(
        handles=[i30_handle],
        fontsize=9,
        loc="lower center",
        frameon=True,
        framealpha=0.92,
        edgecolor="#aaaaaa",
        fancybox=False,
        bbox_to_anchor=(0.5, 0.0),
    )
    ax.add_artist(ax.get_legend())
    # Re-add vulnerability legend so both show
    ax.legend(
        handles=legend_patches + [i30_handle],
        title="Vulnerability Index\n(Jenks, 5 class)",
        title_fontsize=9,
        fontsize=9,
        loc="lower right",
        frameon=True,
        framealpha=0.92,
        edgecolor="#aaaaaa",
        fancybox=False,
    )

    # --- 14. North arrow ------------------------------------------------------
    add_north_arrow(ax, x=0.93, y=0.93)

    # --- 15. Scale bar --------------------------------------------------------
    add_scalebar(ax, length_m=8047, label="5 mi")

    # --- 16. Source footnote -------------------------------------------------
    fig.text(
        0.01, 0.005,
        FOOTNOTE,
        fontsize=7, fontfamily="DejaVu Sans",
        color="#555555", ha="left", va="bottom",
        wrap=True,
    )

    # --- 17. Save ------------------------------------------------------------
    fig.savefig(OUTPUT_PATH, dpi=DPI, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"[Map A] Saved → {OUTPUT_PATH}")


# ---------------------------------------------------------------------------
# Synthetic data generator (for testing without real data)
# ---------------------------------------------------------------------------

def make_synthetic_gdf_dallas() -> gpd.GeoDataFrame:
    """
    Generate a synthetic Dallas County tract GeoDataFrame for testing.
    Replace this with real data loaded from your pipeline.

    In production, load with:
        import geopandas as gpd
        gdf = gpd.read_file("data/raw/tracts_dallas_48113.gpkg")
        # Then merge ACS, HMDA, and Bates stage columns onto gdf
    """
    import numpy as np
    from shapely.geometry import box

    rng = np.random.default_rng(42)
    n   = 200  # approximate number of Dallas County tracts

    # Create a rough grid of synthetic tract polygons within Dallas County bbox
    # Approximate bbox: lon -97.0 to -96.55, lat 32.55 to 33.05
    lon_min, lon_max = -97.0, -96.55
    lat_min, lat_max = 32.55, 33.05
    cell_w = (lon_max - lon_min) / 16
    cell_h = (lat_max - lat_min) / 13

    geoms = []
    for i in range(16):
        for j in range(13):
            if len(geoms) >= n:
                break
            x0 = lon_min + i * cell_w
            y0 = lat_min + j * cell_h
            geoms.append(box(x0, y0, x0 + cell_w, y0 + cell_h))

    geoms = geoms[:n]

    # South Dallas (lat < 32.75) tends toward higher vulnerability
    centroids_lat = np.array([g.centroid.y for g in geoms])
    south_mask    = centroids_lat < 32.75

    pct_renter     = np.where(south_mask,
                               rng.uniform(50, 80, n),
                               rng.uniform(15, 45, n))
    pct_nonwhite   = np.where(south_mask,
                               rng.uniform(55, 90, n),
                               rng.uniform(20, 55, n))
    med_hhinc      = np.where(south_mask,
                               rng.uniform(25000, 55000, n),
                               rng.uniform(60000, 120000, n))
    hmda_denial_rt = np.where(south_mask,
                               rng.uniform(0.18, 0.35, n),
                               rng.uniform(0.08, 0.20, n))
    bates_stage    = np.where(south_mask,
                               rng.integers(1, 4, n),
                               rng.integers(0, 3, n))

    gdf = gpd.GeoDataFrame(
        {
            "GEOID":         [f"48113{str(i).zfill(6)}" for i in range(n)],
            "pct_renter":    pct_renter,
            "pct_nonwhite":  pct_nonwhite,
            "med_hhinc":     med_hhinc,
            "hmda_denial_rt": hmda_denial_rt,
            "bates_stage":   bates_stage,
            "geometry":      geoms,
        },
        crs="EPSG:4326",
    )
    return gdf


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- Load real data ---
    # gdf = gpd.read_file("data/raw/tracts_dallas_48113.gpkg")
    # gdf = gdf.merge(acs_df, on="GEOID")
    # gdf = gdf.merge(hmda_df, on="GEOID")
    # gdf = gdf.merge(bates_df, on="GEOID")

    # --- For testing with synthetic data ---
    gdf = make_synthetic_gdf_dallas()

    make_map_a_vulnerability(gdf)

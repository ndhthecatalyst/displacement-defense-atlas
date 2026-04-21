"""
atlas_map_c_gap.py
==================
Displacement Defense Atlas v0 — Map (c): Need-vs-Investment Gap Map
Dallas County, TX | Thesis: "Below the Line" | Nicholas Donovan Hawkins, TSU

ANALYTICAL PURPOSE:
    This map renders the central empirical finding of the thesis: the
    systematic residual between displacement vulnerability (need) and
    policy investment received. The gap score operationalizes structural
    disinvestment as a spatially legible quantity. Positive values (red)
    flag tracts where vulnerability far exceeds investment — overwhelmingly
    in South Dallas. Negative values (blue) flag tracts where investment
    exceeds vulnerability — overwhelmingly in North Dallas. The diverging
    palette makes the zero-balance line visible, and the I-30 corridor
    functions as a near-perfect dividing line between the two populations.
    Key figures visible in the map: $485M (North) vs. $38M (South) CIP
    vendor residue (12.6× gap); TIF increment ratio 26:1 (Downtown
    Connection $8.83B vs. Grand Park South $333M).

REQUIRED DATA FILES:
    - gdf (GeoDataFrame): Dallas County census tracts, EPSG:4326
      Must contain columns:
        vulnerability_index — float, 0–1, from Map (a) pipeline
        cip_vendor_usd      — float, total CIP vendor spend in dollars
        tif_increment_usd   — float, total TIF increment captured in dollars
        pop_total           — int, total tract population (ACS 2023 B01003)
      Source: data/raw/layer1_investment/; data/raw/layer2_mechanism/
    - tif_gdf (GeoDataFrame, optional): TIF district polygons for annotation
      Source: data/raw/layer1_investment/tif_districts.gpkg

OUTPUTS:
    outputs/figures/atlas_v0_map_c_gap.png  (300 DPI)
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
import contextily as ctx
from shapely.geometry import LineString

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_PATH = "outputs/figures/atlas_v0_map_c_gap.png"
FIG_WIDTH   = 10
FIG_HEIGHT  = 10
DPI         = 300

# ColorBrewer RdBu 5-class — colorblind-safe diverging (red–white–blue)
# Order: strong red, light red, neutral, light blue, strong blue
RDBU_5 = ["#ca0020", "#f4a582", "#f7f7f7", "#92c5de", "#0571b0"]

# Symmetric break points for gap score classification
# gap < -0.4        → class 4 → strong blue (over-invested)
# -0.4 ≤ gap < -0.1 → class 3 → light blue
# -0.1 ≤ gap < +0.1 → class 2 → neutral white
# +0.1 ≤ gap < +0.4 → class 1 → light red
# gap ≥ +0.4        → class 0 → strong red (under-invested)
GAP_BREAKS     = [-np.inf, -0.4, -0.1, 0.1, 0.4, np.inf]
# Map: bin index → color index (reversed so red = high gap)
# np.digitize returns 1–5; subtract 1 for 0-index
GAP_BREAK_LABELS = [
    "< −0.4  (Strongly over-invested)",
    "−0.4 – −0.1  (Mildly over-invested)",
    "−0.1 –  +0.1  (Roughly balanced)",
    "+0.1 – +0.4  (Mildly under-invested)",
    "> +0.4  (Strongly under-invested)",
]
# Color assignment: bins 0–4 map to RDBU_5 reversed
# bin 0 = most negative gap = blue; bin 4 = most positive gap = red
GAP_COLOR_MAP = {
    0: RDBU_5[4],   # strong blue — strongly over-invested
    1: RDBU_5[3],   # light blue
    2: RDBU_5[2],   # neutral
    3: RDBU_5[1],   # light red
    4: RDBU_5[0],   # strong red — strongly under-invested
}

# I-30 corridor (WGS84)
I30_COORDS_WGS84 = [(-97.10, 32.75), (-96.55, 32.75)]

TITLE = "Displacement Defense Atlas v0 | Need–Investment Gap Score | Dallas County, TX"
FOOTNOTE = (
    "Sources: City of Dallas CIP FY2019–2024 (vendor spend by tract); Dallas TIF District "
    "increment records; ACS 2023 (B01003, B25003, B03002, B19013); FFIEC HMDA 2022–23  |  "
    "Hawkins (2027), Below the Line, TSU"
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def minmax_norm(series: pd.Series, invert: bool = False) -> pd.Series:
    mn, mx = series.min(), series.max()
    normed = (series - mn) / (mx - mn) if mx > mn else pd.Series(0.0, index=series.index)
    return 1.0 - normed if invert else normed


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
# Gap score computation
# ---------------------------------------------------------------------------

def compute_gap_score(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Compute the need-vs-investment gap score per tract.

    gap_score = vulnerability_index - normalized_investment_received

    Tracts with pop_total == 0 receive NaN and are masked from the map.
    """
    gdf = gdf.copy()

    # Exclude unpopulated tracts
    pop_mask = gdf["pop_total"] > 0
    gdf.loc[~pop_mask, "gap_score"] = np.nan

    # Per-capita investment
    gdf.loc[pop_mask, "cip_per_cap"] = (
        gdf.loc[pop_mask, "cip_vendor_usd"] /
        gdf.loc[pop_mask, "pop_total"]
    )
    gdf.loc[pop_mask, "tif_per_cap"] = (
        gdf.loc[pop_mask, "tif_increment_usd"] /
        gdf.loc[pop_mask, "pop_total"]
    )

    # Normalize investment components
    gdf.loc[pop_mask, "cip_norm"] = minmax_norm(gdf.loc[pop_mask, "cip_per_cap"])
    gdf.loc[pop_mask, "tif_norm"] = minmax_norm(gdf.loc[pop_mask, "tif_per_cap"])

    # Investment received = mean of normalized components
    gdf.loc[pop_mask, "investment_received"] = (
        gdf.loc[pop_mask, ["cip_norm", "tif_norm"]].mean(axis=1)
    )

    # Gap score
    gdf.loc[pop_mask, "gap_score"] = (
        gdf.loc[pop_mask, "vulnerability_index"] -
        gdf.loc[pop_mask, "investment_received"]
    )

    return gdf


# ---------------------------------------------------------------------------
# Classify gap score into 5 symmetric bins
# ---------------------------------------------------------------------------

def classify_gap(gap_series: pd.Series) -> pd.Series:
    """
    Assign each gap score to one of 5 symmetric bins using GAP_BREAKS.
    Returns integer class labels 0–4 (NaN for masked tracts).
    bin 0 = gap < -0.4  (strongly over-invested, blue)
    bin 4 = gap >= +0.4 (strongly under-invested, red)
    """
    bins = [-np.inf, -0.4, -0.1, 0.1, 0.4, np.inf]
    # np.digitize returns 1-based index; subtract 1 for 0-based
    classes = pd.cut(
        gap_series,
        bins=bins,
        labels=[0, 1, 2, 3, 4],
        include_lowest=True,
    )
    return classes.astype("Int64")  # nullable integer preserves NaN


# ---------------------------------------------------------------------------
# Main map function
# ---------------------------------------------------------------------------

def make_map_c_gap(
    gdf: gpd.GeoDataFrame,
    tif_gdf: gpd.GeoDataFrame = None,
    annotate_tif: bool = True,
) -> None:
    """
    Render Displacement Defense Atlas v0 — Map (c): Need-vs-Investment Gap.

    Parameters
    ----------
    gdf : GeoDataFrame
        Dallas County census tracts in EPSG:4326.
        Must contain: vulnerability_index, cip_vendor_usd,
                      tif_increment_usd, pop_total.
    tif_gdf : GeoDataFrame, optional
        TIF district polygons for optional label annotation.
        If provided, annotates Downtown Connection and Grand Park South.
    annotate_tif : bool
        Whether to add TIF district name labels. Default True.
    """
    os.makedirs("outputs/figures", exist_ok=True)

    # --- 1. Compute gap score ------------------------------------------------
    gdf = compute_gap_score(gdf)

    # --- 2. Classify gap score -----------------------------------------------
    gdf["gap_class"] = classify_gap(gdf["gap_score"])

    # --- 3. Reproject to Web Mercator ----------------------------------------
    gdf_wm = gdf.to_crs(epsg=3857)
    if tif_gdf is not None:
        tif_wm = tif_gdf.to_crs(epsg=3857)
    else:
        tif_wm = None

    # --- 4. I-30 geometry -----------------------------------------------------
    i30_wm = gpd.GeoDataFrame(
        geometry=[LineString(I30_COORDS_WGS84)], crs="EPSG:4326"
    ).to_crs(epsg=3857)

    # --- 5. County boundary ---------------------------------------------------
    county_boundary = gdf_wm.dissolve()

    # --- 6. Create figure ----------------------------------------------------
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    ax.set_aspect("equal")

    # --- 7. Choropleth (gap class 0–4) ----------------------------------------
    for class_val in range(5):
        mask = gdf_wm["gap_class"] == class_val
        if mask.sum() == 0:
            continue
        gdf_wm[mask].plot(
            ax=ax,
            facecolor=GAP_COLOR_MAP[class_val],
            edgecolor="#cccccc",
            linewidth=0.3,
            zorder=2,
        )

    # Masked tracts (NaN gap score) — draw in light grey
    nan_mask = gdf_wm["gap_score"].isna()
    if nan_mask.sum() > 0:
        gdf_wm[nan_mask].plot(
            ax=ax,
            facecolor="#e0e0e0",
            edgecolor="#cccccc",
            linewidth=0.3,
            zorder=2,
        )

    # --- 8. County boundary --------------------------------------------------
    county_boundary.plot(
        ax=ax, facecolor="none", edgecolor="#444444", linewidth=1.2, zorder=3
    )

    # --- 9. I-30 corridor line -----------------------------------------------
    i30_wm.plot(
        ax=ax, color="black", linestyle="--", linewidth=1.5, zorder=5,
        label="I-30 Corridor"
    )
    i30_geom = i30_wm.geometry.iloc[0]
    mid_x = (i30_geom.bounds[0] + i30_geom.bounds[2]) / 2
    mid_y = i30_geom.bounds[1]
    ax.annotate(
        "I-30 Corridor",
        xy=(mid_x, mid_y),
        xytext=(mid_x, mid_y - (gdf_wm.total_bounds[3] - gdf_wm.total_bounds[1]) * 0.04),
        fontsize=7.5, fontstyle="italic", fontfamily="DejaVu Sans",
        ha="center", va="top", color="#222222", zorder=6,
    )

    # --- 10. Optional TIF district annotations --------------------------------
    if annotate_tif and tif_wm is not None and len(tif_wm) > 0:
        # Annotate each named TIF district if "name" column exists
        name_col = None
        for c in ["name", "NAME", "tif_name", "TIF_NAME", "district_name"]:
            if c in tif_wm.columns:
                name_col = c
                break

        downtown_keywords = ["downtown", "connection"]
        grandpark_keywords = ["grand park", "grandpark"]

        for _, row in tif_wm.iterrows():
            if name_col is None:
                break
            nm = str(row[name_col]).lower()
            centroid = row.geometry.centroid
            if any(k in nm for k in downtown_keywords):
                ax.annotate(
                    "Downtown Connection TIF\n($8.83B increment)",
                    xy=(centroid.x, centroid.y),
                    xytext=(centroid.x, centroid.y + 1200),
                    fontsize=7, color="#0571b0",
                    fontfamily="DejaVu Sans", ha="center",
                    arrowprops=dict(arrowstyle="->", color="#0571b0",
                                   lw=0.8, connectionstyle="arc3,rad=0.2"),
                    zorder=8,
                )
            elif any(k in nm for k in grandpark_keywords):
                ax.annotate(
                    "Grand Park South TIF\n($333M increment)",
                    xy=(centroid.x, centroid.y),
                    xytext=(centroid.x - 3000, centroid.y - 2000),
                    fontsize=7, color="#ca0020",
                    fontfamily="DejaVu Sans", ha="center",
                    arrowprops=dict(arrowstyle="->", color="#ca0020",
                                   lw=0.8, connectionstyle="arc3,rad=-0.2"),
                    zorder=8,
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

    # --- 14. Legend (diverging) -----------------------------------------------
    # 5 patches: ordered from most over-invested (blue) to most under-invested (red)
    legend_items = [
        (GAP_COLOR_MAP[4], GAP_BREAK_LABELS[4]),  # strong red — top of list
        (GAP_COLOR_MAP[3], GAP_BREAK_LABELS[3]),
        (GAP_COLOR_MAP[2], GAP_BREAK_LABELS[2]),  # neutral
        (GAP_COLOR_MAP[1], GAP_BREAK_LABELS[1]),
        (GAP_COLOR_MAP[0], GAP_BREAK_LABELS[0]),  # strong blue — bottom of list
    ]
    gap_patches = [
        mpatches.Patch(facecolor=color, edgecolor="#888888",
                       linewidth=0.5, label=label)
        for color, label in legend_items
    ]
    # Masked patch
    masked_patch = mpatches.Patch(
        facecolor="#e0e0e0", edgecolor="#888888", linewidth=0.5,
        label="No data (unpopulated)"
    )
    i30_handle = mlines.Line2D(
        [], [], color="black", linestyle="--", linewidth=1.5,
        label="I-30 Corridor"
    )

    all_handles = gap_patches + [masked_patch, i30_handle]
    legend = ax.legend(
        handles=all_handles,
        title="Gap Score\n(Vulnerability − Investment)\n─────────────────\n"
              "Red = Under-invested  |  Blue = Over-invested",
        title_fontsize=8,
        fontsize=8.5,
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
    print(f"[Map C] Saved → {OUTPUT_PATH}")


# ---------------------------------------------------------------------------
# Synthetic data generator
# ---------------------------------------------------------------------------

def make_synthetic_gap_data(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Generate synthetic CIP/TIF investment data and pre-computed vulnerability
    index for testing Map (c). North Dallas receives outsized investment;
    South Dallas receives minimal investment with high vulnerability.

    In production replace with:
        gdf["vulnerability_index"]  = <from Map (a) pipeline>
        gdf["cip_vendor_usd"]       = <from data/raw/layer1_investment/cip_*.csv>
        gdf["tif_increment_usd"]    = <from data/raw/layer1_investment/tif_*.csv>
        gdf["pop_total"]            = <from ACS 2023 B01003>
    """
    import numpy as np

    rng = np.random.default_rng(42)
    gdf = gdf.copy()

    centroids_lat = gdf.geometry.centroid.y
    north_mask    = centroids_lat > 32.75
    n             = len(gdf)

    # Synthetic vulnerability index (high in South, low in North)
    gdf["vulnerability_index"] = np.where(
        north_mask,
        rng.uniform(0.05, 0.40, n),
        rng.uniform(0.45, 0.95, n),
    )

    # Synthetic CIP spend: $485M North vs $38M South across ~100 North tracts
    # and ~100 South tracts → 12.6× ratio
    north_n  = north_mask.sum()
    south_n  = (~north_mask).sum()

    north_cip = rng.dirichlet(np.ones(north_n)) * 485_000_000
    south_cip = rng.dirichlet(np.ones(south_n)) * 38_000_000
    gdf.loc[north_mask, "cip_vendor_usd"] = north_cip
    gdf.loc[~north_mask, "cip_vendor_usd"] = south_cip

    # Synthetic TIF increment: Downtown Connection area north, Grand Park south
    gdf["tif_increment_usd"] = np.where(
        north_mask,
        rng.uniform(5_000_000, 50_000_000, n),
        rng.uniform(100_000, 2_000_000, n),
    )

    # Population
    gdf["pop_total"] = rng.integers(800, 5000, n)

    return gdf


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- Load real data ---
    # gdf = gpd.read_file("data/raw/tracts_dallas_48113.gpkg")
    # gdf["vulnerability_index"] = <computed from atlas_map_a pipeline>
    # gdf = gdf.merge(cip_df[["GEOID","cip_vendor_usd"]], on="GEOID")
    # gdf = gdf.merge(tif_df[["GEOID","tif_increment_usd"]], on="GEOID")
    # gdf = gdf.merge(acs_pop[["GEOID","pop_total"]], on="GEOID")
    # tif_gdf = gpd.read_file("data/raw/layer1_investment/tif_districts.gpkg")

    # --- For testing with synthetic data ---
    from atlas_map_a_vulnerability import make_synthetic_gdf_dallas
    gdf_base = make_synthetic_gdf_dallas()
    gdf      = make_synthetic_gap_data(gdf_base)

    # Minimal synthetic TIF GeoDataFrame for annotation testing
    from shapely.geometry import box as shpbox
    tif_gdf_test = gpd.GeoDataFrame(
        {
            "name": ["Downtown Connection", "Grand Park South"],
            "geometry": [
                shpbox(-96.83, 32.77, -96.76, 32.83),
                shpbox(-96.80, 32.68, -96.73, 32.74),
            ],
        },
        crs="EPSG:4326",
    )

    make_map_c_gap(gdf, tif_gdf=tif_gdf_test, annotate_tif=True)

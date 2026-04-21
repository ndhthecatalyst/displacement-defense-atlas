# Displacement Defense Atlas v0 — Cartographic Specifications + Python Code
**Thesis:** Below the Line: Development as Governance and the Geography of Displacement Risk in Dallas  
**Author:** Nicholas Donovan Hawkins, Texas Southern University, Freeman Honors College  
**Target Journal:** Urban Affairs Review  
**Version:** Atlas v0  
**Date:** 2025  

---

## Shared Visual Standards (All Three Maps)

| Parameter | Value |
|---|---|
| Figure size | 10 × 10 inches |
| Output DPI | 300 |
| Font family | DejaVu Sans (Matplotlib default) |
| Title size | 14 pt bold |
| Legend text | 9 pt |
| Footnote text | 7 pt |
| Basemap | CartoDB Positron (contextily `providers.CartoDB.Positron`) |
| CRS (input) | EPSG:4326 (WGS84) |
| CRS (plotting) | EPSG:3857 (Web Mercator) |
| I-30 line style | Dashed black, linewidth=1.5, label="I-30 Corridor" |
| I-30 geometry | LineString from (−97.10, 32.75) to (−96.55, 32.75) in WGS84 |
| Output directory | `outputs/figures/` |
| Title format | `Displacement Defense Atlas v0 \| [Map Name] \| Dallas County, TX` |
| Source footnote | `Sources: [relevant sources] \| Hawkins (2027), Below the Line, TSU` |

---

---

# MAP (a): BASELINE VULNERABILITY MAP

## Cartographic Specification

### Analytical Purpose
Maps composite displacement vulnerability by census tract across Dallas County. The index combines five normalized socioeconomic indicators weighted equally to identify tracts most exposed to market-driven displacement pressure. The I-30 corridor serves as a visual reference line demarcating the historic North/South resource divide. Intended as the thesis's baseline spatial argument: structural vulnerability pre-dates and predicts where displacement-enabling tools are subsequently deployed.

### Layer Stack (Bottom → Top)
| Order | Layer | Type | Purpose |
|---|---|---|---|
| 1 | CartoDB Positron basemap | Raster tile | Geographic context, street network, place names |
| 2 | Dallas County boundary | Vector polygon outline | Study area delimiter; `edgecolor='#444444'`, `linewidth=1.2`, `facecolor='none'` |
| 3 | Census tract choropleth | Vector polygon fill | Composite vulnerability index, classified Jenks Natural Breaks, 5 classes |
| 4 | I-30 corridor line | Vector line | North/South reference; dashed black, lw=1.5 |
| 5 | Legend | Inset axes (lower right) | Color classes with break values |
| 6 | Scale bar | Lower left | Miles (primary), 5-mile increment |
| 7 | North arrow | Upper right | Orientation indicator |
| 8 | Title block | Upper center | Map title, 14 pt bold |
| 9 | Source footnote | Lower right, below legend | Data attribution |

### Color Ramp — ColorBrewer OrRd (Sequential, 5-class)
**Palette:** OrRd — orange-red family, perceptually uniform, colorblind-safe (verified: all ColorBrewer sequential palettes are colorblind-safe per the ColorBrewer 2.0 specification; safe for deuteranopia and protanopia).

| Class | Hex | Description | Vulnerability |
|---|---|---|---|
| 1 | `#fef0d9` | Very light tan/cream | Lowest vulnerability |
| 2 | `#fdcc8a` | Light orange | Low-moderate vulnerability |
| 3 | `#fc8d59` | Medium orange | Moderate vulnerability |
| 4 | `#e34a33` | Dark orange-red | High vulnerability |
| 5 | `#b30000` | Deep crimson-red | Highest vulnerability |

Tract boundaries: `edgecolor='#cccccc'`, `linewidth=0.3` (de-emphasized to not compete with fill).

### Classification Scheme
- **Method:** Jenks Natural Breaks (Fisher–Jenks optimization), 5 classes
- **Implementation:** `mapclassify.NaturalBreaks(vulnerability_index_column, k=5)`
- **Rationale:** Natural Breaks minimizes within-class variance and maximizes between-class variance; appropriate for skewed social indicator distributions. Preferred over equal interval for vulnerability indices where data clusters at extremes.
- **Break display in legend:** Show actual computed break values rounded to 2 decimal places (e.g., 0.00–0.18, 0.19–0.34, 0.35–0.51, 0.52–0.67, 0.68–1.00). Do not use fixed/assumed breaks; compute from actual data.

### Index Construction
The composite vulnerability index is the row-mean of five min-max normalized (0–1) input variables per tract:

| Variable | Source | Direction |
|---|---|---|
| Pct. renter-occupied housing units | ACS 5-yr 2023, Table B25003 | Higher = more vulnerable |
| Pct. non-white population | ACS 5-yr 2023, Table B03002 | Higher = more vulnerable |
| Median household income | ACS 5-yr 2023, Table B19013 | Lower = more vulnerable (inverted) |
| HMDA mortgage denial rate | FFIEC HMDA 2022–2023 | Higher = more vulnerable |
| Bates displacement stage | LTDB/UDP Typology v2.1 | Numeric encoding: Early=1, Dynamic=2, Late=3, Stable=0 |

Normalization formula: `x_norm = (x − x_min) / (x_max − x_min)` for each variable; income is `1 − x_norm`.

### Map Furniture
| Element | Placement | Format |
|---|---|---|
| Title | Top center, y=1.02 | DejaVu Sans 14 pt bold, `ha='center'` |
| Legend | Lower right inset (axes=[0.68, 0.04, 0.28, 0.32]) | 5 color patches, labels = break ranges, 9 pt, title "Vulnerability Index" 9 pt bold |
| Scale bar | Lower left (axes=[0.04, 0.04]) | 5-mile units, 2 ticks, black bar |
| North arrow | Upper right (axes=[0.88, 0.88]) | "N ▲" text annotation, 12 pt bold |
| Tract FIPS labels | No — too cluttered at tract density | Suppress |
| Source footnote | Figure bottom, y=−0.01 | 7 pt, left-aligned: "Sources: ACS 2023 (B25003, B03002, B19013); FFIEC HMDA 2022–23; LTDB/UDP Bates Typology v2.1; Dallas County FIPS 48113 | Hawkins (2027), Below the Line, TSU" |

### Output
`outputs/figures/atlas_v0_map_a_vulnerability.png` — 300 DPI PNG

---

## Python Code — Map (a)

```python
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
```

---
---

# MAP (b): TOOL INTENSITY OVERLAY MAP

## Cartographic Specification

### Analytical Purpose
Maps the density and co-presence of displacement-enabling policy tools (CIP capital investment, TIF districts, Opportunity Zones, Public Improvement Districts) by census tract. The map operationalizes the "infrastructure of extraction" argument: tool clusters are concentrated in already-advantaged North Dallas, compounding the North/South investment gap. TIF district boundaries are overlaid as outlines to distinguish districts from tract-level scores; OZ tracts receive hatching to distinguish them from pure tool score. The North-dense/South-sparse contrast should be immediately legible, supporting the 12.6× CIP vendor residue finding.

### Layer Stack (Bottom → Top)
| Order | Layer | Type | Purpose |
|---|---|---|---|
| 1 | CartoDB Positron basemap | Raster tile | Geographic context |
| 2 | Dallas County boundary | Vector polygon outline | Study area delimiter |
| 3 | Tract tool intensity choropleth | Vector polygon fill | Composite tool score (0–4), BuGn sequential |
| 4 | TIF district boundaries | Vector polygon outlines | Overlaid borders, `edgecolor='#1a237e'`, `linewidth=1.2`, `linestyle='-'`, no fill |
| 5 | Opportunity Zone hatching | Vector polygon hatch | OZ tracts re-drawn with `hatch='//'`, `edgecolor='#e65100'`, `facecolor='none'`, `linewidth=0.7` |
| 6 | I-30 corridor line | Vector line | North/South reference; dashed black, lw=1.5 |
| 7 | Legend | Lower right inset | Color classes, TIF outline swatch, OZ hatch swatch |
| 8 | Scale bar | Lower left | Miles (5-mile increment) |
| 9 | North arrow | Upper right | Orientation |
| 10 | Title block | Upper center | Map title |
| 11 | Source footnote | Lower right | Attribution |

### Color Ramp — ColorBrewer BuGn (Sequential, 5-class)
**Palette:** BuGn — blue-green family, perceptually ordered, colorblind-safe (all sequential palettes). Chosen to be visually distinct from the OrRd vulnerability map, enabling side-by-side reading.

| Class | Hex | Description | Tool Intensity |
|---|---|---|---|
| 1 | `#edf8fb` | Very light blue-green | No tools / lowest density |
| 2 | `#b2e2e2` | Light teal | 1 tool present |
| 3 | `#66c2a4` | Medium teal-green | 2 tools present |
| 4 | `#2ca25f` | Dark green | 3 tools present |
| 5 | `#006d2c` | Deep forest green | 4 tools present (maximum) |

Tract boundaries: `edgecolor='#cccccc'`, `linewidth=0.3`.

### Classification Scheme
- **Method:** Integer tool count (0–4) — one point per present tool type per tract
- **Scoring:**  
  `tool_score = cip_present + tif_present + oz_present + pid_present`  
  Where each variable is a binary 0/1 flag indicating whether the tract intersects or contains that tool's footprint.
- **Rationale:** Integer classification is methodologically preferable for this map because the underlying concept (co-presence of mechanisms) is discrete, not continuous. Five classes (0–4 tools) map directly to the five BuGn colors.
- **CIP present:** Binary flag if the tract's assigned CIP vendor spend exceeds $0 (from `data/raw/layer1_investment/cip_*.csv`).
- **TIF present:** Binary flag if the tract intersects any TIF district polygon (from `data/raw/layer1_investment/tif_*.gpkg`).
- **OZ present:** Binary flag if the tract is designated an Opportunity Zone (from `data/raw/layer1_investment/oz_*.gpkg`).
- **PID present:** Binary flag if the tract intersects any Public Improvement District (from `data/raw/layer1_investment/pid_*.gpkg`).

### Overlay Symbology
| Element | Style |
|---|---|
| TIF district outlines | Solid dark blue `#1a237e`, linewidth=1.2, no fill, zorder=4 |
| OZ hatching | Pattern `'//'` (diagonal lines), `edgecolor='#e65100'` (burnt orange), `facecolor='none'`, linewidth=0.7, alpha=0.85, zorder=5 |
| I-30 line | Dashed black, linewidth=1.5, zorder=6 |

### Map Furniture
| Element | Placement | Format |
|---|---|---|
| Title | Top center | 14 pt bold DejaVu Sans |
| Legend | Lower right | 5 color patches (BuGn) + TIF outline swatch + OZ hatch swatch; 9 pt |
| Scale bar | Lower left | 5-mile increment |
| North arrow | Upper right | "N ▲" 12 pt bold |
| Tract FIPS labels | No | Suppress |
| Source footnote | Figure bottom | 7 pt: "Sources: City of Dallas CIP FY2019–2024; Dallas TIF District files; HUD Opportunity Zone designations 2018; Dallas PID records | Hawkins (2027), Below the Line, TSU" |

### Output
`outputs/figures/atlas_v0_map_b_tool_intensity.png` — 300 DPI PNG

---

## Python Code — Map (b)

```python
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
```

---
---

# MAP (c): NEED-VS-INVESTMENT GAP MAP

## Cartographic Specification

### Analytical Purpose
Maps the residual between what each census tract *needs* (as measured by its composite vulnerability index from Map a) and what it has *received* (CIP vendor spend per capita + TIF increment captured, both normalized to 0–1). The gap score makes the 12.6× CIP vendor residue disparity and the 26:1 TIF increment ratio legible at the tract level. Positive gap values (red) signal under-investment relative to need — concentrated in South Dallas. Negative gap values (blue) signal over-investment relative to need — concentrated in North Dallas. The zero-divergence center (white/neutral) marks tracts where investment roughly matches vulnerability. This is the thesis's primary evidentiary map for the governance-as-displacement argument.

**Gap formula:**  
`gap_score = normalized_vulnerability - normalized_investment_received`  
`normalized_investment_received = mean(minmax(cip_spend_per_capita), minmax(tif_increment_per_capita))`

Values range from approximately −1.0 (heavily over-invested / North) to +1.0 (heavily under-invested / South).

### Layer Stack (Bottom → Top)
| Order | Layer | Type | Purpose |
|---|---|---|---|
| 1 | CartoDB Positron basemap | Raster tile | Geographic context |
| 2 | Dallas County boundary | Vector polygon outline | Study area delimiter |
| 3 | Gap score choropleth | Vector polygon fill | Diverging RdBu, 5 classes, symmetric around zero |
| 4 | I-30 corridor line | Vector line | North/South reference; dashed black, lw=1.5 |
| 5 | Annotation labels (optional) | Text | Label Downtown Connection TIF and Grand Park South TIF by name |
| 6 | Legend | Lower right inset | Diverging color bar with zero labeled |
| 7 | Scale bar | Lower left | Miles |
| 8 | North arrow | Upper right | Orientation |
| 9 | Title block | Upper center | Map title |
| 10 | Source footnote | Lower right | Attribution |

### Color Ramp — ColorBrewer RdBu (Diverging, 5-class)
**Palette:** RdBu — red–white–blue diverging, colorblind-safe (blue-red diverging palettes are safe for deuteranopia and protanopia). Red encodes *under-investment* (gap positive, South); blue encodes *over-investment* (gap negative, North). White/neutral at the divergence point.

| Class | Hex | Description | Gap Score Range |
|---|---|---|---|
| 1 | `#ca0020` | Deep red | Strongly under-invested (gap ≈ +0.4 to +1.0) |
| 2 | `#f4a582` | Light salmon/red | Mildly under-invested (gap ≈ +0.1 to +0.4) |
| 3 | `#f7f7f7` | Near-white neutral | Roughly balanced (gap ≈ −0.1 to +0.1) |
| 4 | `#92c5de` | Light steel blue | Mildly over-invested (gap ≈ −0.4 to −0.1) |
| 5 | `#0571b0` | Deep cerulean blue | Strongly over-invested (gap ≈ −1.0 to −0.4) |

Tract boundaries: `edgecolor='#cccccc'`, `linewidth=0.3`.

### Classification Scheme
- **Method:** Quantile classification with forced symmetric breaks, 5 classes
- **Break logic:** Set the middle class as [−threshold, +threshold] where threshold = 0.10 (approximately neutral). Lower two classes divide the negative range (over-invested) into quantiles; upper two classes divide the positive range (under-invested) into quantiles.
- **Alternatively (simpler):** Use equal-interval breaks centered at 0: [−1.0, −0.4, −0.1, +0.1, +0.4, +1.0] — clips extreme values.
- **Recommended implementation:** Use `np.digitize` with manually specified symmetric breaks for reproducibility across datasets.
- **Legend labels:** Show actual break values and directional labels: "Over-invested" (blue end), "Balanced" (center), "Under-invested" (red end).

### Investment Received Calculation
```
cip_per_cap   = cip_vendor_usd / tract_population
tif_per_cap   = tif_increment_usd / tract_population
inv_received  = mean(minmax(cip_per_cap), minmax(tif_per_cap))
gap_score     = vulnerability_index - inv_received
```
Where `vulnerability_index` is the same index computed in Map (a). Tracts with population = 0 are excluded (masked).

### TIF Label Annotations (Optional Enhancement)
Label the two anchor TIF districts by name to ground the 26:1 ratio finding:
- "Downtown Connection TIF\n($8.83B increment)" — annotated at centroid of Downtown Connection TIF polygon, `fontsize=7`, `color='#0571b0'`
- "Grand Park South TIF\n($333M increment)" — annotated at centroid of Grand Park South TIF polygon, `fontsize=7`, `color='#ca0020'`

### Map Furniture
| Element | Placement | Format |
|---|---|---|
| Title | Top center | 14 pt bold DejaVu Sans |
| Legend | Lower right | Diverging 5-patch legend with labels; title "Gap Score\n(Vulnerability − Investment)"; note "Red = Under-invested | Blue = Over-invested"; 9 pt |
| Scale bar | Lower left | 5-mile increment |
| North arrow | Upper right | "N ▲" 12 pt bold |
| Tract FIPS labels | No | Suppress |
| Source footnote | Figure bottom | 7 pt: "Sources: City of Dallas CIP FY2019–2024 (vendor spend by tract); Dallas TIF District increment data; ACS 2023; FFIEC HMDA 2022–23 | Hawkins (2027), Below the Line, TSU" |

### Output
`outputs/figures/atlas_v0_map_c_gap.png` — 300 DPI PNG

---

## Python Code — Map (c)

```python
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
```

---
---

# INTEGRATION SCRIPT: Run All Three Maps

```python
"""
run_atlas_v0.py
===============
Displacement Defense Atlas v0 — Master runner script
Dallas County, TX | Nicholas Donovan Hawkins, TSU

Produces all three formal atlas maps from the Displacement Defense Atlas v0:
    (a) atlas_v0_map_a_vulnerability.png  — Composite vulnerability index
    (b) atlas_v0_map_b_tool_intensity.png — Policy tool intensity overlay
    (c) atlas_v0_map_c_gap.png            — Need-vs-investment gap score

Run from repository root:
    python run_atlas_v0.py

For production use: replace the synthetic data generators with real
data loaded from data/raw/layer1_investment/, data/raw/layer2_mechanism/,
data/raw/layer3_early_warning/, and data/raw/layer4_readiness/.

REQUIRED PACKAGES:
    pip install geopandas matplotlib contextily mapclassify shapely numpy pandas
"""

import os
import sys

# Ensure outputs directory exists
os.makedirs("outputs/figures", exist_ok=True)

# ── MAP A: Baseline Vulnerability ────────────────────────────────────────────
from atlas_map_a_vulnerability import make_map_a_vulnerability, make_synthetic_gdf_dallas

print("=== Generating Map (a): Baseline Vulnerability ===")
gdf_base = make_synthetic_gdf_dallas()
make_map_a_vulnerability(gdf_base)

# ── MAP B: Tool Intensity Overlay ─────────────────────────────────────────────
from atlas_map_b_tool_intensity import make_map_b_tool_intensity, make_synthetic_tool_data

print("=== Generating Map (b): Tool Intensity Overlay ===")
gdf_b, tif_gdf, oz_gdf = make_synthetic_tool_data(gdf_base)
make_map_b_tool_intensity(gdf_b, tif_gdf, oz_gdf)

# ── MAP C: Need-vs-Investment Gap ─────────────────────────────────────────────
from atlas_map_c_gap import make_map_c_gap, make_synthetic_gap_data
from shapely.geometry import box as shpbox
import geopandas as gpd

print("=== Generating Map (c): Need-vs-Investment Gap ===")
gdf_c = make_synthetic_gap_data(gdf_base)
tif_gdf_c = gpd.GeoDataFrame(
    {
        "name": ["Downtown Connection", "Grand Park South"],
        "geometry": [
            shpbox(-96.83, 32.77, -96.76, 32.83),
            shpbox(-96.80, 32.68, -96.73, 32.74),
        ],
    },
    crs="EPSG:4326",
)
make_map_c_gap(gdf_c, tif_gdf=tif_gdf_c, annotate_tif=True)

print("\n✓ All three Atlas v0 maps saved to outputs/figures/")
print("  → outputs/figures/atlas_v0_map_a_vulnerability.png")
print("  → outputs/figures/atlas_v0_map_b_tool_intensity.png")
print("  → outputs/figures/atlas_v0_map_c_gap.png")
```

---
---

# DEPENDENCY + ENVIRONMENT NOTES

## Required Python Packages

```bash
pip install geopandas matplotlib contextily mapclassify shapely numpy pandas
```

## Tested Environment
- Python 3.10+
- geopandas ≥ 0.13
- matplotlib ≥ 3.7
- contextily ≥ 1.3
- mapclassify ≥ 2.5
- shapely ≥ 2.0

## Notes on contextily Basemap
CartoDB Positron tiles require an internet connection. If offline, omit the `ctx.add_basemap()` call or swap for a locally cached tile source. The `alpha=0.4` setting ensures the basemap recedes behind the choropleth fill without obscuring it.

## Notes on mapclassify
`mapclassify.NaturalBreaks` uses the Fisher–Jenks algorithm. For very small tract counts (< 50), consider reducing to `k=4`. The algorithm is deterministic and reproducible given the same input data.

## CRS Pipeline
All GeoDataFrames are ingested in EPSG:4326 (WGS84) and reprojected to EPSG:3857 (Web Mercator) immediately before plotting. This ensures contextily tiles align correctly with the tract polygons.

## Production Data Loading (template)

```python
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
```

---

*End of Displacement Defense Atlas v0 Cartographic Specifications.*  
*File: output_map_specifications.md | Generated for Nicholas Donovan Hawkins, TSU Freeman Honors College*

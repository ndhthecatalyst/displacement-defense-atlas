"""
atlas_v0_map_c_bates_risk_readiness.py
======================================
Displacement Defense Atlas v0 — Map (c), Publication Edition
Dallas County, TX | Thesis: "Below the Line" | Nicholas Donovan Hawkins, TSU

ANALYTICAL PURPOSE
------------------
Two-panel 300 DPI publication figure that pairs (1) the Bates v2.1 displacement
stage choropleth with (2) the H4 Risk × Readiness 2×2 classification, on a
shared Dallas County frame with the I-30 reference line.

Panel 1 (Left): Bates v2.1 seven-class sequential palette
    Dynamic → Late → Early Type 1 → Early Type 2 → Susceptible →
    Historic Loss → Stable. The 54 Susceptible South-of-I-30 tracts are
    outlined in bold black to foreground the thesis target population.

Panel 2 (Right): Risk × Readiness 2×2 cell classification
    HIGH_PRESSURE_LOW_READINESS (n=44) rendered in red (crisis quadrant).
    HIGH_PRESSURE_HIGH_READINESS (n=129) in orange.
    LOW_PRESSURE_HIGH_READINESS (n=194) in green.
    LOW_PRESSURE_LOW_READINESS (n=278) in grey.
    The top 14 crisis tracts (bottom readiness-quartile within the 54
    Susceptible-South priority list) are annotated with their NAMELSAD
    tract numbers.

INPUTS
------
    outputs/tables/h6_bates_full_typology.csv  (645 tracts, Bates v2.1)
    outputs/tables/h4_readiness_index.csv      (645 tracts, readiness + 2×2)
    outputs/tables/h4_priority_54.csv          (ranked; top-14 = crisis)
    outputs/geojson/tracts_pid_join.geojson    (Dallas County tract geometry)

OUTPUTS
-------
    maps/v0/atlas_map_c_bates_risk_readiness.png  (300 DPI)
    outputs/figures/atlas_v0_map_c_bates_risk_readiness.png  (300 DPI copy)

USAGE
-----
    python scripts/analysis/h3_pid_bates_hmda/atlas_v0_map_c_bates_risk_readiness.py
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from shapely.geometry import LineString

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Paths (repo-root-relative)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[3]
H6_PATH   = REPO_ROOT / "outputs" / "tables" / "h6_bates_full_typology.csv"
H4_PATH   = REPO_ROOT / "outputs" / "tables" / "h4_readiness_index.csv"
PRIO_PATH = REPO_ROOT / "outputs" / "tables" / "h4_priority_54.csv"
TRACT_GEO = REPO_ROOT / "outputs" / "geojson" / "tracts_pid_join.geojson"

OUT_PRIMARY   = REPO_ROOT / "maps" / "v0" / "atlas_map_c_bates_risk_readiness.png"
OUT_SECONDARY = REPO_ROOT / "outputs" / "figures" / "atlas_v0_map_c_bates_risk_readiness.png"

# ---------------------------------------------------------------------------
# Figure configuration
# ---------------------------------------------------------------------------

FIG_WIDTH  = 18          # inches; two ~9" square panels side-by-side
FIG_HEIGHT = 10
DPI        = 300

SUPTITLE = "Displacement Stage and Defense Capacity — Dallas County Census Tracts (2023)"
FOOTNOTE = (
    "Sources: City of Dallas CIP vendor records (FY2019–2024); Dallas TIF District increment ledgers; "
    "HUD LIHTC LIHT2024 & HUD Subsidized Housing 2024; IRS BMF 2024; Dallas NEZ shapefile 2024; "
    "ACS 2013 & 2023 5-yr (B01003, B03002, B19013, B25003, B25077); TIGER/Line 2023 tracts  |  "
    "Hawkins (2027), Below the Line, TSU"
)

# --- Bates v2.1 seven-stage sequential palette -----------------------------
# Ordered least-risk (Stable) → highest-risk (Dynamic) in logic; color ramp
# runs cool-green (Stable) → muted blue (Historic Loss) → yellow (Susceptible)
# → orange tones (Early Type 2, Early Type 1) → red (Late) → dark red (Dynamic).
BATES_ORDER = [
    "Dynamic",
    "Late",
    "Early: Type 1",
    "Early: Type 2",
    "Susceptible",
    "Historic Loss",
    "Stable",
]
BATES_COLORS = {
    "Dynamic":        "#7f0000",   # dark red
    "Late":           "#d7301f",   # red
    "Early: Type 1":  "#fc8d59",   # orange
    "Early: Type 2":  "#fdcc8a",   # light orange
    "Susceptible":    "#fef0d9",   # pale yellow
    "Historic Loss":  "#9ecae1",   # muted blue
    "Stable":         "#a1d99b",   # cool green
}

# --- Risk × Readiness 2×2 palette ------------------------------------------
RR_ORDER = [
    "HIGH_PRESSURE_LOW_READINESS",    # crisis quadrant
    "HIGH_PRESSURE_HIGH_READINESS",
    "LOW_PRESSURE_HIGH_READINESS",
    "LOW_PRESSURE_LOW_READINESS",
]
RR_COLORS = {
    "HIGH_PRESSURE_LOW_READINESS":  "#d7191c",   # red — crisis
    "HIGH_PRESSURE_HIGH_READINESS": "#fdae61",   # orange — pressured but defended
    "LOW_PRESSURE_HIGH_READINESS":  "#1a9641",   # green — defended & stable
    "LOW_PRESSURE_LOW_READINESS":   "#bdbdbd",   # grey — thin but stable
}
RR_LABELS = {
    "HIGH_PRESSURE_LOW_READINESS":  "High Pressure · Low Readiness  (n=44, crisis quadrant)",
    "HIGH_PRESSURE_HIGH_READINESS": "High Pressure · High Readiness  (n=129)",
    "LOW_PRESSURE_HIGH_READINESS":  "Low Pressure · High Readiness  (n=194)",
    "LOW_PRESSURE_LOW_READINESS":   "Low Pressure · Low Readiness  (n=278)",
}

# --- I-30 reference line (WGS84) -------------------------------------------
I30_COORDS_WGS84 = [(-97.10, 32.75), (-96.55, 32.75)]

# ---------------------------------------------------------------------------
# Map furniture helpers
# ---------------------------------------------------------------------------

def add_north_arrow(ax, x: float = 0.94, y: float = 0.94, fontsize: int = 11) -> None:
    ax.annotate(
        "N\n▲",
        xy=(x, y), xycoords="axes fraction",
        ha="center", va="center",
        fontsize=fontsize, fontweight="bold",
        fontfamily="DejaVu Sans",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                  edgecolor="#444444", linewidth=0.8, alpha=0.92),
    )


def add_scalebar(ax, length_m: float = 8047, label: str = "5 mi",
                 x0_frac: float = 0.05, y0_frac: float = 0.06) -> None:
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    map_width_m  = xlim[1] - xlim[0]
    map_height_m = ylim[1] - ylim[0]
    x0 = xlim[0] + x0_frac * map_width_m
    y0 = ylim[0] + y0_frac * map_height_m
    ax.plot([x0, x0 + length_m], [y0, y0],
            color="black", linewidth=2, solid_capstyle="butt", zorder=7)
    for xt in (x0, x0 + length_m):
        ax.plot([xt, xt],
                [y0 - map_height_m * 0.005, y0 + map_height_m * 0.005],
                color="black", linewidth=1.5, zorder=7)
    ax.text(x0 + length_m / 2, y0 + map_height_m * 0.015,
            label, ha="center", va="bottom",
            fontsize=8, fontfamily="DejaVu Sans", zorder=7)


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

def load_joined_tracts() -> tuple[gpd.GeoDataFrame, set[str]]:
    """Join tract geometry with H6 Bates v2.1 + H4 readiness.

    Returns
    -------
    gdf : GeoDataFrame
        645 Dallas County tracts in EPSG:3857, with columns:
        bates_typology_v21, risk_readiness_cell, south_of_i30, NAMELSAD.
    crisis_geoids : set[str]
        The 14 top-priority bottom-quartile-readiness tracts (priority_rank 1–14).
    """
    tracts = gpd.read_file(TRACT_GEO)
    tracts["GEOID"] = tracts["GEOID"].astype(str).str.zfill(11)

    h6 = pd.read_csv(H6_PATH, dtype={"GEOID": str})
    h6["GEOID"] = h6["GEOID"].str.zfill(11)
    h6 = h6[["GEOID", "NAMELSAD", "bates_typology_v21", "south_of_i30"]]

    h4 = pd.read_csv(H4_PATH, dtype={"GEOID": str})
    h4["GEOID"] = h4["GEOID"].str.zfill(11)
    h4 = h4[["GEOID", "risk_readiness_cell", "readiness_score",
             "high_pressure", "high_readiness"]]

    gdf = tracts.merge(h6, on="GEOID", how="left") \
                .merge(h4, on="GEOID", how="left")

    # Identify the 14 crisis tracts
    prio = pd.read_csv(PRIO_PATH, dtype={"GEOID": str})
    prio["GEOID"] = prio["GEOID"].str.zfill(11)
    crisis_geoids = set(prio.nsmallest(14, "priority_rank")["GEOID"].tolist())

    # Reproject to Web Mercator
    gdf = gdf.to_crs(epsg=3857)
    return gdf, crisis_geoids


# ---------------------------------------------------------------------------
# Panel renderers
# ---------------------------------------------------------------------------

def draw_common_reference(ax, gdf_wm: gpd.GeoDataFrame, i30_wm: gpd.GeoDataFrame,
                          county_boundary: gpd.GeoDataFrame) -> None:
    """Add county boundary, I-30 line, and extent for a panel."""
    county_boundary.plot(
        ax=ax, facecolor="none", edgecolor="#222222",
        linewidth=1.4, zorder=6,
    )
    i30_wm.plot(
        ax=ax, color="black", linestyle="--", linewidth=1.8, zorder=7,
    )
    # I-30 label
    i30_geom = i30_wm.geometry.iloc[0]
    mid_x = (i30_geom.bounds[0] + i30_geom.bounds[2]) / 2
    total_h = gdf_wm.total_bounds[3] - gdf_wm.total_bounds[1]
    ax.annotate(
        "I-30 Corridor",
        xy=(mid_x, i30_geom.bounds[1]),
        xytext=(mid_x, i30_geom.bounds[1] - total_h * 0.035),
        fontsize=8, fontstyle="italic", fontfamily="DejaVu Sans",
        ha="center", va="top", color="#222222", zorder=8,
    )

    bounds = gdf_wm.total_bounds
    pad_x = (bounds[2] - bounds[0]) * 0.04
    pad_y = (bounds[3] - bounds[1]) * 0.04
    ax.set_xlim(bounds[0] - pad_x, bounds[2] + pad_x)
    ax.set_ylim(bounds[1] - pad_y, bounds[3] + pad_y)
    ax.set_aspect("equal")
    ax.set_axis_off()

    add_north_arrow(ax)
    add_scalebar(ax)


def draw_bates_panel(ax, gdf_wm: gpd.GeoDataFrame, i30_wm: gpd.GeoDataFrame,
                     county_boundary: gpd.GeoDataFrame) -> None:
    """Panel 1: Bates v2.1 7-class choropleth with Susceptible South outlined."""
    # Base choropleth — paint each stage class
    for stage in BATES_ORDER:
        mask = gdf_wm["bates_typology_v21"] == stage
        if mask.sum() == 0:
            continue
        gdf_wm[mask].plot(
            ax=ax,
            facecolor=BATES_COLORS[stage],
            edgecolor="#888888",
            linewidth=0.25,
            zorder=2,
        )

    # 54 Susceptible South tracts — bold outline
    suscep_south = gdf_wm[
        (gdf_wm["bates_typology_v21"] == "Susceptible")
        & (gdf_wm["south_of_i30"] == 1)
    ]
    if len(suscep_south) > 0:
        suscep_south.boundary.plot(
            ax=ax, color="#000000", linewidth=1.6, zorder=5,
        )

    # Common reference (county, I-30, extent, N arrow, scalebar)
    draw_common_reference(ax, gdf_wm, i30_wm, county_boundary)

    ax.set_title(
        "A. Bates v2.1 Displacement Stage\n"
        f"Susceptible South-of-I-30 (n={len(suscep_south)}) outlined in bold",
        fontsize=12, fontweight="bold", fontfamily="DejaVu Sans", pad=8,
    )

    # Legend — Bates stages
    patches = [
        mpatches.Patch(facecolor=BATES_COLORS[s], edgecolor="#555555",
                       linewidth=0.5, label=s)
        for s in BATES_ORDER
    ]
    suscep_handle = mlines.Line2D(
        [], [], color="#000000", linewidth=1.6,
        label=f"Susceptible South (n={len(suscep_south)})",
    )
    i30_handle = mlines.Line2D(
        [], [], color="black", linestyle="--", linewidth=1.8,
        label="I-30 Corridor",
    )
    leg = ax.legend(
        handles=patches + [suscep_handle, i30_handle],
        title="Bates v2.1 Typology",
        title_fontsize=9, fontsize=8.5,
        loc="lower right", frameon=True, framealpha=0.94,
        edgecolor="#aaaaaa", fancybox=False,
    )
    leg.get_title().set_fontweight("bold")


def draw_risk_readiness_panel(ax, gdf_wm: gpd.GeoDataFrame,
                              i30_wm: gpd.GeoDataFrame,
                              county_boundary: gpd.GeoDataFrame,
                              crisis_geoids: set[str]) -> None:
    """Panel 2: Risk × Readiness 2×2 choropleth with HP/LR in red + 14 crisis tracts labeled."""
    for cell in RR_ORDER:
        mask = gdf_wm["risk_readiness_cell"] == cell
        if mask.sum() == 0:
            continue
        gdf_wm[mask].plot(
            ax=ax,
            facecolor=RR_COLORS[cell],
            edgecolor="#888888",
            linewidth=0.25,
            zorder=2,
        )

    # Emphasize the 44 HIGH_PRESSURE_LOW_READINESS tracts (already red; add thin outline)
    hp_lr = gdf_wm[gdf_wm["risk_readiness_cell"] == "HIGH_PRESSURE_LOW_READINESS"]
    if len(hp_lr) > 0:
        hp_lr.boundary.plot(
            ax=ax, color="#7f0000", linewidth=0.9, zorder=4,
        )

    # Reference furniture
    draw_common_reference(ax, gdf_wm, i30_wm, county_boundary)

    # Annotate 14 crisis tracts with NAMELSAD tract number (e.g. "170.09")
    crisis_gdf = gdf_wm[gdf_wm["GEOID"].isin(crisis_geoids)].copy()
    crisis_gdf["short_label"] = (
        crisis_gdf["NAMELSAD"].fillna("").str.replace("Census Tract ", "", regex=False)
    )
    for _, row in crisis_gdf.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        pt = row.geometry.representative_point()
        ax.annotate(
            row["short_label"],
            xy=(pt.x, pt.y),
            fontsize=6.5, fontweight="bold",
            fontfamily="DejaVu Sans",
            ha="center", va="center", color="#111111",
            bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                      edgecolor="#7f0000", linewidth=0.5, alpha=0.88),
            zorder=9,
        )

    ax.set_title(
        "B. Risk × Readiness 2×2 Classification\n"
        f"HIGH_PRESSURE_LOW_READINESS (n={len(hp_lr)}) in red · top-14 crisis tracts labeled",
        fontsize=12, fontweight="bold", fontfamily="DejaVu Sans", pad=8,
    )

    # Legend
    patches = [
        mpatches.Patch(facecolor=RR_COLORS[c], edgecolor="#555555",
                       linewidth=0.5, label=RR_LABELS[c])
        for c in RR_ORDER
    ]
    crisis_handle = mpatches.Patch(
        facecolor="white", edgecolor="#7f0000", linewidth=0.8,
        label="Top-14 crisis tract (label)",
    )
    i30_handle = mlines.Line2D(
        [], [], color="black", linestyle="--", linewidth=1.8,
        label="I-30 Corridor",
    )
    leg = ax.legend(
        handles=patches + [crisis_handle, i30_handle],
        title="H4 Risk × Readiness Quadrant",
        title_fontsize=9, fontsize=8.5,
        loc="lower right", frameon=True, framealpha=0.94,
        edgecolor="#aaaaaa", fancybox=False,
    )
    leg.get_title().set_fontweight("bold")


# ---------------------------------------------------------------------------
# Composite figure
# ---------------------------------------------------------------------------

def build_figure() -> None:
    print("[Map C] Loading data...")
    gdf_wm, crisis_geoids = load_joined_tracts()

    # Diagnostics
    n_suscep_south = int(
        ((gdf_wm["bates_typology_v21"] == "Susceptible")
         & (gdf_wm["south_of_i30"] == 1)).sum()
    )
    n_hp_lr = int((gdf_wm["risk_readiness_cell"] == "HIGH_PRESSURE_LOW_READINESS").sum())
    print(f"[Map C] Tracts joined: {len(gdf_wm)}")
    print(f"[Map C] Susceptible South (bold outline): {n_suscep_south}")
    print(f"[Map C] HIGH_PRESSURE_LOW_READINESS: {n_hp_lr}")
    print(f"[Map C] Top-14 crisis tracts annotated: {len(crisis_geoids)}")

    # Shared geometry: I-30 + county outline
    i30_wm = gpd.GeoDataFrame(
        geometry=[LineString(I30_COORDS_WGS84)], crs="EPSG:4326"
    ).to_crs(epsg=3857)
    county_boundary = gdf_wm.dissolve()

    # Figure
    fig, (axA, axB) = plt.subplots(
        1, 2, figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI,
        gridspec_kw=dict(wspace=0.04),
    )

    draw_bates_panel(axA, gdf_wm, i30_wm, county_boundary)
    draw_risk_readiness_panel(axB, gdf_wm, i30_wm, county_boundary, crisis_geoids)

    # Suptitle + footnote
    fig.suptitle(SUPTITLE, fontsize=15, fontweight="bold",
                 fontfamily="DejaVu Sans", y=0.98)
    fig.text(
        0.01, 0.008, FOOTNOTE,
        fontsize=7.2, fontfamily="DejaVu Sans",
        color="#555555", ha="left", va="bottom",
    )

    # Save
    OUT_PRIMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_SECONDARY.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PRIMARY, dpi=DPI, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    fig.savefig(OUT_SECONDARY, dpi=DPI, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"[Map C] Saved → {OUT_PRIMARY.relative_to(REPO_ROOT)}")
    print(f"[Map C] Saved → {OUT_SECONDARY.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    build_figure()

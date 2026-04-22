"""
atlas_basemap.py — Shared helpers for the Displacement Defense Atlas v1 maps.

Provides:
  - load_basemap_layers()      : Dallas city boundary, I-30 linework, council, tracts
  - add_contextily_basemap()   : muted Carto tiles with graceful offline fallback
  - add_reference_overlay()    : overlays city boundary + I-30 + corridor label
  - add_neighborhood_labels()  : ~8 anchor-place text labels with halos
  - add_scale_and_north()      : one scale bar + one north arrow per figure
  - add_accent_title()         : panel title with left thesis-red accent bar
  - ATLAS_COLORS               : palette dict

All layers are returned already projected to EPSG:3857 (Web Mercator).
"""
from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import MultipleLocator
import numpy as np

try:
    import contextily as cx
    _HAS_CX = True
except ImportError:
    _HAS_CX = False

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Palette — thesis house colors
# ---------------------------------------------------------------------------
ATLAS_COLORS = {
    "thesis_red":   "#7f0000",
    "thesis_green": "#1a9641",
    "navy":         "#0b1a2b",
    "paper":        "#faf7f2",
    "ink":          "#111111",
    "muted":        "#6b6b6b",
    "i30":          "#1a1a1a",
    "city":         "#333333",
    "halo":         "#ffffff",
}

# Anchor places (lon, lat) — drawn on every map in matching style
# (name, lon, lat). Coords tuned to avoid collisions at 16×10" figure scale.
NEIGHBORHOOD_ANCHORS = [
    ("Downtown",       -96.798, 32.790),
    ("Uptown",         -96.812, 32.815),
    ("Oak Cliff",      -96.845, 32.725),
    ("South Dallas",   -96.735, 32.750),
    ("Fair Park",      -96.760, 32.775),
    ("Pleasant Grove", -96.668, 32.735),
    ("West Dallas",    -96.885, 32.778),
    ("Red Bird",       -96.880, 32.665),
    ("Lake Highlands", -96.725, 32.880),
    ("Bishop Arts",    -96.830, 32.750),
]


# ---------------------------------------------------------------------------
# Layer loaders (cached read → project to 3857 once)
# ---------------------------------------------------------------------------
def load_basemap_layers():
    """Return dict of {name: GeoDataFrame in EPSG:3857} for standard reference layers."""
    base = REPO_ROOT / "data" / "raw" / "basemap"
    layers = {}

    dallas = gpd.read_file(base / "dallas_city_boundary.geojson").to_crs(3857)
    layers["dallas_city"] = dallas

    i30 = gpd.read_file(base / "i30_dallas.geojson").to_crs(3857)
    # Dissolve into one linestring for clean plotting
    i30_union = i30.unary_union
    layers["i30"] = gpd.GeoDataFrame(
        {"name": ["I-30"]}, geometry=[i30_union], crs=3857
    )

    council = gpd.read_file(
        REPO_ROOT / "data" / "h4_readiness" / "council" / "council_districts.geojson"
    ).to_crs(3857)
    layers["council"] = council

    tracts = gpd.read_file(
        REPO_ROOT / "outputs" / "geojson" / "tracts_pid_join.geojson"
    ).to_crs(3857)
    tracts["GEOID"] = tracts["GEOID"].astype(str).str.zfill(11)
    layers["tracts"] = tracts

    return layers


# ---------------------------------------------------------------------------
# Contextily basemap w/ offline fallback
# ---------------------------------------------------------------------------
def add_contextily_basemap(ax, zoom=11, provider="positron", alpha=0.55):
    """Attach a muted tile basemap. Silently no-ops if contextily/network unavailable."""
    if not _HAS_CX:
        return False
    try:
        if provider == "positron":
            src = cx.providers.CartoDB.PositronNoLabels
        elif provider == "voyager":
            src = cx.providers.CartoDB.VoyagerNoLabels
        else:
            src = cx.providers.CartoDB.PositronNoLabels
        cx.add_basemap(ax, source=src, zoom=zoom, alpha=alpha, attribution=False)
        return True
    except Exception as exc:
        print(f"[basemap] tile fetch failed ({exc}); continuing without tiles")
        return False


# ---------------------------------------------------------------------------
# Overlays
# ---------------------------------------------------------------------------
def add_reference_overlay(ax, layers, *, show_city=True, show_i30=True,
                          show_council=False, label_i30=True):
    """Draw the shared reference layers: city boundary, I-30, optional council lines."""
    if show_council:
        layers["council"].boundary.plot(
            ax=ax, color="#888", linewidth=0.4, alpha=0.35, zorder=2
        )
    if show_city:
        layers["dallas_city"].boundary.plot(
            ax=ax, color=ATLAS_COLORS["city"], linewidth=1.3, alpha=0.7, zorder=3
        )
    if show_i30:
        layers["i30"].plot(
            ax=ax, color=ATLAS_COLORS["i30"], linewidth=2.2, zorder=5
        )
        # Halo underneath for readability
        layers["i30"].plot(
            ax=ax, color="white", linewidth=4.0, alpha=0.55, zorder=4
        )
        if label_i30:
            # Pick a clean east-side point along the line to place the label
            from pyproj import Transformer
            t = Transformer.from_crs(4326, 3857, always_xy=True)
            # Place label east of downtown where the line runs through suburbs
            lx, ly = t.transform(-96.62, 32.770)
            ax.annotate(
                "I-30", xy=(lx, ly),
                fontsize=9.0, fontweight="bold",
                color=ATLAS_COLORS["i30"],
                path_effects=[pe.withStroke(linewidth=2.8, foreground="white")],
                zorder=10,
            )


def add_neighborhood_labels(ax, fontsize=7.0, subset=None, strong_halo=False):
    """Plot ~10 anchor neighborhoods. Call in EPSG:3857 axes only.

    strong_halo=True yields thicker white halos for dark choropleth backgrounds
    (Layer 4/5 panels with red/brown fills).
    """
    from pyproj import Transformer
    t = Transformer.from_crs(4326, 3857, always_xy=True)
    halo_lw = 3.6 if strong_halo else 2.2
    text_color = "#0a0a0a" if strong_halo else "#222"
    for name, lon, lat in NEIGHBORHOOD_ANCHORS:
        if subset and name not in subset:
            continue
        x, y = t.transform(lon, lat)
        ax.annotate(
            name, xy=(x, y),
            fontsize=fontsize, fontweight="semibold", color=text_color,
            ha="center", va="center",
            path_effects=[pe.withStroke(linewidth=halo_lw, foreground="white")],
            zorder=11,
        )


def add_scale_and_north(ax, *, scale_km=5, anchor="lower left"):
    """Draw a tasteful scale bar + compact north arrow in a single axes."""
    # Manual scale bar (no external dep)
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    bar_m = scale_km * 1000.0
    pad_x = (xmax - xmin) * 0.04
    pad_y = (ymax - ymin) * 0.04
    if anchor == "lower left":
        x0, y0 = xmin + pad_x, ymin + pad_y
    elif anchor == "lower right":
        x0, y0 = xmax - pad_x - bar_m, ymin + pad_y
    else:
        x0, y0 = xmin + pad_x, ymin + pad_y
    # scale line
    ax.plot([x0, x0 + bar_m], [y0, y0], color=ATLAS_COLORS["ink"], lw=2.3,
            solid_capstyle="butt", zorder=20)
    ax.plot([x0, x0 + bar_m], [y0, y0], color="white", lw=4.5, alpha=0.7,
            solid_capstyle="butt", zorder=19)
    ax.text(x0 + bar_m / 2, y0 + pad_y * 0.3, f"{scale_km} km",
            ha="center", va="bottom", fontsize=7.5, fontweight="bold",
            color=ATLAS_COLORS["ink"],
            path_effects=[pe.withStroke(linewidth=2.2, foreground="white")],
            zorder=20)

    # North arrow — top-right corner of same axes
    nx = xmax - pad_x
    ny = ymax - pad_y
    ax.annotate(
        "N", xy=(nx, ny - pad_y * 0.9), xytext=(nx, ny - pad_y * 2.3),
        arrowprops=dict(arrowstyle="-|>", color=ATLAS_COLORS["ink"], lw=1.6),
        ha="center", va="top", fontsize=10, fontweight="bold",
        color=ATLAS_COLORS["ink"],
        path_effects=[pe.withStroke(linewidth=2.2, foreground="white")],
        zorder=20,
    )


# ---------------------------------------------------------------------------
# Titling
# ---------------------------------------------------------------------------
def add_accent_title(ax, letter, title, subtitle=None, *, accent_color=None):
    """Panel title with a left-side colored accent bar. Uses matplotlib text."""
    accent = accent_color or ATLAS_COLORS["thesis_red"]
    # Letter badge
    letter_txt = ax.text(
        0.005, 1.045, letter,
        transform=ax.transAxes, fontsize=11.5, fontweight="bold",
        color=accent, ha="left", va="bottom",
    )
    # Main title (with left pad so it doesn't collide with letter)
    ax.text(
        0.055, 1.045, title,
        transform=ax.transAxes, fontsize=11.5, fontweight="bold",
        color=ATLAS_COLORS["ink"], ha="left", va="bottom",
    )
    if subtitle:
        ax.text(
            0.055, 1.010, subtitle,
            transform=ax.transAxes, fontsize=8.5, fontweight="normal",
            color=ATLAS_COLORS["muted"], ha="left", va="bottom",
            style="italic",
        )


# ---------------------------------------------------------------------------
# Consistent axis framing
# ---------------------------------------------------------------------------
def frame_to_dallas_county(ax, tracts):
    """Zoom the axis to Dallas County bounds with a small pad."""
    xmin, ymin, xmax, ymax = tracts.total_bounds
    pad = (xmax - xmin) * 0.02
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

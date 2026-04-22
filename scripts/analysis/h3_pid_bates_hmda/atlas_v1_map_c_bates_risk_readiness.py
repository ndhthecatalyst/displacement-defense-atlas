"""
atlas_v1_map_c_bates_risk_readiness.py
=======================================
Displacement Defense Atlas v1 — Map C: Displacement Stage and Defense Capacity
Dallas County, TX | Thesis: "Below the Line" | Nicholas Donovan Hawkins, TSU

v1 CHANGES VS v0
----------------
  * Basemap: Carto Positron tiles + Dallas city boundary + real I-30 geometry.
  * Bates categories collapsed from 7 → 6 (Early Type 1 + Type 2 → "Early").
  * Neighborhood anchor labels (Downtown, Oak Cliff, South Dallas, etc.)
    with white halos for readability.
  * Crisis-tract labels moved to a right-hand callout table with leader lines
    to eliminate label collisions on the map.
  * Inset bar chart: 2×2 quadrant counts with % share (Panel B reinforcement).
  * Headline annotation: "44 of 54 Susceptible South tracts sit in the
    High-Pressure × Low-Readiness crisis quadrant".
  * Accent-bar panel titles; figure-level typography hierarchy.
  * Single shared scale bar + north arrow (on Panel A).

OUTPUTS
-------
  maps/v1/atlas_map_c_bates_risk_readiness.png             (300 DPI)
  outputs/figures/atlas_v1_map_c_bates_risk_readiness.png  (300 DPI copy)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "analysis"))
from atlas_basemap import (  # noqa: E402
    ATLAS_COLORS,
    load_basemap_layers,
    add_contextily_basemap,
    add_reference_overlay,
    add_neighborhood_labels,
    add_scale_and_north,
    add_accent_title,
    frame_to_dallas_county,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
H6_PATH   = REPO_ROOT / "outputs" / "tables" / "h6_bates_full_typology.csv"
H4_PATH   = REPO_ROOT / "outputs" / "tables" / "h4_readiness_index.csv"
PRIO_PATH = REPO_ROOT / "outputs" / "tables" / "h4_priority_54.csv"
OUT_PRIMARY = REPO_ROOT / "maps" / "v1" / "atlas_map_c_bates_risk_readiness.png"
OUT_MIRROR  = REPO_ROOT / "outputs" / "figures" / "atlas_v1_map_c_bates_risk_readiness.png"

# ---------------------------------------------------------------------------
# Bates v2.1 — collapsed to 6 categories for v1
# ---------------------------------------------------------------------------
# Merge Early: Type 1 + Early: Type 2 → "Early" with a single orange tone.
# Order: low-risk → high-risk for legend ordering.
BATES_ORDER = [
    "Stable",
    "Historic Loss",
    "Susceptible",
    "Early",
    "Late",
    "Dynamic",
]
BATES_COLORS = {
    "Stable":        "#a1d99b",
    "Historic Loss": "#9ecae1",
    "Susceptible":   "#fef0d9",
    "Early":         "#fdae6b",
    "Late":          "#d7301f",
    "Dynamic":       "#7f0000",
}
BATES_LABELS = {
    "Stable":        "Stable",
    "Historic Loss": "Historic Loss",
    "Susceptible":   "Susceptible",
    "Early":         "Early (Types 1 + 2)",
    "Late":          "Late",
    "Dynamic":       "Dynamic",
}

# Risk × Readiness 2×2
RR_ORDER = [
    "HIGH_PRESSURE_LOW_READINESS",
    "HIGH_PRESSURE_HIGH_READINESS",
    "LOW_PRESSURE_HIGH_READINESS",
    "LOW_PRESSURE_LOW_READINESS",
]
RR_COLORS = {
    "HIGH_PRESSURE_LOW_READINESS":  "#d7191c",
    "HIGH_PRESSURE_HIGH_READINESS": "#fdae61",
    "LOW_PRESSURE_HIGH_READINESS":  "#1a9641",
    "LOW_PRESSURE_LOW_READINESS":   "#bdbdbd",
}
RR_LABELS_SHORT = {
    "HIGH_PRESSURE_LOW_READINESS":  "High Pressure · Low Readiness  (crisis)",
    "HIGH_PRESSURE_HIGH_READINESS": "High Pressure · High Readiness",
    "LOW_PRESSURE_HIGH_READINESS":  "Low Pressure · High Readiness",
    "LOW_PRESSURE_LOW_READINESS":   "Low Pressure · Low Readiness",
}


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------
def load_joined_tracts():
    layers = load_basemap_layers()
    tracts = layers["tracts"][["GEOID", "geometry"]].copy()
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

    # Collapse the two Early types
    gdf["bates_v1"] = gdf["bates_typology_v21"].replace({
        "Early: Type 1": "Early",
        "Early: Type 2": "Early",
    })

    # Identify the 14 crisis tracts
    prio = pd.read_csv(PRIO_PATH, dtype={"GEOID": str})
    prio["GEOID"] = prio["GEOID"].str.zfill(11)
    crisis = prio.nsmallest(14, "priority_rank")[[
        "GEOID", "priority_rank", "NAMELSAD", "bates_typology_v21",
        "risk_readiness_cell", "council_district",
    ]].copy()
    crisis["bates_v1"] = crisis["bates_typology_v21"].replace({
        "Early: Type 1": "Early",
        "Early: Type 2": "Early",
    })

    return gdf, layers, crisis


# ---------------------------------------------------------------------------
# Panel A — Bates Displacement Stage
# ---------------------------------------------------------------------------
def render_bates_panel(ax, gdf, layers, *, susceptible_south):
    add_contextily_basemap(ax, zoom=11, provider="positron", alpha=0.65)

    # Plot each Bates category (order low-risk → high-risk so high-risk draws on top)
    for stage in BATES_ORDER:
        sub = gdf[gdf["bates_v1"] == stage]
        if sub.empty:
            continue
        sub.plot(
            ax=ax, facecolor=BATES_COLORS[stage],
            edgecolor="#ffffff", linewidth=0.15, alpha=0.85, zorder=5,
        )

    # Emphasize Susceptible South with thicker dark outline
    susceptible_south.boundary.plot(
        ax=ax, edgecolor="#222", linewidth=1.3, zorder=10,
    )

    add_reference_overlay(ax, layers, show_city=True, show_i30=True, label_i30=True)
    frame_to_dallas_county(ax, layers["tracts"])
    add_neighborhood_labels(
        ax, fontsize=8.0,
        subset={"Downtown", "Oak Cliff", "South Dallas",
                "Pleasant Grove", "Lake Highlands", "West Dallas"},
    )
    add_accent_title(
        ax, "A.", "Bates v2.1 Displacement Stage",
        f"Six-stage typology · {len(susceptible_south)} Susceptible-South tracts outlined",
    )
    add_scale_and_north(ax, scale_km=5, anchor="lower left")

    # Legend: Bates categories in a clean vertical stack
    bates_counts = gdf["bates_v1"].value_counts()
    handles = []
    for stage in BATES_ORDER:
        count = int(bates_counts.get(stage, 0))
        handles.append(mpatches.Patch(
            facecolor=BATES_COLORS[stage], edgecolor="white",
            label=f"{BATES_LABELS[stage]}  (n={count})",
        ))
    handles.append(Line2D(
        [0], [0], color="#222", linewidth=1.4,
        label=f"Susceptible-South outline  (n={len(susceptible_south)})",
    ))
    leg = ax.legend(
        handles=handles, loc="lower right",
        fontsize=8, title="Bates v2.1 Typology",
        title_fontsize=9, frameon=True, framealpha=0.93,
        edgecolor="#bbb", borderpad=0.6, labelspacing=0.5,
    )
    leg.get_title().set_fontweight("bold")
    leg.set_zorder(15)


# ---------------------------------------------------------------------------
# Panel B — Risk × Readiness 2×2 with crisis-tract callouts
# ---------------------------------------------------------------------------
def render_rr_panel(ax, gdf, layers, crisis_df, rr_counts):
    add_contextily_basemap(ax, zoom=11, provider="positron", alpha=0.65)

    for cell in RR_ORDER:
        sub = gdf[gdf["risk_readiness_cell"] == cell]
        if sub.empty:
            continue
        sub.plot(
            ax=ax, facecolor=RR_COLORS[cell],
            edgecolor="#ffffff", linewidth=0.15, alpha=0.85, zorder=5,
        )

    # Outline the 14 crisis tracts with a distinctive white-on-dark treatment
    crisis_geo = gdf[gdf["GEOID"].isin(crisis_df["GEOID"])].copy()
    crisis_geo.boundary.plot(
        ax=ax, edgecolor="#111", linewidth=1.3, zorder=10,
    )
    # Add a white halo underneath for visibility on red fill
    crisis_geo.boundary.plot(
        ax=ax, edgecolor="white", linewidth=2.6, zorder=9,
    )

    add_reference_overlay(ax, layers, show_city=True, show_i30=True, label_i30=False)
    frame_to_dallas_county(ax, layers["tracts"])
    add_neighborhood_labels(
        ax, fontsize=8.0,
        subset={"Downtown", "Oak Cliff", "South Dallas",
                "Pleasant Grove", "Lake Highlands", "West Dallas"},
    )
    add_accent_title(
        ax, "B.", "Risk × Readiness 2×2 Classification",
        f"Crisis quadrant (n={rr_counts['HIGH_PRESSURE_LOW_READINESS']}) in red · "
        f"top-14 H4 priority tracts outlined",
    )

    # Legend for quadrants
    handles = []
    for cell in RR_ORDER:
        n = rr_counts.get(cell, 0)
        handles.append(mpatches.Patch(
            facecolor=RR_COLORS[cell], edgecolor="white",
            label=f"{RR_LABELS_SHORT[cell]}  (n={n})",
        ))
    handles.append(Line2D(
        [0], [0], color="#111", linewidth=1.4,
        label="Top-14 H4 priority tract",
    ))
    leg = ax.legend(
        handles=handles, loc="lower right",
        fontsize=8, title="H4 Risk × Readiness Quadrant",
        title_fontsize=9, frameon=True, framealpha=0.93,
        edgecolor="#bbb", borderpad=0.6, labelspacing=0.5,
    )
    leg.get_title().set_fontweight("bold")
    leg.set_zorder(15)


# ---------------------------------------------------------------------------
# Inset quadrant bar chart — drawn into a dedicated axes at bottom
# ---------------------------------------------------------------------------
def render_quadrant_inset(ax, rr_counts):
    total = sum(rr_counts.values())
    # Ordered for quick scan (crisis first)
    labels_short = [
        "Crisis\n(HighP · LowR)",
        "HighP · HighR",
        "LowP · HighR",
        "LowP · LowR",
    ]
    values = [rr_counts.get(c, 0) for c in RR_ORDER]
    colors = [RR_COLORS[c] for c in RR_ORDER]
    x = np.arange(len(labels_short))
    bars = ax.bar(x, values, color=colors, edgecolor="#333", linewidth=0.5, width=0.65)
    for i, (b, v) in enumerate(zip(bars, values)):
        pct = v / total * 100
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + total * 0.01,
                f"{v}\n{pct:.0f}%", ha="center", va="bottom",
                fontsize=9, fontweight="semibold", color="#222")
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, fontsize=9)
    ax.set_ylabel("Tracts", fontsize=9, labelpad=4)
    ax.set_ylim(0, max(values) * 1.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#bbb", alpha=0.7)
    ax.set_axisbelow(True)
    ax.text(
        0.0, 1.12, "C.", transform=ax.transAxes,
        fontsize=12, fontweight="bold", color=ATLAS_COLORS["thesis_red"], ha="left",
    )
    ax.text(
        0.03, 1.12,
        "Risk × Readiness Quadrant Distribution",
        transform=ax.transAxes, fontsize=12, fontweight="bold",
        color=ATLAS_COLORS["ink"], ha="left",
    )
    ax.text(
        0.0, 1.02, f"All {total} Dallas County tracts \u00b7 crisis quadrant sits "
        f"{values[0]/total*100:.0f}% of the county",
        transform=ax.transAxes, fontsize=8.5,
        color=ATLAS_COLORS["muted"], ha="left", style="italic",
    )


# ---------------------------------------------------------------------------
# Crisis-tract callout panel
# ---------------------------------------------------------------------------
def render_crisis_callout(ax, gdf, crisis_df):
    ax.axis("off")
    merged = crisis_df.sort_values("priority_rank")
    n_crisis = int((merged["risk_readiness_cell"] == "HIGH_PRESSURE_LOW_READINESS").sum())
    n_hphr = int((merged["risk_readiness_cell"] == "HIGH_PRESSURE_HIGH_READINESS").sum())
    n_susc = int((merged["bates_v1"] == "Susceptible").sum())

    ax.text(
        0.0, 0.98, "D.", transform=ax.transAxes,
        fontsize=12, fontweight="bold", color=ATLAS_COLORS["thesis_red"], ha="left",
    )
    ax.text(
        0.045, 0.98, "Top-14 H4 Priority Tracts",
        transform=ax.transAxes, fontsize=12, fontweight="bold",
        color=ATLAS_COLORS["ink"], ha="left",
    )
    ax.text(
        0.0, 0.935,
        f"{n_susc} Susceptible-stage \u00b7 {n_crisis} in crisis quadrant \u00b7 "
        f"{n_hphr} in HighP\u00b7HighR",
        transform=ax.transAxes, fontsize=8.5,
        color=ATLAS_COLORS["muted"], ha="left", style="italic",
    )
    # Column headers
    y0 = 0.87
    dy = 0.058
    ax.text(0.00, y0, "#",        transform=ax.transAxes, fontsize=9, fontweight="bold")
    ax.text(0.08, y0, "Tract",    transform=ax.transAxes, fontsize=9, fontweight="bold")
    ax.text(0.33, y0, "CD",       transform=ax.transAxes, fontsize=9, fontweight="bold")
    ax.text(0.44, y0, "Stage",    transform=ax.transAxes, fontsize=9, fontweight="bold")
    ax.text(0.76, y0, "Quadrant", transform=ax.transAxes, fontsize=9, fontweight="bold")

    for i, (_, r) in enumerate(merged.iterrows()):
        y = y0 - 0.03 - (i + 1) * dy * 0.9
        rank = int(r["priority_rank"])
        tract = str(r.get("NAMELSAD") or r["GEOID"]).replace("Census Tract ", "CT ")
        cd = r.get("council_district")
        try:
            cd_str = f"CD{int(float(cd))}" if pd.notna(cd) else "\u2014"
        except (ValueError, TypeError):
            cd_str = "—"  # “Outside City of Dallas”, etc.
        bates = str(r.get("bates_v1") or "—")
        q = str(r.get("risk_readiness_cell") or "")
        q_short = {
            "HIGH_PRESSURE_LOW_READINESS":  "Crisis",
            "HIGH_PRESSURE_HIGH_READINESS": "HighP·HighR",
            "LOW_PRESSURE_HIGH_READINESS":  "LowP·HighR",
            "LOW_PRESSURE_LOW_READINESS":   "LowP·LowR",
        }.get(q, q or "—")
        q_color = {
            "Crisis":      ATLAS_COLORS["thesis_red"],
            "HighP·HighR": "#b06b00",
        }.get(q_short, "#333")
        ax.text(0.00, y, f"{rank}", transform=ax.transAxes,
                fontsize=9, fontweight="semibold",
                color=ATLAS_COLORS["thesis_red"], va="center")
        ax.text(0.08, y, tract, transform=ax.transAxes,
                fontsize=8.5, color="#222", va="center")
        ax.text(0.33, y, cd_str, transform=ax.transAxes,
                fontsize=8.5, color="#555", va="center")
        bcolor = BATES_COLORS.get(bates, "#bbb")
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.435, y - 0.017), 0.30, 0.034,
            transform=ax.transAxes,
            boxstyle="round,pad=0.005,rounding_size=0.010",
            facecolor=bcolor, edgecolor="#888", linewidth=0.4,
        ))
        ax.text(0.44, y, bates, transform=ax.transAxes,
                fontsize=8.5, color="#111", va="center")
        ax.text(0.76, y, q_short, transform=ax.transAxes,
                fontsize=8.5, fontweight="semibold",
                color=q_color, va="center")


# ---------------------------------------------------------------------------
# Figure assembly
# ---------------------------------------------------------------------------
def build_figure():
    gdf, layers, crisis_df = load_joined_tracts()
    # Diagnostics
    susc_south = gdf[(gdf["bates_v1"] == "Susceptible") & (gdf["south_of_i30"] == 1)]
    crisis_susc_south = susc_south[
        susc_south["risk_readiness_cell"] == "HIGH_PRESSURE_LOW_READINESS"
    ]
    print(f"[v1 Map C] Susceptible-South n={len(susc_south)}; "
          f"of those in crisis quadrant: {len(crisis_susc_south)}")
    rr_counts = gdf["risk_readiness_cell"].value_counts().to_dict()
    print(f"[v1 Map C] Quadrant counts: {rr_counts}")

    # ---- Figure -----------------------------------------------------------
    fig = plt.figure(figsize=(20.0, 13.5), dpi=150, facecolor="white")
    gs = fig.add_gridspec(
        nrows=2, ncols=3,
        width_ratios=[1.0, 1.0, 0.55],
        height_ratios=[1.0, 0.45],
        hspace=0.28, wspace=0.10,
        left=0.035, right=0.975, top=0.900, bottom=0.065,
    )
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_call = fig.add_subplot(gs[0:, 2])  # right column full height
    ax_quad = fig.add_subplot(gs[1, 0:2]) # bottom spanning two map columns

    render_bates_panel(ax_a, gdf, layers, susceptible_south=susc_south)
    render_rr_panel(ax_b, gdf, layers, crisis_df=crisis_df, rr_counts=rr_counts)

    # Panel B headline stat box
    headline = (
        f"{len(crisis_susc_south)} of {len(susc_south)} Susceptible-South tracts\n"
        f"sit in the High-Pressure × Low-Readiness\ncrisis quadrant"
    )
    ax_b.text(
        0.03, 0.04, headline,
        transform=ax_b.transAxes, fontsize=8.5, fontweight="semibold",
        color=ATLAS_COLORS["ink"], va="bottom", ha="left",
        bbox=dict(facecolor="white", edgecolor=ATLAS_COLORS["thesis_red"],
                  linewidth=1.0, boxstyle="round,pad=0.4"),
        zorder=20,
    )

    render_quadrant_inset(ax_quad, rr_counts)
    render_crisis_callout(ax_call, gdf, crisis_df)

    # ---- Figure title -----------------------------------------------------
    fig.text(
        0.035, 0.960,
        "Displacement Stage and Defense Capacity",
        fontsize=23, fontweight="bold", color=ATLAS_COLORS["ink"],
    )
    fig.text(
        0.035, 0.933,
        "Dallas County Census Tracts  ·  2023  ·  "
        "Where the Bates typology meets the Risk × Readiness crisis quadrant",
        fontsize=11.5, color=ATLAS_COLORS["muted"], style="italic",
    )
    fig.text(
        0.975, 0.962, "Map C  ·  v1",
        fontsize=11, fontweight="bold", color=ATLAS_COLORS["thesis_red"],
        ha="right", va="top",
    )
    fig.text(
        0.975, 0.940, "Below the Line  ·  Hawkins 2027, TSU",
        fontsize=9, color=ATLAS_COLORS["muted"], ha="right", va="top",
        style="italic",
    )

    footer = (
        "Sources: LTDB/UDP Bates Displacement Typology v2.1 (2013–2023); City of Dallas CIP vendor "
        "records FY2019–2024; Dallas TIF District increment ledgers; HUD LIHTC LIHT2024 & Subsidized "
        "Housing 2024; IRS BMF 2024; Dallas NEZ shapefile 2024; ACS 2013 & 2023 5-yr (B01003, B03002, "
        "B19013, B25003, B25077); TIGER/Line 2023 tracts, places, primary roads.\n"
        "Method: Bates v2.1 collapsed to six stages (Early Types 1+2 merged). "
        "Risk × Readiness = H4 tract-level composite (high/low median split on gentrification pressure "
        "× capacity index). Crisis quadrant = HIGH_PRESSURE_LOW_READINESS. "
        "Basemap © CartoDB / OpenStreetMap contributors."
    )
    fig.text(
        0.035, 0.018, footer,
        fontsize=7.3, color=ATLAS_COLORS["muted"],
        ha="left", va="bottom", wrap=True,
    )

    OUT_PRIMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PRIMARY, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT_MIRROR, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[v1 Map C] wrote {OUT_PRIMARY}")
    print(f"[v1 Map C] wrote {OUT_MIRROR}")


if __name__ == "__main__":
    build_figure()

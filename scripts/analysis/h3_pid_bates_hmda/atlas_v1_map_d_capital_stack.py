"""
atlas_v1_map_d_capital_stack.py
================================
Displacement Defense Atlas v1 — Map D, Five-Layer Capital Stack Composite
Dallas County, TX | Thesis: "Below the Line" | Nicholas Donovan Hawkins, TSU

v1 CHANGES VS v0
----------------
  * Layer 4 uses REAL DCAD SFR institutional-ownership share
    (data/h4_readiness/h4_tract_readiness_with_sfr.csv, `institutional_pct`),
    replacing the v0 real-gentrification/demographic-change proxy.
  * Basemap: Carto Positron tiles (muted) + Dallas city boundary
    + real I-30 geometry (TIGER 2023 primary roads).
  * Neighborhood anchor labels (Downtown, Oak Cliff, South Dallas, etc).
  * Vertical colorbars with human-readable tick formatting.
  * Left-accent-bar panel titles; figure-level typography hierarchy.
  * One scale bar + one north arrow placed on Panel A (not per panel).
  * Seventh inset (top-right of figure): horizontal bar of top-10 tracts
    by institutional SFR share with owner names.
  * Footnote split into readable source / method / caveat lines.
  * Composite palette: RdYlGn (green = stacked advantage, red = stacked
    disinvestment) — matches v0 after its post-render fix.

OUTPUTS
-------
  maps/v1/atlas_map_d_capital_stack.png             (300 DPI)
  outputs/figures/atlas_v1_map_d_capital_stack.png  (300 DPI copy)
  outputs/tables/capital_stack_inputs_v2.csv        (real-L4 inputs)
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import numpy as np
import pandas as pd

# Import shared helpers
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
CIP_PATH    = REPO_ROOT / "data" / "raw" / "layer1_investment" / "CIP_Points_All_Bonds.csv"
PID_PATH    = REPO_ROOT / "outputs" / "tables" / "pid_tract_join.csv"
H6_PATH     = REPO_ROOT / "outputs" / "tables" / "h6_bates_full_typology.csv"
SFR_PATH    = REPO_ROOT / "data"    / "h4_readiness" / "h4_tract_readiness_with_sfr.csv"
TRACT_GEO   = REPO_ROOT / "outputs" / "geojson" / "tracts_pid_join.geojson"
INPUT_PATH  = REPO_ROOT / "outputs" / "tables"  / "capital_stack_inputs_v2.csv"
OUT_PRIMARY = REPO_ROOT / "maps" / "v1" / "atlas_map_d_capital_stack.png"
OUT_MIRROR  = REPO_ROOT / "outputs" / "figures" / "atlas_v1_map_d_capital_stack.png"


# ---------------------------------------------------------------------------
# Build inputs with REAL Layer 4
# ---------------------------------------------------------------------------
def build_inputs(force: bool = False) -> pd.DataFrame:
    if INPUT_PATH.exists() and not force:
        print(f"[v1 Map D] Loading cached inputs → {INPUT_PATH.name}")
        return pd.read_csv(INPUT_PATH, dtype={"GEOID": str})

    print("[v1 Map D] Building inputs from raw sources (real L4)...")
    tracts = gpd.read_file(TRACT_GEO)
    tracts["GEOID"] = tracts["GEOID"].astype(str).str.zfill(11)
    tracts_wm = tracts.to_crs(3857)

    # --- L1 CIP spatial-join ------------------------------------------------
    cip = pd.read_csv(CIP_PATH).dropna(subset=["latitude", "longitude", "BondAmount"])
    cip_gdf = gpd.GeoDataFrame(
        cip, geometry=gpd.points_from_xy(cip["longitude"], cip["latitude"]),
        crs="EPSG:4326",
    ).to_crs(3857)
    joined = gpd.sjoin(cip_gdf, tracts_wm[["GEOID", "geometry"]],
                       predicate="within", how="left")
    l1 = joined.groupby("GEOID", dropna=True)["BondAmount"].sum() \
               .reset_index(name="cip_total_usd")

    # --- Core dataframe from H6 --------------------------------------------
    h6 = pd.read_csv(H6_PATH, dtype={"GEOID": str})
    h6["GEOID"] = h6["GEOID"].str.zfill(11)
    df = h6[[
        "GEOID", "pop_2023", "south_of_i30", "bates_typology_v21",
        "tif_present", "oz_designated", "in_pid", "vendor_share_5mi",
        "vuln_index",
    ]].merge(l1, on="GEOID", how="left")
    df["cip_total_usd"] = df["cip_total_usd"].fillna(0)
    df["cip_per_cap"] = np.where(
        df["pop_2023"] > 0, df["cip_total_usd"] / df["pop_2023"], 0
    )

    # --- L2 PID -------------------------------------------------------------
    pid = pd.read_csv(PID_PATH, dtype={"GEOID": str})
    pid["GEOID"] = pid["GEOID"].str.zfill(11)
    df = df.merge(pid[["GEOID", "pid_annual_budget"]], on="GEOID", how="left")
    df["pid_annual_budget"] = df["pid_annual_budget"].fillna(0)
    df["pid_per_cap"] = np.where(
        df["pop_2023"] > 0, df["pid_annual_budget"] / df["pop_2023"], 0
    )

    # --- L3 TIF/OZ binary ---------------------------------------------------
    df["l3_tool_any"] = ((df["tif_present"] == 1) | (df["oz_designated"] == 1)).astype(int)

    # --- L4 REAL SFR institutional share -----------------------------------
    sfr = pd.read_csv(SFR_PATH, dtype={"GEOID": str})
    sfr["GEOID"] = sfr["GEOID"].str.zfill(11)
    keep = ["GEOID", "institutional_parcel_count", "total_sfr_parcels",
            "institutional_pct", "top_owner_1", "top_owner_2", "top_owner_3"]
    df = df.merge(sfr[keep], on="GEOID", how="left")
    for c in ["institutional_parcel_count", "total_sfr_parcels", "institutional_pct"]:
        df[c] = df[c].fillna(0)

    # --- L5 vendor residue --------------------------------------------------
    df["l5_vendor_share"] = df["vendor_share_5mi"].fillna(0)

    # --- Normalize 0-1 ------------------------------------------------------
    def mm(s: pd.Series) -> pd.Series:
        lo, hi = s.min(), s.max()
        return (s - lo) / (hi - lo) if hi > lo else s * 0

    df["L1_cip_norm"]  = mm(df["cip_per_cap"].clip(upper=df["cip_per_cap"].quantile(0.99)))
    df["L2_pid_norm"]  = mm(df["pid_per_cap"].clip(upper=df["pid_per_cap"].quantile(0.99)))
    df["L3_tool_norm"] = df["l3_tool_any"].astype(float)
    df["L4_sfr_norm"]  = mm(df["institutional_pct"].clip(
        upper=df["institutional_pct"].quantile(0.99)))
    df["L5_vendor_norm"] = mm(df["l5_vendor_share"].clip(
        upper=df["l5_vendor_share"].quantile(0.99)))

    df["capital_stack_score"] = df[[
        "L1_cip_norm", "L2_pid_norm", "L3_tool_norm",
        "L4_sfr_norm", "L5_vendor_norm",
    ]].mean(axis=1)

    INPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(INPUT_PATH, index=False)
    print(f"[v1 Map D] Saved inputs → {INPUT_PATH.relative_to(REPO_ROOT)}")
    return df


# ---------------------------------------------------------------------------
# Panel renderer with vertical colorbar
# ---------------------------------------------------------------------------
def render_continuous_panel(ax, gdf_wm, layers, *, value_col, cmap, vmin, vmax,
                            letter, title, subtitle,
                            cbar_label, cbar_fmt="{:.2f}",
                            show_scale=False,
                            highlight_quartile=False,
                            dark_background=False):
    """Plot a continuous choropleth with basemap, overlays, labels, and colorbar."""
    # 1. Basemap tiles
    add_contextily_basemap(ax, zoom=11, provider="positron", alpha=0.65)

    # 2. Choropleth
    gdf_wm.plot(
        ax=ax, column=value_col, cmap=cmap, vmin=vmin, vmax=vmax,
        linewidth=0.15, edgecolor="#ffffff", alpha=0.80, zorder=6,
    )

    # 3. Overlays (city, I-30) and framing
    add_reference_overlay(ax, layers, show_city=True, show_i30=True,
                          label_i30=show_scale)  # label only on the reference panel
    frame_to_dallas_county(ax, layers["tracts"])

    # 4. Sparse neighborhood labels — only 4 anchor places to avoid clutter
    add_neighborhood_labels(
        ax, fontsize=7.5,
        subset={"Downtown", "Oak Cliff", "South Dallas",
                "Pleasant Grove"},
        strong_halo=dark_background,
    )

    # 5. Title block
    add_accent_title(ax, letter, title, subtitle)

    # 6. Inset vertical colorbar on the right inside-of-axes
    sm = ScalarMappable(norm=Normalize(vmin=vmin, vmax=vmax), cmap=cmap)
    sm.set_array([])
    cbar_ax = ax.inset_axes([1.01, 0.08, 0.025, 0.55])
    cb = plt.colorbar(sm, cax=cbar_ax, orientation="vertical")
    cb.ax.tick_params(labelsize=6.5, length=2)
    cb.set_label(cbar_label, fontsize=7, labelpad=4)
    cb.outline.set_linewidth(0.4)
    # Format ticks
    ticks = np.linspace(vmin, vmax, 5)
    cb.set_ticks(ticks)
    cb.set_ticklabels([cbar_fmt.format(t) for t in ticks])

    if show_scale:
        add_scale_and_north(ax, scale_km=5, anchor="lower left")


def render_categorical_panel(ax, gdf_wm, layers, *, value_col, present_color,
                             letter, title, subtitle):
    """TIF/OZ binary — a clean two-category panel."""
    add_contextily_basemap(ax, zoom=11, provider="positron", alpha=0.65)
    absent = gdf_wm[gdf_wm[value_col] == 0]
    present = gdf_wm[gdf_wm[value_col] == 1]
    absent.plot(ax=ax, facecolor="#f2f2f2", edgecolor="#ffffff",
                linewidth=0.15, alpha=0.55, zorder=6)
    present.plot(ax=ax, facecolor=present_color, edgecolor="#ffffff",
                 linewidth=0.2, alpha=0.85, zorder=7)
    add_reference_overlay(ax, layers, show_city=True, show_i30=True, label_i30=False)
    frame_to_dallas_county(ax, layers["tracts"])
    add_neighborhood_labels(
        ax, fontsize=7.5,
        subset={"Downtown", "Oak Cliff", "South Dallas",
                "Pleasant Grove"},
    )
    add_accent_title(ax, letter, title, subtitle)
    # Simple legend
    n_present = int((gdf_wm[value_col] == 1).sum())
    handles = [
        mpatches.Patch(facecolor=present_color, edgecolor="white", label=f"Present  (n={n_present})"),
        mpatches.Patch(facecolor="#f2f2f2", edgecolor="white", label=f"Absent  (n={len(gdf_wm)-n_present})"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=7,
              frameon=True, framealpha=0.9, edgecolor="#ccc")


# ---------------------------------------------------------------------------
# Figure assembly
# ---------------------------------------------------------------------------
def build_figure() -> None:
    df = build_inputs(force=True)
    layers = load_basemap_layers()
    tracts_geo = layers["tracts"]
    tracts_geo["GEOID"] = tracts_geo["GEOID"].astype(str).str.zfill(11)
    gdf = tracts_geo.merge(df, on="GEOID", how="left")

    # Fill nans so plotting doesn't crash on missing tracts
    for c in ["L1_cip_norm", "L2_pid_norm", "L3_tool_norm",
              "L4_sfr_norm", "L5_vendor_norm", "capital_stack_score",
              "l3_tool_any", "institutional_pct", "cip_per_cap",
              "pid_per_cap", "l5_vendor_share"]:
        if c in gdf.columns:
            gdf[c] = gdf[c].fillna(0)

    # Diagnostic
    bot_q = gdf[gdf["capital_stack_score"] <= gdf["capital_stack_score"].quantile(0.25)]
    south_share = (bot_q["south_of_i30"] == 1).mean() * 100
    south_baseline = (gdf["south_of_i30"] == 1).mean() * 100
    print(f"[v1 Map D] bottom-quartile south share: {south_share:.1f}% "
          f"(vs {south_baseline:.1f}% baseline)")
    print(f"[v1 Map D] L4 inst pct: mean={gdf['institutional_pct'].mean():.2f}, "
          f"p95={gdf['institutional_pct'].quantile(0.95):.2f}, "
          f"max={gdf['institutional_pct'].max():.2f}")

    # ---- Figure -----------------------------------------------------------
    fig = plt.figure(figsize=(18.0, 14.0), dpi=150, facecolor="white")

    # 2 × 3 grid for map panels (top 80% of figure), inset bar at bottom
    gs = fig.add_gridspec(
        nrows=3, ncols=3,
        height_ratios=[1.0, 1.0, 0.32],
        hspace=0.30, wspace=0.12,
        left=0.035, right=0.965, top=0.905, bottom=0.065,
    )

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[0, 2])
    ax_d = fig.add_subplot(gs[1, 0])
    ax_e = fig.add_subplot(gs[1, 1])
    ax_f = fig.add_subplot(gs[1, 2])
    ax_bar = fig.add_subplot(gs[2, :])

    # --- Panel A — L1 CIP per cap -----------------------------------------
    render_continuous_panel(
        ax_a, gdf, layers,
        value_col="cip_per_cap", cmap="Greens",
        vmin=0, vmax=gdf["cip_per_cap"].quantile(0.95),
        letter="A.", title="Layer 1 — CIP Per Capita",
        subtitle="Public investment base · FY2012–present bond projects spatial-joined",
        cbar_label="$ / person", cbar_fmt="${:,.0f}",
        show_scale=True,
    )

    # --- Panel B — L2 PID per cap -----------------------------------------
    render_continuous_panel(
        ax_b, gdf, layers,
        value_col="pid_per_cap", cmap="Purples",
        vmin=0, vmax=gdf["pid_per_cap"].quantile(0.99),
        letter="B.", title="Layer 2 — PID Per Capita",
        subtitle="Private supplementation · 33× gap documented in v5 theory",
        cbar_label="$ / person", cbar_fmt="${:,.0f}",
    )

    # --- Panel C — L3 TIF/OZ presence (categorical) -----------------------
    render_categorical_panel(
        ax_c, gdf, layers,
        value_col="l3_tool_any", present_color="#3182bd",
        letter="C.", title="Layer 3 — TIF / Opportunity Zone Presence",
        subtitle="Financial engineering toolkit · binary presence (any tool)",
    )

    # --- Panel D — L4 REAL SFR share --------------------------------------
    render_continuous_panel(
        ax_d, gdf, layers,
        value_col="institutional_pct", cmap="Oranges",
        vmin=0, vmax=gdf["institutional_pct"].quantile(0.95),
        letter="D.", title="Layer 4 — Institutional SFR Share",
        subtitle="DCAD 2025 · share of SFR parcels held by institutional owners",
        cbar_label="% institutional", cbar_fmt="{:.0f}%",
        dark_background=True,
    )

    # --- Panel E — L5 vendor residue --------------------------------------
    render_continuous_panel(
        ax_e, gdf, layers,
        value_col="l5_vendor_share", cmap="Reds",
        vmin=0, vmax=gdf["l5_vendor_share"].quantile(0.99),
        letter="E.", title="Layer 5 — Vendor Residue (5-mi share)",
        subtitle="Where public contracting dollars land · 12.6× gap documented",
        cbar_label="share", cbar_fmt="{:.2f}",
        dark_background=True,
    )

    # --- Panel F — Composite (RdYlGn: green=advantage, red=disinvestment)-
    render_continuous_panel(
        ax_f, gdf, layers,
        value_col="capital_stack_score", cmap="RdYlGn",
        vmin=0, vmax=gdf["capital_stack_score"].quantile(0.98),
        letter="F.", title="Capital Stack Composite  (mean of A–E)",
        subtitle="High = stacked advantage · Low = stacked disinvestment",
        cbar_label="composite score", cbar_fmt="{:.2f}",
        dark_background=True,
    )

    # Add a small in-panel annotation card with the headline stat on Panel F
    stat_text = (
        f"{south_share:.0f}% of bottom-quartile tracts\n"
        f"sit south of I-30  (vs {south_baseline:.0f}% baseline)"
    )
    ax_f.text(
        0.03, 0.04, stat_text,
        transform=ax_f.transAxes, fontsize=7.8, fontweight="semibold",
        color=ATLAS_COLORS["ink"],
        bbox=dict(facecolor="white", edgecolor=ATLAS_COLORS["thesis_red"],
                  linewidth=1.0, boxstyle="round,pad=0.35"),
        zorder=12,
    )

    # --- Inset bar chart: top-10 tracts by institutional share ------------
    # Filter to tracts with meaningful SFR inventories (avoid <5 parcel outliers)
    top = gdf[gdf["total_sfr_parcels"] >= 100].nlargest(10, "institutional_pct").copy()
    top["label"] = top.apply(
        lambda r: f"Tract {str(r['GEOID'])[-6:-2]} · {str(r.get('top_owner_1') or '').title()[:32]}",
        axis=1,
    )
    top = top.iloc[::-1]  # reverse so largest is at top visually
    y_pos = np.arange(len(top))
    # Gradient color — reusing the Layer 4 Oranges ramp
    max_val = top["institutional_pct"].max()
    norm = Normalize(vmin=0, vmax=max_val)
    colors = plt.cm.Oranges(norm(top["institutional_pct"]) * 0.6 + 0.35)
    ax_bar.barh(y_pos, top["institutional_pct"], color=colors, edgecolor="#666",
                linewidth=0.5, height=0.7)
    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels(top["label"], fontsize=9)
    ax_bar.set_xlabel("% of single-family-residential parcels held by institutional owners",
                      fontsize=10, labelpad=6)
    ax_bar.spines["top"].set_visible(False)
    ax_bar.spines["right"].set_visible(False)
    ax_bar.tick_params(axis="x", labelsize=9)
    ax_bar.grid(axis="x", linestyle=":", linewidth=0.5, color="#bbb", alpha=0.7)
    ax_bar.set_axisbelow(True)
    # Value labels — smart placement: inside bar (white) when bar is long enough,
    # outside bar (dark) when bar is short
    for i, v in enumerate(top["institutional_pct"]):
        if v >= max_val * 0.80:
            # inside the bar on the right edge, white text for contrast
            ax_bar.text(v - max_val * 0.01, i, f"{v:.1f}%",
                        va="center", ha="right", fontsize=9,
                        color="white", fontweight="bold",
                        path_effects=[pe.withStroke(linewidth=1.4, foreground="#7a3a00")])
        else:
            ax_bar.text(v + max_val * 0.015, i, f"{v:.1f}%",
                        va="center", ha="left", fontsize=9,
                        color="#333", fontweight="semibold")
    ax_bar.set_xlim(0, max_val * 1.15)
    ax_bar.text(
        0.0, 1.12,
        "G.",
        transform=ax_bar.transAxes, fontsize=12, fontweight="bold",
        color=ATLAS_COLORS["thesis_red"], ha="left",
    )
    ax_bar.text(
        0.015, 1.12,
        "Top-10 Tracts by Institutional SFR Share",
        transform=ax_bar.transAxes, fontsize=12, fontweight="bold",
        color=ATLAS_COLORS["ink"], ha="left",
    )
    ax_bar.text(
        0.0, 1.02,
        "Tracts with ≥100 SFR parcels · top institutional owner shown per tract",
        transform=ax_bar.transAxes, fontsize=8.5,
        color=ATLAS_COLORS["muted"], ha="left", style="italic",
    )

    # --- Figure title + subtitle + footer ---------------------------------
    fig.text(
        0.035, 0.965,
        "The Five-Layer Capital Stack",
        fontsize=22, fontweight="bold", color=ATLAS_COLORS["ink"],
    )
    fig.text(
        0.035, 0.938,
        "Dallas County Census Tracts  ·  2013–2025  ·  "
        "How five capital-stack layers compound across the I-30 line",
        fontsize=11.5, color=ATLAS_COLORS["muted"], style="italic",
    )
    fig.text(
        0.965, 0.968, "Map D  ·  v1",
        fontsize=11, fontweight="bold", color=ATLAS_COLORS["thesis_red"],
        ha="right", va="top",
    )
    fig.text(
        0.965, 0.945, "Below the Line  ·  Hawkins 2027, TSU",
        fontsize=9, color=ATLAS_COLORS["muted"], ha="right", va="top",
        style="italic",
    )

    footer = (
        "Sources: City of Dallas CIP FY2012–present bond points; Dallas OED PID boundaries & 2024 budgets; "
        "2025 Dallas TIF Annual Report; CDFI Fund OZ designations; DCAD 2025 SFR appraisal; "
        "Dallas Vendor Payments FY2019–present (top-18 vendors, 5-mi buffer); ACS 2023 5-yr; "
        "TIGER/Line 2023 (roads, places); LTDB/UDP Bates Typology v2.1.\n"
        "Method: Each layer min-max normalized (winsorized at 99th pctile); composite = mean of 5 layer norms. "
        "Panel D uses DCAD owner-string regex + ≥10-parcel-portfolio threshold to flag institutional holders. "
        "Basemap © CartoDB / OpenStreetMap contributors."
    )
    fig.text(
        0.035, 0.018, footer,
        fontsize=7.2, color=ATLAS_COLORS["muted"],
        ha="left", va="bottom", wrap=True,
    )

    OUT_PRIMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PRIMARY, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT_MIRROR, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[v1 Map D] wrote {OUT_PRIMARY}")
    print(f"[v1 Map D] wrote {OUT_MIRROR}")


if __name__ == "__main__":
    build_figure()

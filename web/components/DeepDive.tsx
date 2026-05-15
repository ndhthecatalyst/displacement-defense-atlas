"use client";

import { useState } from "react";
import { FACTS } from "@/lib/facts";

type Embed = {
  id: string;
  src: string;
  title: string;
  layer: string;
  blurb: React.ReactNode;
  notes: string[];
};

const EMBEDS: Embed[] = [
  {
    id: "composite",
    src: "/maps/v1/00_capital_stack_composite_v1.html",
    title: "Capital-stack composite — full v1 atlas",
    layer: "All five layers",
    blurb: (
      <>
        The full v1 composite as it appears in the working thesis atlas — every
        layer toggleable, panned and zoomed independently. Heavy file (10 MB);
        give it a moment to load.
      </>
    ),
    notes: [
      "645 Dallas County tracts, TIGER 2020.",
      "Composite weighting derives from H1–H4 analysis pipeline (see /scripts/analysis).",
      "Generated from Folium; same engine as the working chapter figures.",
    ],
  },
  {
    id: "cip",
    src: "/maps/v1/01_cip_investment_per_capita_v1.html",
    title: "Layer 1 — CIP investment per capita",
    layer: `Layer 1 · ${FACTS.L1_TOTAL_FY2012_2026}`,
    blurb: (
      <>
        Per-capita Capital Improvement Program allocation by tract. The OLS
        regression behind H1 yields a HOLC-D coefficient of{" "}
        <span className="font-mono text-yellow-300">{FACTS.H1_HOLC_D_BETA}</span>{" "}
        once income and infrastructure controls are added — the 1937 line
        explains the 2025 budget better than current race or income.
      </>
    ),
    notes: [
      "ACS 2018–2023 5-yr population denominator.",
      "CIP series: FY2012, 2017, 2024 bond programs + annual capital plans.",
    ],
  },
  {
    id: "tif",
    src: "/maps/v1/02_tif_oz_tool_density_v1.html",
    title: "Layer 3 — TIF + Opportunity Zone overlay",
    layer: `Layer 3 · ${FACTS.L3_RATIO} ratio`,
    blurb: (
      <>
        TIF subdistrict boundaries (Dallas GIS Hub) layered over Treasury
        Opportunity Zone designations. Of{" "}
        <span className="font-mono text-yellow-300">{FACTS.H4_SUSCEPTIBLE_SOUTH_TRACTS}</span>{" "}
        tracts that the Bates/UDP typology classifies as Susceptible South,{" "}
        <span className="font-mono text-yellow-300">{FACTS.H4_WITH_TIF_OZ}</span>{" "}
        have received either tool.
      </>
    ),
    notes: [
      "TIF lifetime increment values flagged as pending re-derivation per docs/audit/2026-04-26_layer3_audit.md.",
      "OZ source: HUD Open Data layer ef143299845841f8abb95969c01f88b5_13, cross-checked against IRS Notice 2018-48.",
    ],
  },
  {
    id: "vendor",
    src: "/maps/v1/03_vendor_geocode_residue_v1.html",
    title: "Layer 5 — Vendor residue geocoded",
    layer: `Layer 5 · ${FACTS.L5_GAP_MULTIPLIER}`,
    blurb: (
      <>
        Top-18 City of Dallas vendors plotted at their headquarters ZIP
        centroids and sized by total payments received. Of every public dollar
        spent in Dallas,{" "}
        <span className="font-mono text-yellow-300">{FACTS.L5_NORTH_SHARE}</span>{" "}
        flows to vendors HQ'd north of I-30 vs.{" "}
        <span className="font-mono text-yellow-300">{FACTS.L5_SOUTH_SHARE}</span>{" "}
        to those HQ'd south.
      </>
    ),
    notes: [
      "145,551 payment rows (FY2019–present), 8,354 unique vendors geocoded to ZIP5.",
      "Texas Materials Group alone — owned by Irish parent CRH plc — captures " +
        FACTS.H5_TEXAS_MATERIALS_TOTAL +
        " (" +
        FACTS.H5_TEXAS_MATERIALS_CRH_SHARE +
        " of every top-vendor dollar).",
    ],
  },
  {
    id: "sfr",
    src: "/maps/v1/04_institutional_sfr_ownership_v1.html",
    title: "Layer 4 — Institutional single-family rental ownership",
    layer: `Layer 4 · ${FACTS.L4_DFW_MEGA_INVESTOR_UNITS} units`,
    blurb: (
      <>
        Mega-investor SFR holdings across DFW, derived from CoreLogic / ATTOM
        ownership records. The DFW metro contains{" "}
        <span className="font-mono text-yellow-300">{FACTS.L4_DFW_MEGA_INVESTOR_UNITS}</span>{" "}
        institutional SFR units — concentrated at three times the national
        average inside majority-Black neighborhoods.
      </>
    ),
    notes: [
      "Sources: Immergluck et al.; CoreLogic / ATTOM / PropStream ownership records.",
      "Institutional defined as portfolios ≥ 100 SFR units under common LLC ownership.",
    ],
  },
];

export default function DeepDive() {
  const [active, setActive] = useState<string | null>(null);

  return (
    <section className="border-t border-white/10 bg-ink px-6 sm:px-12 py-20">
      <div className="mx-auto max-w-6xl">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-yellow-300/80">
          Deep dive · v1 atlas
        </div>
        <h2 className="mt-3 serif text-3xl sm:text-5xl leading-tight">
          Open the working chapter maps.
        </h2>
        <p className="mt-3 max-w-2xl text-white/70">
          Each card opens the full Folium map used in the working thesis atlas
          — pan, zoom, toggle layers, click any tract for the underlying
          attributes. These are the same artifacts feeding the chapters of{" "}
          <em>Below the Line</em>; they are heavier than the scrolling story
          map above and load on demand.
        </p>

        <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {EMBEDS.map((e) => (
            <button
              key={e.id}
              onClick={() => setActive(e.id)}
              className="group text-left rounded-lg border border-white/10 bg-white/[0.03] p-5 hover:border-yellow-300/40 hover:bg-white/[0.06] transition"
            >
              <div className="font-mono text-[10px] uppercase tracking-wider text-yellow-300/80">
                {e.layer}
              </div>
              <div className="mt-2 serif text-xl leading-tight">{e.title}</div>
              <div className="mt-2 text-sm text-white/70">{e.blurb}</div>
              <div className="mt-3 inline-flex items-center gap-2 text-xs text-yellow-300 group-hover:translate-x-0.5 transition-transform">
                Open map →
              </div>
            </button>
          ))}
        </div>
      </div>

      {active && (
        <Modal embed={EMBEDS.find((e) => e.id === active)!} onClose={() => setActive(null)} />
      )}
    </section>
  );
}

function Modal({ embed, onClose }: { embed: Embed; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-3 sm:p-6"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-6xl h-[90vh] rounded-lg overflow-hidden bg-[#111] border border-white/10 shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 px-5 py-3 border-b border-white/10">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-wider text-yellow-300/80">
              {embed.layer}
            </div>
            <div className="serif text-lg text-white">{embed.title}</div>
          </div>
          <div className="flex items-center gap-3">
            <a
              href={embed.src}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-white/60 hover:text-yellow-300"
            >
              Open in new tab ↗
            </a>
            <button
              onClick={onClose}
              className="rounded-md border border-white/15 px-3 py-1 text-sm text-white/80 hover:bg-white/10"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
        </div>
        <iframe
          src={embed.src}
          className="flex-1 w-full bg-white"
          title={embed.title}
          loading="lazy"
        />
        {embed.notes.length > 0 && (
          <div className="border-t border-white/10 px-5 py-2 text-[11px] text-white/55">
            {embed.notes.map((n, i) => (
              <div key={i}>· {n}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

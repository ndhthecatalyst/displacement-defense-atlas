"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { Scrollama, Step } from "react-scrollama";
import { LayerKey } from "@/lib/layers";
import { FACTS } from "@/lib/facts";

const AtlasMap = dynamic(() => import("./AtlasMap"), { ssr: false });

type StepSpec = {
  id: string;
  layer: LayerKey;
  zoom: "county" | "south" | "downtown";
  eyebrow: string;
  title: string;
  body: React.ReactNode;
  stat?: { value: string; label: string };
};

const STEPS: StepSpec[] = [
  {
    id: "open",
    layer: "vulnerability",
    zoom: "county",
    eyebrow: "Dallas County · 645 census tracts",
    title: "Money is a map.",
    body: (
      <>
        <p>
          Every public dollar spent in Dallas leaves a trace — a procurement
          record, a TIF increment, a tax exemption, a vendor's home address.
          Stack those traces and a shape appears: a city sliced along the
          Interstate 30 corridor.
        </p>
        <p className="mt-3 text-white/70">
          The yellow dashes mark I-30. The orange-red shading is the share of
          residents who are not white. Hover any tract.
        </p>
      </>
    ),
  },
  {
    id: "cip",
    layer: "cip",
    zoom: "county",
    eyebrow: "Layer 1 · Capital Improvement Program",
    title: "$984M of public capital — but where does it land?",
    body: (
      <>
        <p>
          Dallas budgeted{" "}
          <span className="text-yellow-300 font-mono">{FACTS.L1_TOTAL_FY2012_2026}</span>{" "}
          in capital improvements between FY2012 and FY2026. Once you control
          for income and infrastructure need, tracts that the federal HOLC
          maps redlined in 1937 still receive{" "}
          <span className="text-yellow-300 font-mono">{FACTS.H1_HOLC_D_BETA}</span>{" "}
          dollars per capita more — not because they are wealthier, but
          because the discretionary categories (parks, libraries, economic
          development) skew north.
        </p>
        <p className="mt-3 text-white/70">
          Race becomes statistically insignificant once HOLC grade is
          included. The 1937 line still draws today's budget.
        </p>
      </>
    ),
    stat: { value: FACTS.L1_TOTAL_FY2012_2026, label: "CIP, FY2012–2026" },
  },
  {
    id: "tif_oz",
    layer: "tif_oz",
    zoom: "downtown",
    eyebrow: "Layer 3 · TIF + Opportunity Zones",
    title: "Tools that recapture value — for somewhere else.",
    body: (
      <>
        <p>
          Tax-Increment Finance and the federal Opportunity Zone program were
          sold as instruments to redirect capital to disinvested places.
          In Dallas the lifetime increment captured by Downtown TIFs is{" "}
          <span className="text-yellow-300 font-mono">{FACTS.L3_DOWNTOWN_TIF}</span>{" "}
          versus{" "}
          <span className="text-yellow-300 font-mono">{FACTS.L3_GRAND_PARK_SOUTH_TIF}</span>{" "}
          in Grand Park South — a{" "}
          <span className="text-yellow-300 font-mono">{FACTS.L3_RATIO}</span> ratio.
        </p>
        <p className="mt-3 text-white/70">
          Purple = TIF district. Cyan = Opportunity Zone. Of{" "}
          <span className="text-yellow-300 font-mono">{FACTS.H4_SUSCEPTIBLE_SOUTH_TRACTS}</span>{" "}
          Susceptible South tracts,{" "}
          <span className="text-yellow-300 font-mono">{FACTS.H4_WITH_TIF_OZ}</span>{" "}
          have received either tool.
        </p>
      </>
    ),
    stat: { value: FACTS.L3_RATIO, label: "Downtown : Grand Park South TIF" },
  },
  {
    id: "vendor",
    layer: "vendor",
    zoom: "county",
    eyebrow: "Layer 5 · Vendor residue",
    title: "Where does the money go after it's spent?",
    body: (
      <>
        <p>
          We geocoded 145,551 City of Dallas vendor payment rows. Of the
          top-18 vendors,{" "}
          <span className="text-yellow-300 font-mono">{FACTS.L5_NORTH_TOTAL}</span>{" "}
          ({FACTS.L5_NORTH_SHARE}) flowed to firms headquartered north of
          I-30, versus{" "}
          <span className="text-yellow-300 font-mono">{FACTS.L5_SOUTH_TOTAL}</span>{" "}
          ({FACTS.L5_SOUTH_SHARE}) to firms south of it — a{" "}
          <span className="text-yellow-300 font-mono">{FACTS.L5_GAP_MULTIPLIER}</span>{" "}
          extraction gap.
        </p>
        <p className="mt-3 text-white/70">
          83% of every dollar Dallas spends building South Dallas is
          extracted northward in the form of contractor payments.{" "}
          <span className="text-yellow-300 font-mono">{FACTS.H5_TEXAS_MATERIALS_CRH_SHARE}</span>{" "}
          of every top-vendor dollar (
          <span className="text-yellow-300 font-mono">{FACTS.H5_TEXAS_MATERIALS_TOTAL}</span>
          ) flows to a subsidiary of an Irish parent corporation.
        </p>
      </>
    ),
    stat: { value: FACTS.L5_GAP_MULTIPLIER, label: "North : South vendor capture" },
  },
  {
    id: "readiness",
    layer: "readiness",
    zoom: "south",
    eyebrow: "H4 · Defense readiness gap",
    title: "Where the pressure is highest, the defense is thinnest.",
    body: (
      <>
        <p>
          Readiness is the inventory of LIHTC units, HUD-assisted housing,
          NEZ designation, and community organizations that could
          intervene when displacement pressure rises.{" "}
          <span className="text-yellow-300 font-mono">{FACTS.H4_HIGH_PRESSURE_LOW_READINESS}</span>{" "}
          tracts sit in the worst quadrant: high pressure, low readiness.
        </p>
        <p className="mt-3 text-white/70">
          <span className="text-yellow-300 font-mono">{FACTS.H4_IMMEDIATE_PRIORITY}</span>{" "}
          are immediate priority — readiness scores at or below 0.028.
          Red = no defense. Cream = defense exists.
        </p>
      </>
    ),
    stat: { value: FACTS.H4_HIGH_PRESSURE_LOW_READINESS, label: "high-pressure / low-readiness tracts" },
  },
  {
    id: "stack",
    layer: "stack",
    zoom: "county",
    eyebrow: "All five layers, stacked",
    title: "This is what \"investability\" looks like.",
    body: (
      <>
        <p>
          The composite combines pressure (renter share), vulnerability
          (race), and the defense gap (1 − readiness). It is not a forecast.
          It is a portrait of a governance design — a city in which capital
          returns are routed away from majority-Black and Hispanic communities
          south of I-30 not by any single discriminatory policy, but by the
          stacking of five legitimate-looking instruments.
        </p>
        <p className="mt-3 text-white/70">
          Displacement here is not a market failure. It is the working
          output of an architecture.
        </p>
      </>
    ),
  },
];

export default function Story() {
  const [active, setActive] = useState(0);
  const cur = STEPS[active];
  return (
    <div className="relative">
      {/* Sticky map */}
      <div className="sticky top-0 z-0 h-screen w-full">
        <AtlasMap layer={cur.layer} zoomTarget={cur.zoom} />
        {cur.stat && (
          <div className="pointer-events-none absolute right-4 top-4 z-10 rounded-lg border border-white/10 bg-black/70 px-4 py-3 text-right">
            <div className="font-mono text-3xl text-yellow-300">{cur.stat.value}</div>
            <div className="text-[11px] uppercase tracking-wider text-white/60">
              {cur.stat.label}
            </div>
          </div>
        )}
      </div>

      {/* Scroll steps overlaid */}
      <div className="relative z-10 -mt-screen">
        <Scrollama offset={0.55} onStepEnter={({ data }) => setActive(data as number)}>
          {STEPS.map((s, i) => (
            <Step key={s.id} data={i}>
              <section className="min-h-screen flex items-center pointer-events-none">
                <div className="pointer-events-auto ml-4 sm:ml-10 mt-[20vh] mb-[20vh] max-w-md rounded-lg border border-white/10 bg-black/80 backdrop-blur p-5 sm:p-6 shadow-2xl">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-yellow-300/80">
                    {s.eyebrow}
                  </div>
                  <h2 className="mt-2 serif text-2xl sm:text-3xl leading-tight text-white">
                    {s.title}
                  </h2>
                  <div className="mt-3 text-[14px] leading-relaxed text-white/85">
                    {s.body}
                  </div>
                </div>
              </section>
            </Step>
          ))}
        </Scrollama>
      </div>
    </div>
  );
}

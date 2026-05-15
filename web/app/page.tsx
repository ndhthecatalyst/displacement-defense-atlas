import Story from "@/components/Story";
import CityExplorer from "@/components/CityExplorer";
import DeepDive from "@/components/DeepDive";
import { FACTS } from "@/lib/facts";

export default function Home() {
  return (
    <main className="bg-ink text-cream">
      {/* Hero */}
      <section className="relative flex min-h-screen flex-col justify-end px-6 sm:px-12 pb-16 pt-28">
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-[#1a0d05] via-[#0a0a0a] to-[#0a0a0a]" />
        <div className="absolute inset-0 -z-10 opacity-40 [background-image:radial-gradient(rgba(255,200,100,0.18)_1px,transparent_1px)] [background-size:14px_14px]" />
        <div className="max-w-4xl">
          <div className="font-mono text-xs uppercase tracking-[0.25em] text-yellow-300/80">
            Displacement Defense Atlas · v0
          </div>
          <h1 className="mt-4 serif text-5xl sm:text-7xl leading-[1.02] tracking-tight">
            Below the Line.
          </h1>
          <p className="mt-3 serif text-2xl sm:text-3xl text-white/80 leading-tight">
            How money shapes power in Dallas — and the five-layer capital
            stack that decides who gets to stay.
          </p>
          <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl">
            <Stat value={FACTS.L2_GAP_MULTIPLIER} label="PID assessment gap, downtown vs South" />
            <Stat value={FACTS.L3_RATIO} label="TIF capture ratio, Downtown vs Grand Park South" />
            <Stat value={FACTS.L5_GAP_MULTIPLIER} label="Vendor extraction gap, North vs South" />
            <Stat value={FACTS.H4_HIGH_PRESSURE_LOW_READINESS} label="Tracts with high pressure & no defense" />
          </div>
          <div className="mt-10 inline-flex items-center gap-2 text-sm text-white/60">
            <span>Scroll</span>
            <span className="inline-block h-px w-10 bg-white/40" />
            <span>or use the map below</span>
          </div>
        </div>
      </section>

      {/* Scrollytelling */}
      <Story />

      {/* City lookup — pick any municipality and see its tracts aggregated */}
      <CityExplorer />

      {/* Deep dive — Folium v1 atlas embeds */}
      <DeepDive />

      {/* Footer */}
      <footer className="border-t border-white/10 px-6 sm:px-12 py-12 text-sm text-white/60">
        <div className="max-w-4xl space-y-3">
          <div className="serif text-2xl text-white/90">
            About this atlas
          </div>
          <p>
            <em>Below the Line: Development as Governance and the Geography of
            Displacement Risk in Dallas</em>. Undergraduate thesis by Nicholas
            Donovan Hawkins, Texas Southern University (defense Dec 2027).
            Architecture v5 — Five-Layer Capital Stack.
          </p>
          <p>
            All numeric claims trace to{" "}
            <code className="text-yellow-300">docs/FACTS.md</code> in the
            project repository, which is the canonical source of truth and is
            CI-enforced against drift in downstream documents.
          </p>
          <p className="text-white/50">
            Geometry: TIGER 2020 (Dallas County, FIPS 48113). Indicators:
            ACS 2018–2023 5-yr, HMDA 2022–23, Dallas Open Data vendor
            payments (145,551 rows), HOLC Mapping Inequality, Dallas County
            2025 TIF Annual Report, HUD Picture of Subsidized Households,
            LIHTC. Map basemap © OpenStreetMap contributors, © CARTO.
          </p>
          <p className="pt-4 font-mono text-xs text-white/40">
            For research and educational use only. Hawkins (2027).
          </p>
        </div>
      </footer>
    </main>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3">
      <div className="font-mono text-2xl text-yellow-300">{value}</div>
      <div className="mt-1 text-[11px] uppercase tracking-wider text-white/60 leading-snug">
        {label}
      </div>
    </div>
  );
}

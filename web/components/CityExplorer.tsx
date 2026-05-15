"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { LAYERS, LayerKey } from "@/lib/layers";
import { bboxOfFeature, centroidOf, pointInGeometry, BBox } from "@/lib/geo";

const AtlasMap = dynamic(() => import("./AtlasMap"), { ssr: false });

type NominatimHit = {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
  type: string;
  class: string;
  importance: number;
  geojson?: GeoJSON.Geometry;
  boundingbox?: [string, string, string, string];
};

const SUGGESTIONS = [
  "Dallas",
  "Garland",
  "Mesquite",
  "Irving",
  "Richardson",
  "Carrollton",
  "DeSoto",
  "Lancaster",
  "Cedar Hill",
  "Duncanville",
  "Grand Prairie",
];

const LAYER_OPTIONS: LayerKey[] = [
  "vulnerability",
  "cip",
  "tif_oz",
  "vendor",
  "readiness",
  "stack",
];

type Stats = {
  count: number;
  population: number;
  southShare: number;
  pctNonwhite: number;
  medianIncome: number;
  pctRenter: number;
  readiness: number;
  cipPerCap: number;
  tifCount: number;
  ozCount: number;
  highPressureLowReadiness: number;
};

const EMPTY: Stats = {
  count: 0,
  population: 0,
  southShare: 0,
  pctNonwhite: 0,
  medianIncome: 0,
  pctRenter: 0,
  readiness: 0,
  cipPerCap: 0,
  tifCount: 0,
  ozCount: 0,
  highPressureLowReadiness: 0,
};

export default function CityExplorer() {
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [hits, setHits] = useState<NominatimHit[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [boundary, setBoundary] = useState<GeoJSON.Feature | null>(null);
  const [bbox, setBbox] = useState<BBox | null>(null);
  const [cityName, setCityName] = useState<string | null>(null);
  const [layer, setLayer] = useState<LayerKey>("stack");
  const [tracts, setTracts] = useState<GeoJSON.Feature[]>([]);
  const debounceRef = useRef<number | null>(null);

  // Debounced search against Nominatim
  useEffect(() => {
    if (!query || query.length < 2) {
      setHits([]);
      return;
    }
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(async () => {
      setBusy(true);
      setError(null);
      try {
        const url = new URL("https://nominatim.openstreetmap.org/search");
        url.searchParams.set("q", `${query}, Texas, USA`);
        url.searchParams.set("format", "json");
        url.searchParams.set("polygon_geojson", "1");
        url.searchParams.set("addressdetails", "1");
        url.searchParams.set("limit", "6");
        const res = await fetch(url.toString(), {
          headers: { "Accept-Language": "en-US,en" },
        });
        if (!res.ok) throw new Error(`Search failed (${res.status})`);
        const json: NominatimHit[] = await res.json();
        // Keep only city-like results with a real polygon
        const filtered = json.filter(
          (h) =>
            h.geojson &&
            (h.geojson.type === "Polygon" || h.geojson.type === "MultiPolygon")
        );
        setHits(filtered);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Search failed");
      } finally {
        setBusy(false);
      }
    }, 300);
  }, [query]);

  function selectHit(h: NominatimHit) {
    if (!h.geojson) return;
    const feature: GeoJSON.Feature = {
      type: "Feature",
      properties: { name: h.display_name },
      geometry: h.geojson,
    };
    setBoundary(feature);
    setBbox(bboxOfFeature(feature));
    setCityName(prettyCity(h.display_name));
    setHits([]);
    setQuery(prettyCity(h.display_name));
  }

  function clear() {
    setBoundary(null);
    setBbox(null);
    setCityName(null);
    setQuery("");
    setHits([]);
  }

  // Compute stats for tracts whose centroid lies inside the boundary
  const stats: Stats = useMemo(() => {
    if (!boundary || tracts.length === 0) return EMPTY;
    const inside: GeoJSON.Feature[] = [];
    for (const t of tracts) {
      const c = centroidOf(t);
      if (pointInGeometry(c, boundary.geometry)) inside.push(t);
    }
    if (inside.length === 0) return EMPTY;
    let pop = 0,
      south = 0,
      pctnw = 0,
      inc = 0,
      ren = 0,
      ready = 0,
      cip = 0,
      cipN = 0,
      tif = 0,
      oz = 0,
      hplr = 0;
    for (const t of inside) {
      const p = (t.properties || {}) as Record<string, unknown>;
      const pp = num(p.population);
      pop += pp;
      south += num(p.south_of_i30);
      pctnw += num(p.pct_nonwhite);
      inc += num(p.median_income);
      ren += num(p.pct_renter);
      ready += num(p.readiness_score);
      if (num(p.cip_per_capita) > 0) {
        cip += num(p.cip_per_capita);
        cipN++;
      }
      if (num(p.tif_present)) tif++;
      if (num(p.oz_designated)) oz++;
      if (String(p.risk_readiness_cell || "").includes("HIGH_PRESSURE_LOW")) hplr++;
    }
    const n = inside.length;
    return {
      count: n,
      population: pop,
      southShare: south / n,
      pctNonwhite: pctnw / n,
      medianIncome: inc / n,
      pctRenter: ren / n,
      readiness: ready / n,
      cipPerCap: cipN ? cip / cipN : 0,
      tifCount: tif,
      ozCount: oz,
      highPressureLowReadiness: hplr,
    };
  }, [boundary, tracts]);

  return (
    <section className="border-t border-white/10 bg-ink px-6 sm:px-12 py-20">
      <div className="mx-auto max-w-6xl">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-yellow-300/80">
          Explore by city
        </div>
        <h2 className="mt-3 serif text-3xl sm:text-5xl leading-tight">
          Type a city — see who lives inside the line.
        </h2>
        <p className="mt-3 max-w-2xl text-white/70">
          The thesis study area is Dallas County, but the boundaries of any
          municipality can be drawn against the same five-layer measures.
          Boundary geometry comes from OpenStreetMap; the stats below
          aggregate every census tract whose centroid falls inside the city
          limits.
        </p>

        {/* Search controls */}
        <div className="mt-8 flex flex-col sm:flex-row gap-3 sm:items-center">
          <div className="relative flex-1 max-w-md">
            <input
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                if (boundary) clear();
              }}
              placeholder="Search a city (e.g. Dallas, Garland, Mesquite)"
              className="w-full rounded-md border border-white/15 bg-black/60 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-yellow-300/60 focus:outline-none"
            />
            {busy && (
              <div className="absolute right-3 top-2.5 text-xs text-white/40">
                searching…
              </div>
            )}
            {hits.length > 0 && (
              <ul className="absolute z-30 mt-1 w-full overflow-hidden rounded-md border border-white/15 bg-[#111] shadow-2xl">
                {hits.map((h) => (
                  <li key={h.place_id}>
                    <button
                      onClick={() => selectHit(h)}
                      className="block w-full text-left px-3 py-2 text-sm text-white/85 hover:bg-yellow-300/10 hover:text-yellow-300"
                    >
                      <span className="font-medium">{prettyCity(h.display_name)}</span>
                      <span className="ml-2 text-[11px] text-white/40">{h.type}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {error && <div className="mt-1 text-xs text-red-300">{error}</div>}
          </div>

          {/* Layer picker */}
          <div className="flex flex-wrap gap-1.5">
            {LAYER_OPTIONS.map((k) => (
              <button
                key={k}
                onClick={() => setLayer(k)}
                className={`rounded-md border px-2.5 py-1 text-[11px] uppercase tracking-wider transition ${
                  layer === k
                    ? "border-yellow-300/60 bg-yellow-300/10 text-yellow-200"
                    : "border-white/10 text-white/60 hover:border-white/30 hover:text-white"
                }`}
              >
                {LAYERS[k].label.split("·").pop()?.trim() ?? k}
              </button>
            ))}
          </div>
        </div>

        {/* Quick suggestions */}
        <div className="mt-3 flex flex-wrap gap-1.5">
          {SUGGESTIONS.map((c) => (
            <button
              key={c}
              onClick={() => setQuery(c)}
              className="rounded-full border border-white/10 px-3 py-0.5 text-[11px] text-white/55 hover:border-yellow-300/40 hover:text-yellow-300"
            >
              {c}
            </button>
          ))}
          {boundary && (
            <button
              onClick={clear}
              className="rounded-full border border-red-400/30 px-3 py-0.5 text-[11px] text-red-300 hover:bg-red-400/10"
            >
              ✕ clear boundary
            </button>
          )}
        </div>

        {/* Map + stats */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 h-[560px] rounded-lg overflow-hidden border border-white/10">
            <AtlasMap
              layer={layer}
              cityBoundary={boundary}
              fitBbox={bbox}
              onTractsReady={setTracts}
            />
          </div>
          <StatsPanel
            cityName={cityName}
            layer={layer}
            stats={stats}
            attribution={
              boundary
                ? "Boundary: OpenStreetMap contributors / Nominatim. Tract attributes: ACS + project pipelines."
                : "Pick a city to draw its boundary and aggregate its tracts."
            }
          />
        </div>
      </div>
    </section>
  );
}

function StatsPanel({
  cityName,
  layer,
  stats,
  attribution,
}: {
  cityName: string | null;
  layer: LayerKey;
  stats: Stats;
  attribution: string;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="font-mono text-[10px] uppercase tracking-wider text-yellow-300/80">
        {cityName ? "Inside the line" : "Awaiting a city"}
      </div>
      <div className="mt-1 serif text-xl leading-tight">
        {cityName ?? "Type a city above"}
      </div>
      <div className="mt-1 text-[11px] text-white/55">
        Active layer: {LAYERS[layer].label}
      </div>

      {stats.count > 0 ? (
        <>
          <div className="mt-5 grid grid-cols-2 gap-3">
            <Stat label="Tracts inside" value={stats.count.toString()} accent />
            <Stat label="Total population" value={fmtNum(stats.population)} />
            <Stat
              label="South of I-30"
              value={pct(stats.southShare * 100)}
              tone={stats.southShare > 0.5 ? "warn" : "neutral"}
            />
            <Stat label="% non-white (avg)" value={pct(stats.pctNonwhite)} />
            <Stat label="Median income (avg)" value={`$${fmtNum(stats.medianIncome)}`} />
            <Stat label="% renter (avg)" value={pct(stats.pctRenter)} />
            <Stat label="CIP per capita (avg)" value={`$${fmtNum(stats.cipPerCap)}`} />
            <Stat
              label="Readiness score (avg)"
              value={stats.readiness.toFixed(3)}
              tone={stats.readiness < 0.05 ? "warn" : "neutral"}
            />
          </div>

          <div className="mt-5 space-y-1 text-[12px] text-white/75 border-t border-white/10 pt-4">
            <div className="flex justify-between">
              <span>Tracts in TIF district</span>
              <span className="font-mono text-yellow-300">{stats.tifCount}</span>
            </div>
            <div className="flex justify-between">
              <span>Tracts in Opportunity Zone</span>
              <span className="font-mono text-yellow-300">{stats.ozCount}</span>
            </div>
            <div className="flex justify-between">
              <span>High pressure · low readiness</span>
              <span
                className={`font-mono ${
                  stats.highPressureLowReadiness > 0 ? "text-red-300" : "text-yellow-300"
                }`}
              >
                {stats.highPressureLowReadiness}
              </span>
            </div>
          </div>
        </>
      ) : cityName ? (
        <div className="mt-6 rounded-md border border-yellow-300/20 bg-yellow-300/5 p-3 text-sm text-yellow-100/80">
          No Dallas County tracts fall inside this boundary. The atlas study
          area is Dallas County (FIPS 48113); cities elsewhere will draw a
          boundary but produce no stats.
        </div>
      ) : (
        <div className="mt-6 text-sm text-white/55">
          Try one of the suggestions above, or type your own.
        </div>
      )}

      <div className="mt-6 border-t border-white/10 pt-3 text-[10px] leading-snug text-white/35">
        {attribution}
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  accent = false,
  tone = "neutral",
}: {
  label: string;
  value: string;
  accent?: boolean;
  tone?: "neutral" | "warn";
}) {
  return (
    <div className="rounded-md border border-white/10 bg-black/30 p-2.5">
      <div className="text-[10px] uppercase tracking-wider text-white/55">{label}</div>
      <div
        className={`mt-0.5 font-mono text-lg ${
          tone === "warn"
            ? "text-red-300"
            : accent
            ? "text-yellow-300"
            : "text-white"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function num(v: unknown): number {
  const n = typeof v === "number" ? v : Number(v ?? 0);
  return Number.isFinite(n) ? n : 0;
}
function fmtNum(v: number): string {
  if (!Number.isFinite(v)) return "—";
  return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
}
function pct(v: number): string {
  if (!Number.isFinite(v)) return "—";
  return `${v.toFixed(1)}%`;
}
function prettyCity(display: string): string {
  // Nominatim returns "Dallas, Dallas County, Texas, United States"
  return display.split(",").slice(0, 1).join(",").trim();
}

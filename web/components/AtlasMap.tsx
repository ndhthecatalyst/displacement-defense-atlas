"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, { Map as MLMap, MapMouseEvent } from "maplibre-gl";
import { LAYERS, LayerKey, paintFor } from "@/lib/layers";

type Props = {
  layer: LayerKey;
  highlightSouth?: boolean;
  zoomTarget?: "county" | "south" | "downtown";
  cityBoundary?: GeoJSON.Feature | null;
  fitBbox?: [number, number, number, number] | null;
  onTractsReady?: (features: GeoJSON.Feature[]) => void;
};

const TARGETS = {
  county: { center: [-96.78, 32.78] as [number, number], zoom: 9.2 },
  south: { center: [-96.82, 32.7] as [number, number], zoom: 10.4 },
  downtown: { center: [-96.795, 32.78] as [number, number], zoom: 11.5 },
};

// CartoDB Dark style — no API key required
const STYLE_URL =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

export default function AtlasMap({
  layer,
  highlightSouth = true,
  zoomTarget = "county",
  cityBoundary = null,
  fitBbox = null,
  onTractsReady,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const loadedRef = useRef(false);
  const [hover, setHover] = useState<{
    x: number;
    y: number;
    props: Record<string, unknown>;
  } | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE_URL,
      center: TARGETS.county.center,
      zoom: TARGETS.county.zoom,
      attributionControl: { compact: true },
      cooperativeGestures: false,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    map.on("load", async () => {
      const res = await fetch("/data/tracts.geojson");
      const gj = await res.json();

      // Compute derived fields client-side: stack_score
      for (const f of gj.features) {
        const p = f.properties as Record<string, number | string | null | undefined>;
        const press = num(p.pct_renter) / 100;
        const vuln = num(p.pct_nonwhite) / 100;
        const defGap = 1 - clamp01(num(p.readiness_score));
        const south = num(p.south_of_i30);
        p.stack_score = clamp01(0.4 * press + 0.3 * vuln + 0.3 * defGap) * (south ? 1.0 : 0.85);
      }

      map.addSource("tracts", { type: "geojson", data: gj });
      if (onTractsReady) onTractsReady(gj.features as GeoJSON.Feature[]);

      // City boundary source — starts empty; filled via prop changes.
      map.addSource("city", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      map.addLayer({
        id: "tracts-fill",
        type: "fill",
        source: "tracts",
        paint: {
          "fill-color": paintFor(LAYERS[layer]) as never,
          "fill-opacity": 0.78,
        },
      });
      map.addLayer({
        id: "tracts-line",
        type: "line",
        source: "tracts",
        paint: {
          "line-color": "#000",
          "line-width": 0.25,
          "line-opacity": 0.4,
        },
      });
      map.addLayer({
        id: "tracts-hover",
        type: "line",
        source: "tracts",
        paint: { "line-color": "#fff", "line-width": 1.6 },
        filter: ["==", "GEOID", ""],
      });
      // I-30 reference line (approx)
      map.addSource("i30", {
        type: "geojson",
        data: {
          type: "Feature",
          geometry: {
            type: "LineString",
            coordinates: [
              [-97.1, 32.762],
              [-96.55, 32.762],
            ],
          },
          properties: {},
        },
      });
      map.addLayer({
        id: "i30",
        type: "line",
        source: "i30",
        paint: {
          "line-color": "#facc15",
          "line-width": 1.6,
          "line-dasharray": [3, 3],
          "line-opacity": 0.8,
        },
      });

      // City boundary visual layers — drawn above tract fills.
      map.addLayer({
        id: "city-fill",
        type: "fill",
        source: "city",
        paint: { "fill-color": "#22d3ee", "fill-opacity": 0.06 },
      });
      map.addLayer({
        id: "city-outline-glow",
        type: "line",
        source: "city",
        paint: { "line-color": "#22d3ee", "line-width": 6, "line-opacity": 0.25, "line-blur": 4 },
      });
      map.addLayer({
        id: "city-outline",
        type: "line",
        source: "city",
        paint: { "line-color": "#22d3ee", "line-width": 2.2, "line-opacity": 0.95 },
      });

      map.on("mousemove", "tracts-fill", (e: MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
        const f = e.features?.[0];
        if (!f) return;
        map.setFilter("tracts-hover", ["==", "GEOID", String(f.properties?.GEOID ?? "")]);
        map.getCanvas().style.cursor = "pointer";
        setHover({ x: e.point.x, y: e.point.y, props: f.properties as Record<string, unknown> });
      });
      map.on("mouseleave", "tracts-fill", () => {
        map.setFilter("tracts-hover", ["==", "GEOID", ""]);
        map.getCanvas().style.cursor = "";
        setHover(null);
      });

      loadedRef.current = true;
    });

    return () => {
      map.remove();
      mapRef.current = null;
      loadedRef.current = false;
    };
  }, []); // mount once

  // React to layer changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loadedRef.current) return;
    if (map.getLayer("tracts-fill")) {
      map.setPaintProperty("tracts-fill", "fill-color", paintFor(LAYERS[layer]) as never);
    }
  }, [layer]);

  // React to zoom target — only when no explicit bbox is active.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || fitBbox) return;
    const t = TARGETS[zoomTarget];
    map.flyTo({ center: t.center, zoom: t.zoom, duration: 1400, essential: true });
  }, [zoomTarget, fitBbox]);

  // React to city boundary changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loadedRef.current) return;
    const src = map.getSource("city") as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    if (cityBoundary) {
      src.setData({ type: "FeatureCollection", features: [cityBoundary] });
    } else {
      src.setData({ type: "FeatureCollection", features: [] });
    }
  }, [cityBoundary]);

  // React to bbox fit requests
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !fitBbox) return;
    map.fitBounds(
      [
        [fitBbox[0], fitBbox[1]],
        [fitBbox[2], fitBbox[3]],
      ],
      { padding: 60, duration: 1600, maxZoom: 12.5 }
    );
  }, [fitBbox]);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      {hover && <Tooltip x={hover.x} y={hover.y} props={hover.props} layer={layer} />}
      <Legend layer={layer} />
      {highlightSouth && (
        <div className="pointer-events-none absolute left-3 top-3 rounded-md bg-black/60 px-2 py-1 text-[10px] uppercase tracking-wider text-yellow-300">
          ━ ━ ━ I-30 corridor
        </div>
      )}
    </div>
  );
}

function num(v: unknown): number {
  const n = typeof v === "number" ? v : Number(v ?? 0);
  return Number.isFinite(n) ? n : 0;
}
function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}

function Tooltip({
  x,
  y,
  props,
  layer,
}: {
  x: number;
  y: number;
  props: Record<string, unknown>;
  layer: LayerKey;
}) {
  const lay = LAYERS[layer];
  const v = props[lay.field];
  return (
    <div
      className="pointer-events-none absolute z-20 max-w-[260px] rounded-md border border-white/10 bg-black/85 px-3 py-2 text-[11px] leading-snug text-white shadow-xl"
      style={{ left: x + 12, top: y + 12 }}
    >
      <div className="font-mono text-[10px] text-white/50">
        Tract {String(props.GEOID ?? "")} · CD {String(props.council_district ?? "—")}
      </div>
      <div className="mt-1 font-medium">{lay.label}</div>
      <div className="text-yellow-300 font-mono">{fmt(v, lay.unit)}</div>
      <div className="mt-1 grid grid-cols-2 gap-x-2 text-white/70">
        <span>% non-white</span>
        <span className="text-right font-mono">{fmt(props.pct_nonwhite, "%")}</span>
        <span>Median income</span>
        <span className="text-right font-mono">${fmtNum(props.median_income)}</span>
        <span>TIF / OZ</span>
        <span className="text-right font-mono">
          {Number(props.tif_present) ? "TIF " : ""}
          {Number(props.oz_designated) ? "OZ" : ""}
          {!Number(props.tif_present) && !Number(props.oz_designated) ? "—" : ""}
        </span>
        <span>Readiness</span>
        <span className="text-right font-mono">
          {fmt(props.readiness_score, "")}
        </span>
        <span>South of I-30</span>
        <span className="text-right font-mono">{Number(props.south_of_i30) ? "yes" : "no"}</span>
      </div>
      {props.bates_typology_v21 ? (
        <div className="mt-1 text-white/60 italic">{String(props.bates_typology_v21)}</div>
      ) : null}
    </div>
  );
}

function Legend({ layer }: { layer: LayerKey }) {
  const lay = LAYERS[layer];
  return (
    <div className="absolute bottom-3 left-3 z-10 rounded-md border border-white/10 bg-black/70 px-3 py-2 text-white">
      <div className="text-[10px] uppercase tracking-wider text-white/60">{lay.label}</div>
      <div className="mt-0.5 text-[11px] text-white/80">{lay.short}</div>
      {lay.categorical ? (
        <div className="mt-2 flex gap-2 text-[10px]">
          <Swatch color="#7c3aed" label="TIF" />
          <Swatch color="#22d3ee" label="OZ" />
          <Swatch color="#222" label="Neither" />
        </div>
      ) : (
        <div className="mt-2 flex items-center gap-1">
          {(lay.stops ?? []).map(([v, c], i) => (
            <div key={i} className="flex flex-col items-center">
              <div style={{ background: c }} className="h-3 w-7 rounded-sm" />
              <div className="font-mono text-[9px] text-white/60">{fmtAxis(v, lay.unit)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Swatch({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1">
      <span style={{ background: color }} className="inline-block h-3 w-3 rounded-sm" />
      <span className="text-white/70">{label}</span>
    </div>
  );
}

function fmt(v: unknown, unit?: string): string {
  if (v == null || v === "") return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return String(v);
  if (unit === "%") return n > 1.5 ? `${n.toFixed(1)}%` : `${(n * 100).toFixed(2)}%`;
  if (unit === "$") return `$${fmtNum(n)}`;
  return n.toFixed(3);
}
function fmtAxis(v: number, unit?: string): string {
  if (unit === "%") return v > 1.5 ? `${v}` : `${(v * 100).toFixed(0)}%`;
  if (unit === "$") return v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`;
  return v.toString();
}
function fmtNum(v: unknown): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

// Capital stack layer definitions — drive choropleth + narrative.
export type LayerKey =
  | "vulnerability"
  | "cip"
  | "tif_oz"
  | "vendor"
  | "readiness"
  | "stack";

export type LayerSpec = {
  key: LayerKey;
  label: string;
  short: string;
  // Field on the GeoJSON feature properties
  field: string;
  // For categorical fields (tif_present, oz_designated)
  categorical?: boolean;
  // Color stops for numeric fields: [value, hex] pairs
  stops?: Array<[number, string]>;
  // Label format
  unit?: string;
  // Inverted meaning (low = bad)
  inverse?: boolean;
};

const ramp = [
  "#fef0d9",
  "#fdcc8a",
  "#fc8d59",
  "#e34a33",
  "#b30000",
];

export const LAYERS: Record<LayerKey, LayerSpec> = {
  vulnerability: {
    key: "vulnerability",
    label: "Baseline Vulnerability",
    short: "% non-white population",
    field: "pct_nonwhite",
    stops: [
      [0, ramp[0]],
      [25, ramp[1]],
      [50, ramp[2]],
      [75, ramp[3]],
      [90, ramp[4]],
    ],
    unit: "%",
  },
  cip: {
    key: "cip",
    label: "Layer 1 — CIP per capita",
    short: "$ public capital per resident",
    field: "cip_per_capita",
    stops: [
      [0, "#1a1a1a"],
      [200, "#3a2a1a"],
      [600, "#7a4a1a"],
      [1500, "#bf7a1a"],
      [4000, "#f5b941"],
    ],
    unit: "$",
  },
  tif_oz: {
    key: "tif_oz",
    label: "Layer 3 — TIF / OZ presence",
    short: "Where the financial-engineering tools land",
    field: "tif_oz_combined",
    categorical: true,
  },
  vendor: {
    key: "vendor",
    label: "Layer 5 — Vendor residue capture (15-mi)",
    short: "Share of public spend that lands in this tract's HQ orbit",
    field: "vendor_share_15mi",
    stops: [
      [0, "#1a1a1a"],
      [0.001, "#3a2a1a"],
      [0.005, "#7a4a1a"],
      [0.02, "#bf7a1a"],
      [0.08, "#f5b941"],
    ],
    unit: "%",
  },
  readiness: {
    key: "readiness",
    label: "H4 — Defense readiness",
    short: "LIHTC + HUD + community capacity (low = no defense)",
    field: "readiness_score",
    inverse: true,
    stops: [
      [0, "#b30000"],
      [0.05, "#e34a33"],
      [0.15, "#fc8d59"],
      [0.35, "#fdcc8a"],
      [0.7, "#fef0d9"],
    ],
  },
  stack: {
    key: "stack",
    label: "Capital-stack composite",
    short: "Pressure ⨯ vulnerability ⨯ defense gap",
    field: "stack_score",
    stops: [
      [0, ramp[0]],
      [0.25, ramp[1]],
      [0.5, ramp[2]],
      [0.75, ramp[3]],
      [1.0, ramp[4]],
    ],
  },
};

// Build a MapLibre paint expression for a layer
export function paintFor(layer: LayerSpec): unknown {
  if (layer.categorical && layer.field === "tif_oz_combined") {
    return [
      "case",
      ["==", ["get", "tif_present"], 1], "#7c3aed",
      ["==", ["get", "oz_designated"], 1], "#22d3ee",
      "#222",
    ];
  }
  if (!layer.stops) return "#444";
  const expr: unknown[] = [
    "interpolate",
    ["linear"],
    ["coalesce", ["to-number", ["get", layer.field]], 0],
  ];
  for (const [v, c] of layer.stops) {
    expr.push(v, c);
  }
  return expr;
}

// Lightweight geometry helpers — no external deps.

export type LngLat = [number, number];
export type BBox = [number, number, number, number]; // w,s,e,n

export function bboxOfFeature(f: GeoJSON.Feature): BBox {
  let w = Infinity, s = Infinity, e = -Infinity, n = -Infinity;
  walkCoords(f.geometry, ([x, y]) => {
    if (x < w) w = x;
    if (x > e) e = x;
    if (y < s) s = y;
    if (y > n) n = y;
  });
  return [w, s, e, n];
}

function walkCoords(g: GeoJSON.Geometry, cb: (c: LngLat) => void) {
  switch (g.type) {
    case "Point":
      cb(g.coordinates as LngLat);
      break;
    case "LineString":
    case "MultiPoint":
      (g.coordinates as LngLat[]).forEach(cb);
      break;
    case "Polygon":
    case "MultiLineString":
      (g.coordinates as LngLat[][]).forEach((r) => r.forEach(cb));
      break;
    case "MultiPolygon":
      (g.coordinates as LngLat[][][]).forEach((p) => p.forEach((r) => r.forEach(cb)));
      break;
    case "GeometryCollection":
      g.geometries.forEach((sub) => walkCoords(sub, cb));
      break;
  }
}

// Approximate tract centroid via average of outer-ring vertices.
export function centroidOf(f: GeoJSON.Feature): LngLat {
  let sx = 0, sy = 0, n = 0;
  const g = f.geometry;
  const rings: LngLat[][] =
    g.type === "Polygon"
      ? (g.coordinates as LngLat[][])
      : g.type === "MultiPolygon"
      ? ((g.coordinates as LngLat[][][]).flat())
      : [];
  // Use only the largest outer ring
  let best: LngLat[] = [];
  for (const r of rings) {
    if (r.length > best.length) best = r;
  }
  for (const [x, y] of best) {
    sx += x;
    sy += y;
    n++;
  }
  return n > 0 ? [sx / n, sy / n] : [0, 0];
}

// Ray-casting point-in-polygon. Accepts Polygon or MultiPolygon.
export function pointInGeometry([x, y]: LngLat, g: GeoJSON.Geometry): boolean {
  if (g.type === "Polygon") return pointInRings(x, y, g.coordinates as LngLat[][]);
  if (g.type === "MultiPolygon") {
    for (const poly of g.coordinates as LngLat[][][]) {
      if (pointInRings(x, y, poly)) return true;
    }
    return false;
  }
  return false;
}

function pointInRings(x: number, y: number, rings: LngLat[][]): boolean {
  if (rings.length === 0) return false;
  if (!pointInRing(x, y, rings[0])) return false;
  for (let i = 1; i < rings.length; i++) {
    if (pointInRing(x, y, rings[i])) return false; // inside a hole
  }
  return true;
}

function pointInRing(x: number, y: number, ring: LngLat[]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    const intersect =
      yi > y !== yj > y &&
      x < ((xj - xi) * (y - yi)) / (yj - yi + 1e-12) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

export interface Wgs84Point {
  latitude: number;
  longitude: number;
}

export interface LocalMetersPoint {
  x: number;
  z: number;
}

export interface Wgs84Bounds {
  west: number;
  south: number;
  east: number;
  north: number;
}

export interface TileRange {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
  z: number;
}

const earthRadiusMeters = 6378137;

function toRadians(degrees: number): number {
  return degrees * Math.PI / 180;
}

function toDegrees(radians: number): number {
  return radians * 180 / Math.PI;
}

export function lonLatToWebMercator(point: Wgs84Point): { x: number; y: number } {
  const x = earthRadiusMeters * toRadians(point.longitude);
  const y = earthRadiusMeters * Math.log(Math.tan(Math.PI / 4 + toRadians(point.latitude) / 2));
  return { x, y };
}

export function webMercatorToLonLat(point: { x: number; y: number }): Wgs84Point {
  const longitude = toDegrees(point.x / earthRadiusMeters);
  const latitude = toDegrees(2 * Math.atan(Math.exp(point.y / earthRadiusMeters)) - Math.PI / 2);
  return { latitude, longitude };
}

export function localMetersFromLonLat(point: Wgs84Point, origin: Wgs84Point): LocalMetersPoint {
  const originMercator = lonLatToWebMercator(origin);
  const pointMercator = lonLatToWebMercator(point);
  return {
    x: pointMercator.x - originMercator.x,
    z: -(pointMercator.y - originMercator.y)
  };
}

export function lonLatFromLocalMeters(point: LocalMetersPoint, origin: Wgs84Point): Wgs84Point {
  const originMercator = lonLatToWebMercator(origin);
  return webMercatorToLonLat({
    x: originMercator.x + point.x,
    y: originMercator.y - point.z
  });
}

export function lonToTileX(longitude: number, zoom: number): number {
  return Math.floor((longitude + 180) / 360 * 2 ** zoom);
}

export function latToTileY(latitude: number, zoom: number): number {
  const latitudeRadians = toRadians(latitude);
  return Math.floor(
    (1 - Math.log(Math.tan(latitudeRadians) + 1 / Math.cos(latitudeRadians)) / Math.PI) / 2 * 2 ** zoom
  );
}

export function tileXToLon(x: number, zoom: number): number {
  return x / 2 ** zoom * 360 - 180;
}

export function tileYToLat(y: number, zoom: number): number {
  const n = Math.PI - 2 * Math.PI * y / 2 ** zoom;
  return toDegrees(Math.atan(0.5 * (Math.exp(n) - Math.exp(-n))));
}

export function tileBoundsWgs84(x: number, y: number, zoom: number): Wgs84Bounds {
  return {
    west: tileXToLon(x, zoom),
    south: tileYToLat(y + 1, zoom),
    east: tileXToLon(x + 1, zoom),
    north: tileYToLat(y, zoom)
  };
}

export function boundsToTileRange(bounds: Wgs84Bounds, zoom: number): TileRange {
  return {
    minX: lonToTileX(bounds.west, zoom),
    maxX: lonToTileX(bounds.east, zoom),
    minY: latToTileY(bounds.north, zoom),
    maxY: latToTileY(bounds.south, zoom),
    z: zoom
  };
}

export function boundsIntersect(a: Wgs84Bounds, b: Wgs84Bounds): boolean {
  return a.west <= b.east && a.east >= b.west && a.south <= b.north && a.north >= b.south;
}


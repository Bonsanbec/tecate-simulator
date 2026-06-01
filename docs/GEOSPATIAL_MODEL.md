# GEOSPATIAL_MODEL.md — Tecate Simulator: Coordinate Systems & Spatial Relationships

---

## 1. Coordinate System Overview

The repository uses **two primary coordinate systems** and one camera-space system:

| System | Abbreviation | Origin | Units | Used In |
|--------|-------------|--------|-------|---------|
| WGS84 Geographic | GPS | Global | degrees lat/lon | OSM data, panorama positions, API queries |
| Local Cartesian (ETP) | local (x,y) | Parque Hidalgo | meters | Block polygons, facade geometry, graph nodes |
| Camera Space | cam (xc,yc,zc) | Camera position | meters | Perspective projection, homography |

---

## 2. Local Cartesian Projection (Equirectangular Tangent Plane)

### Definition

All geometry in the pipeline is computed in a **local flat-Earth Cartesian coordinate system** centered at **Parque Hidalgo** (the city center):

```python
TECATE_LAT_CENTER = 32.573229   # degrees N
TECATE_LON_CENTER = -116.626536  # degrees W
EARTH_RADIUS = 6378137.0         # meters (WGS84 equatorial)
```

### Forward Transform: GPS → Local (x, y)

```python
def gps_to_local(lat, lon) -> (x, y):
    dx = R * (lon_rad - lon_c_rad) * cos(lat_c_rad)   # East (meters)
    dy = R * (lat_rad - lat_c_rad)                     # North (meters)
    return dx, dy
```

This is a standard **Equirectangular (Plate Carrée) local tangent plane** approximation:
- `x` = East/West offset in meters
- `y` = North/South offset in meters
- **Origin**: (0, 0) at Parque Hidalgo
- The `cos(lat_c_rad)` factor corrects for longitude degree compression at this latitude

**Computed values at Tecate latitude (32.573°N)**:
- `cos(32.573°)` ≈ 0.8416
- 1° latitude ≈ 111,319 m
- 1° longitude ≈ 93,688 m
- Error grows with distance from center (valid within ~5km radius)

### Inverse Transform: Local (x, y) → GPS

```python
def local_to_gps(x, y) -> (lat, lon):
    lat = degrees(y / R + lat_c_rad)
    lon = degrees(x / (R * cos(lat_c_rad)) + lon_c_rad)
```

### Coordinate Range

From the bounding box constants:
```
SW corner (GPS): 32.521704°N, -116.681499°W
NE corner (GPS): 32.580233°N, -116.510525°W
```

Converted to local:
```
SW local: ~(-5,100m, -5,700m)   → 5.1 km West, 5.7 km South of center
NE local: ~(+10,100m, +780m)   → 10.1 km East, 780m North of center
```

**Example from blocks_cache**:
```
block_lat_32.56181_lon_-116.57077
First vertex: [5226.40, -1261.41]  →  5.2 km East, 1.26 km South
```

---

## 3. Block Polygon Coordinate System

Block polygons are stored as **closed lists of (x, y) tuples in local Cartesian meters**:

```
polygon[0] = polygon[-1]  (first equals last — closed)
Winding: Counter-Clockwise (CCW) for valid interior blocks
Signed area < 0 for CCW in standard math orientation
```

**Polygon inward offset**: All block polygons in `reconstruction_export.json` are the **shrunk version** (6m inset), representing the building footprint after accounting for sidewalk setback. Raw polygons from `blocks_cache.json` are the road-network-aligned cycle.

### Normal Computation

For a facade edge from vertex A to vertex B:
```
dx = B.x - A.x
dy = B.y - A.y
normal = [dy, -dx]  (left perpendicular = outward normal for CCW polygon)
normal_normalized = normal / |normal|
```

This outward normal points **away from the block interior** toward the street.

**Direction convention**:
- Normal `[0, 1]` → facing North → heading = 0°
- Normal `[1, 0]` → facing East → heading = 90°
- Normal `[0, -1]` → facing South → heading = 180°
- Normal `[-1, 0]` → facing West → heading = 270°

---

## 4. Camera Position Search Point

For each facade, a **search point** is placed 8 meters outward along the normal:

```
search_x = midpoint_x + 8.0 * normal_x
search_y = midpoint_y + 8.0 * normal_y
(search_lat, search_lon) = local_to_gps(search_x, search_y)
```

This places the query point in the middle of the street, where a Google Street View vehicle would have driven. The 8m offset assumes ~4m sidewalk + ~4m travel lane.

---

## 5. Heading Convention

**Heading** is measured in **degrees clockwise from North** (geographic bearing convention):

```python
heading = math.degrees(math.atan2(-normal_x, -normal_y)) % 360.0
```

Where the negative signs flip the normal to get the **inward-facing** direction (camera looking at facade):
- If normal points North `[0, 1]`, camera faces South → heading = 180°
- If normal points East `[1, 0]`, camera faces West → heading = 270°

This is consistent with Google Street View's `cbp` (camera bearing parameter) convention.

---

## 6. Camera Model

### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `cam_z` | 2.5 m | Camera height above ground (eye level on SV car) |
| `cam_fov` | 75.0° | Horizontal field of view of captured screenshots |
| `W_obs` | 1280 px | Screenshot width |
| `H_obs` | 720 px | Screenshot height |

### Focal Length (pixels)

```python
f = (W_obs - 1) / (2.0 * tan(radians(cam_fov) / 2.0))
f = 1279 / (2 * tan(37.5°)) ≈ 1279 / 1.534 ≈ 833.7 pixels
```

### Camera Coordinate System

For a panorama at position (cam_x, cam_y, cam_z=2.5) with yaw `theta`:

```
v_look  = [sin(theta), cos(theta), 0.0]   # forward (into facade)
v_right = [cos(theta), -sin(theta), 0.0]  # rightward
v_up    = [0.0, 0.0, 1.0]                 # up
```

- **Z-up world** (right-hand, x=East, y=North, z=Up)
- The look vector is **horizontal** (no pitch)
- Roll = 0 (camera assumed level)

### Perspective Projection of a 3D World Point (X, Y, Z)

```python
dx = X - cam_x;  dy = Y - cam_y;  dz = Z - cam_z
x_c = dx*v_right[0] + dy*v_right[1]   # camera-right projection
y_c = dz                               # camera-up projection (only Z)
z_c = dx*v_look[0]  + dy*v_look[1]    # camera-depth projection

px = (W-1)/2 + f * (x_c / z_c)        # pixel column
py = (H-1)/2 - f * (y_c / z_c)        # pixel row (Y flipped)
```

### Facade Projection

For a facade wall quad with corners at A, B (bottom) and A+height, B+height (top):
- The **4 corners** are projected into pixel space
- A **homography matrix** `M` (3×3 perspective transform via `cv2.getPerspectiveTransform`) maps screen coordinates to texture coordinates
- `cv2.warpPerspective` performs the actual warping

---

## 7. Cardinal Direction Assignment

From the facade outward normal `[nx, ny]`:

```python
def cardinal_from_normal(normal):
    if abs(nx) > abs(ny):
        return "east" if nx > 0 else "west"
    else:
        return "north" if ny > 0 else "south"
```

Used for naming texture files: `{block_id}_virtual_{cardinal}_{group_idx}.png`

---

## 8. Roofline Height Estimation

The system estimates building height using **inverse perspective from sky/roofline detection**:

```
Given:
  - Pixel row of detected roofline: y_roof
  - Camera depth to facade at column x: z_c_x
  - Camera height: cam_z = 2.5m
  - Focal length: f

Solved height:
  H_solved = cam_z + z_c_x * ((c_y - y_roof) / f)
```

Where `c_y = (H-1)/2 = 359.5` (image center row).

**Clamp range**: 3.2m – 6.5m (per-column estimate), then `median * 2.0` for block height.
**Typical output**: 7–11m (doubling accounts for the 2D vs full-facade height).

---

## 9. Spatial Grid Index for Road Distance

To efficiently find the nearest road segment, a **50m grid cell index** is pre-built:

```python
grid_size = 50.0  # meters
cell_x = floor(mx / grid_size)
cell_y = floor(my / grid_size)
# Check 3x3 neighborhood of cells
```

Perpendicular point-to-segment distance is computed analytically for candidate edges.

**Street-facing threshold**: `road_distance_meters <= 20.0m`

---

## 10. Block-Level Spatial Filters

### Park Height Rule (Parque Hidalgo)

```python
dist_to_center = sqrt(centroid_x² + centroid_y²)
if dist_to_center <= 50.0:
    height_meters = 1.0   # low park extrusion
```

50m radius from origin (0,0) = Parque Hidalgo.

### Safety Radius Filter

```python
if radius > 0 and dist_to_center > radius:
    skip block
```

### Municipal Polygon Filter

Block centroid (in GPS) must fall inside the INEGI `tecate-polygon.json` boundary (ray-casting point-in-polygon test).

---

## 11. Blender Coordinate System

In `blender_script.py`, the same local Cartesian `(x, y)` coordinates are used **directly** as Blender world coordinates:

```python
BL = (poly[i][0], poly[i][1], z_base)        # (x, y, 0)
TR = (poly[i+1][0], poly[i+1][1], z_base + height)  # (x, y, h)
```

- Blender X = local x (East)
- Blender Y = local y (North)  
- Blender Z = vertical (up)

**No rotation or scale transform** is applied — local meters map 1:1 to Blender meters.

**Camera default position**: `(0.0, -120.0, 110.0)` → 120m South and 110m above origin, looking at Parque Hidalgo from the south.

---

## 12. Terrain Model Coordinate System

The terrain GLB models in `models/tecate/` were generated from INEGI data. From `tecate.md`:

> "INEGI municipal polygon dataset — Coordinate system preserved from original GeoJSON source"

The terrain models use the **INEGI GeoJSON coordinate system** (WGS84 lon/lat in GeoJSON convention). There is **no documented explicit coordinate alignment** between the terrain model and the pipeline's local Cartesian system — this constitutes a known gap (see UNKNOWNS_AND_GAPS.md).

---

## 13. UV Coordinate System

UV coordinates for facade textures:

| Vertex | UV |
|--------|----|
| Bottom-Left | [u_start, 0.0] |
| Bottom-Right | [u_end, 0.0] |
| Top-Right | [u_end, 1.0] |
| Top-Left | [u_start, 1.0] |

For virtual group textures, the U range is `[0.375 + 0.25*(cum_L/L_total), ...]` — the central 25% of the texture width is used, corresponding to the unblurred central region of the warped facade.

For standalone single-facade textures, UVs default to `[[0,0],[1,0],[1,1],[0,1]]`.

---

## 14. Rotation Matrix Convention

The `camera_rotation_matrix` stored in `facades_cache.json` is a **yaw-only 2D→3D rotation matrix**:

```python
yaw_rad = radians(heading)
R = [
  [cos(yaw), -sin(yaw), 0],
  [sin(yaw),  cos(yaw), 0],
  [0,         0,        1]
]
```

This rotates from world space into camera space around the Z-axis (vertical). It is a standard **rotation matrix for heading/bearing**, not a full 6DOF camera pose. Pitch and roll are assumed zero (camera level).

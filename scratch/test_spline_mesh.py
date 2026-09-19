import math

def catmull_rom_spline(P0, P1, P2, P3, num_points=8):
    """Generates Catmull-Rom spline points between P1 and P2."""
    points = []
    for i in range(num_points):
        t = i / num_points
        t2 = t * t
        t3 = t2 * t
        
        # Standard Catmull-Rom matrix
        f0 = -0.5 * t3 + t2 - 0.5 * t
        f1 =  1.5 * t3 - 2.5 * t2 + 1.0
        f2 = -1.5 * t3 + 2.0 * t2 + 0.5 * t
        f3 =  0.5 * t3 - 0.5 * t2
        
        x = P0[0]*f0 + P1[0]*f1 + P2[0]*f2 + P3[0]*f3
        y = P0[1]*f0 + P1[1]*f1 + P2[1]*f2 + P3[1]*f3
        points.append((x, y))
    return points

def generate_fountain_perimeter(samples_per_seg=6):
    # Half control points (X >= 0)
    # 0 is center front (0, 5.0)
    # 11 is center rear (0, -6.4)
    half_cp = [
        (0.0, 5.0),
        (2.3, 4.9),
        (4.5, 4.2),
        (6.2, 2.5),
        (6.4, 1.0),
        (5.5, -0.2),
        (5.6, -1.8),
        (6.1, -3.4),
        (5.2, -4.9),
        (3.2, -5.9),
        (1.5, -6.3),
        (0.0, -6.4)
    ]
    
    # Mirror for X < 0 to form closed ring
    # Order: half_cp (from 0 to 11), then mirrored back from 10 down to 1
    full_cp = list(half_cp)
    for p in reversed(half_cp[1:-1]):
        full_cp.append((-p[0], p[1]))
        
    n = len(full_cp)
    spline_points = []
    for i in range(n):
        p0 = full_cp[(i - 1) % n]
        p1 = full_cp[i]
        p2 = full_cp[(i + 1) % n]
        p3 = full_cp[(i + 2) % n]
        seg = catmull_rom_spline(p0, p1, p2, p3, samples_per_seg)
        spline_points.extend(seg)
        
    return spline_points

pts = generate_fountain_perimeter()
print(f"Total spline points generated: {len(pts)}")
min_x = min(p[0] for p in pts)
max_x = max(p[0] for p in pts)
min_y = min(p[1] for p in pts)
max_y = max(p[1] for p in pts)
print(f"Bounding Box: X in [{min_x:.2f}, {max_x:.2f}] (Span: {max_x - min_x:.2f}m)")
print(f"              Y in [{min_y:.2f}, {max_y:.2f}] (Span: {max_y - min_y:.2f}m)")

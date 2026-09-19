import math

def test_refined_control_points():
    """
    Refined control points to match aerial_fuente.png:
    - Symmetrical about Y axis.
    - Front cut (+Y) is indented/recessed between two front-facing lobes ('ears').
    - P0: (0.0, 4.40) - recessed center of front cut
    - P1: (1.80, 4.55) - edge of front cut
    - P2: (3.60, 5.50) - FRONT LOBE PEAK (projecting forward towards NW)
    - P3: (5.60, 4.20) - front-lateral transition
    - P4: (6.40, 2.20) - LATERAL BULGE
    - P5: (5.40, 0.40) - waist indent
    - P6: (5.40, -1.20) - waist trough
    - P7: (6.10, -3.20) - REAR-LATERAL LOBE
    - P8: (5.00, -5.00) - rear transition
    - P9: (3.00, -6.00) - rear shoulder
    - P10: (0.0, -6.50) - REAR CENTER LOBE (projecting towards park)
    """
    half_cp = [
        (0.00, 4.40),
        (1.80, 4.55),
        (3.60, 5.50),
        (5.60, 4.20),
        (6.40, 2.20),
        (5.40, 0.40),
        (5.40, -1.20),
        (6.10, -3.20),
        (5.00, -5.00),
        (3.00, -6.00),
        (0.00, -6.50)
    ]
    return half_cp

cp = test_refined_control_points()
print(f"Refined half control points: {len(cp)}")
for i, (x, y) in enumerate(cp):
    print(f"  {i:2d}: ({x:5.2f}, {y:5.2f}) | R = {math.hypot(x, y):.2f}m")

import math

def get_half_perimeter_points(num_samples=40):
    """
    Generates half of the fountain perimeter curve for X >= 0.
    Key reference points:
    P0: Center of front cut: (0.0, 5.0)
    P1: Corner of front cut: (2.3, 4.9)
    P2: Front-lateral outer bulge: (6.2, 2.5)
    P3: Lateral waist / indent: (5.4, 0.0)
    P4: Rear-lateral outer bulge: (6.0, -3.2)
    P5: Rear corner / indent: (4.2, -5.4)
    P6: Rear center apex on symmetry axis: (0.0, -6.4)
    """
    control_points = [
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
    return control_points

pts = get_half_perimeter_points()
print(f"Generated {len(pts)} control points for half curve:")
for i, (x, y) in enumerate(pts):
    print(f"  {i:2d}: ({x:5.2f}, {y:5.2f}) | R = {math.hypot(x, y):.2f}m | Angle = {math.degrees(math.atan2(y, x)):.1f}°")

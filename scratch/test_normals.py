import math

# Let's check the direction of generate_perimeter_points
from scripts.generate_fuente_parque_hidalgo import generate_perimeter_points

pts = generate_perimeter_points(samples_per_seg=6)
n = len(pts)

print("First 5 points:")
for i in range(5):
    print(f"  P{i}: ({pts[i][0]:.2f}, {pts[i][1]:.2f})")

# Check P0 to P1:
# P0 is (0.0, 4.40)
# P1 is around (0.30, 4.42) -> X increases!
# That means it goes in the direction of +X (counter-clockwise)!
dx = pts[1][0] - pts[0][0]
dy = pts[1][1] - pts[0][1]
length = math.hypot(dx, dy)
tx, ty = dx / length, dy / length
nx = ty
ny = -tx
print(f"Tangent at P0: ({tx:.2f}, {ty:.2f})")
print(f"Normal (ty, -tx) at P0: ({nx:.2f}, {ny:.2f})")
# At P0 (front cut, Y = 4.40), outward normal should point towards +Y!
# But (ty, -tx): since tx > 0 and ty ~ 0, ny = -tx is NEGATIVE (-1.0)!
# That points towards -Y (INWARD towards the center of the fountain)!

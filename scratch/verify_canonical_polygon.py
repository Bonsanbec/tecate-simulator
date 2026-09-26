import math

poly = [
    (52.66, 40.78),
    (54.00, 20.00),
    (55.20, 0.00),
    (56.40, -20.00),
    (57.30, -31.93),
    (38.00, -33.40),
    (18.00, -34.80),
    (0.00, -36.40),
    (-20.00, -38.00),
    (-39.22, -39.44),
    (-44.98, -37.01),
    (-51.24, -33.40),
    (-52.94, -32.42),
    (-56.61, -3.38),
    (-56.81, -1.15),
    (-59.04, 24.65),
    (-59.50, 29.97),
    (-40.00, 31.80),
    (-20.00, 33.70),
    (0.00, 35.70),
    (20.00, 37.60),
    (36.00, 39.20),
]

area = 0.0
for i in range(len(poly)):
    j = (i + 1) % len(poly)
    area += poly[i][0] * poly[j][1] - poly[j][0] * poly[i][1]
area = abs(area) * 0.5
print(f"Area of polygon: {area:.2f} m² ({area/10000:.3f} ha)")

# Check self-intersections
def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(A,B,C,D):
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

has_self_intersect = False
n = len(poly)
for i in range(n):
    p1, p2 = poly[i], poly[(i+1)%n]
    for j in range(i+2, n):
        if (j+1)%n == i:
            continue
        p3, p4 = poly[j], poly[(j+1)%n]
        if intersect(p1, p2, p3, p4):
            print(f"Self-intersection between seg {i} and {j}!")
            has_self_intersect = True

if not has_self_intersect:
    print("Polygon is completely simple and non-self-intersecting! Valid!")

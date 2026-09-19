"""
Unit tests for Tecate Nomenclatura Urbana street name parsing and geometry rules.
"""
import sys
import os
import math
sys.path.insert(0, os.getcwd())
from scripts.bake_nomenclatura_urbana import standardize_street_name, calculate_optimal_post_orientation

def test_prefix_extraction():
    # Presidentes
    p, m = standardize_street_name("Calle Presidente Pascual Ortiz Rubio")
    assert p == "PDTE."
    assert m == "PASCUAL ORTIZ RUBIO"

    p, m = standardize_street_name("Presidente Lázaro Cárdenas")
    assert p == "PDTE."
    assert m == "LÁZARO CÁRDENAS"

    # Avenidas
    p, m = standardize_street_name("Avenida Benito Juárez")
    assert p == "AV."
    assert m == "BENITO JUÁREZ"

    p, m = standardize_street_name("Av. Nuevo León")
    assert p == "AV."
    assert m == "NUEVO LEÓN"

    # Boulevares
    p, m = standardize_street_name("Boulevard Defensores de Baja California")
    assert p == "BLVD."
    assert m == "DEFENSORES DE B.C."

    # Callejones
    p, m = standardize_street_name("Callejón Libertad")
    assert p == "CJÓN."
    assert m == "LIBERTAD"

    p, m = standardize_street_name("Callejón Reforma")
    assert p == "CJÓN."
    assert m == "REFORMA"

    # Carreteras
    p, m = standardize_street_name("Carretera Mexicali - Tijuana")
    assert p == "CARR."
    assert m == "MEXICALI - TIJUANA"

    # Calles
    p, m = standardize_street_name("Calle 5 de Mayo")
    assert p == "C."
    assert m == "5 DE MAYO"

    p, m = standardize_street_name("Calle Juan Martínez el Pípila")
    assert p == "C."
    assert m == "JUAN MARTÍNEZ EL PÍPILA"

def test_all_uppercase():
    test_cases = [
        "calle presidente pascual ortiz rubio",
        "Avenida Benito Juárez",
        "callejón libertad",
        "esteban cantú"
    ]
    for tc in test_cases:
        p, m = standardize_street_name(tc)
        assert p == p.upper()
        assert m == m.upper()

def test_optimal_yaw_orthogonal():
    # Street 1 along East (1, 0), Street 2 along North (0, 1)
    v1 = (1.0, 0.0)
    v2 = (0.0, 1.0)
    yaw = calculate_optimal_post_orientation(v1, v2)
    # Yaw should be 0 (or multiple of pi)
    yaw_deg = math.degrees(yaw) % 180.0
    assert abs(yaw_deg - 0.0) < 1e-3 or abs(yaw_deg - 180.0) < 1e-3

def test_optimal_yaw_deviation_split():
    # Streets at 80 deg (deviates by 10 deg from 90)
    v1 = (1.0, 0.0)
    v2 = (math.cos(math.radians(80)), math.sin(math.radians(80)))
    yaw = calculate_optimal_post_orientation(v1, v2)
    yaw_deg = math.degrees(yaw)
    # The deviation from 90 should be split evenly (-5 deg)
    assert abs(abs(yaw_deg) - 5.0) < 1e-2

def test_chirality_and_face_orientations():
    """
    Verifica que las rotaciones Euler de las 4 caras de placas:
    1. Tengan determinante +1.0 (cero efecto espejo).
    2. Apunten su vector Normal hacia el observador.
    3. Apunten su vector Right en la dirección de lectura (izquierda a derecha).
    """
    from mathutils import Vector, Euler

    cases = [
        # (Nombre, Euler_deg, Normal esperada, Right esperado)
        ("Placa Inferior Frente (+Y)", (90, 0, 180), Vector((0, 1, 0)), Vector((-1, 0, 0))),
        ("Placa Inferior Dorso (-Y)", (90, 0, 0), Vector((0, -1, 0)), Vector((1, 0, 0))),
        ("Placa Superior Frente (-X)", (90, 0, -90), Vector((-1, 0, 0)), Vector((0, -1, 0))),
        ("Placa Superior Dorso (+X)", (90, 0, 90), Vector((1, 0, 0)), Vector((0, 1, 0))),
    ]
    for name, (rx, ry, rz), exp_norm, exp_right in cases:
        e = Euler((math.radians(rx), math.radians(ry), math.radians(rz)))
        m = e.to_matrix().to_4x4()
        vr = (m @ Vector((1, 0, 0, 0))).to_3d()
        vu = (m @ Vector((0, 1, 0, 0))).to_3d()
        vn = (m @ Vector((0, 0, 1, 0))).to_3d()
        det = m.to_3x3().determinant()

        assert abs(det - 1.0) < 1e-4, f"{name}: Determinante {det} != +1.0 (efecto espejo detectado)"
        assert (vn - exp_norm).length < 1e-4, f"{name}: Normal errónea {vn} != {exp_norm}"
        assert (vr - exp_right).length < 1e-4, f"{name}: Right erróneo {vr} != {exp_right}"
        assert (vu - Vector((0, 0, 1))).length < 1e-4, f"{name}: Up no vertical {vu}"

if __name__ == "__main__":
    test_prefix_extraction()
    print("[PASS] test_prefix_extraction passed.")
    test_all_uppercase()
    print("[PASS] test_all_uppercase passed.")
    test_optimal_yaw_orthogonal()
    print("[PASS] test_optimal_yaw_orthogonal passed.")
    test_optimal_yaw_deviation_split()
    print("[PASS] test_optimal_yaw_deviation_split passed.")
    test_chirality_and_face_orientations()
    print("[PASS] test_chirality_and_face_orientations passed.")
    print("\nALL UNIT TESTS PASSED SUCCESSFULLY!")


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

if __name__ == "__main__":
    test_prefix_extraction()
    print("[PASS] test_prefix_extraction passed.")
    test_all_uppercase()
    print("[PASS] test_all_uppercase passed.")
    test_optimal_yaw_orthogonal()
    print("[PASS] test_optimal_yaw_orthogonal passed.")
    test_optimal_yaw_deviation_split()
    print("[PASS] test_optimal_yaw_deviation_split passed.")
    print("\nALL UNIT TESTS PASSED SUCCESSFULLY!")


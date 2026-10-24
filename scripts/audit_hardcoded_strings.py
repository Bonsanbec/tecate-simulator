#!/usr/bin/env python3
"""
Auditor de Cadenas de Texto Literales (Zero Hardcoded Strings) para Tecate Simulator.

Inspecciona scripts GDScript en busca de cadenas literales crudas no centralizadas
en AppStrings o AppTechnicalStrings.

Uso:
    python3 scripts/audit_hardcoded_strings.py [--scope {ui,systems,all}] [--path DIR] [--strict]
"""

import argparse
import os
import re
import sys
from typing import List, Tuple

# Archivos exentos donde se definen las constantes canónicas o datos de catálogo
WHITELIST_FILES = {
    "systems/core/constants/app_strings.gd",
    "systems/core/constants/app_technical_strings.gd",
    "systems/core/constants/app_constants.gd",
    "systems/characters/character_catalog.gd", # Catálogo de datos dinámicos (Normativa Sec 2.7)
    "systems/minigames/minigame_catalog.gd",   # Catálogo de datos dinámicos (Normativa Sec 2.7)
}

# Carpetas exentas por tratarse de herramientas de importación o tests
EXEMPT_DIRS = {
    ".godot",
    "build",
    "tests",
    "tools",
}

def is_exempt_file(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    if normalized in WHITELIST_FILES:
        return True
    parts = normalized.split("/")
    for part in parts:
        if part in EXEMPT_DIRS:
            return True
    return False

def scan_file_for_hardcoded_strings(file_path: str) -> List[Tuple[int, str]]:
    violations: List[Tuple[int, str]] = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_multiline_comment = False
    in_multiline_docstring = False

    for idx, raw_line in enumerate(lines, 1):
        line = raw_line.strip()

        # Manejar comentarios de línea
        if line.startswith("#"):
            continue

        # Filtrar anotaciones (@export, @onready, etc.)
        if line.startswith("@export") or line.startswith("@onready") or line.startswith("@rpc"):
            continue

        # Filtrar directivas de clase, señal y herencia
        if line.startswith("class_name") or line.startswith("extends") or line.startswith("signal "):
            continue

        # Omitir preload y load canónicos que no usan constantes
        if line.startswith("const ") and ("preload(" in line or "load(" in line):
            continue

        # Buscar literales de comillas dobles o simples
        # Ignoramos NodePaths ($"...", ^"...") y StringNames (&"...")
        cleaned_line = re.sub(r'[\$\^\&]\"[^\"]*\"', '', line)
        cleaned_line = re.sub(r'[\$\^\&]\'[^\']*\'', '', cleaned_line)
        # Ignorar comentarios de fin de línea
        cleaned_line = re.sub(r'#.*$', '', cleaned_line)

        # Buscar strings literales restantes
        matches = re.findall(r'(\"[^\"]+\"|\'[^\']+\')', cleaned_line)
        for m in matches:
            literal = m[1:-1]
            # Omitir cadenas vacías, símbolos de formato técnico o separadores de formato
            if not literal or literal.strip() == "":
                continue
            # Ignorar claves de formato técnico puro como "%s", "%d", "\n", ","
            if literal in ["%s", "%d", "%f", "%4.1f", "\n", " ", "", ",", ":", ".", "->", "|", "/", "\\", "_"]:
                continue
            # Ignorar nombres de propiedades usados en tweens técnicos o metadata
            if literal in ["modulate", "modulate:a", "global_position", "position", "rotation", "scale", "quaternion"]:
                continue
            # Ignorar operadores de tween
            if literal.startswith("modulate") or literal.startswith("position"):
                continue

            violations.append((idx, m))

    return violations

def audit_app_strings_normative(app_strings_path: str) -> List[Tuple[int, str, str]]:
    violations = []
    if not os.path.exists(app_strings_path):
        return violations

    with open(app_strings_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for idx, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if line.startswith("#"):
            continue

        matches = re.findall(r'\"([^\"]*)\"', line)
        for s in matches:
            if "[" in s or "]" in s:
                violations.append((idx, s, "Prohibición de corchetes ([...]) en textos de usuario"))
            if "(" in s or ")" in s:
                violations.append((idx, s, "Prohibición de paréntesis ((...)) en textos o formatos"))
            if "/" in s and s != "km/h" and not s.endswith("km/h"):
                violations.append((idx, s, "Prohibición de barras inclinadas (/); use conjunciones 'y' u 'o'"))
            if "∞" in s:
                violations.append((idx, s, "Prohibición de símbolo infinito (∞); use 'Ilimitado'"))
            if any(ord(c) > 0x1F000 for c in s):
                violations.append((idx, s, "Prohibición de emojis en cadenas de texto"))

            # Detección de mayúsculas sostenidas (ALL CAPS) excepto marca "TECATE" o acrónimos
            words = re.findall(r'\b[A-ZÁÉÍÓÚÑ]{4,}\b', s)
            for w in words:
                if w not in ["TECATE", "BBVA", "TELCEL", "SEND"]:
                    violations.append((idx, s, f"Prohibición de mayúsculas sostenidas: palabra '{w}'"))

    return violations

def audit_directory(base_dir: str, scope: str = "all", strict: bool = False) -> int:
    total_violations = 0
    scanned_files = 0

    print(f"========================================================")
    print(f" AUDITORÍA DE CADENAS DE TEXTO (ZERO HARDCODED STRINGS)")
    print(f" Directorio base: {base_dir} | Ámbito: {scope}")
    print(f"========================================================")

    # 1. Auditoría normativa estricta sobre AppStrings
    app_strings_path = os.path.join(base_dir, "systems/core/constants/app_strings.gd")
    if os.path.exists(app_strings_path):
        norm_violations = audit_app_strings_normative(app_strings_path)
        if norm_violations:
            print(f"\n[VIOLACIÓN NORMATIVA] AppStrings presenta {len(norm_violations)} infracciones de estilo:")
            for line_num, val, rule in norm_violations:
                print(f"  • Línea {line_num}: \"{val}\" -> {rule}")
            total_violations += len(norm_violations)
        else:
            print("[OK] AppStrings cumple al 100% las reglas normativas (sin slashes, corchetes, paréntesis, ALL CAPS ni emojis).")

    for root, dirs, files in os.walk(base_dir):
        # Filtrar directorios exentos
        dirs[:] = [d for d in dirs if d not in EXEMPT_DIRS]

        for file in sorted(files):
            if not file.endswith(".gd"):
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir).replace("\\", "/")

            if is_exempt_file(rel_path):
                continue

            # Filtrar por ámbito si se solicita
            if scope == "ui" and not rel_path.startswith("ui/"):
                continue
            elif scope == "systems" and not rel_path.startswith("systems/"):
                continue

            scanned_files += 1
            file_violations = scan_file_for_hardcoded_strings(full_path)

            if file_violations:
                print(f"\n[VIOLACIÓN] {rel_path} ({len(file_violations)} cadenas literales no centralizadas):")
                for line_num, lit in file_violations:
                    print(f"  • Línea {line_num}: {lit}")
                total_violations += len(file_violations)

    print(f"\n========================================================")
    print(f" RESUMEN DE AUDITORÍA")
    print(f"  Archivos analizados: {scanned_files}")
    print(f"  Infracciones totales: {total_violations}")
    print(f"========================================================")

    if total_violations == 0:
        print("[OK] Cero cadenas literales no centralizadas. Cumplimiento de política exitoso.")
        return 0
    else:
        print(f"[ERROR] Se encontraron {total_violations} infracciones a la política de strings.")
        print("  Corrija las infracciones para cumplir estrictamente con docs/strings.md.")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Auditor de cadenas de texto para Tecate Simulator")
    parser.add_argument("--path", default="godot_project", help="Ruta al proyecto Godot")
    parser.add_argument("--scope", choices=["ui", "systems", "all"], default="ui", help="Ámbito de auditoría")
    parser.add_argument("--strict", action="store_true", help="Modo estricto")
    args = parser.parse_args()

    exit_code = audit_directory(args.path, scope=args.scope, strict=args.strict)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CLI de Control, Observación e Inspección Autónoma de Tecate Simulator.
Permite ejecutar el cliente deshidratado del juego en godot_project/,
gestionar la reimportación automática de assets, inyectar inputs,
extraer telemetría compacta en JSON y generar capturas bajo demanda.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = ROOT_DIR / "godot_project"
RUNNER_SCRIPT = ROOT_DIR / "scripts" / "desiccated_client_runner.gd"

PID_FILE = Path("/tmp/tecate_client.pid")
CMD_FILE = Path("/tmp/tecate_client_cmd.json")
RESP_FILE = Path("/tmp/tecate_client_resp.json")
LOG_FILE = Path("/tmp/godot.log")


def resolve_godot_path() -> str:
    """Detecta el binario oficial de Godot en el sistema."""
    env_path = os.environ.get("GODOT_PATH") or os.environ.get("GODOT")
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path

    candidates = [
        "/Applications/Godot_mono.app/Contents/MacOS/Godot",
        "/Applications/Godot.app/Contents/MacOS/Godot",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c

    for name in ["godot-mono", "godot4", "godot"]:
        found = shutil.which(name)
        if found:
            return found

    return "godot"


def ensure_assets_imported(godot_path: str, force: bool = False) -> None:
    """Valida la presencia de assets importados o ejecuta un pase rápido de importación."""
    imported_dir = PROJECT_DIR / ".godot" / "imported"
    if force or not imported_dir.exists():
        print("[INFO] Ejecutando pase de importación de Godot...", file=sys.stderr)
        subprocess.run(
            [godot_path, "--headless", "--editor", "--quit", "--log-file", str(LOG_FILE)],
            cwd=str(PROJECT_DIR),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


def send_ipc_command(cmd_dict: dict, timeout_sec: float = 6.0) -> dict:
    """Envía un comando al cliente deshidratado en modo sesión y espera respuesta."""
    if not PID_FILE.exists():
        return {"status": "ERROR", "message": "No hay sesión interactiva activa. Ejecuta 'start' primero."}

    # Limpiar respuesta previa si existía
    if RESP_FILE.exists():
        RESP_FILE.unlink()

    with open(CMD_FILE, "w", encoding="utf-8") as f:
        json.dump(cmd_dict, f)

    start_t = time.time()
    while time.time() - start_t < timeout_sec:
        if RESP_FILE.exists():
            try:
                with open(RESP_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                RESP_FILE.unlink()
                return data
            except json.JSONDecodeError:
                pass
        time.sleep(0.05)

    return {"status": "ERROR", "message": "Tiempo de espera agotado esperando respuesta del motor."}


def cmd_run(args: argparse.Namespace) -> int:
    """Ejecuta una inspección atómica en modo One-Shot con cwd en godot_project/."""
    godot = resolve_godot_path()
    ensure_assets_imported(godot, force=args.reimport)

    cmd = [
        godot,
        "--log-file", str(LOG_FILE),
        "--rendering-driver", args.driver,
        "-s", str(RUNNER_SCRIPT),
        "--resolution", "1280x720",
        "--windowed",
        "--"
    ]

    if args.scenario:
        cmd.extend(["--config", str(Path(args.scenario).resolve())])
    if args.hour is not None and not args.scenario:
        cmd.extend(["--hour", str(args.hour)])
    elif args.hour is not None and "--hour" in sys.argv:
        cmd.extend(["--hour", str(args.hour)])
    if args.realtime_sky:
        cmd.append("--realtime-sky")
    if args.perspective and "--perspective" in sys.argv:
        cmd.extend(["--perspective", args.perspective])
    if args.keep_start_menu:
        cmd.append("--keep-start-menu")
    if args.teleport:
        cmd.extend(["--teleport", args.teleport])
    if args.inputs:
        cmd.extend(["--inputs", args.inputs])
    if args.capture_path and "--capture-path" in sys.argv:
        abs_cap = str(Path(args.capture_path).resolve())
        cmd.extend(["--capture-path", abs_cap])
    if args.capture_frame and "--capture-frame" in sys.argv:
        cmd.extend(["--capture-frame", str(args.capture_frame)])
    if args.total_frames and "--total-frames" in sys.argv:
        cmd.extend(["--total-frames", str(args.total_frames)])

    if args.verbose:
        print("[INFO] Ejecutando desde godot_project/:", " ".join(cmd), file=sys.stderr)

    env = os.environ.copy()
    env["TMPDIR"] = "/tmp"

    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )

    telemetry = None
    output_lines = []

    for line in proc.stdout:
        output_lines.append(line)
        if "TELEMETRY_JSON:" in line:
            json_part = line.split("TELEMETRY_JSON:", 1)[1].strip()
            try:
                telemetry = json.loads(json_part)
            except json.JSONDecodeError:
                pass

    proc.wait()

    if telemetry:
        print(json.dumps(telemetry, indent=2 if args.pretty else None, ensure_ascii=False))
        return 0 if telemetry.get("status") == "PASS" else 1

    if proc.returncode != 0:
        print("[ERROR] El proceso de Godot terminó con código:", proc.returncode, file=sys.stderr)
        if args.verbose or not telemetry:
            print("--- Salida de Consola ---", file=sys.stderr)
            print("".join(output_lines[-20:]), file=sys.stderr)
        return proc.returncode

    return 0


def cmd_start(args: argparse.Namespace) -> int:
    """Inicia el cliente deshidratado en modo sesión interactiva (daemon)."""
    if PID_FILE.exists():
        print("[AVISO] Ya existe una sesión activa o un archivo de PID previo.", file=sys.stderr)
        return 0

    godot = resolve_godot_path()
    ensure_assets_imported(godot, force=args.reimport)

    cmd = [
        godot,
        "--log-file", str(LOG_FILE),
        "--rendering-driver", args.driver,
        "-s", str(RUNNER_SCRIPT),
        "--resolution", "1280x720",
        "--windowed",
        "--",
        "--ipc-mode"
    ]
    if args.hour is not None:
        cmd.extend(["--hour", str(args.hour)])

    env = os.environ.copy()
    env["TMPDIR"] = "/tmp"

    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env
    )

    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    print(f"[OK] Sesión interactiva iniciada con PID: {proc.pid}")

    # Esperar a que el motor inicialice la escena
    time.sleep(1.5)
    res = send_ipc_command({"op": "status"}, timeout_sec=15.0)
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res.get("status") == "PASS" else 1


def cmd_status(_args: argparse.Namespace) -> int:
    """Consulta la telemetría del jugador y estado del juego en la sesión activa."""
    res = send_ipc_command({"op": "status"})
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res.get("status") == "PASS" else 1


def cmd_teleport(args: argparse.Namespace) -> int:
    """Teletransporta al jugador a las coordenadas indicadas en la sesión activa."""
    res = send_ipc_command({
        "op": "teleport",
        "position": [args.x, args.y, args.z]
    })
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res.get("status") == "OK" else 1


def cmd_input(args: argparse.Namespace) -> int:
    """Inyecta una acción de input (presionar o soltar) en la sesión activa."""
    if args.duration > 0.0:
        send_ipc_command({"op": "input", "action": args.action, "pressed": True})
        time.sleep(args.duration)
        res = send_ipc_command({"op": "input", "action": args.action, "pressed": False})
    else:
        res = send_ipc_command({"op": "input", "action": args.action, "pressed": not args.release})
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res.get("status") == "OK" else 1


def cmd_capture(args: argparse.Namespace) -> int:
    """Solicita una captura de pantalla del viewport en la sesión activa."""
    abs_path = str(Path(args.path).resolve())
    res = send_ipc_command({
        "op": "capture",
        "path": abs_path
    })
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res.get("status") == "OK" else 1


def cmd_stop(_args: argparse.Namespace) -> int:
    """Detiene la sesión interactiva y libera el proceso."""
    if not PID_FILE.exists():
        print("[INFO] No hay sesión activa registrada.")
        return 0

    send_ipc_command({"op": "stop"}, timeout_sec=2.0)

    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        os.kill(pid, 15) # SIGTERM
    except Exception:
        pass

    if PID_FILE.exists():
        PID_FILE.unlink()
    if CMD_FILE.exists():
        CMD_FILE.unlink()
    if RESP_FILE.exists():
        RESP_FILE.unlink()

    print("[OK] Sesión interactiva detenida.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CLI Autónoma para Inspección y Control de Tecate Simulator (Godot 4)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando: run
    p_run = subparsers.add_parser("run", help="Ejecución atómica One-Shot con telemetría y captura")
    p_run.add_argument("--scenario", type=str, help="Ruta al archivo JSON de escenario/receta")
    p_run.add_argument("--hour", type=float, default=12.0, help="Hora simulada del día (ej. 12.0)")
    p_run.add_argument("--realtime-sky", action="store_true", help="Usar sincronización astronómica en tiempo real")
    p_run.add_argument("--perspective", choices=["1P", "3P"], default="1P", help="Perspectiva de cámara")
    p_run.add_argument("--keep-start-menu", action="store_true", help="No cerrar StartScreen (para probar UI)")
    p_run.add_argument("--teleport", type=str, help="Coordenadas de reubicación: X,Y,Z")
    p_run.add_argument("--inputs", type=str, help="Secuencia de inputs: accion:inicio:duracion")
    p_run.add_argument("--capture-path", type=str, default="scratch/desiccated_capture.png", help="Ruta de imagen")
    p_run.add_argument("--capture-frame", type=int, default=35, help="Frame exacto para la captura")
    p_run.add_argument("--total-frames", type=int, default=40, help="Total de frames a simular")
    p_run.add_argument("--driver", default="opengl3", choices=["opengl3", "vulkan"], help="Driver de renderizado")
    p_run.add_argument("--reimport", action="store_true", help="Forzar reimportación de assets antes de ejecutar")
    p_run.add_argument("--pretty", action="store_true", help="Imprimir JSON formateado legible")
    p_run.add_argument("--verbose", action="store_true", help="Mostrar logs detallados de Godot")
    p_run.set_defaults(func=cmd_run)

    # Subcomando: start
    p_start = subparsers.add_parser("start", help="Iniciar sesión interactiva en segundo plano")
    p_start.add_argument("--hour", type=float, default=12.0, help="Hora simulada del día")
    p_start.add_argument("--driver", default="opengl3", choices=["opengl3", "vulkan"], help="Driver de renderizado")
    p_start.add_argument("--reimport", action="store_true", help="Forzar reimportación de assets")
    p_start.set_defaults(func=cmd_start)

    # Subcomando: status
    p_status = subparsers.add_parser("status", help="Consultar telemetría de la sesión activa")
    p_status.set_defaults(func=cmd_status)

    # Subcomando: teleport
    p_teleport = subparsers.add_parser("teleport", help="Teletransportar al jugador en la sesión activa")
    p_teleport.add_argument("x", type=float, help="Coordenada X")
    p_teleport.add_argument("y", type=float, help="Coordenada Y")
    p_teleport.add_argument("z", type=float, help="Coordenada Z")
    p_teleport.set_defaults(func=cmd_teleport)

    # Subcomando: input
    p_input = subparsers.add_parser("input", help="Inyectar acción de input en la sesión activa")
    p_input.add_argument("action", type=str, help="Nombre de la acción (ej. move_forward, jump, sprint)")
    p_input.add_argument("--duration", type=float, default=0.0, help="Duración en segundos de pulsación")
    p_input.add_argument("--release", action="store_true", help="Liberar en lugar de presionar")
    p_input.set_defaults(func=cmd_input)

    # Subcomando: capture
    p_capture = subparsers.add_parser("capture", help="Capturar pantalla en la sesión activa")
    p_capture.add_argument("path", nargs="?", default="scratch/interactive_capture.png", help="Ruta de salida")
    p_capture.set_defaults(func=cmd_capture)

    # Subcomando: stop
    p_stop = subparsers.add_parser("stop", help="Detener la sesión interactiva activa")
    p_stop.set_defaults(func=cmd_stop)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

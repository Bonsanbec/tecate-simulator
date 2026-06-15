#!/usr/bin/env python3

import math
import argparse
import sys

# ============================================================
# CONFIGURACIÓN DEL MODELO ESPACIAL
# ============================================================

EARTH_RADIUS = 6378137.0

# Parque Hidalgo, Tecate
ORIGIN_LAT = 32.573229
ORIGIN_LON = -116.626536

# Calibración vertical:
# Y=14 ↔ 523 msnm
Y_OFFSET = 509

_LAT0_RAD = math.radians(ORIGIN_LAT)
_LON0_RAD = math.radians(ORIGIN_LON)

# ============================================================
# CONVERSIONES
# ============================================================

def gps_to_local(lat: float, lon: float):
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    x_local = (
        (lon_rad - _LON0_RAD)
        * EARTH_RADIUS
        * math.cos(_LAT0_RAD)
    )

    y_local = (
        (lat_rad - _LAT0_RAD)
        * EARTH_RADIUS
    )

    return x_local, y_local


def local_to_gps(x_local: float, y_local: float):
    lat_rad = _LAT0_RAD + (y_local / EARTH_RADIUS)

    lon_rad = (
        _LON0_RAD
        + x_local
        / (EARTH_RADIUS * math.cos(_LAT0_RAD))
    )

    return (
        math.degrees(lat_rad),
        math.degrees(lon_rad)
    )


def gps_to_minecraft_2d(lat: float, lon: float):
    x_local, y_local = gps_to_local(lat, lon)

    x_mc = round(x_local)
    z_mc = round(-y_local)

    return x_mc, z_mc


def gps_to_minecraft_3d(lat: float, lon: float, altitude_msnm: float):
    x_local, y_local = gps_to_local(lat, lon)

    x_mc = round(x_local)
    z_mc = round(-y_local)
    y_mc = round(altitude_msnm - Y_OFFSET)

    return x_mc, y_mc, z_mc


def minecraft_to_gps_2d(x_mc: float, z_mc: float):
    x_local = x_mc
    y_local = -z_mc

    return local_to_gps(x_local, y_local)


def minecraft_to_gps_3d(x_mc: float, y_mc: float, z_mc: float):
    lat, lon = minecraft_to_gps_2d(x_mc, z_mc)

    altitude_msnm = y_mc + Y_OFFSET

    return lat, lon, altitude_msnm


# ============================================================
# COMANDOS
# ============================================================

def cmd_gps2mc(args):
    x, y, z = gps_to_minecraft_3d(
        args.lat,
        args.lon,
        args.alt
    )

    print(f"{x} {y} {z}")


def cmd_mc2gps(args):
    lat, lon, alt = minecraft_to_gps_3d(
        args.x,
        args.y,
        args.z
    )

    print(f"LAT={lat:.8f}")
    print(f"LON={lon:.8f}")
    print(f"ALT={alt:.2f}")


def interactive():
    print("Spatial Model CLI")
    print("gps <lat> <lon> <alt>")
    print("mc <x> <y> <z>")
    print("exit")
    print()

    while True:
        try:
            line = input("> ").strip()

            if not line:
                continue

            if line.lower() in {"exit", "quit"}:
                break

            parts = line.split()

            if parts[0].lower() == "gps":

                if len(parts) != 4:
                    print("Uso: gps <lat> <lon> <alt>")
                    continue

                lat = float(parts[1])
                lon = float(parts[2])
                alt = float(parts[3])

                x, y, z = gps_to_minecraft_3d(
                    lat,
                    lon,
                    alt
                )

                print(f"X={x} Y={y} Z={z}")

            elif parts[0].lower() == "mc":

                if len(parts) != 4:
                    print("Uso: mc <x> <y> <z>")
                    continue

                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])

                lat, lon, alt = minecraft_to_gps_3d(
                    x,
                    y,
                    z
                )

                print(
                    f"LAT={lat:.8f} "
                    f"LON={lon:.8f} "
                    f"ALT={alt:.2f}"
                )

            else:
                print("Comando desconocido")

        except KeyboardInterrupt:
            print()
            break

        except Exception as ex:
            print(f"Error: {ex}")


# ============================================================
# MAIN
# ============================================================

def build_parser():
    parser = argparse.ArgumentParser(
        description="GPS <-> Minecraft Spatial Model"
    )

    sub = parser.add_subparsers(dest="command")

    gps2mc = sub.add_parser(
        "gps2mc",
        help="GPS -> Minecraft"
    )

    gps2mc.add_argument("lat", type=float)
    gps2mc.add_argument("lon", type=float)
    gps2mc.add_argument("alt", type=float)

    mc2gps = sub.add_parser(
        "mc2gps",
        help="Minecraft -> GPS"
    )

    mc2gps.add_argument("x", type=float)
    mc2gps.add_argument("y", type=float)
    mc2gps.add_argument("z", type=float)

    sub.add_parser(
        "interactive",
        help="Modo interactivo"
    )

    return parser


def main():
    parser = build_parser()

    if len(sys.argv) == 1:
        interactive()
        return

    args = parser.parse_args()

    if args.command == "gps2mc":
        cmd_gps2mc(args)

    elif args.command == "mc2gps":
        cmd_mc2gps(args)

    elif args.command == "interactive":
        interactive()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
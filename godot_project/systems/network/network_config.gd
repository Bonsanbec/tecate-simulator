extends Node

## Autoload Singleton: NetworkConfig
##
## Fuente única de verdad para la configuración de red TKT/1.
## Funciona en TODOS los exports (Android, iOS, Windows, Mac, Linux, Web).
##
## Cadena de prioridad (de menor a mayor):
##   1. Constantes internas en código (mínimo siempre disponible)
##   2. ProjectSettings (baked en project.godot → viajan en el export)
##   3. Archivo .env local en disco (solo activo en desarrollo, NUNCA llega a usuarios)
##
## El usuario final siempre recibe los valores de ProjectSettings.
## El desarrollador puede sobreescribir con .env localmente sin afectar a los usuarios.

# =============================================================================
# CONSTANTES ABSOLUTAS DE RESPALDO (nunca cambian, garantizan arranque mínimo)
# =============================================================================
const _DEFAULT_HOST: String = "api.tecate.bonsanbec.dev"
const _DEFAULT_PORT: int = 52665
const _DEFAULT_TICK_RATE: int = 30
const _DEFAULT_SESSION_TIMEOUT: float = 10.0
const _DEFAULT_INTERPOLATION_DELAY: float = 0.10
const _DEFAULT_LOCAL_DEV: bool = false
const _DEFAULT_DEBUG_NET: bool = false

# =============================================================================
# PROPIEDADES PÚBLICAS (usar estas en el resto del juego)
# =============================================================================
var server_host: String
var server_port: int
var tick_rate: int
var session_timeout: float
var interpolation_delay: float
var is_local_dev: bool
var debug_net: bool

## IP resuelta del servidor (solo disponible tras llamar a resolve() o start_connection)
var resolved_ip: String = ""

func _ready() -> void:
	_load_from_project_settings()
	_try_override_from_env_file()
	_apply_local_dev_flag()
	_log_config()

# =============================================================================
# PASO 1: Leer valores del project.godot (viajan en todos los exports)
# =============================================================================
func _load_from_project_settings() -> void:
	server_host = str(ProjectSettings.get_setting("network/tkt/server_host", _DEFAULT_HOST))
	server_port = int(ProjectSettings.get_setting("network/tkt/server_port", _DEFAULT_PORT))
	tick_rate = int(ProjectSettings.get_setting("network/tkt/tick_rate", _DEFAULT_TICK_RATE))
	session_timeout = float(ProjectSettings.get_setting("network/tkt/session_timeout", _DEFAULT_SESSION_TIMEOUT))
	interpolation_delay = float(ProjectSettings.get_setting("network/tkt/interpolation_delay", _DEFAULT_INTERPOLATION_DELAY))
	is_local_dev = bool(ProjectSettings.get_setting("network/tkt/local_dev", _DEFAULT_LOCAL_DEV))
	debug_net = bool(ProjectSettings.get_setting("network/tkt/debug_net", _DEFAULT_DEBUG_NET))

# =============================================================================
# PASO 2: Sobreescritura opcional con .env local (solo sirve en desarrollo)
# Solo tiene efecto si el archivo .env existe en el sistema de archivos local.
# En builds exportadas a Android/iOS/Windows/etc. FileAccess.file_exists()
# devolverá false y este bloque NO se ejecuta → los usuarios nunca son afectados.
# =============================================================================
func _try_override_from_env_file() -> void:
	var search_paths: Array[String] = [
		"res://.env",
		"res://../.env",
		"res://../server/.env",
		"user://.env",
	]

	for path in search_paths:
		if FileAccess.file_exists(path):
			_parse_env_file(path)
			if debug_net:
				print("[NetworkConfig] Override de .env aplicado desde: ", path)
			break

func _parse_env_file(path: String) -> void:
	var f = FileAccess.open(path, FileAccess.READ)
	if not f:
		return

	while not f.eof_reached():
		var line = f.get_line().strip_edges()
		if line.is_empty() or line.begins_with("#"):
			continue
		if "=" not in line:
			continue

		var parts = line.split("=", true, 1)
		var key = parts[0].strip_edges()
		var val = parts[1].strip_edges().trim_prefix("\"").trim_suffix("\"").trim_prefix("'").trim_suffix("'")

		match key:
			"TECATE_SERVER_HOST", "PUBLIC_HOST":
				server_host = str(val)
			"TECATE_SERVER_PORT", "SERVER_PORT":
				server_port = int(val)
			"TECATE_TICK_RATE", "TICK_RATE":
				tick_rate = int(val)
			"TECATE_LOCAL_DEV":
				is_local_dev = str(val).to_lower() in ["true", "1", "yes"]
			"TECATE_DEBUG_NET":
				debug_net = str(val).to_lower() in ["true", "1", "yes"]

	f.close()

func _apply_local_dev_flag() -> void:
	if is_local_dev:
		server_host = "127.0.0.1"
		resolved_ip = "127.0.0.1"

func _log_config() -> void:
	print("[NetworkConfig] Servidor: %s:%d | TickRate=%d | LocalDev=%s | Debug=%s" % [
		server_host, server_port, tick_rate, is_local_dev, debug_net
	])

# =============================================================================
# API PÚBLICA
# =============================================================================

## Resuelve el nombre de host a IP (necesario si es dominio, no IP directa).
## Retorna "" si la resolución falla (host no disponible → modo offline).
func resolve_host() -> String:
	if is_local_dev or server_host.is_valid_ip_address():
		resolved_ip = server_host
		return resolved_ip

	var ip = IP.resolve_hostname(server_host, IP.TYPE_IPV4)
	if ip.is_valid_ip_address():
		resolved_ip = ip
		if debug_net:
			print("[NetworkConfig] DNS resuelto: %s → %s" % [server_host, ip])
	else:
		resolved_ip = ""
		push_warning("[NetworkConfig] No se pudo resolver '%s'. Modo fuera de línea activo." % server_host)

	return resolved_ip

## True si la última resolución de DNS fue exitosa.
func is_server_reachable() -> bool:
	return resolved_ip != ""

class_name EnvLoader
extends RefCounted

## Utilidad para cargar variables de configuración desde archivos .env en Godot 4.
## Busca en "res://.env", "res://../.env" o "user://.env".

static func load_env() -> Dictionary:
	var env_data: Dictionary = {
		"TECATE_SERVER_HOST": "api.tecate.bonsanbec.dev",
		"TECATE_SERVER_PORT": 52665,
		"TECATE_LOCAL_DEV": false,
		"TECATE_TICK_RATE": 30,
		"TECATE_RECONNECT_DELAY": 3.0,
		"TECATE_INTERPOLATION_DELAY": 0.10,
		"TECATE_DEBUG_NET": false
	}

	var search_paths = [
		"res://.env",
		"res://../server/.env",
		"res://../.env",
		"user://.env"
	]

	for path in search_paths:
		if FileAccess.file_exists(path):
			_parse_env_file(path, env_data)
			break

	# Si está activo el modo desarrollo local, sobreescribir host a 127.0.0.1
	if env_data["TECATE_LOCAL_DEV"]:
		env_data["TECATE_SERVER_HOST"] = "127.0.0.1"

	return env_data

static func _parse_env_file(path: String, out_dict: Dictionary) -> void:
	var f = FileAccess.open(path, FileAccess.READ)
	if not f:
		return

	while not f.eof_reached():
		var line = f.get_line().strip_edges()
		if line.is_empty() or line.begins_with("#"):
			continue
		if "=" in line:
			var parts = line.split("=", true, 1)
			var key = parts[0].strip_edges()
			var val = parts[1].strip_edges().strip_edges().trim_prefix("\"").trim_suffix("\"").trim_prefix("'").trim_suffix("'")

			# Mapeo de variables de server/.env a convención TECATE_*
			if key == "SERVER_BIND_HOST" or key == "PUBLIC_HOST":
				if not out_dict.get("TECATE_LOCAL_DEV", false):
					out_dict["TECATE_SERVER_HOST"] = val
			elif key == "SERVER_PORT":
				out_dict["TECATE_SERVER_PORT"] = int(val)
			elif key == "TICK_RATE":
				out_dict["TECATE_TICK_RATE"] = int(val)
			elif key == "TECATE_SERVER_HOST":
				out_dict["TECATE_SERVER_HOST"] = val
			elif key == "TECATE_SERVER_PORT":
				out_dict["TECATE_SERVER_PORT"] = int(val)
			elif key == "TECATE_LOCAL_DEV":
				out_dict["TECATE_LOCAL_DEV"] = val.to_lower() in ["true", "1", "yes"]
			elif key == "TECATE_DEBUG_NET":
				out_dict["TECATE_DEBUG_NET"] = val.to_lower() in ["true", "1", "yes"]
			else:
				out_dict[key] = val
	f.close()

extends SceneTree

## Runner Externo de Cliente Deshidratado de Tecate Simulator
## Permite la ejecución, control de inputs, telemetría y captura visual
## sin alterar ni integrar una sola línea de código dentro de godot_project/.

var _config: Dictionary = {
	"scene": "",
	"hour": 12.0,
	"realtime_sky": false,
	"skip_start_menu": true,
	"perspective": "1P", # "1P" o "3P"
	"teleport": [],
	"inputs": [], # [{"action": "move_forward", "start_frame": 15, "duration": 20}]
	"capture_frame": 35,
	"capture_path": "scratch/desiccated_capture.png",
	"capture_width": 1024,
	"capture_height": 576,
	"total_frames": 40,
	"ipc_mode": false, # Modo sesión continua escuchando comandos
	"command_file": "/tmp/tecate_client_cmd.json",
	"response_file": "/tmp/tecate_client_resp.json"
}

var _frames: int = 0
var _inst: Node = null
var _player: CharacterBody3D = null
var _sky_system: Node = null
var _start_screen: Node = null
var _is_initialized: bool = false
var _active_actions: Array = []
var _screenshot_saved: bool = false
var _saved_screenshot_path: String = ""
var _saved_screenshot_size: Vector2i = Vector2i.ZERO

func _init() -> void:
	_parse_arguments()
	_load_and_instantiate_scene()

func _parse_arguments() -> void:
	var user_args: PackedStringArray = OS.get_cmdline_user_args()
	var i: int = 0
	while i < user_args.size():
		var arg: String = user_args[i]
		if arg == "--config" and i + 1 < user_args.size():
			_load_config_file(user_args[i + 1])
			i += 2
			continue
		elif arg == "--hour" and i + 1 < user_args.size():
			_config["hour"] = user_args[i + 1].to_float()
			i += 2
			continue
		elif arg == "--realtime-sky":
			_config["realtime_sky"] = true
			i += 1
			continue
		elif arg == "--perspective" and i + 1 < user_args.size():
			_config["perspective"] = user_args[i + 1].to_upper()
			i += 2
			continue
		elif arg == "--keep-start-menu":
			_config["skip_start_menu"] = false
			i += 1
			continue
		elif arg == "--teleport" and i + 1 < user_args.size():
			var parts = user_args[i + 1].split(",")
			if parts.size() == 3:
				_config["teleport"] = [parts[0].to_float(), parts[1].to_float(), parts[2].to_float()]
			i += 2
			continue
		elif arg == "--capture-path" and i + 1 < user_args.size():
			_config["capture_path"] = user_args[i + 1]
			i += 2
			continue
		elif arg == "--capture-frame" and i + 1 < user_args.size():
			_config["capture_frame"] = user_args[i + 1].to_int()
			i += 2
			continue
		elif arg == "--total-frames" and i + 1 < user_args.size():
			_config["total_frames"] = user_args[i + 1].to_int()
			i += 2
			continue
		elif arg == "--inputs" and i + 1 < user_args.size():
			# Formato: "move_forward:15:20,jump:25:5" (accion:inicio:duracion)
			_config["inputs"] = _parse_inputs_arg(user_args[i + 1])
			i += 2
			continue
		elif arg == "--ipc-mode":
			_config["ipc_mode"] = true
			i += 1
			continue
		i += 1

func _load_config_file(file_path: String) -> void:
	var candidates: Array = [
		file_path,
		ProjectSettings.globalize_path("res://../" + file_path),
		ProjectSettings.globalize_path(file_path),
		ProjectSettings.globalize_path("res://" + file_path)
	]
	var found_path: String = ""
	for c in candidates:
		if FileAccess.file_exists(c):
			found_path = c
			break
	if found_path.is_empty():
		return
	var fa = FileAccess.open(found_path, FileAccess.READ)
	if fa:
		var json_str = fa.get_as_text()
		fa.close()
		var parsed = JSON.parse_string(json_str)
		if parsed is Dictionary:
			for k in parsed.keys():
				_config[k] = parsed[k]

func _parse_inputs_arg(raw: String) -> Array:
	var res: Array = []
	var entries = raw.split(",")
	for e in entries:
		var p = e.split(":")
		if p.size() >= 3:
			res.append({
				"action": p[0],
				"start_frame": p[1].to_int(),
				"duration": p[2].to_int()
			})
		elif p.size() == 2:
			res.append({
				"action": p[0],
				"start_frame": 15,
				"duration": p[1].to_int()
			})
	return res

func _load_and_instantiate_scene() -> void:
	var scene_path: String = _config.get("scene", "")
	if scene_path.is_empty():
		scene_path = ProjectSettings.get_setting("application/run/main_scene")
	if scene_path.is_empty():
		scene_path = "res://main.tscn"

	var scene_res = load(scene_path)
	if not scene_res:
		_emit_error_and_exit("No se pudo cargar la escena principal: " + scene_path)
		return

	_inst = scene_res.instantiate()
	root.add_child(_inst)

func _process(_delta: float) -> bool:
	_frames += 1

	if _config.get("ipc_mode", false):
		_process_ipc()
		return false

	_process_batch_mode()
	return false

func _process_batch_mode() -> void:
	# Fase 1: Calibración de Entorno y Atmósfera (Frame 5)
	if _frames == 5:
		_setup_atmosphere_and_sky()

	# Fase 2: Configuración de Jugador, Cámara y HUD (Frame 10)
	if _frames == 10:
		_setup_player_and_menu()

	# Fase 3: Inyección de Inputs Programados
	_process_scheduled_inputs()

	# Fase 4: Captura de Pantalla
	if _frames == _config.get("capture_frame", 35):
		_take_screenshot(_config.get("capture_path", "scratch/desiccated_capture.png"))

	# Fase 5: Finalización y Emisión de Telemetría
	if _frames >= _config.get("total_frames", 40):
		_finalize_and_exit()

func _setup_atmosphere_and_sky() -> void:
	_sky_system = root.find_child("SkySystem", true, false)
	if _sky_system:
		if not _config.get("realtime_sky", false):
			_sky_system.realtime_sync = false
			_sky_system.manual_hour = _config.get("hour", 12.0)
			if _sky_system.has_method("_apply_manual_hour_to_simulated_time"):
				_sky_system._apply_manual_hour_to_simulated_time()

func _setup_player_and_menu() -> void:
	_start_screen = root.find_child("StartScreen", true, false)
	if _start_screen and _config.get("skip_start_menu", true):
		if _start_screen.has_method("close_menu"):
			_start_screen.close_menu()

	_player = root.find_child("Player", true, false) as CharacterBody3D
	if _player:
		# Teletransporte si fue especificado
		var t_pos: Array = _config.get("teleport", [])
		if t_pos.size() == 3:
			_player.global_position = Vector3(t_pos[0], t_pos[1], t_pos[2])
			if "spawn_position" in _player:
				_player.spawn_position = _player.global_position

		# Configurar perspectiva y HUD
		if "camera_director" in _player and _player.camera_director:
			var cam_dir = _player.camera_director
			var mode_req = _config.get("perspective", "1P")
			if mode_req == "3P" and cam_dir.has_method("set_perspective"):
				cam_dir.set_perspective(1) # THIRD_PERSON = 1
			elif cam_dir.cam_1p:
				cam_dir.cam_1p.make_current()

		if "hud" in _player and _player.hud and _player.hud.has_method("show_hud"):
			_player.hud.show_hud()

func _process_scheduled_inputs() -> void:
	var inputs: Array = _config.get("inputs", [])
	for item in inputs:
		var act: String = item.get("action", "")
		var start: int = item.get("start_frame", 0)
		var dur: int = item.get("duration", 0)
		var end_frame: int = start + dur

		if _frames == start:
			Input.action_press(act)
			if not _active_actions.has(act):
				_active_actions.append(act)
		elif _frames == end_frame:
			Input.action_release(act)
			_active_actions.erase(act)

func _take_screenshot(target_rel_path: String) -> void:
	var vp = root.get_viewport()
	if not vp:
		return
	var img = vp.get_texture().get_image()
	if not img:
		return

	var req_w: int = _config.get("capture_width", 1024)
	var req_h: int = _config.get("capture_height", 576)
	if req_w > 0 and req_h > 0 and (img.get_width() != req_w or img.get_height() != req_h):
		img.resize(req_w, req_h, Image.INTERPOLATE_LANCZOS)

	var full_p: String = target_rel_path if target_rel_path.is_absolute_path() else ProjectSettings.globalize_path("res://../" + target_rel_path)
	# Asegurar directorio padre
	var parent_dir = full_p.get_base_dir()
	if not DirAccess.dir_exists_absolute(parent_dir):
		DirAccess.make_dir_recursive_absolute(parent_dir)

	var err = img.save_png(full_p)
	if err == OK:
		_screenshot_saved = true
		_saved_screenshot_path = full_p
		_saved_screenshot_size = img.get_size()

func _finalize_and_exit() -> void:
	# Liberar inputs que pudieran haber quedado activos
	for act in _active_actions:
		Input.action_release(act)
	_active_actions.clear()

	var telemetry: Dictionary = _collect_telemetry()
	print("TELEMETRY_JSON: ", JSON.stringify(telemetry))

	if _inst:
		_inst.queue_free()
	quit(0)

func _collect_telemetry() -> Dictionary:
	var pos: Array = []
	var vel: Array = []
	var on_floor: bool = false
	var input_en: bool = false

	if _player:
		pos = [_player.global_position.x, _player.global_position.y, _player.global_position.z]
		if "velocity" in _player:
			vel = [_player.velocity.x, _player.velocity.y, _player.velocity.z]
		if _player.has_method("is_on_floor"):
			on_floor = _player.is_on_floor()
		if "input_enabled" in _player:
			input_en = _player.input_enabled

	return {
		"status": "PASS",
		"frames_simulated": _frames,
		"player_found": _player != null,
		"player_pos": pos,
		"player_velocity": vel,
		"is_on_floor": on_floor,
		"input_enabled": input_en,
		"screenshot_saved": _screenshot_saved,
		"screenshot_path": _saved_screenshot_path,
		"screenshot_size": [_saved_screenshot_size.x, _saved_screenshot_size.y],
		"fps": Performance.get_monitor(Performance.TIME_FPS)
	}

# -----------------------------------------------------------------------------
# Soporte de Sesión Interactiva IPC (Bajo Demanda CLI)
# -----------------------------------------------------------------------------
func _process_ipc() -> void:
	if _frames == 5:
		_setup_atmosphere_and_sky()
	if _frames == 10:
		_setup_player_and_menu()

	var cmd_file: String = _config.get("command_file", "/tmp/tecate_client_cmd.json")
	var resp_file: String = _config.get("response_file", "/tmp/tecate_client_resp.json")

	if FileAccess.file_exists(cmd_file):
		var fa = FileAccess.open(cmd_file, FileAccess.READ)
		if fa:
			var txt = fa.get_as_text()
			fa.close()
			DirAccess.remove_absolute(cmd_file) # Consumir comando

			var cmd_dict = JSON.parse_string(txt)
			if cmd_dict is Dictionary:
				var res = _execute_ipc_command(cmd_dict)
				var out_fa = FileAccess.open(resp_file, FileAccess.WRITE)
				if out_fa:
					out_fa.store_string(JSON.stringify(res))
					out_fa.close()

func _execute_ipc_command(cmd: Dictionary) -> Dictionary:
	var op: String = cmd.get("op", "")
	if op == "status":
		return _collect_telemetry()
	elif op == "teleport":
		var pos = cmd.get("position", [])
		if pos.size() == 3 and _player:
			_player.global_position = Vector3(pos[0], pos[1], pos[2])
			if "spawn_position" in _player:
				_player.spawn_position = _player.global_position
			return {"status": "OK", "telemetry": _collect_telemetry()}
	elif op == "input":
		var act = cmd.get("action", "")
		var pressed = cmd.get("pressed", true)
		if not act.is_empty():
			if pressed:
				Input.action_press(act)
			else:
				Input.action_release(act)
			return {"status": "OK", "action": act, "pressed": pressed}
	elif op == "capture":
		var path = cmd.get("path", "scratch/interactive_capture.png")
		_take_screenshot(path)
		return {"status": "OK", "path": _saved_screenshot_path, "size": [_saved_screenshot_size.x, _saved_screenshot_size.y]}
	elif op == "stop":
		if _inst:
			_inst.queue_free()
		quit(0)
		return {"status": "STOPPING"}

	return {"status": "UNKNOWN_OP", "op": op}

func _emit_error_and_exit(msg: String) -> void:
	print("TELEMETRY_JSON: ", JSON.stringify({"status": "ERROR", "message": msg}))
	quit(1)

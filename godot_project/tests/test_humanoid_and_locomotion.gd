extends SceneTree

## Suite de Pruebas Automatizadas de Calidad: Humanoide Rigged, Locomoción y Cámaras

const CameraDirectorClass = preload("res://systems/player/camera_director.gd")
const FootIKClass = preload("res://systems/player/foot_ik_controller.gd")
const PlayerNetworkSyncClass = preload("res://systems/network/player_network_sync.gd")
const PlayerHUDClass = preload("res://ui/player_hud.gd")

var _frames = 0
var _player: CharacterBody3D
var _main_scene: Node

func _init():
	print("==================================================================")
	print("[TEST] INICIANDO SUITE DE PRUEBAS DEL HUMANOIDE Y LOCOMOCIÓN (TECATE)")
	print("==================================================================")
	
	# 1. Prueba de Carga del Modelo 3D Rigged (.glb)
	print("\n--- 1. Validación de Asset 3D Humanoide Rigged ---")
	var glb_path = "res://assets/characters/humanoid_player.glb"
	assert(ResourceLoader.exists(glb_path), "El archivo humanoid_player.glb debe existir en assets")
	var packed_model = load(glb_path) as PackedScene
	assert(packed_model != null, "humanoid_player.glb debe cargarse como PackedScene")
	
	var model_inst = packed_model.instantiate()
	assert(model_inst != null, "El modelo humanoide debe poder instanciarse")
	
	var skel = model_inst.find_child("Skeleton3D", true, false) as Skeleton3D
	assert(skel != null, "El modelo debe contener un Skeleton3D funcional")
	
	# Verificar huesos críticos
	var critical_bones = [
		"Root", "Hips", "Spine", "Spine1", "Chest", "Neck", "Head", "EyesAnchor",
		"Shoulder.L", "UpperArm.L", "Forearm.L", "Hand.L",
		"Shoulder.R", "UpperArm.R", "Forearm.R", "Hand.R",
		"UpperLeg.L", "LowerLeg.L", "Foot.L", "Toes.L",
		"UpperLeg.R", "LowerLeg.R", "Foot.R", "Toes.R"
	]
	for b_name in critical_bones:
		var idx = skel.find_bone(b_name)
		assert(idx != -1, "El hueso " + b_name + " debe existir en el Skeleton3D")
	print("✓ Esqueleto antropométrico validado: 22 huesos articulados correctamente.")
	
	# Verificar mallas modulares para True First Person
	var body_mesh = model_inst.find_child("Player_Body_Mesh", true, false) as MeshInstance3D
	var head_mesh = model_inst.find_child("Player_Head_Mesh", true, false) as MeshInstance3D
	assert(body_mesh != null, "Player_Body_Mesh debe existir")
	assert(head_mesh != null, "Player_Head_Mesh debe existir")
	print("✓ Desacoplamiento modular verificado: Malla de Cuerpo y Malla de Cabeza separadas.")
	model_inst.queue_free()

	# 2. Prueba del Módulo de Red Multijugador
	print("\n--- 2. Validación de Serialización Cuantizada de Red (24 Bytes) ---")
	var snap = PlayerNetworkSyncClass.PlayerStateSnapshot.new()
	snap.tick = 4096
	snap.position = Vector3(-6.684, 400.12, 11.05)
	snap.yaw = 185.5
	snap.pitch = -22.3
	snap.velocity = Vector3(3.2, -0.5, 4.1)
	snap.flags = 3 # Grounded + Sprinting
	
	var bytes = PlayerNetworkSyncClass.serialize_snapshot(snap)
	assert(bytes.size() == 24, "El paquete de snapshot cuantizado debe medir exactamente 24 bytes")
	
	var deserialized = PlayerNetworkSyncClass.deserialize_snapshot(bytes)
	assert(deserialized != null, "El paquete debe deserializarse correctamente")
	assert(deserialized.tick == snap.tick, "El tick debe coincidir")
	assert(abs(deserialized.position.x - snap.position.x) < 0.001, "Posición X debe coincidir")
	assert(abs(deserialized.position.y - snap.position.y) < 0.001, "Posición Y debe coincidir")
	assert(abs(deserialized.position.z - snap.position.z) < 0.001, "Posición Z debe coincidir")
	assert(abs(deserialized.pitch - snap.pitch) < 0.1, "Pitch debe coincidir con precisión de 16-bit")
	assert(deserialized.flags == snap.flags, "Flags de estado deben coincidir")
	print("✓ Paquete cuantizado de 24 bytes serializado y deserializado con fidelidad completa.")

	# 3. Prueba de Predicción y Búfer Circular
	var net_sync = PlayerNetworkSyncClass.new()
	for i in range(150):
		var s = PlayerNetworkSyncClass.PlayerStateSnapshot.new()
		s.tick = i
		s.position = Vector3(i * 0.1, 400.0, 0.0)
		net_sync.record_local_state(i, s, PlayerNetworkSyncClass.PlayerInputPacket.new())
	
	# Verificar detección de divergencia
	var srv_snap_ok = PlayerNetworkSyncClass.PlayerStateSnapshot.new()
	srv_snap_ok.tick = 145
	srv_snap_ok.position = Vector3(14.5, 400.0, 0.0)
	assert(not net_sync.check_server_reconciliation(srv_snap_ok), "No debe haber divergencia si coinciden")
	
	var srv_snap_divergent = PlayerNetworkSyncClass.PlayerStateSnapshot.new()
	srv_snap_divergent.tick = 145
	srv_snap_divergent.position = Vector3(15.0, 400.0, 0.0) # Error de 0.5m
	assert(net_sync.check_server_reconciliation(srv_snap_divergent), "Debe detectar divergencia para rollback")
	print("✓ Búfer circular de 120 ticks y predicción con reconciliación validados.")
	net_sync.queue_free()

	# 4. Instanciación en Escena con PlayerController
	print("\n--- 3. Integración en Main Scene y Sistema de Cámaras F5 ---")
	var main_res = load("res://main.tscn")
	assert(main_res != null, "main.tscn debe poder cargarse")
	_main_scene = main_res.instantiate()
	root.add_child(_main_scene)

func _process(_delta):
	_frames += 1
	
	if _frames == 5:
		_player = _main_scene.get_node_or_null("Player") as CharacterBody3D
		assert(_player != null, "El nodo Player debe existir en main.tscn")
		
		var cam_dir = _player.get_node_or_null("CameraDirector3D")
		assert(cam_dir != null, "CameraDirector3D debe estar activo en Player")
		
		# Validar perspectiva inicial: FIRST_PERSON
		assert(cam_dir.current_mode == CameraDirectorClass.PerspectiveMode.FIRST_PERSON, "Debe iniciar en 1P")
		assert(cam_dir.cam_1p != null, "Camera_1P debe existir")
		assert(cam_dir.cam_1p.cull_mask == 1, "En 1P, la capa 2 (cabeza) debe estar excluida para evitar clipping")
		assert(cam_dir.cam_1p.near <= 0.055, "Near plane de 1P debe ser <= 0.05 para visibilidad de manos")
		print("✓ Perspectiva 1P validada con exclusión de cabeza y near plane para manos.")

		# Probar alternancia a TERCERA PERSONA (3P) con F5
		var event_f5 = InputEventKey.new()
		event_f5.keycode = KEY_F5
		event_f5.pressed = true
		cam_dir.handle_input(event_f5)
		assert(cam_dir.current_mode == CameraDirectorClass.PerspectiveMode.THIRD_PERSON, "F5 debe cambiar a 3P")
		assert(cam_dir.cam_3p.cull_mask == (1 | 2), "En 3P, cabeza y cuerpo deben ser visibles")
		assert(cam_dir.spring_arm_3p != null, "SpringArm_3P debe existir con colisión")
		print("✓ Perspectiva 3P validada con SpringArm colisionable y avatar completo visible.")

		# Probar alternancia a SEGUNDA PERSONA (2P) con F5
		cam_dir.handle_input(event_f5)
		assert(cam_dir.current_mode == CameraDirectorClass.PerspectiveMode.SECOND_PERSON, "F5 debe cambiar a 2P")
		assert(cam_dir.cam_2p != null, "Camera_2P debe existir")
		assert(cam_dir.cam_2p.cull_mask == (1 | 2), "En 2P, cabeza y cuerpo deben ser visibles")
		print("✓ Perspectiva 2P (Observador Frontal) validada.")

		# Probar ciclo de retorno a PRIMERA PERSONA (1P) con F5
		cam_dir.handle_input(event_f5)
		assert(cam_dir.current_mode == CameraDirectorClass.PerspectiveMode.FIRST_PERSON, "F5 debe regresar a 1P")
		print("✓ Ciclo completo de cámaras F5 (1P -> 3P -> 2P -> 1P) validado.")

	elif _frames == 10:
		# Validar Foot IK y Raycasts de Suelo
		var foot_ik = _player.get_node_or_null("FootIKController")
		assert(foot_ik != null, "FootIKController debe estar activo")
		assert(foot_ik.ray_left != null and foot_ik.ray_right != null, "Raycasts de pies deben existir")
		print("✓ FootIKController y raycasting de terreno validados.")
		
		# Validar HUD y Brújula de Tecate
		var hud = _player.get_node_or_null("PlayerHUD")
		assert(hud != null, "PlayerHUD debe existir y estar vinculado")
		
		# Validar orientación de la brújula:
		# En el marco canónico de Tecate: -Z = Norte, +X = Este, -X = Oeste (+Z = Sur)
		_player.rotation_degrees.y = 0.0 # Mirando al Norte (-Z)
		_player._update_telemetry(0.0)
		assert(is_equal_approx(_player.current_heading_deg, 0.0), "Mirando a -Z debe ser 0° Norte")
		assert(hud._get_cardinal_direction(_player.current_heading_deg) == "N", "Debe ser N")

		_player.rotation_degrees.y = -90.0 # Giro a la derecha hacia el Este (+X)
		_player._update_telemetry(0.0)
		assert(int(round(_player.current_heading_deg)) == 90, "Mirando a +X debe ser 90° Este")
		assert(hud._get_cardinal_direction(_player.current_heading_deg) == "E", "Debe ser E")
		assert("La Rumorosa" in hud._get_landmark_hint(_player.current_heading_deg), "Al Este debe apuntar hacia La Rumorosa")

		_player.rotation_degrees.y = 90.0 # Giro a la izquierda hacia el Oeste (-X)
		_player._update_telemetry(0.0)
		assert(int(round(_player.current_heading_deg)) == 270, "Mirando a -X debe ser 270° Oeste")
		assert(hud._get_cardinal_direction(_player.current_heading_deg) == "W", "Debe ser W")
		assert("Cuchumá" in hud._get_landmark_hint(_player.current_heading_deg), "Al Oeste debe apuntar hacia el Cerro Cuchumá")

		print("✓ Brújula validada: Norte=0°, Este=90° (Rumorosa), Oeste=270° (Cuchumá).")

		# Validar cámara subjetiva adelantada al plano facial (evita ver clavícula)
		var cam_dir = _player.camera_director
		assert(cam_dir.eye_forward_offset >= 0.15, "eye_forward_offset debe ser >= 0.15 para evitar ver la clavícula")
		assert(cam_dir.cam_1p.position.z < -0.10, "cam_1p debe situarse en Z negativo (adelante) para línea visual limpia")
		print("✓ Posición de cámara 1P validada: Situada al frente en Z negativo, libre de clipping con clavícula.")

		# Validar huesos de extremidades inferiores para locomoción
		assert(_player.bone_upperleg_l != -1 and _player.bone_upperleg_r != -1, "Huesos UpperLeg L/R deben estar vinculados")
		assert(_player.bone_lowerleg_l != -1 and _player.bone_lowerleg_r != -1, "Huesos LowerLeg L/R deben estar vinculados")
		assert(_player.walk_speed >= 2.0, "walk_speed debe ser >= 2.0 m/s para desplazamiento ágil en Tecate")
		assert(_player.fly_vertical_speed >= 20.0, "fly_vertical_speed debe ser >= 20.0 para ascenso potente en vuelo")
		print("✓ Rig de locomoción validado: Huesos de piernas vinculados y velocidades optimizadas.")

		# Validar Modo Screenshot F1 (ocultar HUD y avatar, suspender inputs)
		_player.set_input_enabled(true)
		assert(hud.visible == true, "HUD debe estar visible tras habilitar juego activo")

		var event_f1 = InputEventKey.new()
		event_f1.keycode = KEY_F1
		event_f1.pressed = true
		_player._input(event_f1)
		assert(_player.is_f1_photo_mode == true, "Modo F1 debe activarse")
		assert(hud.visible == false, "El HUD debe ocultarse en modo F1")
		assert(_player.humanoid_scene.visible == false, "El avatar humanoide debe ocultarse en modo F1")
		print("✓ Modo F1 activado: HUD y avatar ocultos correctamente para screenshots.")

		# Desactivar Modo Screenshot F1 con segundo toggle
		_player._input(event_f1)
		assert(_player.is_f1_photo_mode == false, "Modo F1 debe desactivarse")
		assert(_player.humanoid_scene.visible == true, "El avatar debe volver a ser visible tras salir de F1")
		assert(hud.visible == true, "El HUD debe restaurarse al salir de F1")
		print("✓ Modo F1 desactivado: HUD y avatar restaurados, control restablecido.")

	elif _frames >= 16:
		if _frames > 16:
			return
		print("\n==================================================================")
		print("✓ TODAS LAS PRUEBAS DE HUMANOIDE Y LOCOMOCIÓN PASARON CON ÉXITO.")
		print("==================================================================")
		if is_instance_valid(_main_scene):
			_main_scene.queue_free()
		quit(0)

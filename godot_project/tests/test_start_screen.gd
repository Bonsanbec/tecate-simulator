extends SceneTree

const StartScreenClass = preload("res://ui/start_screen.gd")

var _frames = 0
var _instance: Node
var _start_screen: Node
var _player: CharacterBody3D

func _init():
	print("--- Probando suite de pruebas unitarias e integración de StartScreen ---")
	var main_scene = load("res://main.tscn")
	assert(main_scene != null, "main.tscn debe poder cargarse")
	_instance = main_scene.instantiate()
	root.add_child(_instance)
	print("✓ Escena principal instanciada.")

func _process(_delta):
	_frames += 1
	
	if _frames == 6:
		print("\n[Fase 1] Verificando estado inicial de la Pantalla de Inicio...")
		_start_screen = _instance.get_node_or_null("StartScreen")
		assert(_start_screen != null, "El nodo StartScreen debe existir en main.tscn")
		_player = _instance.get_node_or_null("Player") as CharacterBody3D
		assert(_player != null, "El nodo Player debe existir en main.tscn")
		
		# 1. Cámara hacia el Cuchumá
		var cam = _start_screen.menu_camera
		assert(cam != null, "MenuCamera debe existir")
		assert(cam.current, "MenuCamera debe ser la cámara activa inicial")
		assert(cam.far >= 10000.0, "MenuCamera debe tener far plane suficiente para ver el horizonte")
		
		# Verificar que la cámara apunte en dirección al Cuchumá (-X y -Z)
		var cam_forward = -cam.global_transform.basis.z
		var to_cuchuma = (_start_screen.target_cuchuma - cam.global_position).normalized()
		var dot_prod = cam_forward.dot(to_cuchuma)
		print("  • Alineación de cámara con Cerro Cuchumá (dot product): ", dot_prod)
		assert(dot_prod > 0.95, "La cámara del menú debe mirar directamente hacia el Cuchumá")
		
		# 2. UI y Textos
		assert(_start_screen.title_label != null, "TitleLabel debe existir")
		assert(_start_screen.title_label.text == "TECATE", "El título principal debe ser 'TECATE'")
		assert(_start_screen.btn_continue != null, "Botón Continuar debe existir")
		assert(_start_screen.btn_continue.text == "Continuar", "Texto del botón debe ser 'Continuar'")
		assert(_start_screen.btn_respawn != null, "Botón Reaparecer debe existir")
		assert(_start_screen.btn_respawn.text == "Reaparecer", "Texto del botón debe ser 'Reaparecer'")
		assert(_start_screen.btn_quit != null, "Botón Salir debe existir")
		assert(_start_screen.btn_quit.text == "Salir", "Texto del botón debe ser 'Salir'")
		
		# 3. Estado inicial de control y ratón
		assert(_start_screen.is_menu_active, "StartScreen debe iniciar activo")
		assert(not _player.input_enabled, "El jugador no debe tener input activo durante el menú")
		assert(Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "El cursor del ratón debe ser visible en el menú")
		print("✓ Fase 1 completada con éxito.")

	elif _frames == 10:
		print("\n[Fase 2] Probando acción 'Continuar'...")
		_start_screen.btn_continue.emit_signal("pressed")
		
		assert(not _start_screen.is_menu_active, "El menú debe quedar inactivo tras pulsar Continuar")
		assert(not _start_screen.canvas_layer.visible, "La interfaz debe ocultarse")
		assert(_player.input_enabled, "El input del jugador debe activarse")
		assert(_player.camera.current, "La cámara del jugador debe activarse")
		if DisplayServer.get_name() != "headless":
			assert(Input.mouse_mode == Input.MOUSE_MODE_CAPTURED, "El ratón debe ser capturado para jugar")
		print("✓ Fase 2 completada con éxito: Continuar reanuda el juego.")

	elif _frames == 14:
		print("\n[Fase 3] Probando alternancia de menú (tecla Escape)...")
		_start_screen.toggle_menu()
		
		assert(_start_screen.is_menu_active, "El menú debe reabrirse con toggle_menu")
		assert(_start_screen.canvas_layer.visible, "La interfaz debe ser visible")
		assert(not _player.input_enabled, "El input del jugador debe pausarse")
		assert(_start_screen.menu_camera.current, "La cámara del menú hacia el Cuchumá debe activarse")
		assert(Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "El ratón debe volver a ser visible")
		print("✓ Fase 3 completada con éxito: Pausa/Reapertura funcional.")

	elif _frames == 18:
		print("\n[Fase 4] Probando acción 'Reaparecer'...")
		# Mover jugador a una posición lejana
		_player.global_position = Vector3(500.0, 480.0, 300.0)
		_player.velocity = Vector3(10.0, 5.0, -10.0)
		_player.is_flying = true
		
		_start_screen.btn_respawn.emit_signal("pressed")
		
		assert(not _start_screen.is_menu_active, "El menú debe cerrarse tras reaparecer")
		assert(_player.input_enabled, "El input del jugador debe estar activo")
		assert(not _player.is_flying, "El vuelo debe restablecerse al reaparecer")
		assert(_player.velocity == Vector3.ZERO, "La velocidad debe ser cero al reaparecer")
		
		var dist_to_spawn = _player.global_position.distance_to(_player.spawn_position)
		print("  • Distancia al punto de reaparición inicial: ", dist_to_spawn, "m (pos: ", _player.global_position, ")")
		assert(dist_to_spawn < 1.0, "El jugador debe haber vuelto a la posición inicial en Parque Hidalgo")
		print("✓ Fase 4 completada con éxito: Reaparecer restablece al jugador en Parque Hidalgo.")

	elif _frames >= 22:
		print("\n=======================================================")
		print("✓ TODAS LAS PRUEBAS DE LA PANTALLA DE INICIO PASARON EXITOSAMENTE.")
		print("=======================================================")
		_instance.queue_free()
		quit(0)

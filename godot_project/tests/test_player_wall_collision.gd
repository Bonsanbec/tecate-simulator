extends SceneTree

var _frames = 0
var _scene: Node
var _player: CharacterBody3D
var _start_pos: Vector3

func _init():
	print("--- TEST DE LOCOMOCIÓN PEATONAL CONTRA EL KIOSKO ---")
	var main_res = load("res://main.tscn")
	_scene = main_res.instantiate()
	root.add_child(_scene)

func _process(_delta):
	_frames += 1
	if _frames == 1:
		_player = _scene.get_node_or_null("Player") as CharacterBody3D
		assert(_player != null, "Player debe existir en main.tscn")
		# Posicionar al player a 2 metros de la escalinata del Kiosko (Kiosko en Z=2.68)
		# La base octagonal del kiosko tiene radio ~4.5m, la escalinata llega hasta Z ~ 7.0
		# Posicionamos al player en Z = 8.5 y caminamos hacia -Z (hacia el kiosko)
		_player.global_position = Vector3(-6.6844, 401.0, 8.5)
		_start_pos = _player.global_position
		print("Player posicionado en: ", _start_pos)
		print("Caminando hacia la escalinata/base del Kiosko (hacia -Z)...")
		return

	# Aplicar gravedad normal y velocidad hacia -Z
	_player.velocity = Vector3(0, -9.8, -3.0)
	_player.move_and_slide()
	
	if _frames % 10 == 0:
		print("Frame %2d: Player pos = %s, on_wall = %s, on_floor = %s, slide_count = %d" % [
			_frames, _player.global_position, _player.is_on_wall(), _player.is_on_floor(), _player.get_slide_collision_count()
		])
		if _player.get_slide_collision_count() > 0:
			var col = _player.get_slide_collision(0)
			print("   --> Colisionando con: ", col.get_collider().name)

	if _frames >= 60:
		var distance_traveled = _start_pos.distance_to(_player.global_position)
		print("\nResultado tras 60 frames:")
		print("Posición inicial: ", _start_pos)
		print("Posición final  : ", _player.global_position)
		print("Distancia recorrida: ", distance_traveled)
		
		# Si atravesó el Kiosko (la escalinata y base están entre Z=6.5 y Z=2.68),
		# sin colisiones el jugador llegaría hasta Z = 5.5 o menos.
		# Con colisiones, debe impactar y detenerse o subir la escalinata pero colisionar con CollisionStructure
		var hit_kiosko = false
		for i in range(_player.get_slide_collision_count()):
			var c = _player.get_slide_collision(i)
			if c.get_collider().name == "CollisionStructure" or c.get_collider().name.begins_with("Col_") or c.get_collider().get_parent().name == "Kiosko":
				hit_kiosko = true
				break
		if hit_kiosko or _player.is_on_wall():
			print("✓ ÉXITO: El jugador colisionó y fue detenido/restringido por la estructura del Kiosko!")
		else:
			print("Posición final Z = ", _player.global_position.z)
			
		_scene.queue_free()
		quit(0)

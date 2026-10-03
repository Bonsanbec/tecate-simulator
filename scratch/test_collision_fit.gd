extends SceneTree

var player: CharacterBody3D
var bus: Node3D
var step = 0

func _init() -> void:
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	bus = scene_res.instantiate()
	root.add_child(bus)
	
	player = CharacterBody3D.new()
	player.set_script(load("res://player.gd"))
	var col = CollisionShape3D.new()
	var cap = CapsuleShape3D.new()
	cap.height = 2.0
	cap.radius = 0.4
	col.shape = cap
	col.position = Vector3(0, 1.0, 0)
	player.add_child(col)
	root.add_child(player)

func _process(_delta: float) -> bool:
	step += 1
	if step == 2:
		# Situar jugador exactamente en ExitPoint del asiento 1
		var seat = bus.get_node("Seats/Seat_Passenger_1")
		var exit_pt = seat.get_node("ExitPoint")
		player.global_position = exit_pt.global_position
		print("ExitPoint pos: ", exit_pt.global_position)
		print("Player pos: ", player.global_position)
	elif step == 3:
		# Probar colisión
		var res = PhysicsTestMotionParameters3D.new()
		res.from = player.global_transform
		var result = PhysicsTestMotionResult3D.new()
		var collides = PhysicsServer3D.body_test_motion(player.get_rid(), res, result)
		print("¿Colisiona inmediatamente al pararse en ExitPoint? ", collides)
		if collides:
			print("Colisión con RID: ", result.get_collider_rid())
			print("Colisión con objeto: ", result.get_collider())
			print("Punto de contacto: ", result.get_collision_point())
			print("Normal: ", result.get_collision_normal())
			print("Profundidad penetración: ", result.get_collision_depth())
			
		quit(0)
		return true
	return false

extends SceneTree

var main_scene: Node
var bus: Node
var player: Node
var step = 0

func _init() -> void:
	var scene_res = load("res://main.tscn")
	main_scene = scene_res.instantiate()
	root.add_child(main_scene)
	
	player = main_scene.find_child("Player", true, false)
	bus = main_scene.find_child("Bus_El_Hongo_Central", true, false)
	
	print("--- TEST STAND UP EXPERIMENT ---")
	print("Player: ", player)
	print("Bus: ", bus)
	print("Bus pos: ", bus.global_position)
	print("Bus velocity: ", bus.velocity)

func _process(_delta: float) -> bool:
	step += 1
	if step == 3:
		# Sentar al jugador en el primer asiento de pasajero
		var p_seats = bus.get_available_passenger_seats()
		print("Available passenger seats: ", p_seats.size())
		var seat = p_seats[0]
		print("Target seat: ", seat.name, " seat pos=", seat.global_position)
		var sat = player.sit_in_seat(seat)
		print("Player sat_in_seat result: ", sat)
		print("Player pos while sitting: ", player.global_position)
	elif step == 6:
		print("\n--- LLAMANDO STAND_UP() ---")
		print("Bus pos before stand_up: ", bus.global_position)
		print("Player pos before stand_up: ", player.global_position)
		var exit_pos_calc = player.current_seat.get_exit_global_position()
		print("Seat exit_point global_pos: ", exit_pos_calc)
		var stood = player.stand_up()
		print("stand_up() result: ", stood)
		print("Player pos immediately after stand_up: ", player.global_position)
		print("Player velocity: ", player.velocity)
	elif step >= 7 and step <= 15:
		print("Frame %d after stand_up: player pos=%s vel=%s on_floor=%s" % [step, player.global_position, player.velocity, player.is_on_floor()])
		if player.get_slide_collision_count() > 0:
			for ci in range(player.get_slide_collision_count()):
				var col = player.get_slide_collision(ci)
				print("   Collision with: ", col.get_collider().name, " norm=", col.get_normal(), " depth=", col.get_depth())
	elif step == 20:
		print("Dist from bus center: ", player.global_position.distance_to(bus.global_position))
		quit(0)
		return true
	return false

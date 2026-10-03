extends SceneTree

var bus: Node
var frame_count = 0

func _init() -> void:
	var scene_res = load("res://assets/vehicles/bus_hongo.tscn")
	bus = scene_res.instantiate()
	root.add_child(bus)
	bus.global_position = Vector3(0, 400.33, 0)
	
	print("--- INSPECCIÓN DE COLISIÓN DEL AUTOBÚS ---")
	print("Bus class: ", bus.get_class())
	print("Bus collision_layer: ", bus.collision_layer, " mask: ", bus.collision_mask)
	
	var direct_col_shapes = []
	for child in bus.get_children():
		if child is CollisionShape3D:
			direct_col_shapes.append(child)
	print("Direct CollisionShape3D count on bus: ", direct_col_shapes.size())
	
	var all_col_objects = bus.find_children("*", "CollisionObject3D", true, false)
	print("Total CollisionObject3D inside bus: ", all_col_objects.size())
	for co in all_col_objects:
		print("  - ", co.name, " (", co.get_class(), ") layer=", co.collision_layer, " mask=", co.collision_mask)
		for c in co.get_children():
			if c is CollisionShape3D:
				print("      shape: ", c.shape.get_class() if c.shape else "null")
				
	var rays = bus.suspension_rays
	print("Suspension rays count: ", rays.size())
	for r in rays:
		print("  Ray: ", r.name, " pos: ", r.position, " target: ", r.target_position, " mask: ", r.collision_mask)

func _process(_delta: float) -> bool:
	frame_count += 1
	if frame_count <= 10:
		print("Process Frame %d: pos=%s vel=%s" % [frame_count, bus.global_position, bus.velocity])
	if frame_count >= 15:
		bus.free()
		quit(0)
		return true
	return false

extends SceneTree

var _frames = 0
var _scene: Node

func _init():
	print("--- INICIANDO DIAGNÓSTICO DE COLISIÓN FÍSICA ---")
	var main_res = load("res://main.tscn")
	_scene = main_res.instantiate()
	root.add_child(_scene)

func _process(_delta):
	_frames += 1
	if _frames == 3:
		var space_state = root.get_world_3d().direct_space_state
		
		# 1. Probar raycast hacia el Kiosko
		# Kiosko está en (-6.6844, 400.2132, 2.6878)
		var ray_from = Vector3(-6.6844, 401.0, 15.0)
		var ray_to = Vector3(-6.6844, 401.0, 0.0)
		var query = PhysicsRayQueryParameters3D.create(ray_from, ray_to)
		query.collide_with_areas = false
		query.collide_with_bodies = true
		query.collision_mask = 1
		
		var hit = space_state.intersect_ray(query)
		print("\n1. Raycast hacia el Kiosko:")
		print("   From: ", ray_from, " To: ", ray_to)
		if hit.is_empty():
			print("   --> RESULTADO: NO HUBO IMPACTO (El rayo atravesó el Kiosko)")
		else:
			print("   --> RESULTADO: IMPACTÓ con: ", hit.collider.name, " en ", hit.position)

		# 2. Probar raycast hacia BBVA
		# BBVA está cerca de (-66.8, 400, -24.81)
		var bbva_node = _scene.get_node_or_null("BBVA")
		if bbva_node:
			print("\n2. Inspección del nodo BBVA:")
			print("   Global Pos: ", bbva_node.global_position)
			var sb_count = 0
			var col_shapes_active = 0
			_count_physics(bbva_node, sb_count, col_shapes_active)
			
			var ray_bbva_from = bbva_node.global_position + Vector3(0, 2.0, 15.0)
			var ray_bbva_to = bbva_node.global_position + Vector3(0, 2.0, -5.0)
			var q_bbva = PhysicsRayQueryParameters3D.create(ray_bbva_from, ray_bbva_to)
			var hit_bbva = space_state.intersect_ray(q_bbva)
			print("   Raycast BBVA From: ", ray_bbva_from, " To: ", ray_bbva_to)
			if hit_bbva.is_empty():
				print("   --> RESULTADO: NO HUBO IMPACTO (El rayo atravesó BBVA)")
			else:
				print("   --> RESULTADO: IMPACTÓ con: ", hit_bbva.collider.name, " en ", hit_bbva.position)
				
		# 3. Inspeccionar el StaticBody y CollisionShape del Kiosko
		var kiosko = _scene.get_node_or_null("Kiosko")
		if kiosko:
			print("\n3. Inspección detallada del nodo Kiosko:")
			_dump_hierarchy(kiosko, "  ")

		_scene.queue_free()
		quit(0)

func _count_physics(node: Node, sb: int, cs: int):
	for c in node.get_children():
		if c is StaticBody3D:
			sb += 1
			print("   - StaticBody3D encontrado: ", c.name, " layer: ", c.collision_layer, " RID: ", c.get_rid())
			for sc in c.get_children():
				if sc is CollisionShape3D:
					print("     * CollisionShape3D: ", sc.name, " shape: ", sc.shape, " disabled: ", sc.disabled)
					if sc.shape is ConcavePolygonShape3D:
						var faces = sc.shape.get_faces()
						print("       ConcavePolygon faces count: ", faces.size())
		_count_physics(c, sb, cs)

func _dump_hierarchy(node: Node, indent: String):
	var extra = ""
	if node is CollisionShape3D:
		extra = " (SHAPE: " + str(node.shape) + " disabled=" + str(node.disabled) + ")"
		if node.shape is ConcavePolygonShape3D:
			extra += " [faces: " + str(node.shape.get_faces().size()) + "]"
	elif node is StaticBody3D:
		extra = " (COLLISION LAYER=" + str(node.collision_layer) + " RID=" + str(node.get_rid()) + ")"
	print(indent, "- ", node.name, " [", node.get_class(), "]", extra)
	for child in node.get_children():
		_dump_hierarchy(child, indent + "  ")

extends SceneTree

## Test automatizado de verificación de colisiones estáticas en tiempo de importación

func _init():
	print("\n========================================================")
	print("TEST: Verificación de Colisiones Estáticas en Tiempo de Importación")
	print("========================================================")
	
	var main_scene = load("res://main.tscn")
	assert(main_scene != null, "main.tscn debe poder cargarse")
	var instance = main_scene.instantiate()
	root.add_child(instance)
	
	var buildings_to_test = [
		"BBVA",
		"Edificio_Cardenas_33",
		"Edificio_Cardenas_25",
		"Hotel_Tecate",
		"Palacio_Municipal",
		"Continuo_La_Panza",
		"Edificio_Juarez_235",
		"Manzana_Central_2009",
		"Kiosko",
		"Fuente_Parque_Hidalgo",
		"Parque_Miguel_Hidalgo"
	]
	
	var total_colliders = 0
	var total_structural_bodies = 0
	var forbidden_colliders = 0
	
	for b_name in buildings_to_test:
		var node = instance.get_node_or_null(b_name)
		if not node:
			push_error("No se encontró el nodo: " + b_name)
			continue
			
		var col_count = 0
		var body_count = 0
		var bad_names: Array[String] = []
		
		var bodies: Array[StaticBody3D] = []
		_gather_static_bodies(node, bodies)
		
		for body in bodies:
			body_count += 1
			for child in body.get_children():
				if child is CollisionShape3D:
					col_count += 1
					var parent_mesh = body.get_parent()
					if parent_mesh and (parent_mesh.name.begins_with("Txt_") or parent_mesh.name.begins_with("Texto_") or parent_mesh.name.begins_with("Rotulo_")):
						bad_names.append(parent_mesh.name)
						forbidden_colliders += 1
		
		total_colliders += col_count
		total_structural_bodies += body_count
		print(" • %-25s: %3d StaticBodies | %3d CollisionShapes (Bad: %d)" % [b_name, body_count, col_count, bad_names.size()])
		assert(col_count > 0, "El edificio %s debe tener colisiones importadas" % b_name)
		assert(bad_names.size() == 0, "No debe haber colisiones en textos decorativos")

	print("--------------------------------------------------------")
	print("RESULTADO GLOBAL:")
	print("  Total StaticBodies estructurales : ", total_structural_bodies)
	print("  Total CollisionShapes analíticas  : ", total_colliders)
	print("  Colisiones prohibidas en textos  : ", forbidden_colliders)
	print("✓ Todas las aserciones pasaron exitosamente.")
	print("========================================================\n")
	
	instance.queue_free()
	quit(0)

func _gather_static_bodies(node: Node, out_list: Array[StaticBody3D]) -> void:
	if node is StaticBody3D:
		out_list.append(node)
	for child in node.get_children():
		_gather_static_bodies(child, out_list)

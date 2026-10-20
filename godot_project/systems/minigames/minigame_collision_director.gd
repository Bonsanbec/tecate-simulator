class_name MinigameCollisionDirector
extends Node

## MinigameCollisionDirector
## Gestor dinámico y desacoplado de reglas de colisión específicas por minijuego.
## Permite suspender o mitigar selectivamente colisionadores estructurales (ej. barandales,
## vallas perimetrales o parapetos) durante la ejecución de una competición y restaurarlos
## íntegramente al concluir o cancelarse el minijuego.

const MinigameCatalogClass = preload("res://systems/minigames/minigame_catalog.gd")

var _snapshots: Array[Dictionary] = []

func _exit_tree() -> void:
	restore_all_overrides()

## Aplica las reglas de anulación o alteración de colisiones definidas para el minijuego indicado.
## Retorna el número de CollisionShape3D alterados exitosamente.
func apply_overrides_for_game(game_id: int, scene_root: Node) -> int:
	if not scene_root:
		return 0

	var minigame_data: Dictionary = MinigameCatalogClass.get_minigame(game_id)
	if minigame_data.is_empty():
		return 0

	if not minigame_data.has(AppTechnicalStrings.KEY_COLLISION_OVERRIDES):
		return 0

	var overrides_list = minigame_data.get(AppTechnicalStrings.KEY_COLLISION_OVERRIDES, [])
	if overrides_list.is_empty():
		return 0

	# Si ya existían anulaciones activas previas, restaurar primero para evitar colisiones huérfanas
	if not _snapshots.is_empty():
		restore_all_overrides()

	var modified_count: int = 0

	for rule in overrides_list:
		if not rule is Dictionary:
			continue

		var shape_patterns: Array = rule.get(AppTechnicalStrings.KEY_SHAPE_PATTERNS, [])
		if shape_patterns.is_empty():
			continue

		var mode: String = rule.get(
			AppTechnicalStrings.KEY_MODE,
			AppTechnicalStrings.COLLISION_OVERRIDE_MODE_DISABLED
		)
		var height_ratio: float = float(rule.get(
			AppTechnicalStrings.KEY_LOW_OBSTACLE_HEIGHT_RATIO,
			0.20
		))

		var candidate_shapes: Array[CollisionShape3D] = []
		_find_matching_shapes_recursive(scene_root, shape_patterns, candidate_shapes)

		for col_shape in candidate_shapes:
			if not is_instance_valid(col_shape):
				continue

			# Guardar instantánea del estado canónico original
			var snapshot: Dictionary = {
				"node_ref": col_shape,
				"original_disabled": col_shape.disabled,
				"original_scale": col_shape.scale,
				"original_position": col_shape.position
			}
			_snapshots.append(snapshot)

			# Aplicar la política de colisión solicitada
			match mode:
				AppTechnicalStrings.COLLISION_OVERRIDE_MODE_DISABLED:
					col_shape.disabled = true
					modified_count += 1

				AppTechnicalStrings.COLLISION_OVERRIDE_MODE_LOW_OBSTACLE:
					# Mitigar la altura vertical para que actúe como bordillo bajo tropezable
					col_shape.scale.y = col_shape.scale.y * height_ratio
					modified_count += 1

				_:
					col_shape.disabled = true
					modified_count += 1

	return modified_count

## Restaura de inmediato todos los colisionadores a su geometría y estado canónico original.
## Retorna el número de colisionadores restablecidos.
func restore_all_overrides() -> int:
	if _snapshots.is_empty():
		return 0

	var restored_count: int = 0
	for snap in _snapshots:
		var col_shape = snap.get("node_ref") as CollisionShape3D
		if col_shape and is_instance_valid(col_shape):
			col_shape.disabled = snap.get("original_disabled", false)
			col_shape.scale = snap.get("original_scale", Vector3.ONE)
			col_shape.position = snap.get("original_position", Vector3.ZERO)
			restored_count += 1

	_snapshots.clear()
	return restored_count

## Retorna el total de colisionadores actualmente intervenidos por el director.
func get_active_override_count() -> int:
	return _snapshots.size()

## Búsqueda recursiva de CollisionShape3D cuyos nombres satisfagan alguno de los patrones dados.
func _find_matching_shapes_recursive(node: Node, patterns: Array, out_shapes: Array[CollisionShape3D]) -> void:
	if node is CollisionShape3D:
		var node_name: String = node.name
		for pat in patterns:
			if node_name.match(pat):
				out_shapes.append(node)
				break

	for child in node.get_children():
		_find_matching_shapes_recursive(child, patterns, out_shapes)

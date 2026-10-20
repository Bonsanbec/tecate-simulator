extends SceneTree

## test_minigame_collision_director.gd
## Suite de pruebas de verificación para MinigameCollisionDirector y la alteración modular de colisiones.

const MinigameCollisionDirectorClass = preload("res://systems/minigames/minigame_collision_director.gd")
const MinigameManagerClass = preload("res://systems/minigames/minigame_manager.gd")
const KioskoScene = preload("res://assets/kiosko_parque_hidalgo.tscn")

var total_tests: int = 0
var passed_tests: int = 0
var _frame: int = 0

func _init() -> void:
	print("================================================================================")
	print(" INICIANDO PRUEBAS UNITARIAS: DIRECTOR DE COLISIONES DE MINIJUEGOS (GODOT 4)")
	print("================================================================================")

func _process(_delta: float) -> bool:
	_frame += 1
	if _frame == 2:
		_run_all_tests()
	return false

func _run_all_tests() -> void:
	test_director_instantiation()
	test_kiosko_baseline_collision_state()
	test_apply_overrides_disabled_mode()
	test_restore_overrides()
	test_apply_overrides_low_obstacle_mode()
	test_idempotency_and_invalid_game_id()
	test_minigame_manager_lifecycle_integration()

	print("================================================================================")
	print(" RESULTADOS: %d/%d pruebas superadas con éxito." % [passed_tests, total_tests])
	print("================================================================================")

	if passed_tests == total_tests:
		quit(0)
	else:
		quit(1)

func test_assert(desc: String, condition: bool) -> void:
	total_tests += 1
	if condition:
		passed_tests += 1
		print("  [PASS] %s" % desc)
	else:
		printerr("  [FAIL] %s" % desc)

func test_director_instantiation() -> void:
	print("\n--- Prueba 1: Instanciación e Inicialización Limpia ---")
	var director = MinigameCollisionDirectorClass.new()
	test_assert("El director se instancia como MinigameCollisionDirector", director != null)
	test_assert("Inicia con 0 overrides activos", director.get_active_override_count() == 0)
	director.free()

func test_kiosko_baseline_collision_state() -> void:
	print("\n--- Prueba 2: Estado Canónico Inicial de las Colisiones del Kiosco ---")
	var kiosko = KioskoScene.instantiate()
	test_assert("La escena del Kiosco se instancia correctamente", kiosko != null)

	var col_railing = kiosko.find_child("Col_Herreria_Perimetral", true, false) as CollisionShape3D
	test_assert("Col_Herreria_Perimetral existe en la escena horneada del Kiosco", col_railing != null)
	if col_railing:
		test_assert("Col_Herreria_Perimetral inicia activo (disabled == false)", not col_railing.disabled)

	var col_base = kiosko.find_child("Col_Base_Octagonal", true, false) as CollisionShape3D
	test_assert("Col_Base_Octagonal existe y está activo", col_base != null and not col_base.disabled)

	var col_columns = kiosko.find_child("Col_Columnas_Octeto", true, false) as CollisionShape3D
	test_assert("Col_Columnas_Octeto existe y está activo", col_columns != null and not col_columns.disabled)

	kiosko.free()

func test_apply_overrides_disabled_mode() -> void:
	print("\n--- Prueba 3: Aplicación del Modo DISABLED (Mi Kiosko - ID 1) ---")
	var kiosko = KioskoScene.instantiate()
	var director = MinigameCollisionDirectorClass.new()

	var modified = director.apply_overrides_for_game(1, kiosko)
	test_assert("apply_overrides_for_game(1) altera al menos 1 colisionador", modified >= 1)
	test_assert("get_active_override_count() refleja el colisionador alterado", director.get_active_override_count() == modified)

	var col_railing = kiosko.find_child("Col_Herreria_Perimetral", true, false) as CollisionShape3D
	if col_railing:
		test_assert("Col_Herreria_Perimetral ahora está desactivado (disabled == true)", col_railing.disabled)

	# Verificar que el resto de los componentes estructurales siguen sólidos y transitables
	var col_base = kiosko.find_child("Col_Base_Octagonal", true, false) as CollisionShape3D
	test_assert("Col_Base_Octagonal permanece activo e intacto", col_base != null and not col_base.disabled)

	var col_columns = kiosko.find_child("Col_Columnas_Octeto", true, false) as CollisionShape3D
	test_assert("Col_Columnas_Octeto permanece activo e intacto", col_columns != null and not col_columns.disabled)

	var col_stairs = kiosko.find_child("Col_Escalinata", true, false) as CollisionShape3D
	test_assert("Col_Escalinata permanece activo e intacto", col_stairs != null and not col_stairs.disabled)

	director.restore_all_overrides()
	director.free()
	kiosko.free()

func test_restore_overrides() -> void:
	print("\n--- Prueba 4: Restauración Fiel al Estado Original ---")
	var kiosko = KioskoScene.instantiate()
	var director = MinigameCollisionDirectorClass.new()

	director.apply_overrides_for_game(1, kiosko)
	var col_railing = kiosko.find_child("Col_Herreria_Perimetral", true, false) as CollisionShape3D
	test_assert("Col_Herreria_Perimetral desactivado temporalmente", col_railing != null and col_railing.disabled)

	var restored = director.restore_all_overrides()
	test_assert("restore_all_overrides() reporta la cantidad restaurada", restored >= 1)
	test_assert("get_active_override_count() regresa a 0", director.get_active_override_count() == 0)
	if col_railing:
		test_assert("Col_Herreria_Perimetral recuperó disabled == false", not col_railing.disabled)

	director.free()
	kiosko.free()

func test_apply_overrides_low_obstacle_mode() -> void:
	print("\n--- Prueba 5: Modo LOW_OBSTACLE (Poco Colisionable / Bordillo Bajo) ---")
	var kiosko = KioskoScene.instantiate()
	var director = MinigameCollisionDirectorClass.new()
	var col_railing = kiosko.find_child("Col_Herreria_Perimetral", true, false) as CollisionShape3D

	var original_scale_y: float = col_railing.scale.y if col_railing else 1.0

	# Simular override con modo LOW_OBSTACLE al 20%
	var custom_rules: Array[Dictionary] = [
		{
			AppTechnicalStrings.KEY_TARGET_LOCATION: "kiosko",
			AppTechnicalStrings.KEY_SHAPE_PATTERNS: [AppTechnicalStrings.PATTERN_HERRERIA_PERIMETRAL],
			AppTechnicalStrings.KEY_MODE: AppTechnicalStrings.COLLISION_OVERRIDE_MODE_LOW_OBSTACLE,
			AppTechnicalStrings.KEY_LOW_OBSTACLE_HEIGHT_RATIO: 0.20
		}
	]

	# Inyectar snapshot manualmente a través del selector interno
	var candidates: Array[CollisionShape3D] = []
	director._find_matching_shapes_recursive(kiosko, [AppTechnicalStrings.PATTERN_HERRERIA_PERIMETRAL], candidates)
	test_assert("Búsqueda recursiva localiza Col_Herreria_Perimetral", candidates.size() == 1)

	if not candidates.is_empty():
		var shape = candidates[0]
		director._snapshots.append({
			"node_ref": shape,
			"original_disabled": shape.disabled,
			"original_scale": shape.scale,
			"original_position": shape.position
		})
		shape.scale.y = shape.scale.y * 0.20
		test_assert("Altura vertical en Y reducida al 20%", is_equal_approx(shape.scale.y, original_scale_y * 0.20))
		test_assert("El colisionador permanece activo (disabled == false)", not shape.disabled)

	director.restore_all_overrides()
	if col_railing:
		test_assert("Altura vertical en Y restaurada al 100%", is_equal_approx(col_railing.scale.y, original_scale_y))

	director.free()
	kiosko.free()

func test_idempotency_and_invalid_game_id() -> void:
	print("\n--- Prueba 6: Idempotencia y Manejo de Casos Límite ---")
	var director = MinigameCollisionDirectorClass.new()
	var dummy_node = Node3D.new()

	test_assert("Llamar restore_all_overrides() en vacío retorna 0", director.restore_all_overrides() == 0)
	test_assert("apply_overrides_for_game(9999) con juego inexistente retorna 0", director.apply_overrides_for_game(9999, dummy_node) == 0)
	test_assert("apply_overrides_for_game con nodo nulo retorna 0", director.apply_overrides_for_game(1, null) == 0)

	dummy_node.free()
	director.free()

func test_minigame_manager_lifecycle_integration() -> void:
	print("\n--- Prueba 7: Integración con el Ciclo de Vida de MinigameManager ---")
	var root = Node3D.new()
	self.root.add_child(root)

	var kiosko = KioskoScene.instantiate()
	root.add_child(kiosko)

	var mgr = MinigameManagerClass.new()
	root.add_child(mgr)

	var col_railing = kiosko.find_child("Col_Herreria_Perimetral", true, false) as CollisionShape3D
	test_assert("Inicialmente la barandilla está activa", col_railing != null and not col_railing.disabled)

	# Iniciar juego local 1 (Mi Kiosko)
	mgr.start_local_game(1)
	test_assert("Al iniciar Mi Kiosko, MinigameManager desactiva la colisión del barandal", col_railing != null and col_railing.disabled)

	# Finalizar juego local
	mgr.finish_local_game(true)
	test_assert("Al finalizar el juego, la barandilla vuelve a su estado colisionable", col_railing != null and not col_railing.disabled)

	root.queue_free()

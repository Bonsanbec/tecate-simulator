extends SceneTree

## Suite de Pruebas Automatizadas: Unificación de Ciudadanos y Jugadores en Tecate Simulator
## Verifica que ciudadanos autónomos y jugadores remotos compartan la misma entidad
## base CitizenEntity (CharacterBody3D con cápsula antropométrica y rig 3D),
## que PlayerController herede de ella con control local, y que la gestión
## pertenezca al servidor TKT/1.

const CitizenEntityClass = preload("res://systems/characters/citizen_entity.gd")
const PlayerControllerClass = preload("res://systems/player/player_controller.gd")
const RemotePlayerClass = preload("res://systems/network/remote_player.gd")
const RemoteNPCClass = preload("res://systems/network/remote_npc.gd")
const MultiplayerManagerClass = preload("res://systems/network/multiplayer_manager.gd")
const TKTCodecClass = preload("res://systems/network/tkt_codec.gd")

var total_tests: int = 0
var passed_tests: int = 0

func _init() -> void:
	print("\n========================================================")
	print(" INICIANDO TEST: UNIFICACIÓN DE CIUDADANOS Y JUGADORES")
	print("========================================================")

	_test_citizen_entity_structure()
	_test_player_inheritance_and_control()
	_test_remote_entities_unification()
	_test_network_snapshot_interpolation()
	_test_multiplayer_manager_unification()

	print("\n========================================================")
	print(" RESUMEN: %d / %d pruebas superadas." % [passed_tests, total_tests])
	print("========================================================")

	if passed_tests == total_tests:
		print("✓ TODAS LAS PRUEBAS DE UNIFICACIÓN DE CIUDADANOS PASARON CON ÉXITO.\n")
		quit(0)
	else:
		printerr("✗ ALGUNAS PRUEBAS FALLARON.")
		quit(1)

func assert_test(cond: bool, msg: String) -> void:
	total_tests += 1
	if cond:
		passed_tests += 1
		print("[PASS] %s" % msg)
	else:
		printerr("[FAIL] %s" % msg)

func _test_citizen_entity_structure() -> void:
	print("\n--- 1. Validación Estructural de CitizenEntity ---")
	var citizen = CitizenEntityClass.new()
	citizen.setup(3001, true, "Don Miguel")
	root.add_child(citizen)

	assert_test(citizen is CharacterBody3D, "CitizenEntity hereda de CharacterBody3D")
	assert_test(citizen.collision_shape != null, "CitizenEntity inicializa CollisionShape3D")
	assert_test(citizen.collision_shape.shape is CapsuleShape3D, "El colisionador es una CapsuleShape3D")

	var capsule = citizen.collision_shape.shape as CapsuleShape3D
	assert_test(is_equal_approx(capsule.radius, 0.25), "El radio de la cápsula es canónico (0.25 m)")
	assert_test(is_equal_approx(capsule.height, 1.75), "La altura de la cápsula es canónica (1.75 m)")

	assert_test(citizen.skeleton != null, "CitizenEntity carga e inicializa Skeleton3D")
	assert_test(citizen.nameplate_label != null, "CitizenEntity contiene Nameplate 3D billboard")
	assert_test(citizen.nameplate_label.text == "Don Miguel", "Nameplate refleja el nombre del ciudadano")
	assert_test(citizen.is_locally_controlled == false, "CitizenEntity autónoma tiene is_locally_controlled = false")
	assert_test(citizen.mesh_head == null or citizen.mesh_head.layers == 1, "La cabeza de un ciudadano autónomo está en Capa 1 (visible en 1P)")

	citizen.queue_free()

func _test_player_inheritance_and_control() -> void:
	print("\n--- 2. Validación de PlayerController como Especialización de CitizenEntity ---")
	var player = PlayerControllerClass.new()
	root.add_child(player)
	player._ready()

	assert_test(player is CitizenEntityClass, "PlayerController es instancia y hereda de CitizenEntity")
	assert_test(player is CharacterBody3D, "PlayerController es un CharacterBody3D con cuerpo físico")
	assert_test(player.collision_shape != null, "PlayerController hereda la cápsula de colisión de CitizenEntity")
	assert_test(player.is_locally_controlled == true, "PlayerController activa is_locally_controlled = true")
	assert_test(player.nameplate_label != null and not player.nameplate_label.visible, "El nameplate local está oculto en primera persona")
	assert_test(player.camera_director != null, "PlayerController inicializa su CameraDirector3D local")
	assert_test(player.foot_ik != null, "PlayerController inicializa FootIKController")
	assert_test(player.mesh_head == null or player.mesh_head.layers == 2, "La cabeza del jugador local está en Capa 2 (oculta en 1P)")

	player.queue_free()

func _test_remote_entities_unification() -> void:
	print("\n--- 3. Validación de Entidades Remotas Unificadas ---")
	var remote_player = RemotePlayerClass.new()
	remote_player.setup(12, false, "Jugador #12")
	root.add_child(remote_player)

	var remote_npc = RemoteNPCClass.new()
	remote_npc.setup(3002, true, "Doña Rosa")
	root.add_child(remote_npc)

	assert_test(remote_player is CitizenEntityClass, "RemotePlayer hereda de CitizenEntity")
	assert_test(remote_npc is CitizenEntityClass, "RemoteNPC hereda de CitizenEntity")
	assert_test(remote_player is CharacterBody3D, "RemotePlayer posee cuerpo físico CharacterBody3D")
	assert_test(remote_npc is CharacterBody3D, "RemoteNPC posee cuerpo físico CharacterBody3D")
	assert_test(remote_player.nameplate_label.modulate.r > 0.8, "RemotePlayer utiliza paleta cálida de jugador")
	assert_test(remote_npc.nameplate_label.modulate.g > 0.8, "RemoteNPC utiliza paleta verde cívica de ciudadano")
	assert_test(remote_player.mesh_head == null or remote_player.mesh_head.layers == 1, "La cabeza del jugador remoto está en Capa 1 (visible en 1P)")
	assert_test(remote_npc.mesh_head == null or remote_npc.mesh_head.layers == 1, "La cabeza del NPC remoto está en Capa 1 (visible en 1P)")

	remote_player.queue_free()
	remote_npc.queue_free()

func _test_network_snapshot_interpolation() -> void:
	print("\n--- 4. Validación de Interpolación de Red en CitizenEntity ---")
	var citizen = CitizenEntityClass.new()
	citizen.setup(3003, true, "Juan Carlos")
	root.add_child(citizen)

	var rec1 = TKTCodecClass.EntityRecord.new()
	rec1.entity_id = 3003
	rec1.entity_type = TKTCodecClass.EntityType.NPC
	rec1.position = Vector3(0, 400, 0)
	rec1.yaw = 0.0
	rec1.velocity = Vector3(1.3, 0, 0)

	var rec2 = TKTCodecClass.EntityRecord.new()
	rec2.entity_id = 3003
	rec2.entity_type = TKTCodecClass.EntityType.NPC
	rec2.position = Vector3(5, 400, 0)
	rec2.yaw = 90.0
	rec2.velocity = Vector3(1.3, 0, 0)

	citizen.push_snapshot_record(rec1, 1000)
	citizen.push_snapshot_record(rec2, 1100)

	assert_test(citizen.snapshot_history.size() == 2, "El búfer de snapshots registra las muestras recibidas")
	var sampled = citizen._sample_interpolated_state(1.050)
	assert_test(sampled.has("position") and sampled.has("velocity"), "El muestreo de interpolación genera estado válido")
	assert_test(sampled["position"].x >= 0.0 and sampled["position"].x <= 5.0, "La posición X está correctamente interpolada")

	# Probar actualización de locomoción procedural
	citizen._update_procedural_locomotion(0.033, Vector3(1.3, 0, 0))
	assert_test(citizen.locomotion_phase > 0.0, "La fase de locomoción avanza proporcional a la velocidad horizontal")

	citizen.queue_free()

func _test_multiplayer_manager_unification() -> void:
	print("\n--- 5. Validación de MultiplayerManager con CitizenEntity ---")
	var mgr = MultiplayerManagerClass.new()
	root.add_child(mgr)
	mgr._ready()

	var p_rec = TKTCodecClass.EntityRecord.new()
	p_rec.entity_id = 55
	p_rec.entity_type = TKTCodecClass.EntityType.PLAYER
	p_rec.position = Vector3(-10, 400, 10)
	p_rec.yaw = 45.0
	p_rec.velocity = Vector3.ZERO

	var npc_rec = TKTCodecClass.EntityRecord.new()
	npc_rec.entity_id = 3004
	npc_rec.entity_type = TKTCodecClass.EntityType.NPC
	npc_rec.position = Vector3(-50, 400, 12)
	npc_rec.yaw = 180.0
	npc_rec.velocity = Vector3(0, 0, 1.2)

	var entities: Array[TKTCodec.EntityRecord] = []
	entities.append(p_rec)
	entities.append(npc_rec)
	mgr._on_snapshot_received(10, entities)

	var rem_p = mgr.active_remote_players.get(55)
	var rem_npc = mgr.active_remote_npcs.get(3004)

	assert_test(rem_p != null, "MultiplayerManager instanció al jugador remoto 55")
	assert_test(rem_p is CitizenEntityClass, "El jugador remoto 55 es instancia de CitizenEntity")
	assert_test(rem_npc != null, "MultiplayerManager instanció al ciudadano remoto 3004")
	assert_test(rem_npc is CitizenEntityClass, "El ciudadano remoto 3004 es instancia de CitizenEntity")
	assert_test(rem_npc.citizen_name == "Carmen", "El ciudadano 3004 recibe su nombre cívico asignado")

	mgr.queue_free()

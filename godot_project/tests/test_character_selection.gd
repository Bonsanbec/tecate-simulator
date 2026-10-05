extends SceneTree

## Suite de Pruebas: Sistema de Selección y Sincronización de Personajes
## Verifica el catálogo paramétrico CharacterCatalog, CitizenProfile, CitizenEntity,
## el codec binario TKT/1 (CHARACTER_SELECT) y el flujo de StartScreen.

const CharacterCatalogClass = preload("res://systems/characters/character_catalog.gd")
const CitizenProfileClass = preload("res://systems/characters/citizen_profile.gd")
const CitizenEntityClass = preload("res://systems/characters/citizen_entity.gd")
const TKTCodecClass = preload("res://systems/network/tkt_codec.gd")
const StartScreenClass = preload("res://ui/start_screen.gd")

var total_tests: int = 0
var passed_tests: int = 0
var _frames: int = 0
var _screen: StartScreen = null

func _init() -> void:
	print("\n========================================================")
	print(" INICIANDO TEST: SISTEMA DE SELECCIÓN DE PERSONAJES")
	print("========================================================")

	_test_character_catalog()
	_test_citizen_unification_and_no_axel_placeholder()
	_test_tkt_codec_character_select()

	var start_screen_scene = load("res://ui/start_screen.tscn")
	assert_test(start_screen_scene != null, "start_screen.tscn cargado correctamente")
	_screen = start_screen_scene.instantiate() as StartScreen
	root.add_child(_screen)

func _process(_delta: float) -> bool:
	_frames += 1

	if _frames == 4:
		print("\n--- 4. Validación de Flujo de UI y Transición de StartScreen ---")
		assert_test(_screen.is_menu_active, "StartScreen inicia activa")
		assert_test(_screen.current_screen_state == StartScreen.MenuScreenState.MAIN_MENU, "Estado inicial es MAIN_MENU")
		assert_test(_screen.has_chosen_character == false, "has_chosen_character es inicialmente falso")
		assert_test(_screen.char_select_container != null, "char_select_container existe en escena")
		assert_test(not _screen.char_select_container.visible, "char_select_container inicia oculto")

		# Simular pulsación de Continuar sin haber elegido personaje: debe abrir selección de personaje
		_screen.btn_continue.emit_signal("pressed")
		assert_test(_screen.is_menu_active, "Menú sigue activo durante selección de personaje")
		assert_test(_screen.current_screen_state == StartScreen.MenuScreenState.CHARACTER_SELECT, "Pulsar Continuar sin personaje transiciona a CHARACTER_SELECT")
		assert_test(_screen.char_select_container.visible, "char_select_container se vuelve visible tras Continuar")

		# Simular selección de Diseñador (Eli)
		_screen.btn_select_eli.emit_signal("pressed")
		assert_test(_screen.selected_character_id == "eli", "Seleccionado personaje 'eli'")

		# Confirmar selección: debe cerrar el menú
		_screen.btn_confirm_selection.emit_signal("pressed")
		assert_test(_screen.has_chosen_character, "has_chosen_character se vuelve verdadero tras confirmar")
		assert_test(not _screen.is_menu_active, "El menú se cierra tras confirmar personaje")

		# Reabrir menú y presionar Reaparecer: siempre debe abrir selección de personaje
		_screen.open_menu()
		assert_test(_screen.is_menu_active, "Menú reabierto")
		_screen.btn_respawn.emit_signal("pressed")
		assert_test(_screen.current_screen_state == StartScreen.MenuScreenState.CHARACTER_SELECT, "Pulsar Reaparecer transiciona siempre a CHARACTER_SELECT")

		print("\n========================================================")
		print(" RESUMEN: %d / %d pruebas superadas." % [passed_tests, total_tests])
		print("========================================================")

		if passed_tests == total_tests:
			print("✓ TODAS LAS PRUEBAS DE SELECCIÓN DE PERSONAJE PASARON CON ÉXITO.\n")
			_screen.queue_free()
			quit(0)
		else:
			printerr("✗ ALGUNAS PRUEBAS FALLARON.")
			_screen.queue_free()
			quit(1)
	return false

func assert_test(cond: bool, msg: String) -> void:
	total_tests += 1
	if cond:
		passed_tests += 1
		print("[PASS] %s" % msg)
	else:
		printerr("[FAIL] %s" % msg)

func _test_character_catalog() -> void:
	print("\n--- 1. Validación de CharacterCatalog Paramétrico ---")
	var ids = CharacterCatalogClass.get_character_ids()
	assert_test(ids.has("axel") and ids.has("eli"), "CharacterCatalog registra tanto 'axel' como 'eli'")
	assert_test(ids.size() == 2, "CharacterCatalog contiene exactamente 2 personajes configurados")

	var data_axel = CharacterCatalogClass.get_character_data("axel")
	assert_test(data_axel["display_name"] == "Camarada", "Display name de Axel es 'Camarada'")
	assert_test(data_axel["codename"] == "Axel", "Codename de Axel es 'Axel'")
	assert_test(ResourceLoader.exists(data_axel["card_path"]), "Tarjeta gráfica axel_card.png existe en disco")
	assert_test(ResourceLoader.exists(data_axel["model_path"]), "Modelo 3D axel.glb existe en disco")

	var data_eli = CharacterCatalogClass.get_character_data("eli")
	assert_test(data_eli["display_name"] == "Diseñador", "Display name de Eli es 'Diseñador'")
	assert_test(data_eli["codename"] == "Eli", "Codename de Eli es 'Eli'")
	assert_test(ResourceLoader.exists(data_eli["card_path"]), "Tarjeta gráfica eli_card.png existe en disco")
	assert_test(ResourceLoader.exists(data_eli["model_path"]), "Modelo 3D eli.glb existe en disco")

	# Diversidad paramétrica sin placeholder fijo
	var id_even = CharacterCatalogClass.get_character_id_for_entity(3000)
	var id_odd = CharacterCatalogClass.get_character_id_for_entity(3001)
	assert_test(id_even != id_odd, "get_character_id_for_entity distribuye identidades alternadas entre IDs pares e impares")

	# Colores firma centralizados
	var col_axel = CharacterCatalogClass.get_character_theme_color("axel")
	var col_eli = CharacterCatalogClass.get_character_theme_color("eli")
	assert_test(col_axel != col_eli, "Axel y Eli tienen colores firma centralizados y diferenciados en el catálogo")
	assert_test(col_axel == Color(0.85, 0.16, 0.16, 1.0), "Axel utiliza el esquema Rojo Tecate (#D82A2A)")
	assert_test(col_eli == Color(0.0, 0.33, 0.72, 1.0), "Eli utiliza el esquema Azul Cobalto (#0055B8)")

func _test_citizen_unification_and_no_axel_placeholder() -> void:
	print("\n--- 2. Validación de CitizenEntity sin Axel como Placeholder Fijo ---")
	var profile_axel = CitizenProfileClass.create_axel_profile()
	assert_test(profile_axel != null and profile_axel.identity_id == "axel", "Perfil de Axel creado desde catálogo")

	var profile_eli = CitizenProfileClass.create_eli_profile()
	assert_test(profile_eli != null and profile_eli.identity_id == "eli", "Perfil de Eli creado desde catálogo")

	var c_odd = CitizenEntityClass.new()
	c_odd.setup(3001, true, "Ciudadano #3001")
	root.add_child(c_odd)
	c_odd._ready()
	assert_test(c_odd.identity_id != "", "Ciudadano impar inicializado con identidad válida")

	var c_even = CitizenEntityClass.new()
	c_even.setup(3002, true, "Ciudadano #3002")
	root.add_child(c_even)
	c_even._ready()
	assert_test(c_even.identity_id != "", "Ciudadano par inicializado con identidad válida")
	assert_test(c_odd.identity_id != c_even.identity_id, "Ciudadanos vecinos no comparten forzosamente el mismo avatar monolítico")

	# Conmutación dinámica de identidad
	c_odd.apply_identity("eli")
	assert_test(c_odd.identity_id == "eli", "CitizenEntity transicionó dinámicamente a Eli")
	assert_test(c_odd.humanoid_scene != null, "HumanoidAvatar reconstruido para Eli")

	c_odd.apply_identity("axel")
	assert_test(c_odd.identity_id == "axel", "CitizenEntity transicionó dinámicamente a Axel")

	c_odd.queue_free()
	c_even.queue_free()

func _test_tkt_codec_character_select() -> void:
	print("\n--- 3. Validación de Codec TKT/1 (CHARACTER_SELECT) ---")
	assert_test(TKTCodecClass.EventCode.CHARACTER_SELECT == 11, "Código numérico de CHARACTER_SELECT es 11")

	var enc_axel = TKTCodecClass.encode_character_select_data("axel")
	var dec_axel = TKTCodecClass.decode_character_select_data(enc_axel)
	assert_test(dec_axel == "axel", "Codificación y decodificación de personaje 'axel' preservada con fidelidad")

	var enc_eli = TKTCodecClass.encode_character_select_data("eli")
	var dec_eli = TKTCodecClass.decode_character_select_data(enc_eli)
	assert_test(dec_eli == "eli", "Codificación y decodificación de personaje 'eli' preservada con fidelidad")

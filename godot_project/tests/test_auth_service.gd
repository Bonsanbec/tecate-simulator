extends SceneTree

const AuthService = preload("res://systems/network/auth_service.gd")

## Prueba Unitaria Automatizada para AuthService (Identidad Asíncrona No Bloqueante).
## Ejecutar con: /Applications/Godot_mono.app/Contents/MacOS/Godot --headless --path godot_project -s tests/test_auth_service.gd

var total_tests: int = 0
var passed_tests: int = 0

func _init() -> void:
	print("================================================================================")
	print(" INICIANDO PRUEBAS UNITARIAS DE AUTENTICACIÓN E IDENTIDAD LOCAL (AUTHSERVICE)")
	print("================================================================================")

	var auth = AuthService.new()
	root.add_child(auth)

	# Esperar un momento para que el hilo secundario complete la carga inicial
	var max_wait_frames = 60
	while not auth.is_loaded and max_wait_frames > 0:
		await process_frame
		max_wait_frames -= 1

	test_assert("AuthService completa la carga de forma asíncrona", auth.is_loaded)
	test_assert("UUID no está vacío", not auth.player_uuid.is_empty())
	test_assert("UUID tiene formato válido (longitud 36)", auth.player_uuid.length() == 36)
	test_assert("Secreto criptográfico tiene 64 caracteres hex", auth.auth_secret.length() == 64)
	test_assert("Nombre de jugador por defecto existe", not auth.display_name.is_empty())

	var token = auth.get_auth_token()
	test_assert("Token generado no está vacío", not token.is_empty())
	var parts = token.split(":")
	test_assert("Token contiene 3 partes separadas por dos puntos (UUID:SECRET:NAME)", parts.size() >= 3)
	test_assert("Primera parte del token coincide con player_uuid", parts[0] == auth.player_uuid)
	test_assert("Segunda parte del token coincide con auth_secret", parts[1] == auth.auth_secret)

	# Probar guardado asíncrono
	var nuevo_nombre = "Tecatense VIP"
	var nuevo_personaje = "eli"
	auth.save_identity_async(nuevo_nombre, nuevo_personaje)

	# Esperar a que se guarde
	var save_frames = 60
	while auth._is_saving and save_frames > 0:
		await process_frame
		save_frames -= 1

	test_assert("Propiedad display_name actualizada", auth.display_name == nuevo_nombre)
	test_assert("Propiedad preferred_character_id actualizada", auth.preferred_character_id == nuevo_personaje)

	# Verificar persistencia en disco leyendo directamente
	test_assert("Archivo de identidad existe en user://", FileAccess.file_exists(AuthService.IDENTITY_FILE_PATH))
	var f = FileAccess.open(AuthService.IDENTITY_FILE_PATH, FileAccess.READ)
	if f:
		var text = f.get_as_text()
		f.close()
		var p = JSON.parse_string(text)
		test_assert("JSON en disco parsea correctamente", p is Dictionary)
		test_assert("JSON en disco contiene nuevo_nombre", p.get("display_name") == nuevo_nombre)
		test_assert("JSON en disco contiene nuevo_personaje", p.get("preferred_character_id") == nuevo_personaje)
	else:
		test_assert("No se pudo leer archivo en user://", false)

	print("================================================================================")
	print(" RESULTADOS: %d/%d pruebas superadas con éxito." % [passed_tests, total_tests])
	print("================================================================================")

	auth.queue_free()
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

class_name AuthService
extends Node

## Servicio de Autenticación Ligera y Gestión No Bloqueante de Identidad para Tecate Simulator.
##
## Administra las credenciales locales del cliente en user://player_identity.json.
## Utiliza WorkerThreadPool para despachar lecturas y escrituras asíncronas a un
## segundo hilo, garantizando que el hilo principal de renderizado nunca sufra caídas
## de fotogramas ni bloqueos durante el arranque o guardado de perfil.

signal identity_loaded(player_uuid: String, display_name: String, character_id: String)
signal identity_saved()

const IDENTITY_FILE_PATH: String = "user://player_identity.json"

var player_uuid: String = ""
var auth_secret: String = ""
var display_name: String = "Ciudadano"
var preferred_character_id: String = "axel"
var is_loaded: bool = false

var _is_saving: bool = false
var _pending_save: bool = false

func _ready() -> void:
	load_identity_async()

## Inicia la carga asíncrona de identidad en un hilo secundario sin congelar la pantalla de inicio
func load_identity_async() -> void:
	WorkerThreadPool.add_task(Callable(self, "_thread_load_identity"))

func _thread_load_identity() -> void:
	var loaded_data: Dictionary = {}

	if FileAccess.file_exists(IDENTITY_FILE_PATH):
		var file = FileAccess.open(IDENTITY_FILE_PATH, FileAccess.READ)
		if file:
			var json_text = file.get_as_text()
			file.close()
			var test_json = JSON.new()
			var parse_err = test_json.parse(json_text)
			if parse_err == OK and test_json.data is Dictionary:
				loaded_data = test_json.data

	# Si no existe o está corrupto, generar identidad nueva con criptografía aleatoria
	if loaded_data.is_empty() or not loaded_data.has("player_uuid") or not loaded_data.has("auth_secret"):
		loaded_data = _generate_new_identity_dict()
		_write_identity_file(loaded_data)

	# Asignar propiedades en el hilo principal
	call_deferred("_finalize_load", loaded_data)

func _finalize_load(data: Dictionary) -> void:
	player_uuid = str(data.get("player_uuid", ""))
	auth_secret = str(data.get("auth_secret", ""))
	display_name = str(data.get("display_name", "Ciudadano"))
	preferred_character_id = str(data.get("preferred_character_id", "axel"))
	is_loaded = true

	print("[AuthService] Identidad cargada asíncronamente: UUID=%s | Nombre='%s' | Personaje='%s'" % [
		player_uuid, display_name, preferred_character_id
	])
	identity_loaded.emit(player_uuid, display_name, preferred_character_id)

## Genera un UUIDv4 y un secreto criptográfico de 32 bytes en formato hexadecimal
func _generate_new_identity_dict() -> Dictionary:
	var crypto = Crypto.new()
	var uuid_bytes = crypto.generate_random_bytes(16)

	# Ajustar versión 4 y variante RFC 4122
	uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x40 # Versión 4
	uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80 # Variante RFC 4122

	var hex_chars = []
	for b in uuid_bytes:
		hex_chars.append("%02x" % b)

	var new_uuid = "%s%s%s%s-%s%s-%s%s-%s%s-%s%s%s%s%s%s" % hex_chars
	var secret_bytes = crypto.generate_random_bytes(32)
	var secret_hex = ""
	for b in secret_bytes:
		secret_hex += "%02x" % b

	return {
		"player_uuid": new_uuid,
		"auth_secret": secret_hex,
		"display_name": "Ciudadano Tecatense",
		"preferred_character_id": "axel",
		"created_at": Time.get_unix_time_from_system()
	}

## Guarda de forma no bloqueante cualquier modificación al perfil (nombre o personaje)
func save_identity_async(p_display_name: String, p_character_id: String) -> void:
	display_name = p_display_name if not p_display_name.is_empty() else display_name
	preferred_character_id = p_character_id if not p_character_id.is_empty() else preferred_character_id

	if _is_saving:
		_pending_save = true
		return

	_is_saving = true
	var payload = {
		"player_uuid": player_uuid,
		"auth_secret": auth_secret,
		"display_name": display_name,
		"preferred_character_id": preferred_character_id,
		"last_saved_at": Time.get_unix_time_from_system()
	}
	WorkerThreadPool.add_task(Callable(self, "_thread_save_identity").bind(payload))

func _thread_save_identity(payload: Dictionary) -> void:
	_write_identity_file(payload)
	call_deferred("_finalize_save")

func _write_identity_file(data: Dictionary) -> void:
	var file = FileAccess.open(IDENTITY_FILE_PATH, FileAccess.WRITE)
	if file:
		var json_str = JSON.stringify(data, "\t")
		file.store_string(json_str)
		file.close()

func _finalize_save() -> void:
	_is_saving = false
	identity_saved.emit()
	if _pending_save:
		_pending_save = false
		save_identity_async(display_name, preferred_character_id)

## Devuelve el token codificado en formato 'UUID:SECRET:NAME' para el paquete HELLO
func get_auth_token() -> String:
	if player_uuid.is_empty() or auth_secret.is_empty():
		return ""
	return "%s:%s:%s" % [player_uuid, auth_secret, display_name]

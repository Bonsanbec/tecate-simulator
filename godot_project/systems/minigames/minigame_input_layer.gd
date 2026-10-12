class_name MinigameInputLayer
extends Node

## Capa de Entrada Contextual para Minijuegos.
## Captura y reasigna inputs de forma aislada:
## - [M]: Abre/cierra el Menú de Minijuegos estilo Wii Party.
## - [Q]: Inicia o abre el selector de minijuegos de la ubicación actual.
## - [Y / N]: Acepta o declina convocatorias de reta en red.
## - [Backspace]: Concluye una sesión de práctica local.

const MinigameCatalogClass = preload("res://systems/minigames/minigame_catalog.gd")

@export var minigame_manager_path: NodePath = ^"../MinigameManager"
@export var wii_party_menu_path: NodePath = ^"../WiiPartyMinigameMenu"
@export var player_path: NodePath = ^"../Player"

var minigame_manager: Node = null
var wii_party_menu: Node = null
var player: Node = null

func _ready() -> void:
	_resolve_nodes()

func _resolve_nodes() -> void:
	if has_node(minigame_manager_path):
		minigame_manager = get_node(minigame_manager_path)
	elif get_parent() and get_parent().has_node("MinigameManager"):
		minigame_manager = get_parent().get_node("MinigameManager")

	if has_node(wii_party_menu_path):
		wii_party_menu = get_node(wii_party_menu_path)
	elif get_parent() and get_parent().has_node("WiiPartyMinigameMenu"):
		wii_party_menu = get_parent().get_node("WiiPartyMinigameMenu")

	if has_node(player_path):
		player = get_node(player_path)
	elif get_parent() and get_parent().has_node("Player"):
		player = get_parent().get_node("Player")

func _input(event: InputEvent) -> void:
	_resolve_nodes()
	if not (event is InputEventKey and event.pressed and not event.is_echo()):
		return

	# Si el menú Wii Party está abierto, [Escape] o [M] lo cierran
	if wii_party_menu and "is_open" in wii_party_menu and wii_party_menu.is_open:
		if event.keycode == KEY_ESCAPE or event.keycode == KEY_M:
			wii_party_menu.close_menu()
			if get_viewport():
				get_viewport().set_input_as_handled()
			return

func _unhandled_input(event: InputEvent) -> void:
	_resolve_nodes()
	if not minigame_manager:
		return

	if event is InputEventKey and event.pressed and not event.is_echo():
		# 0. Alternar Menú de Minijuegos Estilo Wii Party con [M]
		if event.keycode == KEY_M:
			if wii_party_menu and wii_party_menu.has_method("toggle_menu"):
				var loc_id = _get_player_active_location_id()
				wii_party_menu.toggle_menu(loc_id)
				if get_viewport():
					get_viewport().set_input_as_handled()
				return

		# 0b. Acción contextual de ubicación con [Q]
		if event.keycode == KEY_Q:
			var loc_id = _get_player_active_location_id()
			if not loc_id.is_empty():
				_trigger_location_minigame(loc_id)
				if get_viewport():
					get_viewport().set_input_as_handled()
				return

		# 0c. Salir de sesión de práctica local con [Backspace]
		if event.keycode == KEY_BACKSPACE:
			if "is_local_practice" in minigame_manager and minigame_manager.is_local_practice:
				minigame_manager.finish_local_practice(true)
				if get_viewport():
					get_viewport().set_input_as_handled()
				return

		# 1. Responder a Convocatoria Pendiente [Y / N]
		if minigame_manager.current_state == MinigameManager.ClientMinigameState.INVITATION_PENDING:
			if event.keycode == KEY_Y:
				minigame_manager.send_join_response(minigame_manager.current_game_id, true)
				if get_viewport():
					get_viewport().set_input_as_handled()
				return
			elif event.keycode == KEY_N:
				minigame_manager.send_join_response(minigame_manager.current_game_id, false)
				if get_viewport():
					get_viewport().set_input_as_handled()
				return

	# 2. Acciones durante partida activa
	if minigame_manager.current_state == MinigameManager.ClientMinigameState.ACTIVE and minigame_manager.is_participating:
		match minigame_manager.current_game_id:
			1:  # Mi Kiosko
				_handle_kiosko_input(event)
			3:  # Quemados
				_handle_quemados_input(event)

func _get_player_active_location_id() -> String:
	if not player or not is_instance_valid(player):
		return ""
	if "_nearby_minigame_location_id" in player and not player._nearby_minigame_location_id.is_empty():
		return player._nearby_minigame_location_id
	return ""

func _trigger_location_minigame(location_id: String) -> void:
	var loc_info = MinigameCatalogClass.get_location_info(location_id)
	var games = MinigameCatalogClass.get_minigames_by_location(location_id)
	if games.is_empty():
		return

	var primary_id = int(loc_info.get("primary_game_id", games[0]["id"]))
	var primary_game = MinigameCatalogClass.get_minigame(primary_id)

	# Si la ubicación tiene un único juego jugable o si el juego principal es de Fase 1 y se presiona [Q]:
	# Si hay varios juegos en la ubicación (ej. Kiosko o Explanada), abrir el menú Wii Party filtrado
	# o iniciar el principal si solo hay 1 jugable:
	if games.size() > 1 and wii_party_menu and wii_party_menu.has_method("open_menu"):
		wii_party_menu.open_menu(location_id)
		wii_party_menu.select_minigame(primary_id)
	elif primary_game.get("is_playable", false):
		minigame_manager.start_or_summon_minigame(
			primary_id,
			0,
			primary_game.get("max_players", 8),
			primary_game.get("arena_id", 1)
		)
	elif wii_party_menu and wii_party_menu.has_method("open_menu"):
		wii_party_menu.open_menu(location_id)
		wii_party_menu.select_minigame(primary_id)

func _handle_kiosko_input(event: InputEvent) -> void:
	# Bloqueo / Parry [Clic Derecho o Tecla F]
	if (event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT and event.pressed) or (event is InputEventKey and event.keycode == KEY_F and event.pressed and not event.is_echo()):
		minigame_manager.send_game_action(2, 0, 0.65, Vector3.ZERO)
		if get_viewport():
			get_viewport().set_input_as_handled()

func _handle_quemados_input(event: InputEvent) -> void:
	# Tiro de Pelota Balística [Clic Izquierdo o Tecla G]
	if (event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED) or (event is InputEventKey and event.keycode == KEY_G and event.pressed and not event.is_echo()):
		var look_dir = Vector3(0, 0, 1)
		if player and is_instance_valid(player):
			var cam = player.get_viewport().get_camera_3d() if player.get_viewport() else null
			if cam:
				look_dir = -cam.global_transform.basis.z.normalized()
			else:
				look_dir = -player.global_transform.basis.z.normalized()

		minigame_manager.send_game_action(4, 0, 18.0, look_dir)
		if get_viewport():
			get_viewport().set_input_as_handled()

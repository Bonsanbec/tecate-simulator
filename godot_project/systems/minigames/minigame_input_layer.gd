class_name MinigameInputLayer
extends Node

## Capa de Entrada Contextual para Minijuegos.
## Captura y reasigna inputs de forma aislada sin saturar PlayerController.

@export var minigame_manager_path: NodePath = ^"../MinigameManager"
@export var player_path: NodePath = ^"../Player"

var minigame_manager: Node = null
var player: Node = null

func _ready() -> void:
	if has_node(minigame_manager_path):
		minigame_manager = get_node(minigame_manager_path)
	elif get_parent() and get_parent().has_node("MinigameManager"):
		minigame_manager = get_parent().get_node("MinigameManager")

	if has_node(player_path):
		player = get_node(player_path)
	elif get_parent() and get_parent().has_node("Player"):
		player = get_parent().get_node("Player")

func _unhandled_input(event: InputEvent) -> void:
	if not minigame_manager:
		return

	# 1. Responder a Convocatoria Pendiente [Y / N]
	if minigame_manager.current_state == MinigameManager.ClientMinigameState.INVITATION_PENDING:
		if event is InputEventKey and event.pressed and not event.is_echo():
			if event.keycode == KEY_Y:
				minigame_manager.send_join_response(minigame_manager.current_game_id, true)
				get_viewport().set_input_as_handled()
				return
			elif event.keycode == KEY_N:
				minigame_manager.send_join_response(minigame_manager.current_game_id, false)
				get_viewport().set_input_as_handled()
				return

	# 2. Acciones durante partida activa
	if minigame_manager.current_state == MinigameManager.ClientMinigameState.ACTIVE and minigame_manager.is_participating:
		match minigame_manager.current_game_id:
			1:  # Mi Kiosko
				_handle_kiosko_input(event)
			3:  # Quemados
				_handle_quemados_input(event)

func _handle_kiosko_input(event: InputEvent) -> void:
	# Bloqueo / Parry [Clic Derecho o Tecla F]
	if (event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT and event.pressed) or (event is InputEventKey and event.keycode == KEY_F and event.pressed and not event.is_echo()):
		minigame_manager.send_game_action(2, 0, 0.65, Vector3.ZERO)
		get_viewport().set_input_as_handled()

func _handle_quemados_input(event: InputEvent) -> void:
	# Tiro de Pelota Balística [Clic Izquierdo o Tecla G]
	if (event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED) or (event is InputEventKey and event.keycode == KEY_G and event.pressed and not event.is_echo()):
		var look_dir = Vector3(0, 0, 1)
		if player and is_instance_valid(player):
			var cam = player.get_viewport().get_camera_3d()
			if cam:
				look_dir = -cam.global_transform.basis.z.normalized()
			else:
				look_dir = -player.global_transform.basis.z.normalized()

		minigame_manager.send_game_action(4, 0, 18.0, look_dir)
		get_viewport().set_input_as_handled()

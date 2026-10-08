class_name MinigameManager
extends Node

## Orquestador Central y Coordinador de Eventos / Minijuegos para Tecate Simulator
## Gestiona la convocatoria de retas, ciclo de vida de actividades,
## preservación de estado espacial y entrega de recompensas económicas locales.

signal minigame_registered(game_id: String, display_name: String)
signal minigame_started(game_id: String, display_name: String)
signal minigame_countdown(seconds_left: int)
signal minigame_ended(game_id: String, results: Dictionary)
signal minigame_cancelled(game_id: String)

const MinigameBaseClass = preload("res://systems/minigames/core/minigame_base.gd")
const ProfileEconomyClass = preload("res://systems/minigames/economy/profile_economy.gd")
const MinigameMiKioskoClass = preload("res://systems/minigames/games/mi_kiosko/minigame_mi_kiosko.gd")
const MinigameLasTraesClass = preload("res://systems/minigames/games/las_traes/minigame_las_traes.gd")
const MinigameQuemadosClass = preload("res://systems/minigames/games/quemados/minigame_quemados.gd")

var active_minigame: MinigameBaseClass = null
var economy: ProfileEconomyClass = null
var registered_minigames: Dictionary = {}

func _ready() -> void:
	economy = ProfileEconomyClass.new()
	_register_default_minigames()

func _register_default_minigames() -> void:
	register_minigame("mi_kiosko", "Mi Kiosko", MinigameMiKioskoClass)
	register_minigame("las_traes", "Las Traes", MinigameLasTraesClass)
	register_minigame("quemados", "Quemados", MinigameQuemadosClass)

func register_minigame(game_id: String, display_name: String, script_class: Variant) -> void:
	registered_minigames[game_id] = {
		"id": game_id,
		"name": display_name,
		"class": script_class
	}
	minigame_registered.emit(game_id, display_name)

func is_minigame_active() -> bool:
	return active_minigame != null and active_minigame.current_state != MinigameBaseClass.GameState.IDLE

func start_minigame(game_id: String, participants: Array, config: Dictionary = {}) -> bool:
	if is_minigame_active():
		push_warning("MinigameManager: No se puede iniciar '%s', ya hay un minijuego en curso ('%s')." % [game_id, active_minigame.minigame_id])
		return false

	if not registered_minigames.has(game_id):
		push_error("MinigameManager: Minijuego '%s' no está registrado en el catálogo." % game_id)
		return false

	var meta = registered_minigames[game_id]
	var minigame_instance: MinigameBaseClass = meta["class"].new()
	minigame_instance.name = "ActiveMinigame_" + game_id
	add_child(minigame_instance)

	# Vincular señales del minijuego
	minigame_instance.countdown_tick.connect(_on_countdown_tick)
	minigame_instance.minigame_completed.connect(_on_minigame_completed)

	active_minigame = minigame_instance

	var setup_ok = active_minigame.setup(participants, config)
	if not setup_ok:
		_cleanup_active()
		return false

	active_minigame.start_countdown()
	minigame_started.emit(game_id, meta["name"])
	return true

func cancel_minigame() -> void:
	if not is_minigame_active():
		return
	var id = active_minigame.minigame_id
	active_minigame.cleanup_and_restore()
	_cleanup_active()
	minigame_cancelled.emit(id)

func _on_countdown_tick(seconds_left: int) -> void:
	minigame_countdown.emit(seconds_left)

func _on_minigame_completed(results: Dictionary) -> void:
	if not active_minigame:
		return

	var game_id = active_minigame.minigame_id
	var winner_id = results.get("winner_id", "")

	# Otorgar recompensas en la economía local
	if economy:
		var is_local_winner = (winner_id == "local_player" or winner_id == "Player")
		var prize = active_minigame.reward_first_place if is_local_winner else active_minigame.reward_participation
		economy.record_game_finished(is_local_winner, prize)

	minigame_ended.emit(game_id, results)

	# Restaurar jugadores tras breve pausa de celebración
	active_minigame.cleanup_and_restore()
	_cleanup_active()

func _cleanup_active() -> void:
	if active_minigame:
		if is_instance_valid(active_minigame):
			active_minigame.queue_free()
		active_minigame = null

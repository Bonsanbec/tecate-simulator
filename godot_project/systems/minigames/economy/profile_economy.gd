class_name ProfileEconomy
extends RefCounted

## Gestor de Economía Persistente y Cosméticos Locales para Tecate Simulator
## Maneja los "Pesos Tecatenses" (o Corcholatas), registro de victorias y catálogo
## de accesorios desbloqueables guardados en disco del usuario.

const SAVE_PATH: String = "user://player_economy_profile.json"

var balance_pesos: int = 100
var total_victorias: int = 0
var minijuegos_jugados: int = 0
var unlocked_items: Array[String] = ["elote_con_chile"]
var equipped_hat: String = ""
var equipped_accessory: String = ""

func _init() -> void:
	load_profile()

func load_profile() -> bool:
	if not FileAccess.file_exists(SAVE_PATH):
		return false

	var file = FileAccess.open(SAVE_PATH, FileAccess.READ)
	if not file:
		return false

	var text = file.get_as_text()
	file.close()

	var json = JSON.new()
	var error = json.parse(text)
	if error != OK:
		return false

	var data = json.data
	if data is Dictionary:
		balance_pesos = int(data.get("balance_pesos", 100))
		total_victorias = int(data.get("total_victorias", 0))
		minijuegos_jugados = int(data.get("minijuegos_jugados", 0))
		equipped_hat = str(data.get("equipped_hat", ""))
		equipped_accessory = str(data.get("equipped_accessory", ""))

		unlocked_items.clear()
		for item in data.get("unlocked_items", []):
			unlocked_items.append(str(item))

		if not unlocked_items.has("elote_con_chile"):
			unlocked_items.append("elote_con_chile")
		return true

	return false

func save_profile() -> bool:
	var data = {
		"balance_pesos": balance_pesos,
		"total_victorias": total_victorias,
		"minijuegos_jugados": minijuegos_jugados,
		"unlocked_items": unlocked_items,
		"equipped_hat": equipped_hat,
		"equipped_accessory": equipped_accessory,
		"last_saved_unix": Time.get_unix_time_from_system()
	}

	var json_str = JSON.stringify(data, "\t")
	var file = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if not file:
		return false

	file.store_string(json_str)
	file.close()
	return true

func add_pesos(amount: int) -> int:
	if amount > 0:
		balance_pesos += amount
		save_profile()
	return balance_pesos

func spend_pesos(amount: int) -> bool:
	if amount <= 0:
		return true
	if balance_pesos >= amount:
		balance_pesos -= amount
		save_profile()
		return true
	return false

func unlock_cosmetic(item_id: String, cost_pesos: int = 0) -> bool:
	if unlocked_items.has(item_id):
		return true

	if cost_pesos > 0:
		if not spend_pesos(cost_pesos):
			return false

	unlocked_items.append(item_id)
	save_profile()
	return true

func has_cosmetic(item_id: String) -> bool:
	return unlocked_items.has(item_id)

func record_game_finished(is_winner: bool, prize_pesos: int = 15) -> void:
	minijuegos_jugados += 1
	if is_winner:
		total_victorias += 1
	add_pesos(prize_pesos)
	save_profile()

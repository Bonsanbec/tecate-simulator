extends SceneTree

var _frames = 0
var _instance: Node

func _init():
	print("--- Probando ejecución continua de main.tscn ---")
	var main_scene = load("res://main.tscn")
	assert(main_scene != null, "main.tscn debe poder cargarse")
	_instance = main_scene.instantiate()
	root.add_child(_instance)
	print("✓ main.tscn agregada al árbol de escena.")

func _process(_delta):
	_frames += 1
	if _frames == 5:
		var sky_sys: SkySystem = _instance.get_node_or_null("SkySystem")
		assert(sky_sys != null, "SkySystem debe existir")
		assert(sky_sys.celestial_state != null, "CelestialState debe haberse calculado")
		assert(sky_sys.current_weather != null, "CurrentWeather debe haberse obtenido")
		print("Frame 5 comprobado:")
		print("  • Sol dir: ", sky_sys.celestial_state.sun_direction)
		print("  • Luna dir: ", sky_sys.celestial_state.moon_direction)
		print("  • Clima: ", sky_sys.current_weather.condition)
		print("  • Capas de Nubes: ", sky_sys.cloud_manager.get_child_count(), " capas activas.")
		print("  • Cuchuma Stratus Altitud Y: ", sky_sys.cloud_manager.layer_cuchuma.global_position.y, "m")
		print("  • Cumulus Altitud Y: ", sky_sys.cloud_manager.layer_cumulus.global_position.y, "m")
		print("  • Cirrus Altitud Y: ", sky_sys.cloud_manager.layer_cirrus.global_position.y, "m")
	elif _frames == 10:
		var sky_sys: SkySystem = _instance.get_node_or_null("SkySystem")
		sky_sys.realtime_sync = false
		sky_sys.manual_hour = 24.0
		sky_sys._apply_manual_hour_to_simulated_time()
		print("✓ manual_hour = 24.0 probado sin errores de datetime.")
	elif _frames >= 18:
		print("✓ 18 frames ejecutados con éxito continuo.")
		_instance.queue_free()
		quit(0)


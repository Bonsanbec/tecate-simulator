class_name CitizenProfile
extends Resource

## Perfil de Identidad de Ciudadano / Avatar para Tecate Simulator
## Define las características visuales, modelo 3D GLB, props y metadatos
## antropométricos de los personajes de Tecate basados en personas reales.

@export var identity_id: String = "axel"
@export var display_name: String = "Axel"
@export var model_path: String = "res://assets/characters/citizens/axel.glb"
@export var archetype: String = "urban_youth" # "urban_youth", "formal_beige", "casual_street", "formal_artist"
@export var preferred_greeting: String = "¡Qué onda! Bienvenidos a Tecate."
@export var voice_pitch: float = 1.0
@export var walk_speed_modifier: float = 1.0
@export var enable_skin_sss: bool = true
@export var sss_strength: float = 0.32
@export var sss_color: Color = Color(0.92, 0.45, 0.35, 1.0) # Tono subdérmico cálido

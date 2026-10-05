class_name DestructibleProp3D
extends StaticBody3D

## Objeto Urbano Destruible para Tecate Simulator
## Permite a cualquier elemento del entorno (mobiliario urbano, señales, bombas de gasolina, bancas)
## poseer una barra de vida centralizada y ser destruido al agotar sus puntos de salud.

const HealthComponentClass = preload("res://systems/combat/health_component.gd")
const HealthBar3DClass = preload("res://ui/health_bar_3d.gd")
const EntityHealthDefaultsClass = preload("res://systems/combat/entity_health_defaults.gd")

signal prop_destroyed(prop: Node3D, attacker: Node)

@export var prop_name: String = "Objeto Urbano"
@export var entity_type_name: String = "PROP_MEDIUM"
@export var custom_max_health: float = 0.0

var health_component: HealthComponentClass = null
var health_bar_3d: HealthBar3DClass = null

func _ready() -> void:
	add_to_group("destructible_props")
	add_to_group("damageable")
	_initialize_health()

func _initialize_health() -> void:
	if health_component == null:
		health_component = get_node_or_null("HealthComponent") as HealthComponentClass
		if not health_component:
			health_component = HealthComponentClass.new()
			health_component.name = "HealthComponent"
			health_component.auto_initialize = false
			add_child(health_component)

	var target_hp = custom_max_health if custom_max_health > 0.0 else EntityHealthDefaultsClass.get_default_health_for_type(entity_type_name)
	health_component.initialize(target_hp)
	health_component.died.connect(_on_died)

	if health_bar_3d == null:
		health_bar_3d = get_node_or_null("HealthBar3D") as HealthBar3DClass
		if not health_bar_3d:
			health_bar_3d = HealthBar3DClass.new()
			health_bar_3d.name = "HealthBar3D"
			health_bar_3d.billboard_offset = Vector3(0, 1.2, 0)
			add_child(health_bar_3d)

	health_bar_3d.setup(health_component)

func take_damage(amount: float, attacker: Node = null) -> float:
	if health_component:
		return health_component.take_damage(amount, attacker)
	return 0.0

func _on_died(attacker: Node) -> void:
	prop_destroyed.emit(self, attacker)
	# Efecto visual rápido de fragmentación o destello al destruirse
	_spawn_destruction_effect()
	queue_free()

func _spawn_destruction_effect() -> void:
	var effect_mesh = MeshInstance3D.new()
	var box = BoxMesh.new()
	box.size = Vector3(0.5, 0.5, 0.5)
	effect_mesh.mesh = box

	var mat = StandardMaterial3D.new()
	mat.albedo_color = Color(0.9, 0.3, 0.1, 1.0)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.4, 0.0, 1.0)
	effect_mesh.material_override = mat

	if get_parent():
		get_parent().add_child(effect_mesh)
		effect_mesh.global_position = global_position
		# Desaparecer efecto tras 0.5 segundos
		var tween = effect_mesh.create_tween()
		tween.tween_property(effect_mesh, "scale", Vector3.ZERO, 0.5)
		tween.tween_callback(effect_mesh.queue_free)

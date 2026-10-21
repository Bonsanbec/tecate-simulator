class_name AppTechnicalStrings
extends RefCounted

## Constantes Técnicas y Operativas Centralizadas para Tecate Simulator
##
## Centraliza rutas canónicas de escenas, nombres de acciones de entrada,
## identificadores de grupos de nodos, nombres de capas de colisión,
## claves de persistencia y parámetros sintácticos del motor Godot.
##
## Referencia normativa: docs/strings.md

# =============================================================================
# RUTAS DE ESCENAS Y RECURSOS CANÓNICOS
# =============================================================================
const SCENE_MAIN: String = "res://main.tscn"
const SCENE_START_SCREEN: String = "res://ui/start_screen.tscn"
const SCENE_PLAYER_HUD: String = "res://ui/player_hud.tscn"
const SCENE_SKY_SYSTEM: String = "res://systems/environment/sky_system.tscn"
const SCENE_CITIZEN_ENTITY: String = "res://systems/network/citizen_entity.tscn"
const SCENE_REMOTE_PLAYER: String = "res://systems/network/remote_player.tscn"
const SCENE_REMOTE_VEHICLE: String = "res://systems/network/remote_vehicle.tscn"
const SCENE_BUS_HONGO: String = "res://assets/vehicles/bus_hongo.tscn"

# Fuentes y Tipografías
const FONT_DIN_CONDENSED_BOLD: String = "res://assets/fonts/DIN_Condensed_Bold.ttf"

# =============================================================================
# ACCIONES DEL MAPA DE ENTRADA (INPUTMAP)
# =============================================================================
const ACTION_MOVE_FORWARD: String = "move_forward"
const ACTION_MOVE_BACKWARD: String = "move_backward"
const ACTION_MOVE_LEFT: String = "move_left"
const ACTION_MOVE_RIGHT: String = "move_right"
const ACTION_JUMP: String = "jump"
const ACTION_SPRINT: String = "sprint"
const ACTION_INTERACT: String = "interact"
const ACTION_CAMERA_TOGGLE: String = "camera_toggle"
const ACTION_TOGGLE_MENU: String = "toggle_menu"
const ACTION_TOGGLE_MINIGAMES: String = "toggle_minigame_menu"
const ACTION_VEHICLE_ACCEL: String = "vehicle_accelerate"
const ACTION_VEHICLE_BRAKE: String = "vehicle_brake"
const ACTION_VEHICLE_STEER_LEFT: String = "vehicle_steer_left"
const ACTION_VEHICLE_STEER_RIGHT: String = "vehicle_steer_right"

# =============================================================================
# GRUPOS DE LA JERARQUÍA DE NODOS DE GODOT
# =============================================================================
const GROUP_PLAYERS: String = "players"
const GROUP_REMOTE_PLAYERS: String = "remote_players"
const GROUP_VEHICLES: String = "vehicles"
const GROUP_PROPS: String = "props"
const GROUP_SEATS: String = "seats"
const GROUP_PUMP_ZONES: String = "pump_zones"
const GROUP_MINIGAME_ZONES: String = "minigame_zones"
const GROUP_MINIGAME_MANAGER: String = "minigame_manager"
const GROUP_BUILDINGS: String = "buildings"
const GROUP_DESTRUCTIBLE: String = "destructible"

# =============================================================================
# IDENTIFICADORES DE NODOS CANÓNICOS
# =============================================================================
const NODE_PLAYER: String = "Player"
const NODE_NETWORK_CLIENT: String = "NetworkClient"
const NODE_MINIGAME_MANAGER: String = "MinigameManager"
const NODE_SKY_SYSTEM: String = "SkySystem"
const NODE_CAMERA_3D: String = "Camera3D"
const NODE_ANIMATION_PLAYER: String = "AnimationPlayer"
const NODE_CANVAS_LAYER: String = "CanvasLayer"
const NODE_AUTH_SERVICE: String = "AuthService"
const NODE_PHONE_MENU: String = "PhoneMenu"
const NODE_WII_PARTY_MENU: String = "PhoneMenu" # Alias de compatibilidad hacia NODE_PHONE_MENU

# =============================================================================
# RED Y PROTOCOLO MULTIJUGADOR TKT
# =============================================================================
const NET_DEFAULT_HOST: String = "api.tecate.bonsanbec.dev"
const NET_DEFAULT_PORT: int = 52665
const NET_PROTOCOL_VERSION: String = "TKT/1"
const NET_SAVE_IDENTITY_FILE: String = "user://auth_identity.json"

# =============================================================================
# IDENTIFICADORES DE PERSONAJES
# =============================================================================
const CHAR_ID_AXEL: String = "axel"
const CHAR_ID_ELI: String = "eli"
const CHAR_ID_ASTORGA: String = "astorga"

# =============================================================================
# NOMBRES DE MÉTODOS REFLECTIVOS Y LLAMADAS DINÁMICAS
# =============================================================================
const METHOD_SET_INPUT_ENABLED: StringName = &"set_input_enabled"
const METHOD_APPLY_IDENTITY: StringName = &"apply_identity"
const METHOD_OPEN_MENU: StringName = &"open_menu"
const METHOD_RESPAWN: StringName = &"respawn"
const METHOD_SEND_CHARACTER_SELECT: StringName = &"send_character_select"
const METHOD_SET_TEXT: StringName = &"set_text"

# =============================================================================
# PROPIEDADES DE TEMA DE INTERFAZ (THEME OVERRIDES)
# =============================================================================
const THEME_FONT: StringName = &"font"
const THEME_NORMAL_FONT: StringName = &"normal_font"
const THEME_FONT_SIZE: StringName = &"font_size"
const THEME_FONT_COLOR: StringName = &"font_color"
const THEME_FONT_HOVER_COLOR: StringName = &"font_hover_color"
const THEME_FONT_FOCUS_COLOR: StringName = &"font_focus_color"
const THEME_FONT_PRESSED_COLOR: StringName = &"font_pressed_color"
const THEME_FONT_SHADOW_COLOR: StringName = &"font_shadow_color"
const THEME_SHADOW_OFFSET_X: StringName = &"shadow_offset_x"
const THEME_SHADOW_OFFSET_Y: StringName = &"shadow_offset_y"
const THEME_SHADOW_OUTLINE_SIZE: StringName = &"shadow_outline_size"
const THEME_STYLE_NORMAL: StringName = &"normal"
const THEME_STYLE_HOVER: StringName = &"hover"
const THEME_STYLE_FOCUS: StringName = &"focus"
const THEME_STYLE_PRESSED: StringName = &"pressed"
const THEME_STYLE_PANEL: StringName = &"panel"
const THEME_MARGIN_LEFT: StringName = &"margin_left"
const THEME_MARGIN_RIGHT: StringName = &"margin_right"
const THEME_MARGIN_TOP: StringName = &"margin_top"
const THEME_MARGIN_BOTTOM: StringName = &"margin_bottom"
const THEME_SEPARATION: StringName = &"separation"
const THEME_H_SEPARATION: StringName = &"h_separation"
const THEME_V_SEPARATION: StringName = &"v_separation"

# =============================================================================
# EXTENSIONES DE ARCHIVO Y SUFIJOS
# =============================================================================
const EXT_GLB: String = ".glb"
const EXT_TSCN: String = ".tscn"
const EXT_TRES: String = ".tres"
const EXT_PNG: String = ".png"
const EXT_JSON: String = ".json"
const EXT_GD: String = ".gd"
const EXT_TTF: String = ".ttf"

# =============================================================================
# MODIFICADORES Y REGLAS DE COLISIÓN DE MINIJUEGOS
# =============================================================================
const NODE_MINIGAME_COLLISION_DIRECTOR: String = "MinigameCollisionDirector"
const KEY_COLLISION_OVERRIDES: String = "collision_overrides"
const KEY_TARGET_LOCATION: String = "target_location"
const KEY_SHAPE_PATTERNS: String = "shape_patterns"
const KEY_MODE: String = "mode"
const KEY_LOW_OBSTACLE_HEIGHT_RATIO: String = "low_obstacle_height_ratio"

const COLLISION_OVERRIDE_MODE_DISABLED: String = "disabled"
const COLLISION_OVERRIDE_MODE_LOW_OBSTACLE: String = "low_obstacle"

const PATTERN_HERRERIA_PERIMETRAL: String = "*Herreria_Perimetral*"
const PATTERN_BARANDAL: String = "*Barandal*"
const PATTERN_RAILING: String = "*Railing*"

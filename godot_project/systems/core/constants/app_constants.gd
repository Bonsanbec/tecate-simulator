class_name AppConstants
extends RefCounted

## Fachada Canónica de Constantes para Tecate Simulator
##
## Provee un punto de acceso de alto nivel que delega y expone transversalmente
## las constantes fundamentales de AppStrings y AppTechnicalStrings.
##
## Referencia normativa: docs/strings.md

# Delegaciones de Marca y Título
const APP_NAME: String = AppStrings.APP_NAME
const APP_SHORT_NAME: String = AppStrings.APP_SHORT_NAME
const APP_TITLE_TECATE: String = AppStrings.APP_TITLE_TECATE
const APP_SUBTITLE: String = AppStrings.APP_SUBTITLE

# Delegaciones de Acciones Comunes
const ACTION_INTERACT: String = AppTechnicalStrings.ACTION_INTERACT
const ACTION_CAMERA_TOGGLE: String = AppTechnicalStrings.ACTION_CAMERA_TOGGLE
const ACTION_TOGGLE_MENU: String = AppTechnicalStrings.ACTION_TOGGLE_MENU
const ACTION_TOGGLE_MINIGAMES: String = AppTechnicalStrings.ACTION_TOGGLE_MINIGAMES

# Delegaciones de Grupos Fundamentales
const GROUP_PLAYERS: String = AppTechnicalStrings.GROUP_PLAYERS
const GROUP_VEHICLES: String = AppTechnicalStrings.GROUP_VEHICLES
const GROUP_SEATS: String = AppTechnicalStrings.GROUP_SEATS

# Delegaciones de Rutas Canónicas
const SCENE_MAIN: String = AppTechnicalStrings.SCENE_MAIN
const SCENE_START_SCREEN: String = AppTechnicalStrings.SCENE_START_SCREEN
const SCENE_PLAYER_HUD: String = AppTechnicalStrings.SCENE_PLAYER_HUD

class_name RemotePlayer
extends "res://systems/characters/citizen_entity.gd"

## Representación visual, física y cinemática interpolada de un jugador remoto en Tecate Simulator.
## Hereda de CitizenEntity compartiendo el cuerpo físico (CharacterBody3D con cápsula antropométrica),
## el rig 3D antropométrico, la locomoción procedural y la interpolación Hermite cúbica.

func setup(id: int, _is_npc: bool = false, p_name: String = "") -> void:
	super.setup(id, false, p_name if not p_name.is_empty() else ("Jugador #%d" % id))

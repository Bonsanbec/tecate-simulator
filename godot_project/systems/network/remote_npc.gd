class_name RemoteNPC
extends "res://systems/characters/citizen_entity.gd"

## Representación visual, física e interpolada de un ciudadano o agente peatonal coordinado por el servidor TKT/1.
## Hereda de CitizenEntity compartiendo el cuerpo físico (CharacterBody3D con cápsula antropométrica),
## el rig 3D antropométrico, la locomoción procedural y la interpolación Hermite cúbica.

func setup(id: int, _is_npc: bool = true, npc_name: String = "") -> void:
	super.setup(id, true, npc_name if not npc_name.is_empty() else ("Ciudadano #%d" % id))

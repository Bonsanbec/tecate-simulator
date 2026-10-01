class_name BusHongoController
extends RouteVehicle

## Controlador Canónico Paramétrico para el Autobús 'El Hongo' (Mercedes-Benz Marcopolo Boxer OF)
## Admite configuración individual por instancia de número de unidad, placas y concesión oficial.

@export_group("Identidad de Unidad")
@export var unit_number: String = "24":
	set(value):
		unit_number = value
		_update_parametric_labels()

@export var license_plate: String = "A-30530-A":
	set(value):
		license_plate = value
		_update_parametric_labels()

@export var concession_id: String = "TKT-A-19-00006":
	set(value):
		concession_id = value
		_update_parametric_labels()

@export var route_destination: String = "TECATE   EL HONGO   LA RUMOROSA":
	set(value):
		route_destination = value
		_update_parametric_labels()

func _ready() -> void:
	super._ready()
	_update_parametric_labels()

func _update_parametric_labels() -> void:
	var label_unit_l = get_node_or_null("ParametricLabels/Label_Unit_Left") as Label3D
	if label_unit_l:
		label_unit_l.text = unit_number

	var label_unit_r = get_node_or_null("ParametricLabels/Label_Unit_Right") as Label3D
	if label_unit_r:
		label_unit_r.text = unit_number

	var label_unit_rear = get_node_or_null("ParametricLabels/Label_Unit_Rear") as Label3D
	if label_unit_rear:
		label_unit_rear.text = unit_number

	var label_plate_front = get_node_or_null("ParametricLabels/Label_Plate_Front") as Label3D
	if label_plate_front:
		label_plate_front.text = license_plate

	var label_plate_rear = get_node_or_null("ParametricLabels/Label_Plate_Rear") as Label3D
	if label_plate_rear:
		label_plate_rear.text = license_plate

	var label_concession = get_node_or_null("ParametricLabels/Label_Concession_Rear") as Label3D
	if label_concession:
		label_concession.text = concession_id

	var label_dest = get_node_or_null("ParametricLabels/Label_Destination_Front") as Label3D
	if label_dest:
		label_dest.text = route_destination

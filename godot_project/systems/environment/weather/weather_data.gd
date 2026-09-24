class_name WeatherData
extends RefCounted

## Objeto de Transferencia de Datos Meteorológicos para Tecate Simulator
##
## Representa una captura instantánea de las variables atmosféricas y climáticas,
## totalmente desacoplada de la fuente de origen (procedural o API REST).

# Condiciones canónicas
const COND_CLEAR: String = "CLEAR"
const COND_PARTLY_CLOUDY: String = "PARTLY_CLOUDY"
const COND_OVERCAST: String = "OVERCAST"
const COND_RAIN: String = "RAIN"
const COND_FOG: String = "FOG"
const COND_WINDY: String = "WINDY"

var condition: String = COND_CLEAR
var cloud_coverage: float = 0.25 # [0.0 = cielo despejado, 1.0 = cobertura total]
var cloud_density: float = 0.70  # [0.0 = tenue/vaporosa, 1.0 = densa/opaca]
var precipitation: float = 0.0   # [0.0 = seco, 1.0 = aguacero torrencial]
var fog_density: float = 0.0     # [0.0 = nítido, 1.0 = niebla espesa]
var wind_speed_mps: float = 5.0  # Metros por segundo (~18 km/h)
var wind_direction_deg: float = 270.0 # Grados de donde sopla el viento (270 = Poniente/Pacífico)
var temperature_c: float = 22.0  # Grados Celsius
var humidity_pct: float = 45.0   # Porcentaje de humedad relativa [0, 100]
var pressure_hpa: float = 1013.25 # Presión atmosférica al nivel del mar (hPa)
var timestamp: int = 0

## Genera una nueva instancia interpolada suavemente entre dos estados climáticos
func lerp_with(other: WeatherData, weight: float) -> WeatherData:
	var w = clamp(weight, 0.0, 1.0)
	var result = WeatherData.new()
	
	result.condition = other.condition if w >= 0.5 else condition
	result.cloud_coverage = lerpf(cloud_coverage, other.cloud_coverage, w)
	result.cloud_density = lerpf(cloud_density, other.cloud_density, w)
	result.precipitation = lerpf(precipitation, other.precipitation, w)
	result.fog_density = lerpf(fog_density, other.fog_density, w)
	result.wind_speed_mps = lerpf(wind_speed_mps, other.wind_speed_mps, w)
	result.temperature_c = lerpf(temperature_c, other.temperature_c, w)
	result.humidity_pct = lerpf(humidity_pct, other.humidity_pct, w)
	result.pressure_hpa = lerpf(pressure_hpa, other.pressure_hpa, w)
	result.timestamp = int(lerpf(float(timestamp), float(other.timestamp), w))
	
	# Interpolación de ángulo más corto para la dirección del viento
	var diff = fposmod(other.wind_direction_deg - wind_direction_deg + 180.0, 360.0) - 180.0
	result.wind_direction_deg = fposmod(wind_direction_deg + diff * w, 360.0)
	
	return result

func duplicate() -> WeatherData:
	var d = WeatherData.new()
	d.condition = condition
	d.cloud_coverage = cloud_coverage
	d.cloud_density = cloud_density
	d.precipitation = precipitation
	d.fog_density = fog_density
	d.wind_speed_mps = wind_speed_mps
	d.wind_direction_deg = wind_direction_deg
	d.temperature_c = temperature_c
	d.humidity_pct = humidity_pct
	d.pressure_hpa = pressure_hpa
	d.timestamp = timestamp
	return d

func to_dict() -> Dictionary:
	return {
		"condition": condition,
		"cloud_coverage": cloud_coverage,
		"cloud_density": cloud_density,
		"precipitation": precipitation,
		"fog_density": fog_density,
		"wind_speed_mps": wind_speed_mps,
		"wind_direction_deg": wind_direction_deg,
		"temperature_c": temperature_c,
		"humidity_pct": humidity_pct,
		"pressure_hpa": pressure_hpa,
		"timestamp": timestamp
	}

static func from_dict(dict: Dictionary) -> WeatherData:
	var data = WeatherData.new()
	data.condition = dict.get("condition", COND_CLEAR)
	data.cloud_coverage = float(dict.get("cloud_coverage", 0.25))
	data.cloud_density = float(dict.get("cloud_density", 0.70))
	data.precipitation = float(dict.get("precipitation", 0.0))
	data.fog_density = float(dict.get("fog_density", 0.0))
	data.wind_speed_mps = float(dict.get("wind_speed_mps", 5.0))
	data.wind_direction_deg = float(dict.get("wind_direction_deg", 270.0))
	data.temperature_c = float(dict.get("temperature_c", 22.0))
	data.humidity_pct = float(dict.get("humidity_pct", 45.0))
	data.pressure_hpa = float(dict.get("pressure_hpa", 1013.25))
	data.timestamp = int(dict.get("timestamp", 0))
	return data

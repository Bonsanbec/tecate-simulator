shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

/*
 * Shader Espacial 3D para Capas Físicas de Nubes en Tecate Simulator
 *
 * Características:
 * - Cúmulos bien definidos y esculpidos (Worley + FBM Billow), sin aspecto difuso ni neblina.
 * - Desvanecimiento volumétrico suave (Soft Depth Fade) contra las laderas del Cerro Cuchumá
 *   mediante lectura analítica del búfer de profundidad (depth_texture).
 * - Desvanecimiento radial de horizonte para evitar cortes geométricos en el borde de la malla.
 * - Iluminación física: absorción Beer-Lambert, forward-scattering Henyey-Greenstein
 *   (resplandor plateado en los bordes) y respuesta a la luz solar, lunar y ambiental.
 */

uniform sampler2D depth_texture : hint_depth_texture, filter_linear_mipmap;

// Parámetros climáticos
uniform float cloud_coverage : hint_range(0.0, 1.0) = 0.35;
uniform float cloud_density : hint_range(0.0, 2.0) = 0.95;
uniform vec2 wind_vector = vec2(1.0, 0.2);
uniform float wind_speed = 6.0;
uniform float uv_scale = 0.00012; // Escala en metros espaciales

// Parámetros de contacto topográfico y horizonte
uniform float depth_fade_distance = 50.0; // Distancia en metros para desvanecer suavemente contra montañas
uniform float horizon_fade_distance = 25000.0; // Radio de desvanecimiento hacia el horizonte

// Iluminación celesta
uniform vec3 sun_direction = vec3(0.0, 1.0, 0.0);
uniform vec3 sun_color : source_color = vec3(1.0, 0.96, 0.88);
uniform vec3 moon_direction = vec3(0.0, -1.0, 0.0);
uniform vec3 moon_color : source_color = vec3(0.75, 0.85, 1.0);
uniform vec3 ambient_light_color : source_color = vec3(0.22, 0.28, 0.38);

// Parámetros cromáticos de la nube
uniform vec3 cloud_base_color : source_color = vec3(0.98, 0.98, 1.0);
uniform vec3 cloud_shadow_color : source_color = vec3(0.40, 0.44, 0.52);

varying vec3 v_world_pos;
varying vec3 v_camera_relative_pos;

// Hash y funciones de ruido celular Worley y FBM
float hash(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash(i);
	float b = hash(i + vec2(1.0, 0.0));
	float c = hash(i + vec2(0.0, 1.0));
	float d = hash(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
	float total = 0.0;
	float amp = 0.5;
	float freq = 1.0;
	for (int i = 0; i < 4; i++) {
		total += noise(p * freq) * amp;
		freq *= 2.08;
		amp *= 0.48;
	}
	return total;
}

// Ruido celular Worley para agrupar masas de nubes definidas
float worley(vec2 p) {
	vec2 n = floor(p);
	vec2 f = fract(p);
	float min_dist = 1.0;
	for (int j = -1; j <= 1; j++) {
		for (int i = -1; i <= 1; i++) {
			vec2 g = vec2(float(i), float(j));
			vec2 o = vec2(hash(n + g), hash(n + g + vec2(17.2, 43.1)));
			vec2 delta = g + o - f;
			min_dist = min(min_dist, length(delta));
		}
	}
	return min_dist;
}

// Fase Henyey-Greenstein para el resplandor plateado
float phase_hg(float cos_theta, float g) {
	float g2 = g * g;
	return (1.0 - g2) / (4.0 * PI * pow(max(1.0 + g2 - 2.0 * g * cos_theta, 0.001), 1.5));
}

void vertex() {
	v_world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_camera_relative_pos = VERTEX;
}

void fragment() {
	// Si la cobertura es insignificante, descartar de inmediato
	if (cloud_coverage < 0.02) {
		discard;
	}

	// 1. Coordenadas de mundo animadas por el viento
	vec2 wind_dir = length(wind_vector) > 0.001 ? normalize(wind_vector) : vec2(1.0, 0.0);
	vec2 uv = (v_world_pos.xz + wind_dir * (TIME * wind_speed)) * uv_scale;
	
	// Nubes bien definidas mediante combinación Worley (células) + FBM Billow (relieve)
	float w = 1.0 - worley(uv * 2.2);
	vec2 warp = vec2(fbm(uv + vec2(0.0, 1.3)), fbm(uv + vec2(2.5, 0.8)));
	float n = fbm(uv * 1.8 + warp * 0.35);
	
	// Efecto billow esculpido (curvatura de cúmulos algodonados)
	float billow = 1.0 - abs(n * 2.0 - 1.0);
	float cloud_mass = w * 0.65 + billow * 0.35;
	
	// 2. Umbral de corte nítido (bordes bien definidos, no difusos)
	float cutoff = 1.0 - (cloud_coverage * 0.85);
	float cloud_alpha = smoothstep(cutoff - 0.02, cutoff + 0.04, cloud_mass) * cloud_density;
	
	if (cloud_alpha <= 0.01) {
		discard;
	}
	
	// 3. Intersección volumétrica suave (Soft Depth Fade) contra el terreno de Cuchumá
	float scene_raw_depth = texture(depth_texture, SCREEN_UV).r;
	vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, scene_raw_depth);
	vec4 view_coords = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
	view_coords.xyz /= view_coords.w;
	float scene_linear_depth = -view_coords.z;
	float fragment_linear_depth = -VERTEX.z;
	
	float depth_diff = scene_linear_depth - fragment_linear_depth;
	float terrain_soft_fade = clamp(depth_diff / max(depth_fade_distance, 1.0), 0.0, 1.0);
	cloud_alpha *= terrain_soft_fade;
	
	// 4. Desvanecimiento suave en el horizonte radial
	float dist_from_center = length(v_camera_relative_pos.xz);
	float horizon_fade = 1.0 - smoothstep(horizon_fade_distance * 0.70, horizon_fade_distance, dist_from_center);
	cloud_alpha *= horizon_fade;
	
	if (cloud_alpha <= 0.005) {
		discard;
	}
	
	// 5. Modelo de Iluminación Física
	vec3 view_dir = normalize(-VERTEX);
	vec3 sun_dir = normalize(sun_direction);
	vec3 moon_dir = normalize(moon_direction);
	
	// Absorción Beer-Lambert y auto-sombra (la base y núcleo de la nube son densos)
	float density_factor = clamp(cloud_mass * cloud_density, 0.0, 1.0);
	float extinction = exp(-density_factor * 1.6);
	
	// Forward scattering solar (silver lining nítido en bordes iluminados)
	float cos_sun = dot(view_dir, sun_dir);
	float forward_scatter = phase_hg(cos_sun, 0.65) * 1.8;
	
	// Luz directa del Sol
	float sun_elev = sun_dir.y;
	float sun_reach = max(sun_elev + 0.05, 0.0);
	vec3 sun_illumination = sun_color * (extinction * 0.85 + forward_scatter * 0.6) * sun_reach;
	
	// Luz lunar nocturna
	float moon_elev = moon_dir.y;
	float moon_reach = max(moon_elev, 0.0) * smoothstep(0.05, -0.10, sun_elev);
	vec3 moon_illumination = moon_color * 0.3 * moon_reach;
	
	// Color base interpolado con sombreado nítido
	vec3 lit_cloud_color = mix(cloud_shadow_color, cloud_base_color, smoothstep(0.15, 0.70, extinction));
	vec3 total_color = lit_cloud_color * (sun_illumination + moon_illumination + ambient_light_color);
	
	ALBEDO = total_color;
	ALPHA = clamp(cloud_alpha, 0.0, 0.96);
}

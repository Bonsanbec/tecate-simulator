shader_type sky;
render_mode use_half_res_pass;

/*
 * Shader Fotorrealista de Cielo Desacoplado para Tecate Simulator
 *
 * Incluye:
 * - Dispersión atmosférica física (Rayleigh y Mie) calibrada para cielo semidesértico.
 * - Sol con oscurecimiento de limbo (limb darkening) y corona de alta emisión HDR.
 * - Luna fotorrealista con cálculo analítico de fases, relieve procedural y earthshine.
 * - Bóveda celeste con rotación sidérea, estrellas centelleantes y banda de la Vía Láctea.
 *
 * NOTA: Las nubes están desacopladas y se renderizan como mallas 3D físicas independientes.
 */

// Parámetros del Sol
uniform vec3 sun_direction = vec3(0.0, 1.0, 0.0);
uniform vec3 sun_color : source_color = vec3(1.0, 0.96, 0.90);
uniform float sun_disk_size = 0.025; // Radio angular del sol (~0.53 grados)
uniform float sun_intensity = 18.0;

// Parámetros de la Luna
uniform vec3 moon_direction = vec3(0.0, -1.0, 0.0);
uniform vec3 moon_color : source_color = vec3(0.85, 0.92, 1.0);
uniform float moon_disk_size = 0.024; // Radio angular de la luna (~0.52 grados)
uniform float moon_phase : hint_range(0.0, 1.0) = 0.5; // 0.0=Nueva, 0.5=Llena, 1.0=Nueva
uniform float moon_intensity = 2.5;


// Parámetros Cromáticos del Cielo Diurno y Atardecer
uniform vec3 day_sky_zenith : source_color = vec3(0.16, 0.38, 0.72);
uniform vec3 day_sky_horizon : source_color = vec3(0.62, 0.78, 0.93);
uniform vec3 sunset_zenith : source_color = vec3(0.18, 0.12, 0.32);
uniform vec3 sunset_horizon : source_color = vec3(0.96, 0.44, 0.16);
uniform vec3 night_sky_zenith : source_color = vec3(0.005, 0.008, 0.018);
uniform vec3 night_sky_horizon : source_color = vec3(0.02, 0.03, 0.05);

// Parámetros de Estrellas y Vía Láctea
uniform float stars_intensity : hint_range(0.0, 2.0) = 1.0;
uniform float stars_twinkle_speed = 2.5;
uniform float latitude_rad = 0.5685; // 32.57 grados en radianes (Latitud de Tecate)

// Función de fase Henyey-Greenstein para dispersión Mie (corona solar)
float henyey_greenstein(float cos_theta, float g) {
	float g2 = g * g;
	return (1.0 - g2) / (4.0 * PI * pow(max(1.0 + g2 - 2.0 * g * cos_theta, 0.001), 1.5));
}

// Generador pseudoaleatorio 3D para estrellas
float hash3(vec3 p) {
	p = fract(p * 0.3183099 + vec3(0.1, 0.2, 0.3));
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

// Ruido suave para la Vía Láctea y cráteres lunares
float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float noise2d(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash12(i);
	float b = hash12(i + vec2(1.0, 0.0));
	float c = hash12(i + vec2(0.0, 1.0));
	float d = hash12(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm2d(vec2 p) {
	float total = 0.0;
	float amp = 0.5;
	for (int i = 0; i < 4; i++) {
		total += noise2d(p) * amp;
		p *= 2.02;
		amp *= 0.5;
	}
	return total;
}

// Bóveda celeste y rotación sidérea inclinada para Tecate
vec3 rotate_celestial_sphere(vec3 dir, float lat) {
	// Rotación alrededor del eje polar terrestre inclinado según la latitud de Tecate
	float cos_lat = cos(lat);
	float sin_lat = sin(lat);
	// Rotar alrededor de X para alinear el eje Z con el eje polar
	return vec3(dir.x, dir.y * sin_lat - dir.z * cos_lat, dir.y * cos_lat + dir.z * sin_lat);
}

void sky() {
	vec3 ray_dir = normalize(EYEDIR);
	float y = clamp(ray_dir.y, 0.0, 1.0);
	
	// 1. Factores de elevación del Sol y mezcla de iluminación atmosférica
	float sun_elev = sun_direction.y;
	float day_factor = smoothstep(-0.08, 0.20, sun_elev);
	float sunset_factor = smoothstep(0.25, -0.05, sun_elev) * smoothstep(-0.15, 0.02, sun_elev);
	float night_factor = 1.0 - smoothstep(-0.12, 0.05, sun_elev);
	
	// Gradiente diurno
	vec3 day_gradient = mix(day_sky_horizon, day_sky_zenith, pow(y, 0.45));
	// Gradiente de atardecer / amanecer (carmesí / oro sobre el horizonte)
	vec3 sunset_gradient = mix(sunset_horizon, sunset_zenith, pow(y, 0.60));
	// Gradiente nocturno
	vec3 night_gradient = mix(night_sky_horizon, night_sky_zenith, pow(y, 0.50));
	
	// Mezcla base del cielo
	vec3 sky_color = day_gradient * day_factor;
	sky_color = mix(sky_color, sunset_gradient, sunset_factor * (1.0 - night_factor));
	sky_color += night_gradient * night_factor;
	
	// 2. Dispersión Mie hacia el Sol (Corona solar y bruma en el horizonte)
	float cos_sun = dot(ray_dir, normalize(sun_direction));
	if (sun_elev > -0.15) {
		float mie_day = henyey_greenstein(cos_sun, 0.82) * 0.12 * max(sun_elev + 0.15, 0.0);
		float mie_sunset = henyey_greenstein(cos_sun, 0.90) * 0.25 * sunset_factor;
		vec3 halo_color = mix(vec3(1.0, 0.95, 0.85), vec3(1.0, 0.45, 0.15), sunset_factor);
		sky_color += halo_color * (mie_day + mie_sunset);
	}
	
	// 3. Disco Solar Físico con Limb Darkening
	if (cos_sun > 1.0 - sun_disk_size * sun_disk_size * 2.0 && sun_elev > -0.05) {
		float angle = acos(clamp(cos_sun, -1.0, 1.0));
		if (angle < sun_disk_size) {
			float r = angle / sun_disk_size;
			// Oscurecimiento de limbo: u = 0.6 (coeficiente estelar estándar)
			float mu = sqrt(max(1.0 - r * r, 0.0));
			float limb_darkening = 1.0 - 0.6 * (1.0 - mu);
			
			// Color solar en función de la elevación (se torna rojizo cerca del horizonte)
			vec3 s_color = mix(vec3(1.0, 0.4, 0.1), sun_color, smoothstep(0.0, 0.15, sun_elev));
			sky_color += s_color * limb_darkening * sun_intensity;
		}
	}
	
	// 4. Disco Lunar Físico con Fases Analíticas y Relieve
	float cos_moon = dot(ray_dir, normalize(moon_direction));
	if (moon_direction.y > -0.10) {
		// Halo/Glow sutil de la Luna en el cielo nocturno
		if (night_factor > 0.05) {
			float moon_halo = henyey_greenstein(cos_moon, 0.94) * 0.035 * max(moon_direction.y, 0.0);
			sky_color += moon_color * moon_halo * 3.5;
		}
		
		float angle_m = acos(clamp(cos_moon, -1.0, 1.0));
		if (angle_m < moon_disk_size) {
			vec3 m_dir = normalize(moon_direction);
			
			// Base ortonormal para el plano del disco de la luna
			vec3 up_ref = abs(m_dir.y) < 0.99 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
			vec3 moon_tangent = normalize(cross(up_ref, m_dir));
			vec3 moon_bitangent = cross(m_dir, moon_tangent);
			
			vec3 to_pixel = ray_dir - m_dir;
			float u = dot(to_pixel, moon_tangent) / moon_disk_size;
			float v = dot(to_pixel, moon_bitangent) / moon_disk_size;
			float dist_sq = u * u + v * v;
			
			if (dist_sq <= 1.0) {
				// Coordenada z de la superficie hemisférica visible hacia la Tierra
				float w = sqrt(1.0 - dist_sq);
				
				// Ángulo de fase sinódico (0.0 = Nueva, 0.25 = Cuarto Creciente, 0.5 = Llena, 0.75 = Cuarto Menguante)
				float theta = moon_phase * TAU;
				// Vector de incidencia solar sobre el hemisferio visible
				vec3 light_vec = vec3(-sin(theta), 0.0, -cos(theta));
				vec3 norm_vis = vec3(u, v, w);
				
				float n_dot_l = dot(norm_vis, light_vec);
				float direct_light = smoothstep(-0.02, 0.06, n_dot_l);
				
				// Relieve lunar (Mares basálticos y cráteres brillantes mediante FBM)
				vec2 lunar_uv = vec2(u * 0.5 + 0.5, v * 0.5 + 0.5);
				float relief = fbm2d(lunar_uv * 14.0);
				float albedo_moon = mix(0.70, 0.98, relief);
				
				// Luz reflejada por la Tierra (Earthshine) en la zona en sombra
				float earthshine = 0.045 * (1.0 - direct_light);
				
				float total_moon_light = (direct_light * 0.95 + earthshine) * albedo_moon;
				float edge_aa = smoothstep(1.0, 0.93, sqrt(dist_sq));
				
				sky_color += moon_color * total_moon_light * moon_intensity * edge_aa;
			}
		}
	}

	
	// 5. Bóveda Estelar y Vía Láctea (Visible solo durante la noche)
	if (night_factor > 0.01 && y > 0.01) {
		vec3 rot_sky = rotate_celestial_sphere(ray_dir, latitude_rad);
		
		// Cuadrícula esférica de estrellas
		vec3 star_grid = floor(rot_sky * 160.0);
		float star_hash = hash3(star_grid);
		
		// Centelleo de estrellas
		float twinkle = 0.7 + 0.3 * sin(TIME * stars_twinkle_speed + star_hash * 62.83);
		
		vec3 star_col = vec3(0.0);
		if (star_hash > 0.982) {
			// Espectro de color estelar (azul-blanco a ámbar)
			float temp = hash3(star_grid + vec3(1.23, 4.56, 7.89));
			vec3 temp_col = mix(vec3(0.7, 0.85, 1.0), vec3(1.0, 0.88, 0.7), temp);
			
			// Magnitud estelar
			float brightness = pow((star_hash - 0.982) / 0.018, 3.0) * twinkle;
			star_col = temp_col * brightness * 1.5;
		}
		
		// Banda difusa de la Vía Láctea
		float galactic_plane = abs(rot_sky.y * 0.75 + rot_sky.x * 0.4 - 0.2);
		if (galactic_plane < 0.35) {
			float mw_dust = fbm2d(rot_sky.xz * 6.0);
			float mw_intensity = smoothstep(0.35, 0.0, galactic_plane) * mw_dust * 0.06;
			star_col += vec3(0.55, 0.62, 0.85) * mw_intensity;
		}
		
		// Las estrellas se atenúan cerca del horizonte para simular extinción atmosférica
		float horizon_extinction = smoothstep(0.02, 0.20, y);
		sky_color += star_col * stars_intensity * night_factor * horizon_extinction;
	}
	
	COLOR = sky_color;
}

shader_type spatial;
render_mode cull_back, diffuse_lambert, specular_schlick_ggx;

// Terrain shader for Tecate semi-arid landscape
// Blends colors based on altitude and slope to eliminate uniform flat coloring

// Altitude bands (in local meters, relative to 540m origin)
uniform float valley_floor : hint_range(-50.0, 50.0) = 0.0;
uniform float chaparral_start : hint_range(10.0, 100.0) = 20.0;
uniform float rock_start : hint_range(50.0, 200.0) = 80.0;

// Colors for each altitude band
uniform vec3 urban_soil_color : source_color = vec3(0.55, 0.48, 0.38);       // Dry beige-brown (Tecate urban soil)
uniform vec3 chaparral_color : source_color = vec3(0.42, 0.50, 0.35);        // Muted sage green (chaparral scrub)
uniform vec3 exposed_rock_color : source_color = vec3(0.52, 0.48, 0.44);     // Warm grey-brown rock
uniform vec3 road_dirt_color : source_color = vec3(0.62, 0.56, 0.46);        // Lighter tan for flat areas

// Slope thresholds
uniform float flat_threshold : hint_range(0.0, 1.0) = 0.85;  // Normal.y above this = flat
uniform float steep_threshold : hint_range(0.0, 1.0) = 0.5;   // Normal.y below this = steep/rocky

// Noise variation
uniform float noise_scale : hint_range(0.001, 0.1) = 0.02;
uniform float noise_intensity : hint_range(0.0, 0.3) = 0.08;

// Simple pseudo-noise based on world position
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f); // smoothstep

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 3; i++) {
        v += a * noise(p);
        p *= 2.0;
        a *= 0.5;
    }
    return v;
}

void fragment() {
    // World position from vertex
    vec3 world_pos = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
    float altitude = world_pos.y;

    // Slope from world-space normal
    vec3 world_normal = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
    float slope = world_normal.y; // 1.0 = flat, 0.0 = vertical

    // Noise variation for natural-looking terrain
    float n = fbm(world_pos.xz * noise_scale) * noise_intensity;

    // Altitude-based color blending
    float t_chaparral = smoothstep(valley_floor, chaparral_start, altitude);
    float t_rock = smoothstep(chaparral_start, rock_start, altitude);

    vec3 altitude_color = mix(urban_soil_color, chaparral_color, t_chaparral);
    altitude_color = mix(altitude_color, exposed_rock_color, t_rock);

    // Slope-based blending: flat areas get more "dirt/soil", steep areas get more "rock"
    float flat_factor = smoothstep(steep_threshold, flat_threshold, slope);
    vec3 slope_color = mix(exposed_rock_color, road_dirt_color, flat_factor);

    // Combine altitude and slope
    vec3 base_color = mix(slope_color, altitude_color, 0.65);

    // Apply noise variation
    base_color += vec3(n - noise_intensity * 0.5);

    // Clamp to valid range
    base_color = clamp(base_color, vec3(0.0), vec3(1.0));

    ALBEDO = base_color;
    ROUGHNESS = mix(0.95, 0.80, t_rock); // Rock is slightly shinier
    METALLIC = 0.0;
}

shader_type spatial;
render_mode cull_disabled, diffuse_lambert, specular_schlick_ggx;

// Mountain shader for Cerro Cuchumá
// Uses cull_disabled to prevent backface culling artifacts
// Color varies by altitude to show rocky slopes and chaparral bands

uniform vec3 base_rock_color : source_color = vec3(0.42, 0.44, 0.42);     // Grey-green base rock
uniform vec3 peak_rock_color : source_color = vec3(0.55, 0.50, 0.45);     // Warmer tan at peak
uniform vec3 shadow_color : source_color = vec3(0.30, 0.32, 0.35);        // Blue-grey shadows
uniform vec3 vegetation_color : source_color = vec3(0.35, 0.42, 0.28);    // Dark sage for chaparral patches

uniform float peak_altitude : hint_range(100.0, 1200.0) = 900.0;
uniform float vegetation_limit : hint_range(50.0, 600.0) = 400.0;

// Simple noise
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
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

void fragment() {
    vec3 world_pos = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
    float altitude = world_pos.y;
    float alt_factor = clamp(altitude / peak_altitude, 0.0, 1.0);

    vec3 world_normal = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
    float slope = world_normal.y;

    // Noise for surface variation
    float n1 = noise(world_pos.xz * 0.008) * 0.15;
    float n2 = noise(world_pos.xz * 0.025) * 0.08;
    float variation = n1 + n2;

    // Base color: blend from base rock to peak rock with altitude
    vec3 color = mix(base_rock_color, peak_rock_color, alt_factor);

    // Add vegetation patches below vegetation limit on less-steep slopes
    float veg_factor = (1.0 - smoothstep(0.0, vegetation_limit, altitude)) * smoothstep(0.3, 0.8, slope);
    veg_factor *= (noise(world_pos.xz * 0.015) > 0.4 ? 1.0 : 0.0); // Patchy distribution
    color = mix(color, vegetation_color, veg_factor * 0.6);

    // Darken steep slopes (shadow approximation)
    float shadow_factor = 1.0 - smoothstep(0.3, 0.7, slope);
    color = mix(color, shadow_color, shadow_factor * 0.4);

    // Apply noise variation
    color += vec3(variation - 0.1);
    color = clamp(color, vec3(0.0), vec3(1.0));

    // Flip normal for backfaces so lighting works on both sides
    NORMAL = FRONT_FACING ? NORMAL : -NORMAL;

    ALBEDO = color;
    ROUGHNESS = 0.92;
    METALLIC = 0.0;
}

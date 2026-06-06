shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D texture_albedo_roughness : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D texture_normal_height : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;

uniform float depth_scale : hint_range(0.0, 0.5) = 0.08;
uniform float min_layers : hint_range(1.0, 64.0) = 8.0;
uniform float max_layers : hint_range(1.0, 128.0) = 32.0;
uniform float lod_fade_start : hint_range(0.0, 200.0) = 25.0;
uniform float lod_fade_distance : hint_range(1.0, 100.0) = 15.0;

void fragment() {
    // 1. Calculate tangent space view vector V
    // VIEW in Godot 4 spatial shaders is the vector from vertex to camera in view space.
    // Multiplying on the right by the TBN matrix transforms it from view to tangent space.
    mat3 tbn = mat3(TANGENT, BINORMAL, NORMAL);
    vec3 V = normalize(VIEW * tbn);
    
    // 2. Calculate LOD fade based on distance to camera (length of VERTEX in view space)
    float dist = length(VERTEX);
    float pom_fade = clamp((lod_fade_start + lod_fade_distance - dist) / lod_fade_distance, 0.0, 1.0);
    
    vec2 uv = UV;
    
    if (pom_fade > 0.01) {
        // 3. Parallax Occlusion Mapping (POM) Ray Marching
        // Oblique view angles require more steps for precision
        float num_layers = mix(max_layers, min_layers, abs(V.z));
        float layer_depth = 1.0 / num_layers;
        float current_layer_depth = 0.0;
        
        // Parallax offset in tangent space (tangent X, Y divided by Z to project along view vector)
        float v_z = max(V.z, 0.001);
        vec2 p = V.xy * (depth_scale * pom_fade) / v_z;
        vec2 delta_uv = p / num_layers;
        
        vec2 current_uv = UV;
        // height = texture(texture_normal_height, uv).a.
        // depth = 1.0 - height (0 is wall surface, 1 is deepest recess).
        float current_depth_value = 1.0 - texture(texture_normal_height, current_uv).a;
        
        // March until ray is beneath height map surface
        while (current_layer_depth < current_depth_value) {
            current_uv -= delta_uv;
            current_depth_value = 1.0 - texture(texture_normal_height, current_uv).a;
            current_layer_depth += layer_depth;
        }
        
        // 4. Intersection refinement (POM linear interpolation between steps)
        vec2 prev_uv = current_uv + delta_uv;
        float next_depth = current_depth_value - current_layer_depth;
        float prev_depth = (1.0 - texture(texture_normal_height, prev_uv).a) - (current_layer_depth - layer_depth);
        
        float weight = next_depth / (next_depth - prev_depth);
        uv = mix(current_uv, prev_uv, weight);
    }
    
    // 5. Sample final PBR textures at displaced UV
    vec4 albedo_rough = texture(texture_albedo_roughness, uv);
    vec4 norm_height = texture(texture_normal_height, uv);
    
    ALBEDO = albedo_rough.rgb;
    ROUGHNESS = albedo_rough.a;
    
    // Heuristic: Set metallic properties based on height value in normal_height texture
    // Wall height = 255 (1.0), Door height = 230 (0.9), Window height = 216 (0.85)
    float height_val = norm_height.a;
    METALLIC = 0.0;
    if (height_val < 0.88 && height_val > 0.82) {
        METALLIC = 0.2; // Window reflectivity
    }
    
    // Unpack normal map from RGB channels
    vec3 normal_map = norm_height.rgb * 2.0 - 1.0;
    NORMAL_MAP = normal_map;
    NORMAL_MAP_DEPTH = 1.0;
}

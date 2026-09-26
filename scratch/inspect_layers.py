import bpy
from mathutils import Vector

kiosko = Vector((-6.6844, 2.6878)) # Godot X, Z

for glb_name in ['manzanas_baked.glb', 'roadways_baked.glb', 'tecate2.glb']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=f'godot_project/assets/{glb_name}')
    except Exception as e:
        print(f"Could not load {glb_name}: {e}")
        continue
    
    print(f"\n=================== {glb_name} ===================")
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            mesh = obj.data
            # In glTF imported to Blender: Godot X is Blender X, Godot Z is Blender -Y, Godot Y is Blender Z
            # So Godot (-6.68, 2.68) is Blender (-6.68, -2.68)
            near_faces = []
            for p in mesh.polygons:
                center = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
                if (center.x - (-6.6844))**2 + (center.y - (-2.6878))**2 < 90**2:
                    near_faces.append(p)
            print(f"Object '{obj.name}' has {len(near_faces)} faces near park.")
            if near_faces:
                # Group by material
                mat_faces = {}
                for p in near_faces:
                    m_name = mesh.materials[p.material_index].name if p.material_index < len(mesh.materials) else "None"
                    mat_faces.setdefault(m_name, []).append(p)
                for m_name, f_list in mat_faces.items():
                    # Calculate bounding box of this material's faces
                    f_verts = set()
                    for p in f_list:
                        for vi in p.vertices:
                            f_verts.add(vi)
                    v_cos = [mesh.vertices[vi].co for vi in f_verts]
                    min_x = min(v.x for v in v_cos)
                    max_x = max(v.x for v in v_cos)
                    min_y = min(v.y for v in v_cos)
                    max_y = max(v.y for v in v_cos)
                    min_z = min(v.z for v in v_cos)
                    max_z = max(v.z for v in v_cos)
                    total_area = sum(p.area for p in f_list)
                    print(f"  Material '{m_name}': {len(f_list)} faces, {len(v_cos)} verts, total area={total_area:.1f} m²")
                    print(f"    X: [{min_x:.1f}, {max_x:.1f}], Y: [{min_y:.1f}, {max_y:.1f}], Z(elev): [{min_z:.2f}, {max_z:.2f}]")

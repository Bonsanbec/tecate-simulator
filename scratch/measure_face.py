import bpy
img = bpy.data.images.load("scratch/humans/axel2_face_crop.png")
w, h = img.size[0], img.size[1]
print(f"Dimensiones de axel2_face_crop.png: {w}x{h}")

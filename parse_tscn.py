import re

with open("godot_project/main.tscn") as f:
    content = f.read()

for match in re.finditer(r'\[node name="(.*?)"[\s\S]*?transform = Transform3D\((.*?)\)', content):
    name = match.group(1)
    transform = match.group(2)
    print(f"{name}: {transform}")

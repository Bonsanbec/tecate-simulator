@tool
extends SceneTree

func _init():
    var scene = load("res://assets/buildings/edificio_cardenas_25.tscn")
    if not scene:
        print("ERROR: No se pudo cargar edificio_cardenas_25.tscn")
        quit(1)
        return
    var inst = scene.instantiate()
    print("Escena cargada:", inst.name)
    for child in inst.get_children():
        print("Nodo:", child.name, " tipo:", child.get_class())
        if child is CollisionShape3D:
            print("  Col shape:", child.shape.get_class(), " size:", child.shape.size if "size" in child.shape else "N/A", " pos:", child.position)
        elif child.name == "ModelInstance":
            print("  ModelInstance hijos:")
            for sub in child.get_children():
                print("    Sub:", sub.name, " tipo:", sub.get_class(), " pos:", sub.position if "position" in sub else "N/A", " rot:", sub.rotation_degrees if "rotation_degrees" in sub else "N/A")
                for sub2 in sub.get_children():
                    print("      Sub2:", sub2.name, " tipo:", sub2.get_class(), " pos:", sub2.position if "position" in sub2 else "N/A", " rot:", sub2.rotation_degrees if "rotation_degrees" in sub2 else "N/A")
    quit(0)

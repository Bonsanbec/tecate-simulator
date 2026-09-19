extends SceneTree

def _init():
    var t = Transform3D()
    t = t.rotated(Vector3(0, 1, 0), PI/2)
    print("Rotated 90 deg around Y: ", t)
    
    var t2 = Transform3D(Vector3(0,0,-1), Vector3(0,1,0), Vector3(1,0,0), Vector3.ZERO)
    print("Constructed from vectors: ", t2)
    quit()

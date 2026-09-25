
@tool
extends SceneTree
func _init():
    var t = Transform3D(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
    print('basis.x (row 0?): ', t.basis.x)
    print('basis.y (row 1?): ', t.basis.y)
    print('basis.z (row 2?): ', t.basis.z)
    print('t.origin: ', t.origin)
    var rot = Transform3D(Basis(Vector3.UP, deg_to_rad(45)), Vector3.ZERO)
    print('45 deg Y rot Transform3D: ', rot)
    quit()

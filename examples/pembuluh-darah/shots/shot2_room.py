"""
Beat 2 (4.5-7.5 s, 90 frames): "mungkin kamu kira cuma cukup untuk satu ruangan."

Whip-in from beat 1's tilt, landing low between the man's heels. The red line runs ahead
into an open cut-away room on the blue: 5 m x 3.5 m, tape measures along both side walls.
Low tracking shot along the line to near the far wall, where the line stops at the 5 m mark.
Last 18 frames creep toward the cut end (hand-off: beat 3 flies into it).

  blender -b --python shots/shot2_room.py -- --check
"""
import os, sys, math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common
from common import zdf, bpy, Vector

a = common.args()
zdf.new_scene(seconds=3.0, samples=64, preview=a.preview)
man = common.man_shoes()
room = common.build_room(with_line=True)
cam = zdf.camera(loc=(0, 0.6, 0.16), target=(common.LINE_X, common.ROOM_Y1, 0.2), lens=20)
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 5.6
focus = bpy.data.objects.new("Focus", None)
bpy.context.scene.collection.objects.link(focus)
cam.data.dof.focus_object = focus
zdf.blue_backdrop()
g = zdf.ground("catcher")
g.location.z = -0.003            # below the room floor top (z=0): avoids z-fighting
common.room_lights()

X, Y1 = common.LINE_X, common.ROOM_Y1
far_target = Vector((X, Y1, 0.35))
# f1-9: whip-in (lands between his heels), f9-72: track along the line, f72-90: creep to the cut end
corner = Vector((X + 0.7, Y1, 0.7))     # between the line end and the right wall's 5 m mark
common.key_cam(cam, 9, (0.0, 0.6, 0.16), far_target)
common.key_cam(cam, 40, (X - 0.55, -1.3, 0.32), corner)
common.key_cam(cam, 72, (X - 1.0, -3.0, 0.55), corner)
common.key_cam(cam, 90, (X - 0.65, -3.65, 0.36), common.LINE_END + Vector((0.15, 0, 0.12)))
zdf.ease_all(cam)
# whip: start rotated 50 deg in yaw, motion blur smears it
r = cam.rotation_euler.copy()
cam.rotation_euler = (r.x + math.radians(10), r.y, r.z + math.radians(50))
cam.keyframe_insert("rotation_euler", frame=1)
common.fix_euler_flips(cam)
for f, loc in ((1, (0, -0.3, 0.05)), (40, (X, -4.0, 0.3)), (72, (X + 0.6, Y1 + 0.3, 0.5)), (90, tuple(common.LINE_END))):
    focus.location = loc
    focus.keyframe_insert("location", frame=f)

xl, xr = X - common.ROOM_W / 2, X + common.ROOM_W / 2
common.finish(a, "beat2", [
    (9, [("left shoe", zdf.bone_world(man, "LeftToeBase")), ("right shoe", zdf.bone_world(man, "RightToeBase")),
         ("room front", (X, common.ROOM_Y0, 0.0)), ("line end", common.LINE_END)]),
    (72, [("line end", common.LINE_END), ("5m tape L", (xl, Y1 + 0.05, 1.0)), ("5m tape R", (xr, Y1 + 0.05, 1.0)),
          ("room front L", (xl, common.ROOM_Y0 + 1.0, 0.0))]),
    (90, [("line end", common.LINE_END), ("5m tape R", (xr, Y1 + 0.05, 1.0))]),
])

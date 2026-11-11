"""
Beat 4 (14-19 s, 150 frames): "Ilmuwan memperkirakan, kalau digabung, panjangnya sekitar 100.000 kilometer."

Back in the tape-lined room (pulling back from beat 3). At f24 the line punches through the
far wall: the plaster plug blows out in chunks and the line races off across the blue to the
horizon. The camera rises to top-down (the room shrinks below), keeps rising and passes
through a cloud deck (z 30-42), ending in white: that hides the join into beat 5.
The line's thickness grows with altitude so it stays readable (scale cheat).

  blender -b --python shots/shot4_stretch.py -- --check
"""
import os, sys, math, random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common
from common import zdf, bpy, Vector

a = common.args()
zdf.new_scene(seconds=5.0, samples=64, preview=a.preview)
sc = bpy.context.scene
sc.cycles.volume_step_rate = 4.0      # clouds: coarse steps are fine at this distance
sc.cycles.volume_max_steps = 96
man = common.man_shoes()
room = common.build_room(with_line=True)
zdf.blue_backdrop()
g = zdf.ground("catcher")
g.scale = (40, 40, 1)                  # catcher must cover the top-down view at altitude
g.location.z = -0.003                  # below the room floor top (z=0): avoids z-fighting
common.room_lights()
X, Y1 = common.LINE_X, common.ROOM_Y1

# --- line extension through the wall to the horizon ----------------------------
FL = common.FLOOR
ext = zdf.tube_curve([tuple(common.LINE_END), (X, Y1 - 0.4, FL), (X, Y1 - 30, FL), (X, -2500, FL)],
                     radius=common.LINE_RADIUS, mat=bpy.data.materials["LineMat"], name="LineExt")
ext.data.bevel_factor_mapping_end = "SPLINE"
ext.data.bevel_factor_end = 0
ext.data.keyframe_insert("bevel_factor_end", frame=23)
for f, v in ((26, 0.0003), (34, 0.012), (60, 1.0)):   # bursts through, then races off
    ext.data.bevel_factor_end = v
    ext.data.keyframe_insert("bevel_factor_end", frame=f)
for c in (ext.data, room["line"].data):            # thicken with altitude (scale cheat)
    for f, r in ((60, common.LINE_RADIUS), (100, 0.09), (150, 0.45)):
        c.bevel_depth = r
        c.keyframe_insert("bevel_depth", frame=f)
    zdf.ease_all(c)

# --- the plaster plug blows out (simple ballistics, no simulation) ---------------
rnd = random.Random(4)
G = -9.81
plug = room["plug"]
plug.hide_render = False
plug.keyframe_insert("hide_render", frame=1)
plug.hide_render = True
plug.keyframe_insert("hide_render", frame=24)
for ch in room["chunks"]:
    ch.hide_render = True
    ch.keyframe_insert("hide_render", frame=1)
    ch.hide_render = False
    ch.keyframe_insert("hide_render", frame=24)
    p0 = ch.location.copy()
    v = Vector((rnd.uniform(-1.6, 1.6), -rnd.uniform(2.5, 6.0), rnd.uniform(0.8, 3.2)))
    w = Vector((rnd.uniform(-12, 12) for _ in range(3)))
    ch.keyframe_insert("location", frame=24)
    ch.keyframe_insert("rotation_euler", frame=24)
    for f in range(26, 72, 2):
        t = (f - 24) / 30
        z = p0.z + v.z * t + 0.5 * G * t * t
        if z < 0.03:
            z = 0.03
            v.x *= 0.5
            v.y *= 0.5
        ch.location = (p0.x + v.x * t, p0.y + v.y * t, z)
        ch.rotation_euler = w * min(t, 0.6)
        ch.keyframe_insert("location", frame=f)
        ch.keyframe_insert("rotation_euler", frame=f)

# --- cloud deck ---------------------------------------------------------------
bpy.ops.mesh.primitive_cube_add(size=1, location=(X, Y1, 36))
cl = bpy.context.active_object
cl.name = "CloudDeck"
cl.scale = (500, 500, 12)
bpy.ops.object.transform_apply(scale=True)
m = bpy.data.materials.new("Cloud")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
vol = nt.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Color"].default_value = (1, 1, 1, 1)
vol.inputs["Anisotropy"].default_value = 0.5
tc = nt.nodes.new("ShaderNodeTexCoord")
nz = nt.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 0.035
nz.inputs["Detail"].default_value = 5
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = 0.45
mr.inputs["From Max"].default_value = 0.68
mr.inputs["To Max"].default_value = 0.3
nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], vol.inputs["Density"])
nt.links.new(vol.outputs[0], out.inputs["Volume"])
vol.inputs["Emission Color"].default_value = (1, 1, 1, 1)
nt.links.new(mr.outputs["Result"], vol.inputs["Emission Strength"])   # self-lit: no grey undersides
cl.data.materials.append(m)
# clouds only exist once the camera starts its climb (from below they read as dark blobs)
cl.hide_render = True
cl.keyframe_insert("hide_render", frame=1)
cl.hide_render = False
cl.keyframe_insert("hide_render", frame=92)

# --- camera --------------------------------------------------------------------
cam = zdf.camera(loc=(X, Y1 + 0.65, 0.16), target=common.LINE_END, lens=20)
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 8
look = bpy.data.objects.new("Look", None)
sc.collection.objects.link(look)
cam.data.dof.focus_object = look
con = cam.constraints.new("TRACK_TO")
con.target = look
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"
wall_hole = Vector((X, Y1, 0.25))
for f, c, l in ((1, (X, Y1 + 0.65, 0.16), common.LINE_END),        # continuing the pull-back
                (20, (X - 0.9, -2.9, 0.6), wall_hole + Vector((0.45, 0, 0.3))),
                (40, (X - 0.6, -2.6, 0.95), wall_hole + Vector((0.2, -2, 0))),
                (70, (X, -4.0, 6.0), Vector((X, -10, 0))),
                (100, (X, -6.6, 22.0), Vector((X, -6.7, 0))),
                (150, (X, -6.6, 75.0), Vector((X, -6.7, 0)))):
    cam.location = c
    cam.keyframe_insert("location", frame=f)
    look.location = l
    look.keyframe_insert("location", frame=f)
zdf.ease_all(cam)
zdf.ease_all(look)

common.finish(a, "beat4", [
    (1, [("line end", common.LINE_END)]),
    (24, [("hole", wall_hole), ("5m tape R", (X + common.ROOM_W / 2, Y1 + 0.05, 1.0))]),
    (60, [("line far", (X, -40, 0))]),
    (100, [("room centre", (X, (common.ROOM_Y0 + Y1) / 2, 0)), ("man", (0, 0, 0)), ("line", (X, -25, 0))]),
])

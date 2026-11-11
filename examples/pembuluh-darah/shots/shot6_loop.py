"""
Beats 6 + 7 (26-32 s, 180 frames):
6 (f1-135):  "Dan setetes darah cuma butuh sekitar satu menit untuk satu putaran penuh."
7 (f136-180): no narration - the reaction.

Opens on the sky-blue card that beat 5 ends on, tilting/dropping down out of the sky onto the
man in his suit, waist-up (continuous hand-off from space: no door-swing).
X-ray to the vessels; a glowing drop leaves the heart, runs down the left arm to the hand and back,
down the left leg to the foot and back, and returns to the heart, which pulses as it goes.
The camera pulls back to full body to follow it, then pushes in again for beat 7:
the x-ray fades back to the suit, his head snaps down to look at his chest and his shoulders rise.

  blender -b --python shots/shot6_loop.py -- --check
"""
import os, sys, math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common
from common import zdf, bpy, Vector

a = common.args()
zdf.new_scene(seconds=6.0, samples=64, preview=a.preview)
B = common.build_body()
man, mus, vessels, heart = B["man"], B["mus"], B["vessels"], B["heart"]
zdf.blue_backdrop()
zdf.ground("catcher")
zdf.sun(energy=3.5, rot_deg=(48, 0, 32))
zdf.area_fill(energy=250)

# --- x-ray in (beat 6) and out (beat 7) -------------------------------------------
common.layer_alpha(man, [(14, 1), (30, 0), (136, 0), (152, 1)])
common.layer_alpha(mus, [(1, 0), (14, 0), (30, 0.12), (136, 0.12), (150, 0)])
common.layer_alpha(vessels, [(1, 0), (16, 0), (32, 1), (136, 1), (150, 0)])
common.layer_alpha(heart, [(1, 0), (16, 0), (32, 1), (136, 1), (150, 0)])

# heart pulses as the drop travels
base = heart.scale.copy()
for i, f0 in enumerate(range(34, 134, 20)):
    for df, s in ((0, 1.0), (4, 1.18), (9, 1.0)):
        heart.scale = base * s
        heart.keyframe_insert("scale", frame=f0 + df)

# --- the drop's route: heart -> hand -> heart side -> foot -> heart ---------------
bw = lambda n: zdf.bone_world(mus, n)
H = heart.location.copy()
back = Vector((0, -0.03, 0))           # return path runs a little in front (the veins)
route = [H, bw("Spine2") + Vector((0.05, -0.02, 0.06)), bw("LeftShoulder"), bw("LeftArm"), bw("LeftForeArm"),
         bw("LeftHand"), bw("LeftHandMiddle2"),
         bw("LeftHand") + back, bw("LeftForeArm") + back, bw("LeftArm") + back, bw("Spine1") + Vector((0.04, -0.05, 0)),
         bw("Hips") + Vector((0.06, -0.06, 0)), bw("LeftUpLeg"), bw("LeftLeg"), bw("LeftFoot"), bw("LeftToeBase"),
         bw("LeftFoot") + back, bw("LeftLeg") + back, bw("LeftUpLeg") + back, bw("Hips") + Vector((0.02, -0.08, 0)),
         bw("Spine1") + Vector((0.03, -0.07, 0)), H]
path = zdf.tube_curve([tuple(p) for p in route], radius=0.0, name="DropPath", smooth=True)
path.data.bevel_depth = 0
path.hide_render = True
path.data.use_path = True
path.data.path_duration = 100
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, location=(0, 0, 0), segments=24, ring_count=12)
drop = bpy.context.active_object
drop.name = "Drop"
bpy.ops.object.shade_smooth()
drop.data.materials.append(zdf.mat_principled("DropGlow", (1.0, 0.25, 0.25), rough=0.2,
                                              emit=(1.0, 0.18, 0.18), emit_strength=14))
fp = drop.constraints.new("FOLLOW_PATH")
fp.target = path
fp.use_fixed_location = True
for f, v in ((34, 0.0), (128, 1.0)):
    fp.offset_factor = v
    fp.keyframe_insert("offset_factor", frame=f)
drop.scale = (0.001,) * 3
drop.keyframe_insert("scale", frame=31)
for f, s in ((35, 1.0), (128, 1.0), (134, 0.001)):
    drop.scale = (s,) * 3
    drop.keyframe_insert("scale", frame=f)
for fc in zdf._fcurves(drop):
    if "offset_factor" in fc.data_path:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.easing = "EASE_IN_OUT"

# --- beat 7 acting: head snaps down, shoulders rise --------------------------------
for f in (150,):
    for n in ("Neck", "Head", "LeftShoulder", "RightShoulder"):
        zdf.key_bone(man, n, f)
zdf.rotate_bone_world(man, "Neck", (1, 0, 0), 10)
zdf.rotate_bone_world(man, "Head", (1, 0, 0), 24)
zdf.rotate_bone_world(man, "LeftShoulder", (0, 1, 0), -7)
zdf.rotate_bone_world(man, "RightShoulder", (0, 1, 0), 7)
for n in ("Neck", "Head", "LeftShoulder", "RightShoulder"):
    zdf.key_bone(man, n, 157)                  # the snap: 7 frames
zdf.rotate_bone_world(man, "Head", (1, 0, 0), -4)
zdf.key_bone(man, "Head", 168)                 # small settle
zdf.key_bone(man, "Head", 180)

# --- camera ----------------------------------------------------------------------
cam = zdf.camera(loc=(0, -1.55, 1.28), target=(0, 0, 1.22), lens=40)
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 3.5
focus = bpy.data.objects.new("Focus", None)
bpy.context.scene.collection.objects.link(focus)
focus.location = (0, -0.05, 1.1)
cam.data.dof.focus_object = focus
for f, c, t in ((1, (0, -1.7, 2.9), (0, 0, 3.6)),             # in the sky above him (blue card)
                (13, (0, -1.55, 1.28), (0, 0, 1.22)),         # drop + tilt down: lands waist-up
                (34, (0, -1.42, 1.30), (0, 0, 1.24)),         # creep in on the heart
                (60, (0, -2.6, 1.10), (0, 0, 1.0)),           # drop heads down the arm
                (90, (0, -3.3, 0.98), (0, 0, 0.9)),           # full body for the leg
                (135, (0, -3.15, 1.0), (0, 0, 0.92)),
                (150, (0, -2.4, 1.18), (0, 0, 1.15)),         # beat 7: push in
                (180, (0, -1.9, 1.32), (0, 0, 1.36))):
    common.key_cam(cam, f, c, t)
zdf.ease_all(cam)
common.fix_euler_flips(cam)
# same sky-blue card beat 5 ends on, clearing while the camera drops onto him
zdf.fill_card(cam, zdf.BLUE_MID, [(1, 1.0), (2, 1.0), (9, 0.0)], name="BlueIn")

common.finish(a, "beat6", [
    (13, [("head", zdf.bone_world(man, "Head")), ("heart", H), ("waist", bw("Hips"))]),
    (60, [("hand", bw("LeftHand")), ("heart", H)]),
    (100, [("foot", bw("LeftToeBase")), ("head", zdf.bone_world(man, "HeadTop_End"))]),
    (175, [("head", zdf.bone_world(man, "Head")), ("chest", H), ("hand L", bw("LeftHand"))]),
])

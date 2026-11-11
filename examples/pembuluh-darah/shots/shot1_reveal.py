"""
Beat 1 (0-4.5 s, frames 1-135):
"Kalau semua pembuluh darahmu ditarik keluar dan disambung jadi satu,"

The man in a suit stands on blue. X-ray reveal goes suit, then muscle, then the red vessel network.
The vessels drain out through his fingertips as threads that drop to the floor and
merge into one red line running toward the camera. Camera: one straight eased push-in,
then a tilt down at the end to hand the line to beat 2.

Run:
  blender -b --python shots/shot1_reveal.py -- --preview --stills 1,30,60,95,125,135
  blender -b --python shots/shot1_reveal.py -- --preview           (50% preview animation)
  blender -b --python shots/shot1_reveal.py -- --range 1-68        (final, chunk A)
"""
import os, sys, math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common
from common import zdf, bpy, Vector

a = common.args()
zdf.new_scene(seconds=4.5, samples=64, preview=a.preview)
B = common.build_body()
man, mus, vessels, heart = B["man"], B["mus"], B["vessels"], B["heart"]

# --- Camera: full body -> hands, straight dolly on the view axis -------------
cam = zdf.camera(loc=(0, -3.1, 1.02), target=(0, 0, 0.9), lens=40)
focus = bpy.data.objects.new("Focus", None)
bpy.context.scene.collection.objects.link(focus)
focus.location = (0, -0.05, 0.9)
cam.data.dof.use_dof = True
cam.data.dof.focus_object = focus
cam.data.dof.aperture_fstop = 2.8
zdf.blue_backdrop()
zdf.ground("catcher")
zdf.sun(energy=3.5, rot_deg=(48, 0, 32))
zdf.area_fill(energy=250)
zdf.dolly(cam, dist=1.35, f0=1, f1=135)
# hand-off: tilt down to follow the line on the floor (eased, last 0.8 s)
r0 = cam.rotation_euler.copy()
cam.keyframe_insert("rotation_euler", frame=111)
cam.rotation_euler = (r0.x - math.radians(14), r0.y, r0.z)
cam.keyframe_insert("rotation_euler", frame=135)
zdf.ease_all(cam)

# --- X-ray reveal timing ------------------------------------------------------
common.layer_alpha(mus, [(1, 0), (20, 0), (32, 1), (50, 1), (68, 0.12), (100, 0.12), (122, 0)])
common.layer_alpha(man, [(16, 1), (40, 0), (104, 0), (130, 1)])
common.layer_alpha(vessels, [(1, 0), (40, 0), (54, 1)])
common.layer_alpha(heart, [(1, 0), (40, 0), (54, 1)])

# heart: two beats, then empties as the vessels drain
for f, s in ((54, 1.0), (60, 1.15), (64, 1.0), (72, 1.15), (76, 1.0), (96, 1.0), (114, 0.01)):
    heart.scale = (0.9 * s, 0.75 * s, 1.1 * s)
    heart.keyframe_insert("scale", frame=f)

# vessels drain outward (every spline runs trunk -> skin / fingertips)
cd = vessels.data
for f, v in ((78, 0.0), (116, 1.0)):
    cd.bevel_factor_start = v
    cd.keyframe_insert("bevel_factor_start", frame=f)

# --- Threads out of the 10 fingertips, merging into one floor line ---------------
FLOOR = common.FLOOR
merge = common.MERGE                       # just in front of his feet
far = common.LINE_END                      # same path as the room line in beats 2 and 4
thread_mat = zdf.mat_blood("Thread")
threads = []
for side in ("Left", "Right"):
    tips = zdf.fingertips(mus, side)
    centre = sum(tips, Vector()) / len(tips)
    gather = centre + Vector((0, -0.03, -0.12))            # 5 threads meet below the hand
    land = Vector((gather.x * 0.85, gather.y - 0.14, FLOOR))
    for i, tip in enumerate(tips):
        sway = Vector((0, -0.02 - 0.01 * i, 0))
        pts = [tip, tip.lerp(gather, 0.55) + Vector((0, 0, -0.02)), gather,
               gather.lerp(land, 0.35) + sway, gather.lerp(land, 0.75) + sway * 2,
               land + Vector((0, 0, 0.02)), land.lerp(merge, 0.5) + Vector((0, -0.06, 0)),
               merge, merge.lerp(far, 0.12), merge.lerp(far, 0.5), far]
        t = zdf.tube_curve([tuple(p) for p in pts], radius=0.0024, mat=thread_mat,
                           name=f"Thread_{side}{i}", smooth=True)
        t.data.bevel_factor_mapping_end = "SPLINE"
        for k, p in enumerate(t.data.splines[0].points):
            p.radius = 1.0 if k < 7 else common.LINE_RADIUS / 0.0024   # floor part = room line width
        zdf.grow_curve(t, 80 + i, 135)            # tiny stagger: threads leave one by one
        zdf.ease_all(t.data)
        threads.append(t)

common.finish(a, "beat1", [
    (1, [("head", zdf.bone_world(man, "Head")), ("feet", Vector((0, 0, 0)))]),
    (135, [("merge", merge), ("hand_L", zdf.bone_world(man, "LeftHand"))]),
])

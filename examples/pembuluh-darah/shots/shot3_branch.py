"""
Beat 3 (7.5-14 s, 195 frames):
"Tapi arteri terus bercabang jadi pipa yang makin kecil, sampai kapiler yang lebih tipis dari rambut."

Macro world on the flat blue. Starts facing the cut end of a thick glossy artery (the line's end),
rises over it and flies along one branch path through 8 generations of forks, each smaller,
down to a capillary bed. A human hair (10x a capillary's width) drifts across at the end, diagonally through the focus plane.
Last 15 frames: a fast pull-back (motion-blurred) that hands off to beat 4.
Scale is cheated large (trunk radius 2 m) so depth of field behaves like a macro lens.

  blender -b --python shots/shot3_branch.py -- --check
"""
import os, sys, math, random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common
from common import zdf, bpy, Vector
from mathutils import Matrix

a = common.args()
zdf.new_scene(seconds=6.5, samples=64, preview=a.preview)
zdf.blue_backdrop(style="flat")
zdf.sun(energy=3.0, rot_deg=(35, 0, 30))
zdf.area_fill(energy=40000, loc=(-30, -40, 40), size=30)

rnd = random.Random(11)
GENS = 8
R0, L0 = 2.0, 22.0
RK, LK = 0.62, 0.72
art = zdf.mat_principled("Artery", (0.86, 0.03, 0.04), rough=0.28, sss=0.15)
cd = bpy.data.curves.new("Tree", "CURVE")
cd.dimensions = "3D"
cd.bevel_depth = 1.0
cd.bevel_resolution = 16         # round cut faces, no visible facets
cd.use_fill_caps = True
cd.materials.append(art)


def tube(p0, p1, r0, r1, bend):
    sp = cd.splines.new("NURBS")
    mid = p0.lerp(p1, 0.5) + bend
    pts = [p0, p0.lerp(mid, 0.6), mid, mid.lerp(p1, 0.4), p1]
    sp.points.add(len(pts) - 1)
    for i, (pt, co) in enumerate(zip(sp.points, pts)):
        pt.co = (*co, 1)
        pt.radius = r0 + (r1 - r0) * i / (len(pts) - 1)
    sp.order_u = 3
    sp.use_endpoint_u = True
    sp.resolution_u = 8


path = []        # the branch the camera follows: (start, end, radius)
leaves = []


def grow(p, d, r, length, gen, on_path):
    end = p + d * length
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    bend = side * rnd.uniform(-0.08, 0.08) * length + Vector((0, 0, rnd.uniform(-0.05, 0.05) * length))
    tube(p, end, r, r * 0.92, bend)
    if on_path:
        path.append((p, end, r))
    if gen == GENS:
        leaves.append((end, r))
        return
    kids = 3 if gen >= GENS - 2 else 2          # capillary beds branch more
    spread = math.radians(rnd.uniform(28, 40))
    pick = rnd.randrange(kids)
    for k in range(kids):
        ang = (-spread + 2 * spread * k / (kids - 1)) + math.radians(rnd.uniform(-6, 6))
        tilt = math.radians(rnd.uniform(-12, 12))
        nd = (Matrix.Rotation(ang, 3, Vector((0, 0, 1))) @ Matrix.Rotation(tilt, 3, side) @ d).normalized()
        grow(end, nd, r * RK, length * LK, gen + 1, on_path and k == pick)


grow(Vector((0, 0, 0)), Vector((0, 1, 0)), R0, L0, 0, True)
# capillary bed: link each leaf to its two nearest leaves
for i, (p, r) in enumerate(leaves):
    near = sorted(((q - p).length, q) for j, (q, _) in enumerate(leaves) if j != i)[:2]
    for dist, q in near:
        if dist < 8 * L0 * LK ** GENS:
            tube(p, q, r * 0.8, r * 0.8, Vector((0, 0, rnd.uniform(-0.3, 0.3))))
tree = bpy.data.objects.new("Tree", cd)
bpy.context.scene.collection.objects.link(tree)
print("BRANCH tubes", len(cd.splines), "path gens", len(path), "leaf radius", round(path[-1][2], 4))

# --- camera: face the cut end, rise over, then ride the path (one generation per ~19 frames) ---
cam = zdf.camera(loc=(0, -16, 0.4), target=(0, 0, 0), lens=40)
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 4
look = bpy.data.objects.new("Look", None)
bpy.context.scene.collection.objects.link(look)
cam.data.dof.focus_object = look
con = cam.constraints.new("TRACK_TO")
con.target = look
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"


def key(f, cam_loc, look_loc):
    cam.location = cam_loc
    cam.keyframe_insert("location", frame=f)
    look.location = look_loc
    look.keyframe_insert("location", frame=f)


key(1, Vector((0, -16, 0.4)), Vector((0, 0, 0)))          # cut end fills the middle of frame
key(22, Vector((0, -6.5, 1.2)), Vector((0, 0, 0)))         # push in on the cut face
key(36, Vector((0, -2.0, 5.5)), path[0][0].lerp(path[0][1], 0.5))   # rise over the trunk
f = 36
step = (160 - 36) / len(path)          # top-down view of the bed reached at f160, held to f180
for i, (p0, p1, r) in enumerate(path):
    f = round(36 + step * (i + 1))
    d = (p1 - p0).normalized()
    nxt = path[i + 1] if i + 1 < len(path) else (p1, p1 + d * r * 8, r)
    last = i == len(path) - 1
    # final generation: rise to look DOWN onto the capillary bed (parents stay behind/below frame)
    cam_loc = (p1 + Vector((0, -r * 25, r * 200))) if last else (p1 - d * r * 7 + Vector((0, 0, r * 3.2)))
    if last:
        key(f, cam_loc, p1)
        continue
    key(f, cam_loc, nxt[0].lerp(nxt[1], 0.6))
end_cam, end_look = cam.location.copy(), look.location.copy()
# hair: 10x a capillary's radius. It must read as HAIR with depth (viewer feedback on the
# first cut: "doesn't look like a hair / no depth"): zdf.hair_strand gives cuticle scales,
# a double highlight and translucent edges, and the strand runs DIAGONALLY through the focal
# plane - the far end dips under the capillary bed, the near end rises toward the lens and
# goes soft - so it overlaps the vessels, casts a shadow on them and has real depth.
cap_r = path[-1][2]
hair_c = end_look + Vector((0, 0, cap_r * 3))       # crosses the bed at the focus distance
hdir = Vector((0.35, 1, 0.33)).normalized()         # rises ~100r toward the camera over 300r
hair = zdf.hair_strand(hair_c - hdir * cap_r * 300, hair_c + hdir * cap_r * 300, radius=cap_r * 10,
                       color=(0.42, 0.26, 0.12), name="Hair")
hair_home = hair.location.copy()
for fr, off in ((132, Vector((cap_r * 160, 0, 0))), (166, Vector((0, 0, 0))), (195, Vector((-cap_r * 70, 0, 0)))):
    hair.location = hair_home + off
    hair.keyframe_insert("location", frame=fr)
key(180, end_cam + Vector((0, path[-1][2] * 8, -path[-1][2] * 25)), end_look)   # slow creep in while holding
# fast pull-back (hand-off to beat 4)
key(195, end_cam + (end_cam - end_look).normalized() * 40 + Vector((0, 0, 12)), end_look)
zdf.ease_all(cam)
zdf.ease_all(look)
zdf.ease_all(hair)
hair.hide_render = True                 # only exists for the capillary moment
hair.keyframe_insert("hide_render", frame=1)
hair.hide_render = False
hair.keyframe_insert("hide_render", frame=128)

common.finish(a, "beat3", [
    (1, [("cut end", Vector((0, 0, 0)))]),
    (60, [("path", path[2][1])]),
    (120, [("path", path[5][1])]),
    (166, [("capillary", path[-1][1]), ("hair", hair_c)]),
])

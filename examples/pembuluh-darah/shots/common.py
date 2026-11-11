"""Shared builders for the blood-vessel short.
Beats 1, 6, 7 reuse the body. Beats 2 and 4 reuse the tape-lined room.

Every shot script takes the same arguments after '--':
  --check            build the scene, save shots/beatN.blend, print framing checks. NO render.
  --preview          50% resolution, 16 samples (for --stills or a full preview)
  --stills 1,40,90   render only these frames
  --range 1-68       render a frame range (to split a beat across two Blender processes)
  --out DIR          output folder (default renders/beatN[_preview])
"""
import sys, os, argparse, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # this example's folder


def _zdf_dir():
    """Find the skill's scripts/ folder: $ZDF_SCRIPTS, this repo, or an installed skill."""
    cands = [os.environ.get("ZDF_SCRIPTS", ""),
             os.path.join(ROOT, "..", "..", "skills", "zack-d-short", "scripts"),
             os.path.join(os.path.expanduser("~"), ".claude", "skills", "zack-d-short", "scripts")]
    for c in cands:
        if c and os.path.exists(os.path.join(c, "zdf.py")):
            return os.path.abspath(c)
    raise FileNotFoundError("zdf.py not found: set ZDF_SCRIPTS to <repo>/skills/zack-d-short/scripts")


sys.path.append(_zdf_dir())
import bpy
import zdf
from mathutils import Vector

ASSETS = os.path.join(ROOT, "assets")
# Characters are NOT in the repo (Mixamo licence forbids redistributing the raw files).
# Download two Mixamo characters as FBX (see assets/README.md) or point these env vars at your own.
MAN_FBX = os.environ.get("ZDF_HERO_FBX", os.path.join(ASSETS, "hero.fbx"))     # dressed man, outer layer
MUSCLE_FBX = os.environ.get("ZDF_XRAY_FBX", os.path.join(ASSETS, "xray.fbx"))  # skinless/muscle figure, x-ray layer
ARM_DOWN = 72

# --- one floor line runs through beats 1, 2 and 4 ------------------------------
FLOOR = 0.006
LINE_X = 0.06
MERGE = Vector((LINE_X, -0.32, FLOOR))    # where the fingertip threads meet (beat 1)
ROOM_Y0, ROOM_Y1 = -1.5, -6.5             # open front / back wall (5 m deep)
ROOM_W, ROOM_H = 3.5, 2.6
LINE_END = Vector((LINE_X, ROOM_Y1 + 0.06, FLOOR))   # stops at the far wall = 5 m mark
LINE_RADIUS = 0.011                       # floor line (thicker than the threads so it reads wide)


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--stills", default="")
    ap.add_argument("--range", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--save", default="")
    return ap.parse_args(argv)


# ---------------------------------------------------------------------------
# Body
# ---------------------------------------------------------------------------
def build_body(n_branches=900):
    """Man (Ch33) + muscle layer (Ch30) at the same origin, both arms-down,
    a vessel network grown inside the muscle figure, and a heart."""
    man = zdf.import_character(MAN_FBX)
    zdf.relax_arms(man, ARM_DOWN)
    mus = zdf.import_character(MUSCLE_FBX)
    zdf.relax_arms(mus, ARM_DOWN)
    vessels = zdf.vessel_network(mus, zdf.char_mesh(mus), n_branches=n_branches)
    s1 = zdf.bone_world(mus, "Spine1")
    s2 = zdf.bone_world(mus, "Spine2")
    chest = s1.lerp(s2, 0.75) + Vector((0.025, -0.045, 0))   # slightly to his left, forward
    hrt = zdf.heart(chest, size=0.042)
    return dict(man=man, mus=mus, vessels=vessels, heart=hrt)


def layer_alpha(rig_or_obj, keys):
    """keys: [(frame, alpha), ...] applied to every mesh of a character (or one object)."""
    objs = [c for c in rig_or_obj.children if c.type == "MESH"] if rig_or_obj.type == "ARMATURE" else [rig_or_obj]
    for f, a in keys:
        for o in objs:
            zdf.set_alpha(o, a, frame=f)


def man_shoes():
    """Just the man standing (for beats 2/4 where only his feet/legs are seen)."""
    man = zdf.import_character(MAN_FBX)
    zdf.relax_arms(man, ARM_DOWN)
    return man


# ---------------------------------------------------------------------------
# Tape-lined room (beats 2 and 4)
# ---------------------------------------------------------------------------
def _box(name, center, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


def _tape_strip(name, x, z, inward, img_name, height=0.12):
    """Flat strip along a side wall from the open front (5 m mark at the back).
    UVs are laid out so the numbers read left-to-right from inside the room."""
    me = bpy.data.meshes.new(name)
    y0, y1 = ROOM_Y0, ROOM_Y1
    x = x + inward * 0.004
    verts = [(x, y0, z - height / 2), (x, y1, z - height / 2), (x, y1, z + height / 2), (x, y0, z + height / 2)]
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    # right wall (inward -1): viewer's right is the back -> u grows to the back, 'ltr' image
    # left wall  (inward +1): viewer's right is the front -> u grows to the front, 'rtl' image
    us = [0, 1, 1, 0] if inward < 0 else [1, 0, 0, 1]
    for li, (u, v) in enumerate(zip(us, [0, 0, 1, 1])):
        uv.data[li].uv = (u, v)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.45
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(ASSETS, img_name), check_existing=True)
    t.interpolation = "Cubic"
    nt.links.new(t.outputs[0], p.inputs["Base Color"])
    me.materials.append(m)
    return o


def build_room(with_line=True, hole_plug=True):
    """5 m x 3.5 m cut-away room on the blue: three walls, no ceiling, open front.
    Tape-measure strips along both side walls (1 m high and just above the skirting).
    The back wall has a 0.5 m plug of loose plaster chunks where the line ends,
    so beat 4 can blow it out. Returns dict of objects."""
    tape_ok = os.path.exists(os.path.join(ASSETS, "tape_ltr.png"))
    if not tape_ok:
        raise FileNotFoundError("run: python shots/gen_tape.py  (makes assets/tape_*.png)")
    wall = zdf.mat_principled("Plaster", (0.80, 0.81, 0.80), rough=0.9)
    skirt = zdf.mat_principled("Skirting", (0.97, 0.97, 0.97), rough=0.5)
    floor_m = _wood_floor()
    cx = LINE_X
    xl, xr = cx - ROOM_W / 2, cx + ROOM_W / 2
    yc = (ROOM_Y0 + ROOM_Y1) / 2
    depth = ROOM_Y0 - ROOM_Y1
    t = 0.1
    objs = {}
    objs["floor"] = _box("RoomFloor", (cx, yc, -0.01), (ROOM_W, depth, 0.02), floor_m)
    objs["wall_l"] = _box("WallL", (xl - t / 2, yc, ROOM_H / 2), (t, depth, ROOM_H), wall)
    objs["wall_r"] = _box("WallR", (xr + t / 2, yc, ROOM_H / 2), (t, depth, ROOM_H), wall)
    # back wall with a hole (0.5 wide x 0.5 high) at the line end
    hw, hh = 0.5, 0.5
    yb = ROOM_Y1 - t / 2
    left_w = (cx - hw / 2) - (xl - t)
    right_w = (xr + t) - (cx + hw / 2)
    objs["wall_b1"] = _box("WallB_L", ((xl - t) + left_w / 2, yb, ROOM_H / 2), (left_w, t, ROOM_H), wall)
    objs["wall_b2"] = _box("WallB_R", ((cx + hw / 2) + right_w / 2, yb, ROOM_H / 2), (right_w, t, ROOM_H), wall)
    objs["wall_b3"] = _box("WallB_Top", (cx, yb, hh + (ROOM_H - hh) / 2), (hw, t, ROOM_H - hh), wall)
    chunks = []
    if hole_plug:
        # one solid plug for the intact wall; the loose chunks only appear at the break (beat 4)
        objs["plug"] = _box("WallB_Plug", (cx, yb, hh / 2), (hw, t, hh), wall)
        n = 5
        s = hw / n
        for i in range(n):
            for j in range(n):
                c = _box(f"Chunk_{i}_{j}", (cx - hw / 2 + s * (i + 0.5), yb, s * (j + 0.5)), (s * 0.985, t * 0.985, s * 0.985), wall)
                c.hide_render = True
                chunks.append(c)
    objs["chunks"] = chunks
    # skirting boards
    for nm, x in (("SkirtL", xl + 0.006), ("SkirtR", xr - 0.006)):
        _box(nm, (x, yc, 0.04), (0.012, depth, 0.08), skirt)
    _box("SkirtB", (cx, ROOM_Y1 + 0.006, 0.04), (ROOM_W, 0.012, 0.08), skirt)
    # tape strips: waist height and just above the skirting, on both side walls
    for z, h in ((1.0, 0.32), (0.17, 0.12)):        # oversized "giant tape" so the numbers read on camera
        _tape_strip(f"TapeL_{z}", xl, z, +1, "tape_rtl.png", h)
        _tape_strip(f"TapeR_{z}", xr, z, -1, "tape_ltr.png", h)
    if with_line:
        objs["line"] = floor_line()
    return objs


def _wood_floor():
    """Matte oak planks along the room (y): Brick texture rotated 90 deg, grain from noise."""
    m = bpy.data.materials.new("WoodFloor")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.68          # low gloss: no sky reflections
    p.inputs["Specular IOR Level"].default_value = 0.3
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(90))
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.5
    br.squash = 1.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 2.4      # plank length (m)
    br.inputs["Row Height"].default_value = 0.18      # plank width (m)
    br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = (*zdf._lin((0.58, 0.40, 0.24)), 1)
    br.inputs["Color2"].default_value = (*zdf._lin((0.50, 0.33, 0.19)), 1)
    br.inputs["Mortar"].default_value = (*zdf._lin((0.25, 0.16, 0.09)), 1)
    grain_map = nt.nodes.new("ShaderNodeMapping")
    grain_map.inputs["Scale"].default_value = (0.15, 6.0, 1.0)   # streaks along the planks
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 4.0
    nz.inputs["Detail"].default_value = 6
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs[0], br.inputs["Vector"])
    nt.links.new(mp.outputs[0], grain_map.inputs["Vector"])
    nt.links.new(grain_map.outputs[0], nz.inputs["Vector"])
    nt.links.new(br.outputs["Color"], mix.inputs[6])
    gray = nt.nodes.new("ShaderNodeMapRange")          # greyscale grain 0.75..1.0
    gray.inputs["To Min"].default_value = 0.75
    nt.links.new(nz.outputs["Fac"], gray.inputs["Value"])
    nt.links.new(gray.outputs["Result"], mix.inputs[7])
    nt.links.new(mix.outputs[2], p.inputs["Base Color"])
    return m


def floor_line(extra=None):
    """The red line from the man's feet to the far wall (5 m mark)."""
    pts = [MERGE + Vector((0, 0.25, 0)), MERGE, LINE_END]
    o = zdf.tube_curve([tuple(p) for p in pts], radius=LINE_RADIUS, mat=zdf.mat_blood("LineMat"), name="FloorLine")
    return o


def room_lights():
    zdf.sun(energy=3.2, rot_deg=(42, 0, -28))
    d = bpy.data.lights.new("RoomFill", "AREA")
    d.energy = 450
    d.size = 4
    o = bpy.data.objects.new("RoomFill", d)
    bpy.context.scene.collection.objects.link(o)
    o.location = (LINE_X, (ROOM_Y0 + ROOM_Y1) / 2, 4.5)


# ---------------------------------------------------------------------------
# Camera helpers
# ---------------------------------------------------------------------------
def key_cam(cam, f, loc, target, lens=None):
    """Keyframe location + a look-at rotation (no constraint, so whips can be layered)."""
    cam.location = loc
    zdf.look_at(cam, target)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
    if lens:
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=f)


def fix_euler_flips(cam):
    """Keep consecutive rotation keys continuous (no 360 deg spins between look-ats)."""
    for fc in zdf._fcurves(cam):
        if fc.data_path != "rotation_euler":
            continue
        kps = fc.keyframe_points
        for i in range(1, len(kps)):
            prev = kps[i - 1].co[1]
            v = kps[i].co[1]
            while v - prev > math.pi:
                v -= 2 * math.pi
            while v - prev < -math.pi:
                v += 2 * math.pi
            kps[i].co[1] = v
        fc.update()


# ---------------------------------------------------------------------------
# Check (no render) and render
# ---------------------------------------------------------------------------
def check(checks):
    """checks: [(frame, [(label, Vector|object), ...]), ...]
    Prints where each point lands in the 9:16 frame (0..1, origin bottom-left),
    flags anything off-frame or behind the camera. Never renders."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    cam = sc.camera
    bad = 0
    for f, items in checks:
        sc.frame_set(f)
        row = []
        for label, p in items:
            if isinstance(p, bpy.types.Object):
                p = p.matrix_world.translation
            v = world_to_camera_view(sc, cam, Vector(p))
            ok = v.z > 0 and -0.02 <= v.x <= 1.02 and -0.02 <= v.y <= 1.02
            bad += not ok
            row.append(f"{label}=({v.x:.2f},{v.y:.2f}{'' if ok else ' OFF'})")
        print(f"CHECK f{f:>3}: " + "  ".join(row))
    print(f"CHECK done: {bad} point(s) off-frame")


def finish(a, beat, checks=()):
    sc = bpy.context.scene
    blend = os.path.join(ROOT, "shots", f"{beat}.blend")
    if a.check:
        check(checks)
        zdf.save(blend)
        print("CHECK saved", blend)
        return
    if a.save:
        zdf.save(a.save)
    out = a.out or os.path.join(ROOT, "renders", beat + ("_preview" if a.preview else ""))
    if not os.path.isabs(out):            # Blender's cwd is not the project: anchor relative paths
        out = os.path.join(ROOT, out)
    if a.stills:
        for f in [int(x) for x in a.stills.split(",")]:
            zdf.render_frames(out, still_frame=f)
        return
    if a.range:
        s, e = a.range.split("-")
        sc.frame_start, sc.frame_end = int(s), int(e)
    zdf.render_frames(out)


def render(a, out_dir):   # kept for shot1_reveal.py
    finish(a, "beat1")

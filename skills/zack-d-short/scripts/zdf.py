"""
zdf.py - Blender helper library for "Zack D. Films"-style vertical 3D shorts.

Import inside a Blender Python script:

    import sys; sys.path.append(r"<skill>/scripts")
    import zdf
    zdf.new_scene(seconds=4)
    zdf.blue_backdrop()
    man = zdf.import_character(r"assets/hero.fbx")
    zdf.relax_arms(man)
    cam = zdf.camera(loc=(0, -4.2, 1.0), target=(0, 0, 0.95), lens=50)
    zdf.dolly(cam, axis_vec=(0, 1, 0), dist=1.5, f0=1, f1=90)
    zdf.render_frames("//renders/shot1/")

All values come from frame measurements of 9 reference shorts (see SKILL.md).
Tested on Blender 5.2 LTS.
"""
import bpy, math, os
from mathutils import Vector

# ---------------------------------------------------------------------------
# Measured style constants
# ---------------------------------------------------------------------------
FPS = 30
RES = (1080, 1920)
# Backdrop: radial gradient, light centre -> saturated sky blue edges.
BLUE_EDGE = (0.30, 0.75, 1.00)      # ~ #4DC0FF measured at frame edges
BLUE_MID = (0.53, 0.82, 1.00)       # ~ #87D1FF
BLUE_CENTER = (0.72, 0.88, 1.00)    # ~ #B8E0FF light centre behind subject
BLUE_FLAT = (0.33, 0.64, 0.87)      # ~ #53A4DF (splinter/skin macro shots)
WHITE_STUDIO = (0.97, 0.97, 0.97)   # dental/medical cut-away shots
FIELD_GREEN = (0.24, 0.42, 0.10)    # stylised field / ground
BLOOD_RED = (0.80, 0.02, 0.03)      # vessels, wounds, arrows (flat, saturated)
GLOW_GREEN = (0.25, 1.00, 0.05)     # "this property is special" highlight
GLOW_MAGENTA = (0.85, 0.20, 1.00)   # "force / energy" highlight
GLOW_YELLOW = (1.00, 0.85, 0.10)    # pus/cells/particles, safety highlight


def _lin(c):
    """sRGB 0-1 -> linear, so hex-measured colours match on screen."""
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
def new_scene(seconds=4.0, engine="CYCLES", samples=64, preview=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start = 1
    sc.frame_end = max(1, int(round(seconds * FPS)))
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 50 if preview else 100
    sc.render.engine = "CYCLES" if engine == "CYCLES" else "BLENDER_EEVEE"
    if sc.render.engine == "CYCLES":
        sc.cycles.samples = 16 if preview else samples
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 6
        # x-ray reveals stack many see-through layers (suit, hair cards, muscle);
        # the default limit of 8 renders them black
        sc.cycles.transparent_max_bounces = 64
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            for t in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
                try:
                    prefs.compute_device_type = t
                    prefs.get_devices()
                    if any(d.type == t for d in prefs.devices):
                        for d in prefs.devices:
                            d.use = d.type == t
                        sc.cycles.device = "GPU"
                        break
                except TypeError:
                    continue
        except Exception:
            pass
    # Camera realism: motion blur on (fast moves smear like the refs)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    # Keeps saturated sky blue AND rolls highlights off (Standard clips, AgX greys blue)
    vs = sc.view_settings
    try:
        vs.view_transform = "Khronos PBR Neutral"
    except TypeError:
        vs.view_transform = "Standard"
    vs.look = "None"
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    world = bpy.data.worlds.new("ZDF_World")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*_lin(BLUE_MID), 1)
    bg.inputs[1].default_value = 0.6
    return sc


def sun(energy=3.5, rot_deg=(50, 0, 35), color=(1.0, 0.97, 0.92), angle_deg=3):
    """Single warm key sun, soft-ish shadows (refs show one clear cast shadow)."""
    d = bpy.data.lights.new("Key", "SUN")
    d.energy = energy
    d.color = color
    d.angle = math.radians(angle_deg)
    o = bpy.data.objects.new("Key", d)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = [math.radians(a) for a in rot_deg]
    return o


def area_fill(energy=300, loc=(-3, -3, 3), size=4):
    d = bpy.data.lights.new("Fill", "AREA")
    d.energy = energy
    d.size = size
    o = bpy.data.objects.new("Fill", d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 1)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def mat_emission(name, color, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*_lin(color), 1)
    em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def mat_principled(name, color, rough=0.5, metal=0.0, sss=0.0, emit=None, emit_strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*_lin(color), 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Subsurface Weight"].default_value = sss
    if sss:
        p.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
        p.inputs["Subsurface Scale"].default_value = 0.01
    if emit:
        p.inputs["Emission Color"].default_value = (*_lin(emit), 1)
        p.inputs["Emission Strength"].default_value = emit_strength
    p.inputs["Alpha"].default_value = alpha
    return m


def mat_blood(name="Blood"):
    """Flat, glossy, saturated red. The refs never use realistic dark blood."""
    return mat_principled(name, (0.85, 0.03, 0.04), rough=0.25, sss=0.3)


def set_alpha(obj_or_mat, alpha, frame=None):
    """Fade any material (x-ray reveal, 'body turns see-through'). Keyframe with frame."""
    mats = [obj_or_mat] if isinstance(obj_or_mat, bpy.types.Material) else [s.material for s in obj_or_mat.material_slots if s.material]
    for m in dict.fromkeys(mats):
        nt = m.node_tree
        p = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not p:
            continue
        # A multiply node in front of Alpha, so textured cut-outs (hair) still fade
        fade = nt.nodes.get("ZDF_Fade")
        if fade is None:
            fade = nt.nodes.new("ShaderNodeMath")
            fade.name = "ZDF_Fade"
            fade.operation = "MULTIPLY"
            fade.inputs[0].default_value = p.inputs["Alpha"].default_value
            if p.inputs["Alpha"].is_linked:
                nt.links.new(p.inputs["Alpha"].links[0].from_socket, fade.inputs[0])
            nt.links.new(fade.outputs[0], p.inputs["Alpha"])
        fade.inputs[1].default_value = alpha
        try:
            m.surface_render_method = "DITHERED"
        except AttributeError:
            pass
        if frame is not None:
            fade.inputs[1].keyframe_insert("default_value", frame=frame)


def glow_overlay(obj, color=GLOW_GREEN, strength=6.0, f_on=None, f_off=None, ramp=6):
    """Zack's 'highlight' device: whole object washes in a glowing colour, then fades.
    Implemented by mixing emission into every material and keyframing the strength."""
    for slot in obj.material_slots:
        m = slot.material
        if not m:
            continue
        m = m.copy()
        slot.material = m
        p = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not p:
            continue
        p.inputs["Emission Color"].default_value = (*_lin(color), 1)
        sock = p.inputs["Emission Strength"]
        if f_on is None:
            sock.default_value = strength
            continue
        for f, v in ((f_on - 1, 0), (f_on + ramp, strength)):
            sock.default_value = v
            sock.keyframe_insert("default_value", frame=f)
        if f_off is not None:
            for f, v in ((f_off, strength), (f_off + ramp, 0)):
                sock.default_value = v
                sock.keyframe_insert("default_value", frame=f)


# ---------------------------------------------------------------------------
# Backdrop / ground
# ---------------------------------------------------------------------------
def blue_backdrop(cam=None, style="radial", light_strength=0.6):
    """The signature sky-blue backdrop, built in the WORLD shader:
    camera rays see a screen-space radial gradient (light centre, saturated edges);
    everything else (lighting, reflections) sees a soft sky blue. Because it is the world,
    ground(kind='catcher') shows soft shadows on the blue with no horizon seam
    (the 'floating in blue' look of the armour / vessel shots).
    style: 'radial' (default) | 'flat' (macro skin shots) | 'white' (dental/medical)."""
    world = bpy.context.scene.world
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    mix = nt.nodes.new("ShaderNodeMixShader")
    lp = nt.nodes.new("ShaderNodeLightPath")
    light = nt.nodes.new("ShaderNodeBackground")
    light.inputs[0].default_value = (*_lin(BLUE_MID), 1)
    light.inputs[1].default_value = light_strength
    seen = nt.nodes.new("ShaderNodeBackground")
    seen.inputs[1].default_value = 1.0
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(light.outputs[0], mix.inputs[1])
    nt.links.new(seen.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    if style == "radial":
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        # Mapping = in*scale + location -> centre of frame at 0, circular in 9:16
        mp.inputs["Location"].default_value = (-0.5 * 9 / 16, -0.42, 0)  # centre a bit above middle
        mp.inputs["Scale"].default_value = (9 / 16, 1.0, 1)
        grad = nt.nodes.new("ShaderNodeTexGradient")
        grad.gradient_type = "SPHERICAL"
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        cr = ramp.color_ramp
        # spherical value: 1 at centre, ~0.45 at frame edges, ~0.35 in corners
        cr.elements[0].position = 0.42
        cr.elements[0].color = (*_lin(BLUE_EDGE), 1)
        cr.elements[1].position = 0.97
        cr.elements[1].color = (*_lin(BLUE_CENTER), 1)
        e = cr.elements.new(0.68)
        e.color = (*_lin(BLUE_MID), 1)
        nt.links.new(tc.outputs["Window"], mp.inputs["Vector"])
        nt.links.new(mp.outputs[0], grad.inputs[0])
        nt.links.new(grad.outputs[1], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], seen.inputs[0])
    else:
        col = BLUE_FLAT if style == "flat" else WHITE_STUDIO
        seen.inputs[0].default_value = (*_lin(col), 1)
        if style == "white":
            light.inputs[0].default_value = (1, 1, 1, 1)
    return world


def ground(kind="field", size=200):
    """kind: 'field' (flat stylised green with mowing stripes),
    'catcher' (invisible, only catches shadows over the blue backdrop)."""
    bpy.ops.mesh.primitive_plane_add(size=size)
    g = bpy.context.active_object
    g.name = "ZDF_Ground"
    if kind == "catcher":
        g.is_shadow_catcher = True
        return g
    m = bpy.data.materials.new("ZDF_Field")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.9
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_profile = "SAW"
    wave.inputs["Scale"].default_value = 0.6
    wave.inputs["Distortion"].default_value = 0
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 400
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*_lin(FIELD_GREEN), 1)
    mix.inputs[7].default_value = (*_lin((0.27, 0.46, 0.12)), 1)
    stripe = nt.nodes.new("ShaderNodeMath")
    stripe.operation = "GREATER_THAN"
    stripe.inputs[1].default_value = 0.5
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], stripe.inputs[0])
    nt.links.new(stripe.outputs[0], mix.inputs[0])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], p.inputs["Normal"])
    nt.links.new(mix.outputs[2], p.inputs["Base Color"])
    g.data.materials.append(m)
    return g


# ---------------------------------------------------------------------------
# Character (Mixamo FBX, e.g. Ch30_nonPBR.fbx)
# ---------------------------------------------------------------------------
def import_character(path, skin_slots=None):
    """Import a Mixamo FBX and rebuild its spec/gloss materials as Principled.
    Returns the armature. skin_slots: material names that contain skin (get SSS).
    Default: any material whose diffuse texture is mostly skin-toned is guessed."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            _fix_mixamo_material(slot.material, skin_slots)
        for poly in o.data.polygons:
            poly.use_smooth = True
    # Drop the 2-frame T-pose action so we can pose freely
    if arm.animation_data:
        arm.animation_data.action = None
    return arm


def _fix_mixamo_material(m, skin_slots):
    if not m or not m.use_nodes:
        return
    nt = m.node_tree
    imgs = {n.image.name: n.image for n in nt.nodes if n.type == "TEX_IMAGE" and n.image}
    by_kind = {}
    for img in imgs.values():
        fp = (img.filepath or img.name).lower()
        for k in ("diffuse", "normal", "gloss", "specular"):
            if k in fp:
                by_kind[k] = img
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(p.outputs[0], out.inputs[0])
    diff = None
    if "diffuse" in by_kind:
        diff = t = nt.nodes.new("ShaderNodeTexImage")
        t.image = by_kind["diffuse"]
        nt.links.new(t.outputs[0], p.inputs["Base Color"])
        # Hair cards / eyelashes keep cut-outs in the diffuse alpha
        if _has_alpha(t.image):
            nt.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
            try:
                m.surface_render_method = "DITHERED"
            except AttributeError:
                pass
    if "normal" in by_kind:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = by_kind["normal"]
        t.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 0.8
        nt.links.new(t.outputs[0], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], p.inputs["Normal"])
    if "gloss" in by_kind:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = by_kind["gloss"]
        t.image.colorspace_settings.name = "Non-Color"
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(t.outputs[0], inv.inputs[1])
        clamp = nt.nodes.new("ShaderNodeMapRange")
        clamp.inputs["To Min"].default_value = 0.35  # matte, never waxy
        clamp.inputs["To Max"].default_value = 0.9
        nt.links.new(inv.outputs[0], clamp.inputs["Value"])
        nt.links.new(clamp.outputs[0], p.inputs["Roughness"])
    else:
        p.inputs["Roughness"].default_value = 0.6
    p.inputs["Specular IOR Level"].default_value = 0.4
    p.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    p.inputs["Subsurface Scale"].default_value = 0.005
    is_skin = (m.name in skin_slots) if skin_slots else _looks_like_skin(by_kind.get("diffuse"))
    if is_skin:
        p.inputs["Subsurface Weight"].default_value = 0.15
    elif diff is not None and "hair" not in m.name.lower():
        # Mixed atlas (skin + clothes in one texture, e.g. Ch33): SSS only where
        # the diffuse is skin-toned, via a hue/saturation/value mask.
        hsv = nt.nodes.new("ShaderNodeSeparateColor")
        hsv.mode = "HSV"
        nt.links.new(diff.outputs[0], hsv.inputs[0])
        def cmp(sock, op, val):
            n = nt.nodes.new("ShaderNodeMath")
            n.operation = op
            n.inputs[1].default_value = val
            nt.links.new(sock, n.inputs[0])
            return n.outputs[0]
        def mul(a, b):
            n = nt.nodes.new("ShaderNodeMath")
            n.operation = "MULTIPLY"
            nt.links.new(a, n.inputs[0])
            nt.links.new(b, n.inputs[1])
            return n.outputs[0]
        H, S, V = hsv.outputs[0], hsv.outputs[1], hsv.outputs[2]
        mask = mul(mul(cmp(H, "LESS_THAN", 0.11), cmp(S, "GREATER_THAN", 0.18)),
                   mul(cmp(S, "LESS_THAN", 0.75), cmp(V, "GREATER_THAN", 0.2)))
        nt.links.new(cmp(mask, "MULTIPLY", 0.15), p.inputs["Subsurface Weight"])
        is_skin = "masked"
    m["zdf_skin"] = is_skin if isinstance(is_skin, str) else bool(is_skin)


def _has_alpha(img):
    if img.channels < 4 or img.alpha_mode == "NONE":
        return False
    try:
        px = img.pixels[:]
        n = len(px) // 4
        step = max(1, n // 20000)
        return any(px[i * 4 + 3] < 0.5 for i in range(0, n, step))
    except Exception:
        return False


def _looks_like_skin(img):
    if img is None:
        return False
    try:
        px = img.pixels[:]
        n = len(px) // 4
        step = max(1, n // 4000)
        hits = tot = 0
        for i in range(0, n, step):
            r, g, b = px[i * 4], px[i * 4 + 1], px[i * 4 + 2]
            if r + g + b < 0.05:
                continue
            tot += 1
            if r > g > b and r > 0.35 and (r - b) > 0.12:
                hits += 1
        return tot and hits / tot > 0.25
    except Exception:
        return False


def bone(arm, name):
    """Find a pose bone by plain name. Mixamo prefixes vary per export
    ('mixamorig:', 'mixamorig1:', 'mixamorig9:' ...), so match on the part after ':'."""
    pb = arm.pose.bones.get(name)
    if pb is None:
        pb = next((b for b in arm.pose.bones if b.name.split(":")[-1] == name), None)
    if pb is None:
        raise KeyError(f"{name} not in {arm.name} (e.g. {arm.pose.bones[0].name})")
    return pb


def relax_arms(arm, down_deg=72, frame=None):
    """T-pose -> natural standing pose (Zack's characters stand arms-down, relaxed).
    Rotates each upper arm about the character's forward axis through the shoulder,
    so it works whatever the Mixamo bone roll is."""
    from mathutils import Matrix
    fwd = (arm.matrix_world.to_3x3().inverted() @ Vector((0, 1, 0))).normalized()
    for side, sgn in (("Left", 1), ("Right", -1)):
        pb = bone(arm, f"{side}Arm")
        # character faces -Y: its left arm points +X world; +angle about +Y lowers +X
        head_w = arm.matrix_world @ pb.head
        sgn_w = 1 if head_w.x > (arm.matrix_world.translation.x) else -1
        R = Matrix.Rotation(math.radians(down_deg) * sgn_w, 4, fwd)
        h = pb.head.copy()
        pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ pb.matrix
        bpy.context.view_layer.update()
        if frame is not None:
            pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == "QUATERNION" else "rotation_euler", frame=frame)
    bpy.context.view_layer.update()


def key_bone(arm, name, frame):
    pb = bone(arm, name)
    pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == "QUATERNION" else "rotation_euler", frame=frame)


def rotate_bone_world(arm, name, axis_world, deg, frame=None):
    """Rotate a pose bone about a WORLD axis through its head (on top of its current pose).
    Use for acting beats on Mixamo rigs whatever their bone roll, e.g. a head nod:
    rotate_bone_world(man, 'Head', (1,0,0), 25)  (character faces -Y: +X tips the head forward/down)."""
    from mathutils import Matrix
    pb = bone(arm, name)
    axis = (arm.matrix_world.to_3x3().inverted() @ Vector(axis_world)).normalized()
    h = pb.head.copy()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ pb.matrix
    bpy.context.view_layer.update()
    if frame is not None:
        key_bone(arm, name, frame)


def char_mesh(arm):
    return next(c for c in arm.children if c.type == "MESH")


def head_height(arm):
    """World Z of the head bone tail, for camera framing."""
    pb = bone(arm, "Head")
    return (arm.matrix_world @ pb.tail).z


# ---------------------------------------------------------------------------
# Anatomy: procedural vessel network
# ---------------------------------------------------------------------------
VESSEL_CHAINS = [
    ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head"],   # not HeadTop_End: pokes out of the skull
    ["Spine2", "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandMiddle3", "LeftHandMiddle4"],
    ["Spine2", "RightShoulder", "RightArm", "RightForeArm", "RightHand", "RightHandMiddle1", "RightHandMiddle2", "RightHandMiddle3", "RightHandMiddle4"],
    ["Hips", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "LeftToe_End"],
    ["Hips", "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase", "RightToe_End"],
]
for _side in ("Left", "Right"):
    for _f in ("Thumb", "Index", "Ring", "Pinky"):
        VESSEL_CHAINS.append([f"{_side}Hand"] + [f"{_side}Hand{_f}{i}" for i in (1, 2, 3, 4)])


def bone_world(arm, name, tail=False):
    pb = bone(arm, name)
    return arm.matrix_world @ (pb.tail if tail else pb.head)


def fingertips(arm, side="Left"):
    """World positions of the 5 fingertips (tail of each *4 bone)."""
    return [bone_world(arm, f"{side}Hand{f}4", tail=True) for f in ("Thumb", "Index", "Middle", "Ring", "Pinky")]


def vessel_network(arm, body, n_branches=900, seed=7, inset=0.007, radius=0.006,
                   vein_share=0.35, name="Vessels"):
    """Grow a red branching vessel network inside a posed body mesh.
    Trunks follow the bone chains (spine, limbs, fingers). Branches run from a trunk
    to points just under the skin (denser near the surface, so the silhouette still
    reads), each splitting twice more. Arteries bright red, veins darker.
    Every spline runs trunk -> skin, so animating bevel_factor_start 0 -> 1 makes the
    vessels drain outward (towards skin and fingertips).
    Pose the armature BEFORE calling. Returns the curve object (static, not skinned)."""
    import random
    from mathutils.kdtree import KDTree
    rnd = random.Random(seed)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    mw = body.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    verts = [(mw @ v.co, (nm @ v.normal).normalized()) for v in me.vertices]
    ev.to_mesh_clear()
    kd = KDTree(len(verts))
    for i, (co, _) in enumerate(verts):
        kd.insert(co, i)
    kd.balance()
    from mathutils.bvhtree import BVHTree
    ev2 = body.evaluated_get(dg)
    me2 = ev2.to_mesh()
    me2.transform(mw)
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me2.vertices], [tuple(pl.vertices) for pl in me2.polygons])
    ev2.to_mesh_clear()

    def inside(p):
        loc, nrm, _, _ = bvh.find_nearest(p)
        return loc is None or (p - loc).dot(nrm) <= 0.002

    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = radius
    cd.bevel_resolution = 2
    cd.use_fill_caps = True
    cd.bevel_factor_mapping_start = "SPLINE"
    cd.bevel_factor_mapping_end = "SPLINE"
    art = mat_principled(name + "_Artery", (0.86, 0.03, 0.04), rough=0.3, sss=0.2)
    vein = mat_principled(name + "_Vein", (0.50, 0.02, 0.07), rough=0.35, sss=0.2)
    cd.materials.append(art)
    cd.materials.append(vein)

    def add(points, radii, mat_idx):
        sp = cd.splines.new("POLY")
        sp.points.add(len(points) - 1)
        for p, co, r in zip(sp.points, points, radii):
            p.co = (*co, 1)
            p.radius = r
        sp.material_index = mat_idx

    def jitter(a, b, amt):
        mid = a.lerp(b, rnd.uniform(0.35, 0.65))
        d = (b - a)
        perp = d.cross(Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))))
        if perp.length > 1e-6:
            mid += perp.normalized() * amt * d.length
        return mid

    def surface_target(p, rmin, rmax):
        found = kd.find_range(p, rmax)
        rnd.shuffle(found)
        for co, idx, dist in found:
            if dist < rmin:
                continue
            n = verts[idx][1]
            if n.dot(co - p) > 0.2 * dist:      # skin that faces away from the trunk
                t = co - n * inset
                if inside(p.lerp(t, 0.5)) and inside(p.lerp(t, 0.25)) and inside(p.lerp(t, 0.75)):
                    return t                    # whole branch stays inside the body
        return None

    # trunks
    samples = []
    for chain in VESSEL_CHAINS:
        try:
            pts = [bone_world(arm, b) for b in chain]   # heads only: *_End tails poke out of the body
        except KeyError:
            continue
        pts = [p for i, p in enumerate(pts) if i == 0 or (p - pts[i - 1]).length > 1e-4]
        if len(pts) < 2:
            continue
        thick = 1.6 if chain[0] in ("Hips", "Spine2") and len(chain) > 6 else 0.7
        add(pts, [thick * (1 - 0.6 * i / (len(pts) - 1)) for i in range(len(pts))], 0)
        add([p + Vector((0.012, 0.008, 0)) for p in pts], [thick * 0.8 * (1 - 0.6 * i / (len(pts) - 1)) for i in range(len(pts))], 1)
        for a, b in zip(pts, pts[1:]):
            n = max(1, int((b - a).length / 0.025))
            samples += [a.lerp(b, k / n) for k in range(n)]

    # branches -> twigs -> capillaries
    for _ in range(n_branches):
        p = rnd.choice(samples)
        e = surface_target(p, 0.02, rnd.uniform(0.08, 0.2))
        if e is None:
            continue
        mi = 1 if rnd.random() < vein_share else 0
        add([p, jitter(p, e, 0.25), e], [0.45, 0.3, 0.18], mi)
        for _k in range(2):
            s = p.lerp(e, rnd.uniform(0.5, 0.95))
            t = surface_target(s, 0.015, 0.06)
            if t is None:
                continue
            add([s, jitter(s, t, 0.3), t], [0.2, 0.13, 0.08], mi)
            if rnd.random() < 0.5:
                u = surface_target(t, 0.01, 0.035)
                if u is not None:
                    add([t, jitter(t, u, 0.4), u], [0.08, 0.06, 0.05], mi)
    o = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(o)
    print(f"vessel_network: {len(cd.splines)} splines")
    return o


def heart(loc, size=0.055, name="Heart"):
    """Simple glossy red heart blob (scale-keyframe it to pulse)."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=size, location=loc, segments=24, ring_count=16)
    h = bpy.context.active_object
    h.name = name
    h.scale = (0.9, 0.75, 1.1)
    h.rotation_euler = (0, math.radians(-25), math.radians(20))
    bpy.ops.object.shade_smooth()
    h.data.materials.append(mat_principled(name + "Mat", (0.75, 0.03, 0.05), rough=0.25, sss=0.3))
    return h


# ---------------------------------------------------------------------------
# Camera grammar
# ---------------------------------------------------------------------------
def camera(loc=(0, -5, 1.0), target=(0, 0, 1.0), lens=50, dof_target=None, fstop=2.8):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.sensor_width = 36
    cd.clip_end = 5000
    c = bpy.data.objects.new("Cam", cd)
    bpy.context.scene.collection.objects.link(c)
    bpy.context.scene.camera = c
    c.location = loc
    look_at(c, target)
    if dof_target is not None:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        if isinstance(dof_target, bpy.types.Object):
            cd.dof.focus_object = dof_target
        else:
            cd.dof.focus_distance = (Vector(dof_target) - Vector(loc)).length
    return c


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def _ease(kp_list, interp="BEZIER", easing="AUTO"):
    for kp in kp_list:
        kp.interpolation = interp
        kp.easing = easing
        kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def _fcurves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    # Blender 5.x layered actions
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                out.extend(cb.fcurves)
    return out


def ease_all(obj):
    for fc in _fcurves(obj):
        _ease(fc.keyframe_points)


def dolly(cam, axis_vec=None, dist=1.0, f0=1, f1=None, hold_end=True):
    """Signature move: a straight dolly along ONE axis (default: camera's view axis),
    eased in/out, no orbit, no lateral drift. Positive dist = push in."""
    sc = bpy.context.scene
    f1 = f1 or sc.frame_end
    if axis_vec is None:
        axis_vec = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    axis_vec = Vector(axis_vec).normalized()
    start = cam.location.copy()
    cam.location = start
    cam.keyframe_insert("location", frame=f0)
    cam.location = start + axis_vec * dist
    cam.keyframe_insert("location", frame=f1)
    ease_all(cam)
    return cam


def keyframe_path(cam, keys, target=None):
    """keys: list of (frame, (x,y,z)) ; optional target (object or point) tracked.
    Use for pull-back-and-up and tracking moves. Every key is eased."""
    for f, loc in keys:
        cam.location = loc
        cam.keyframe_insert("location", frame=f)
    if target is not None:
        con = cam.constraints.new("TRACK_TO")
        if isinstance(target, bpy.types.Object):
            con.target = target
        else:
            e = bpy.data.objects.new("CamTarget", None)
            bpy.context.scene.collection.objects.link(e)
            e.location = target
            con.target = e
        con.track_axis = "TRACK_NEGATIVE_Z"
        con.up_axis = "UP_Y"
    ease_all(cam)


def handheld(cam, amount=0.004, speed=0.6):
    """Very subtle drift so locked shots don't feel CG. Keep tiny (refs have ~0 lateral)."""
    for i in range(3):
        fc = cam.driver_add("rotation_euler", i)
        base = cam.rotation_euler[i]
        fc.driver.expression = f"{base:.5f} + noise.noise(({i * 10}+frame*{speed / 30:.4f}, 0, 0))*{amount}"


def whip_out(cam, f0, frames=6, deg=35, axis=2):
    """Exit move for a whip-pan transition: fast eased rotation at the END of a shot.
    Pair with whip_in on the next shot; motion blur sells it. Hard cuts are rare (~1/7)."""
    r = cam.rotation_euler.copy()
    cam.keyframe_insert("rotation_euler", frame=f0)
    r[axis] += math.radians(deg)
    cam.rotation_euler = r
    cam.keyframe_insert("rotation_euler", frame=f0 + frames)
    for fc in _fcurves(cam):
        if fc.data_path == "rotation_euler":
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.easing = "EASE_IN"


def whip_in(cam, frames=6, deg=35, axis=2, f0=1):
    r = cam.rotation_euler.copy()
    start = r.copy()
    start[axis] -= math.radians(deg)
    cam.rotation_euler = start
    cam.keyframe_insert("rotation_euler", frame=f0)
    cam.rotation_euler = r
    cam.keyframe_insert("rotation_euler", frame=f0 + frames)
    for fc in _fcurves(cam):
        if fc.data_path == "rotation_euler":
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.easing = "EASE_OUT"


# ---------------------------------------------------------------------------
# Props / overlays
# ---------------------------------------------------------------------------
def red_arrow(loc=(0, 0, 1), rot_deg=(0, 0, 0), scale=0.3, name="Arrow"):
    """Chunky glossy 3D arrow (used in sword short to show motion direction)."""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    pts = [(-0.25, 0), (0.25, 0), (0.25, 1.0), (0.55, 1.0), (0, 1.6), (-0.55, 1.0), (-0.25, 1.0)]
    verts_f = [bm.verts.new((x, y, 0.12)) for x, y in pts]
    verts_b = [bm.verts.new((x, y, -0.12)) for x, y in pts]
    bm.faces.new(verts_f)
    bm.faces.new(list(reversed(verts_b)))
    n = len(pts)
    for i in range(n):
        bm.faces.new((verts_f[i], verts_f[(i + 1) % n], verts_b[(i + 1) % n], verts_b[i]))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot_deg]
    o.scale = (scale,) * 3
    bev = o.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.03
    bev.segments = 3
    o.data.materials.append(mat_principled("ArrowRed", (0.9, 0.02, 0.02), rough=0.2))
    return o


def grow_curve(curve_obj, f0, f1):
    """Animate a curve 'drawing itself' (thread, vessel, distance line)."""
    cd = curve_obj.data
    cd.bevel_factor_start = 0.0
    cd.bevel_factor_end = 0.0
    cd.keyframe_insert("bevel_factor_end", frame=f0)
    cd.bevel_factor_end = 1.0
    cd.keyframe_insert("bevel_factor_end", frame=f1)


def tube_curve(points, radius=0.01, mat=None, name="Tube", smooth=False):
    """Poly tube through points. smooth=True makes it a NURBS curve (order 3) that
    flows through the start and end points, for organic threads and lines."""
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = radius
    cd.bevel_resolution = 4
    cd.use_fill_caps = True
    sp = cd.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, co in zip(sp.points, points):
        p.co = (*co, 1)
    if smooth:
        sp.type = "NURBS"
        sp.order_u = 3
        sp.use_endpoint_u = True
        sp.resolution_u = 16
    o = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        cd.materials.append(mat)
    return o


def hair_strand(p0, p1, radius, color=(0.42, 0.26, 0.12), wave=0.04, seed=3, name="Hair"):
    """A single human hair for macro shots, built so it reads as HAIR, not a brown rod.

    What sells it (lesson from viewer feedback on a flat-looking hair):
      * cuticle scales: overlapping saw-tooth bands along the strand (~0.1 x diameter apart)
        drive a bump, so highlights break up the way real hair does under a microscope
      * two highlights: a sharp white coat highlight + a broader warm one from the base layer
      * translucent amber edges, darker melanin core (subsurface + facing ramp)
      * a slight wave along its length (real hair is never a straight cylinder)
    Depth comes from the SHOT, not just the shader: run the strand diagonally through
    the focal plane (one end rising toward the lens and blurring, the other dipping behind
    the subject) so it overlaps things and casts a shadow. See SKILL.md, section 5.
    """
    import random
    rnd = random.Random(seed)
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = radius
    cd.bevel_resolution = 12
    cd.use_fill_caps = True
    sp = cd.splines.new("NURBS")
    n = 12
    sp.points.add(n - 1)
    ph1, ph2 = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
    for i, pt in enumerate(sp.points):          # built along local +X, then oriented
        t = i / (n - 1)
        pt.co = (t * L, math.sin(t * 5.1 + ph1) * wave * L * 0.3, math.sin(t * 3.3 + ph2) * wave * L * 0.2, 1)
    sp.order_u = 4
    sp.use_endpoint_u = True
    sp.resolution_u = 24
    o = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(o)
    o.location = p0
    o.rotation_euler = (p1 - p0).to_track_quat("X", "Z").to_euler()

    m = bpy.data.materials.new(name + "Mat")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.38           # broad warm (secondary) highlight
    p.inputs["Specular Tint"].default_value = (*_lin(tuple(min(1, c * 1.6) for c in color)), 1)
    p.inputs["Coat Weight"].default_value = 0.6          # sharp white (primary) highlight
    p.inputs["Coat Roughness"].default_value = 0.12
    p.inputs["Subsurface Weight"].default_value = 0.35
    p.inputs["Subsurface Radius"].default_value = (1.0, 0.55, 0.25)
    p.inputs["Subsurface Scale"].default_value = radius * 0.6
    # colour: darker core, lighter translucent rim
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.45
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*_lin(tuple(c * 0.7 for c in color)), 1)
    ramp.color_ramp.elements[1].color = (*_lin(tuple(min(1, c * 1.5) for c in color)), 1)
    nt.links.new(lw.outputs["Facing"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], p.inputs["Base Color"])
    # cuticle scales: saw bands along local X, wobbled so the scale edges are irregular
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.5 / radius
    nz.inputs["Detail"].default_value = 2
    mixv = nt.nodes.new("ShaderNodeVectorMath")
    mixv.operation = "MULTIPLY_ADD"
    mixv.inputs[1].default_value = (radius * 0.25,) * 3
    nt.links.new(nz.outputs["Color"], mixv.inputs[0])
    nt.links.new(tc.outputs["Object"], mixv.inputs[2])
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "X"
    wv.wave_profile = "SAW"
    period = 2 * radius * 0.12                           # scale spacing ~0.12 x diameter
    wv.inputs["Scale"].default_value = 2 * math.pi / (20 * period)
    wv.inputs["Distortion"].default_value = 0.0
    nt.links.new(mixv.outputs[0], wv.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = radius * 0.04
    nt.links.new(wv.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], p.inputs["Normal"])
    nt.links.new(bump.outputs[0], p.inputs["Coat Normal"])
    cd.materials.append(m)
    return o


def fill_card(cam, color=BLUE_MID, keys=((1, 1.0),), name="FillCard"):
    """A flat colour card glued to the lens, faded by keys [(frame, alpha), ...].
    Pure emission (unlit), so it is the SAME colour in every scene - use it to hand off
    between two worlds through a shared colour: end shot A on the card, start shot B on it.
    e.g. space -> dive into the atmosphere -> sky blue -> blue backdrop. Unlike a
    door-swing it keeps the palette and the motion continuous."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.parent = cam
    o.location = (0, 0, -0.2)
    o.scale = (0.4, 0.4, 1)
    m = mat_principled(name, (0, 0, 0), rough=1, emit=color, emit_strength=1.0)
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Specular IOR Level"].default_value = 0.0
    o.data.materials.append(m)
    for prop in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission"):
        setattr(o, prop, False)
    for f, a in keys:
        set_alpha(m, a, frame=f)
    return o


def brand_text(body="ZACK D FILMS", loc=(0, 0, 0), size=0.2, color=(0.15, 0.15, 0.15), name="Brand"):
    """Zack brands props (car door, armour, boat, field). Use YOUR channel name."""
    td = bpy.data.curves.new(name, "FONT")
    td.body = body
    td.size = size
    td.align_x = "CENTER"
    td.extrude = 0.002
    for f in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/verdanab.ttf"):
        if os.path.exists(f):
            td.font = bpy.data.fonts.load(f)
            break
    o = bpy.data.objects.new(name, td)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    td.materials.append(mat_principled(name + "Mat", color, rough=0.5))
    return o


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
def render_frames(out_dir, still_frame=None):
    sc = bpy.context.scene
    out_dir = bpy.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    if still_frame is not None:
        sc.frame_set(still_frame)
        sc.render.filepath = os.path.join(out_dir, f"still_{still_frame:04d}.png")
        bpy.ops.render.render(write_still=True)
        return sc.render.filepath
    sc.render.filepath = os.path.join(out_dir, "f_")
    bpy.ops.render.render(animation=True)
    return out_dir


def save(path):
    bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath(path))

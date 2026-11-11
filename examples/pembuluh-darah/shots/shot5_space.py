"""
Beat 5 (19-26 s, 210 frames): "Itu lebih dari dua kali keliling Bumi, atau seperempat jalan ke Bulan."

Emerges from cloud-white into orbit. The red line wraps the Earth twice, peels off into
space toward the Moon and stops 26% of the way (100,000 km of 384,400 km).
Camera: eased orbital rise, a long pull-back that reveals the Moon top-right, a short hold,
then a fast dive back into Earth's atmosphere that fills the frame with sky blue (hand-off to beat 6).
Scale: Earth radius 10 units, Moon radius 2.73 (true size ratio). The Moon distance is CHEATED to
24 Earth radii (true: 60.3) so both bodies read on a phone; the line still stops at 26% of the
way, so the proportion the narration states stays correct.

Textures (optional, used when present in assets/, otherwise procedural):
  earth_day.jpg  earth_clouds.jpg  earth_night.jpg  moon.jpg   (equirectangular)
Downloaded 2026-11-10 from NASA (public domain):
  earth_day.jpg   Blue Marble Next Generation, Dec 2004, topo+bathy 5400x2700 (assets.science.nasa.gov)
  earth_night.jpg Black Marble 2016, 3 km, resized 13500 -> 8192 px (assets.science.nasa.gov)
  moon.jpg        LRO colour map lroc_color_poles_4k.tif, CGI Moon Kit (svs.gsfc.nasa.gov)
  earth_clouds.jpg is not available on NASA's current site, so clouds stay procedural.

  blender -b --python shots/shot5_space.py -- --check
"""
import os, sys, math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common
from common import zdf, bpy, Vector
from mathutils import Matrix

a = common.args()
zdf.new_scene(seconds=7.0, samples=64, preview=a.preview)
sc = bpy.context.scene
A = common.ASSETS
R = 10.0
MOON_POS = Vector((300.0, 0.0, 523.0)).normalized() * 240.0   # 24 R (true 60.3 R), see docstring
MOON_R = 2.73
QUARTER = 0.26
LIGHT_DIR = Vector((-0.95, -0.2, 0.25)).normalized()   # direction TOWARD the sun


def tex(path, nt, colorspace=None):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    if colorspace:
        t.image.colorspace_settings.name = colorspace
    return t


# --- space world: black with stars (camera rays only) ---------------------------
w = sc.world
nt = w.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground")
tc = nt.nodes.new("ShaderNodeTexCoord")
vor = nt.nodes.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 260
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = 0.035
mr.inputs["From Max"].default_value = 0.0
mr.inputs["To Max"].default_value = 3.0
mr.clamp = True
nt.links.new(tc.outputs["Generated"], vor.inputs["Vector"])
nt.links.new(vor.outputs["Distance"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], bg.inputs["Strength"])
bg.inputs["Color"].default_value = (1, 1, 1, 1)
nt.links.new(bg.outputs[0], out.inputs[0])

# --- Earth ---------------------------------------------------------------------
def sphere(name, r, loc=(0, 0, 0), seg=128):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    return o


earth = sphere("Earth", R)
earth.rotation_euler = (math.radians(-18), 0, math.radians(200))
m = bpy.data.materials.new("EarthMat")
m.use_nodes = True
nt = m.node_tree
p = nt.nodes["Principled BSDF"]
p.inputs["Roughness"].default_value = 0.65
day = os.path.join(A, "earth_day.jpg")
if os.path.exists(day):
    nt.links.new(tex(day, nt).outputs[0], p.inputs["Base Color"])
else:   # procedural: noise continents, ocean, ice caps
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 10
    land = nt.nodes.new("ShaderNodeMath")
    land.operation = "GREATER_THAN"
    land.inputs[1].default_value = 0.53
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*zdf._lin((0.24, 0.42, 0.18)), 1)
    ramp.color_ramp.elements[1].color = (*zdf._lin((0.62, 0.52, 0.33)), 1)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*zdf._lin((0.03, 0.14, 0.38)), 1)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    absz = nt.nodes.new("ShaderNodeMath")
    absz.operation = "ABSOLUTE"
    ice = nt.nodes.new("ShaderNodeMath")
    ice.operation = "GREATER_THAN"
    ice.inputs[1].default_value = 0.82
    mix2 = nt.nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    mix2.inputs[7].default_value = (0.9, 0.92, 0.95, 1)
    norm = nt.nodes.new("ShaderNodeVectorMath")
    norm.operation = "NORMALIZE"
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], land.inputs[0])
    nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
    nt.links.new(land.outputs[0], mix.inputs[0])
    nt.links.new(ramp.outputs[0], mix.inputs[7])
    nt.links.new(tc.outputs["Object"], norm.inputs[0])
    nt.links.new(norm.outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], absz.inputs[0])
    nt.links.new(absz.outputs[0], ice.inputs[0])
    nt.links.new(ice.outputs[0], mix2.inputs[0])
    nt.links.new(mix.outputs[2], mix2.inputs[6])
    nt.links.new(mix2.outputs[2], p.inputs["Base Color"])
night = os.path.join(A, "earth_night.jpg")
if os.path.exists(night):
    # city lights only on the night side: strength = 1.2 * smoothstep(sun-facing 0.1 -> -0.15)
    # (the Black Marble map has a blue base that would tint the day side otherwise)
    t = tex(night, nt)
    nt.links.new(t.outputs[0], p.inputs["Emission Color"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = LIGHT_DIR
    dark = nt.nodes.new("ShaderNodeMapRange")
    dark.interpolation_type = "SMOOTHSTEP"
    dark.inputs["From Min"].default_value = 0.1
    dark.inputs["From Max"].default_value = -0.15
    dark.inputs["To Max"].default_value = 1.2
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    nt.links.new(dot.outputs["Value"], dark.inputs["Value"])
    nt.links.new(dark.outputs["Result"], p.inputs["Emission Strength"])
earth.data.materials.append(m)

clouds = sphere("Clouds", R * 1.008)
clouds.rotation_euler = earth.rotation_euler
cm = bpy.data.materials.new("CloudsMat")
cm.use_nodes = True
nt = cm.node_tree
p = nt.nodes["Principled BSDF"]
p.inputs["Base Color"].default_value = (1, 1, 1, 1)
p.inputs["Roughness"].default_value = 0.9
cpath = os.path.join(A, "earth_clouds.jpg")
if os.path.exists(cpath):
    nt.links.new(tex(cpath, nt, "Non-Color").outputs[0], p.inputs["Alpha"])
else:
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 4.5
    nz.inputs["Detail"].default_value = 8
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.5
    mr.inputs["From Max"].default_value = 0.75
    mr.inputs["To Max"].default_value = 0.85
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], p.inputs["Alpha"])
cm.surface_render_method = "DITHERED"
clouds.data.materials.append(cm)

atmo = sphere("Atmosphere", R * 1.035, seg=96)
am = bpy.data.materials.new("AtmoMat")
am.use_nodes = True
nt = am.node_tree
nt.nodes.clear()
o = nt.nodes.new("ShaderNodeOutputMaterial")
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (*zdf._lin((0.35, 0.65, 1.0)), 1)
em.inputs["Strength"].default_value = 2.5
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
lw = nt.nodes.new("ShaderNodeLayerWeight")
lw.inputs["Blend"].default_value = 0.25
pw = nt.nodes.new("ShaderNodeMath")
pw.operation = "POWER"
pw.inputs[1].default_value = 2.5
mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lw.outputs["Facing"], pw.inputs[0])
nt.links.new(pw.outputs[0], mx.inputs[0])
nt.links.new(tr.outputs[0], mx.inputs[1])
nt.links.new(em.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], o.inputs[0])
atmo.data.materials.append(am)
atmo.visible_shadow = False

# --- Moon ------------------------------------------------------------------------
moon = sphere("Moon", MOON_R, MOON_POS, seg=96)
mm = bpy.data.materials.new("MoonMat")
mm.use_nodes = True
nt = mm.node_tree
p = nt.nodes["Principled BSDF"]
p.inputs["Roughness"].default_value = 0.95
mpath = os.path.join(A, "moon.jpg")
if os.path.exists(mpath):
    nt.links.new(tex(mpath, nt).outputs[0], p.inputs["Base Color"])
else:
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3
    nz.inputs["Detail"].default_value = 12
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.18, 0.18, 0.19, 1)
    ramp.color_ramp.elements[1].color = (0.55, 0.55, 0.56, 1)
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 6
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], p.inputs["Base Color"])
    nt.links.new(vo.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], p.inputs["Normal"])
moon.data.materials.append(mm)

# --- sun: lights the camera-facing side of both bodies ---------------------------
sun = zdf.sun(energy=4.0, rot_deg=(0, 0, 0), color=(1.0, 0.98, 0.95), angle_deg=0.5)
light_dir = LIGHT_DIR
sun.rotation_euler = (-light_dir).to_track_quat("-Z", "Y").to_euler()

# --- the line: 2 wraps (slight helix), then off toward the Moon --------------------
tilt = Matrix.Rotation(math.radians(16), 3, Vector((1, 0, 0)))
pts = []
TURNS, N = 2.0, 160
for i in range(N + 1):
    th = math.radians(-60) + 2 * math.pi * TURNS * i / N
    rr = R * 1.02
    pts.append(tilt @ Vector((rr * math.cos(th), rr * math.sin(th), (i / N - 0.5) * 0.9)))
wrap_len = sum((pts[i + 1] - pts[i]).length for i in range(N))
tangent = (pts[-1] - pts[-2]).normalized()
mdir = MOON_POS.normalized()
end = mdir * (QUARTER * MOON_POS.length)
p1 = pts[-1] + tangent * 18
p2 = p1.lerp(end, 0.35) + mdir * 10
dep = [p1, p2, p2.lerp(end, 0.5), end]
all_pts = pts + dep
total = wrap_len + sum((all_pts[i + 1] - all_pts[i]).length for i in range(N, len(all_pts) - 1))
line = zdf.tube_curve([tuple(v) for v in all_pts], radius=0.06, mat=zdf.mat_blood("SpaceLine"), name="SpaceLine", smooth=True)
line.data.bevel_factor_mapping_end = "SPLINE"
wrap_frac = wrap_len / total
for f, v in ((1, 0.0), (95, wrap_frac), (104, wrap_frac + 0.01), (184, 1.0)):
    line.data.bevel_factor_end = v
    line.data.keyframe_insert("bevel_factor_end", frame=f)
for f, r in ((100, 0.06), (150, 0.35), (205, 1.3)):          # thicken as we pull back
    line.data.bevel_depth = r
    line.data.keyframe_insert("bevel_depth", frame=f)
zdf.ease_all(line.data)
# line glows a little so it reads against black
lm = bpy.data.materials["SpaceLine"]
pr = lm.node_tree.nodes["Principled BSDF"]
pr.inputs["Emission Color"].default_value = (*zdf._lin((0.9, 0.05, 0.06)), 1)
pr.inputs["Emission Strength"].default_value = 1.5

# --- camera ------------------------------------------------------------------------
cam = zdf.camera(loc=(0, -30, 6), target=(0, 0, 0), lens=40)
cam.data.clip_end = 5000
look = bpy.data.objects.new("Look", None)
sc.collection.objects.link(look)
con = cam.constraints.new("TRACK_TO")
con.target = look
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"
final_look = MOON_POS * 0.5
final_cam = final_look + Vector((0, -330, 0))
keys = [(1, Vector((-12, -24, 4)), Vector((0, 0, 0))),
        (50, Vector((-4, -30, 10)), Vector((0, 0, 0))),
        (95, Vector((8, -34, 16)), Vector((2, 0, 3)))]
# pull-back in log space so it feels like one smooth zoom-out
for i, f in enumerate((116, 134, 150, 166, 178)):   # reveal finishes at f178, holds to f194
    t = (i + 1) / 5
    d = 34 * (330 / 34) ** t
    look_i = Vector((2, 0, 3)).lerp(final_look, t ** 2.2)    # keep Earth framed until far enough out
    cam_i = look_i + Vector((0, -d, 0)) + Vector((8, 0, 16)) * (1 - t)
    keys.append((f, cam_i, look_i))
keys.append((194, final_cam + Vector((0, 10, 0)), final_look))   # slow creep while holding on the Moon
# hand-off to beat 6 (replaces the old door-swing, which viewers found jarring: it jumped
# from black space to the blue room with a flat card flip). The camera dives back down to
# Earth, into the bright atmosphere, and the frame fills with sky blue. Beat 6 opens on the
# SAME blue card and drops out of the sky onto the man, so colour and motion carry across.
keys.append((203, Vector((6, -70, 14)), Vector((0, 0, 0))))
keys.append((210, Vector((1.5, -12.6, 3.2)), Vector((0, 0, 0))))   # inside the atmosphere glow
for f, c, l in keys:
    cam.location = c
    cam.keyframe_insert("location", frame=f)
    look.location = l
    look.keyframe_insert("location", frame=f)
zdf.ease_all(cam)
zdf.ease_all(look)

# white-out at the start (continues beat 4's cloud deck), fading in 12 frames
zdf.fill_card(cam, (1, 1, 1), [(1, 1.0), (3, 1.0), (14, 0.0)], name="WhiteIn")
# sky-blue out at the end: the atmosphere swallows the frame (beat 6 starts on this colour)
zdf.fill_card(cam, zdf.BLUE_MID, [(1, 0.0), (203, 0.0), (209, 1.0)], name="BlueOut")

print(f"SPACE wrap fraction {wrap_frac:.3f}; line end at {end.length / MOON_POS.length:.0%} of the way to the Moon;"
      f" textures: {[n for n in ('earth_day.jpg', 'earth_clouds.jpg', 'earth_night.jpg', 'moon.jpg') if os.path.exists(os.path.join(A, n))] or 'none (procedural)'}")
lit = Vector((-12, -24, 4)).normalized().dot(light_dir)
print(f"SPACE start view lit fraction ~{(1 + lit) / 2:.0%}")
common.finish(a, "beat5", [
    (20, [("earth", Vector((0, 0, 0))), ("earth top", Vector((0, 0, R)))]),
    (95, [("earth", Vector((0, 0, 0))), ("wrap end", pts[-1])]),
    (121, [("earth", Vector((0, 0, 0)))]),
    (150, [("earth", Vector((0, 0, 0))), ("line end", end)]),
    (170, [("earth", Vector((0, 0, 0))), ("moon", MOON_POS)]),
    (186, [("earth", Vector((0, 0, 0))), ("moon", MOON_POS), ("line end", end)]),
    (194, [("earth", Vector((0, 0, 0))), ("moon", MOON_POS), ("line end", end)]),
    (203, [("earth", Vector((0, 0, 0)))]),
])

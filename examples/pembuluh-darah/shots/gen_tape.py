#!/usr/bin/env python3
"""Generate the giant wall tape-measure textures for the beat 2/4 room.
Run with system Python (needs Pillow):  python shots/gen_tape.py
Writes assets/tape_ltr.png (0 at the left end) and assets/tape_rtl.png (0 at the right end,
glyphs still upright) - one per side wall so both read correctly from inside the room."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
LENGTH_CM = 500
PX_PER_CM = 12
W, H = LENGTH_CM * PX_PER_CM, 150
YELLOW, EDGE, INK, RED = (242, 194, 27), (176, 132, 0), (25, 25, 25), (200, 16, 40)


def font(size, bold=True):
    for f in ("arialbd.ttf" if bold else "arial.ttf", "verdanab.ttf", "DejaVuSans-Bold.ttf"):
        for d in ("C:/Windows/Fonts", "/usr/share/fonts/truetype/dejavu"):
            p = os.path.join(d, f)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def make(reverse):
    im = Image.new("RGB", (W, H), YELLOW)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, 5], fill=EDGE)
    d.rectangle([0, H - 6, W - 1, H - 1], fill=EDGE)
    small, metre = font(34), font(78)
    for cm in range(0, LENGTH_CM + 1):
        x = (LENGTH_CM - cm if reverse else cm) * PX_PER_CM
        x = min(max(x, 2), W - 3)
        if cm % 100 == 0:
            d.rectangle([x - 2, 6, x + 2, H - 7], fill=RED)
        elif cm % 10 == 0:
            d.rectangle([x - 1, 6, x + 1, 70], fill=INK)
        elif cm % 5 == 0:
            d.line([x, 6, x, 46], fill=INK, width=2)
        else:
            d.line([x, 6, x, 28], fill=INK, width=1)
        if cm % 10 == 0 and cm % 100 not in (0, 90) and 0 < cm < LENGTH_CM:  # 90 sits under the metre label
            t = str(cm % 100)
            tw = d.textlength(t, font=small)
            d.text((x - tw / 2, 76), t, fill=INK, font=small)
        if cm % 100 == 0 and cm > 0:
            t = f"{cm // 100} m"
            tw = d.textlength(t, font=metre)
            tx = x - tw - 14 if not reverse else x + 14
            if not reverse and cm == LENGTH_CM:
                tx = x - tw - 14
            d.text((tx, 40), t, fill=RED, font=metre)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "tape_rtl.png" if reverse else "tape_ltr.png")
    im.save(p)
    print("wrote", p)


if __name__ == "__main__":
    make(False)
    make(True)

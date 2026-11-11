#!/usr/bin/env python3
"""
fetch_space_textures.py - download NASA Earth/Moon maps (public domain) for space shots.

    python fetch_space_textures.py assets/

Writes (equirectangular):
  earth_day.jpg    Blue Marble Next Generation, December, topo + bathy, 5400x2700
  earth_night.jpg  Black Marble 2016 city lights, resized to 8192 px wide
  moon.jpg         LRO colour map (CGI Moon Kit, lroc_color_poles_4k.tif) converted to JPEG

There is no current NASA cloud map URL that works, so zdf/shot scripts draw clouds procedurally.
NASA imagery is public domain; credit "NASA" in your video description.
Needs Pillow. Files already present are skipped.
"""
import os, sys, urllib.request

SRC = {
    "earth_day.jpg": "https://assets.science.nasa.gov/content/dam/science/esd/eo/images/bmng/"
                     "bmng-topography-bathymetry/december/world.topo.bathy.200412.3x5400x2700.jpg",
    "earth_night.jpg": "https://assets.science.nasa.gov/content/dam/science/esd/eo/images/imagerecords/"
                       "144000/144898/BlackMarble_2016_3km.jpg",
    "moon.jpg": "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_poles_4k.tif",
}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "assets"
    os.makedirs(out, exist_ok=True)
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None            # Black Marble is 13500x6750
    for name, url in SRC.items():
        dst = os.path.join(out, name)
        if os.path.exists(dst):
            print("have", dst)
            continue
        tmp = dst + ".download" + os.path.splitext(url)[1]
        print("get ", url)
        req = urllib.request.Request(url, headers={"User-Agent": "zdf-texture-fetch/1.0"})
        with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
        im = Image.open(tmp).convert("RGB")
        if im.width > 8192:
            im = im.resize((8192, 4096), Image.LANCZOS)
        im.save(dst, quality=92)
        os.remove(tmp)
        print("wrote", dst, im.size)


if __name__ == "__main__":
    main()

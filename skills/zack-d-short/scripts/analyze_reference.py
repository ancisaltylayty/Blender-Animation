#!/usr/bin/env python3
"""
analyze_reference.py - study reference shorts the way this skill was built.

For each YouTube URL / id (or local .mp4):
  * downloads video + auto-subs (English, or --lang xx) (yt-dlp) into <out>/vids
  * contact sheets at 2 fps, 8x4 tiles (16 s per sheet) -> <out>/sheets/<id>_N.jpg
  * hard-cut times (ffmpeg scdet, threshold 8)
  * integrated loudness (EBU R128)
  * clean transcript, word count, words/second
  * edge + centre colour of the frame at 25% (backdrop check)
Writes <out>/report.md. Then READ every sheet image and write a beat table
(time | caption | what is on screen | camera move | transition) per video.

Usage: python analyze_reference.py OUT_DIR URL_OR_ID [URL_OR_ID ...] [--lang id]
Needs: yt-dlp, ffmpeg/ffprobe on PATH, Pillow.
"""
import os, re, subprocess, sys

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def vid_id(x):
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", x)
    return m.group(1) if m else os.path.splitext(os.path.basename(x))[0]

def transcript(srt):
    if not os.path.exists(srt):
        return ""
    lines = []
    for b in open(srt, encoding="utf-8").read().strip().split("\n\n"):
        for x in [l.strip() for l in b.split("\n")[2:] if l.strip()]:
            if x not in lines[-2:]:
                lines.append(x)
    return " ".join(lines)

def main():
    args = sys.argv[1:]
    lang = "en"
    if "--lang" in args:                 # subtitle language, e.g. --lang id for Indonesian refs
        k = args.index("--lang"); lang = args[k + 1]; del args[k:k + 2]
    out = args[0]
    items = args[1:]
    vd, sd = os.path.join(out, "vids"), os.path.join(out, "sheets")
    os.makedirs(vd, exist_ok=True); os.makedirs(sd, exist_ok=True)
    rep = ["# Reference analysis\n"]
    for it in items:
        i = vid_id(it)
        mp4 = it if it.endswith(".mp4") else os.path.join(vd, i + ".mp4")
        if not os.path.exists(mp4):
            run(["yt-dlp", "-q", "--no-warnings", "-f", "bv*[height<=1280]+ba/b[height<=1280]/b",
                 "--merge-output-format", "mp4", "--write-auto-subs", "--sub-langs", lang,
                 "--convert-subs", "srt", "-o", os.path.join(vd, "%(id)s.%(ext)s"), "--",
                 f"https://www.youtube.com/watch?v={i}"])
        title = run(["yt-dlp", "--no-warnings", "--skip-download", "--print", "%(title)s | %(view_count)s views", "--", i]).stdout.strip() if not it.endswith(".mp4") else i
        dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4]).stdout.strip() or 0)
        run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "fps=2,scale=200:-1,tile=8x4",
             os.path.join(sd, f"{i}_%d.jpg")])
        sc = run(["ffmpeg", "-nostats", "-i", mp4, "-vf", "scdet=threshold=8:sc_pass=0", "-an", "-f", "null", "-"]).stderr
        cuts = [float(x) for x in re.findall(r"lavfi\.scd\.time: ([\d.]+)", sc)]
        lu = re.findall(r"I:\s+(-?[\d.]+) LUFS", run(["ffmpeg", "-nostats", "-i", mp4, "-af", "ebur128", "-f", "null", "-"]).stderr)
        txt = transcript(os.path.join(vd, i + f".{lang}.srt"))
        n = len(txt.split())
        png = os.path.join(sd, f"{i}_probe.png")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur * 0.25:.2f}", "-i", mp4, "-frames:v", "1", png])
        cols = ""
        try:
            from PIL import Image
            im = Image.open(png).convert("RGB"); w, h = im.size
            cols = f"edge {im.getpixel((8, h // 3))}  top-centre {im.getpixel((w // 2, 12))}"
        except Exception as e:
            cols = f"(colour probe failed: {e})"
        sheets = sorted(f for f in os.listdir(sd) if f.startswith(i + "_") and f.endswith(".jpg"))
        rep += [f"## {i} - {title}",
                f"- duration {dur:.1f}s, words {n}, {n / dur if dur else 0:.2f} words/s",
                f"- hard cuts ({len(cuts)}): {', '.join(f'{c:.1f}' for c in cuts) or 'none (one continuous camera)'}",
                f"- loudness {lu[-1] if lu else '?'} LUFS",
                f"- colours: {cols}",
                f"- sheets (2 fps, cell = 0.5 s, 32 cells = 16 s): {', '.join(sheets)}",
                f"- transcript: {txt}", ""]
    open(os.path.join(out, "report.md"), "w", encoding="utf-8").write("\n".join(rep))
    print("\n".join(rep))

if __name__ == "__main__":
    main()

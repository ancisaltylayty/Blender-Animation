#!/usr/bin/env python3
"""
assemble.py - join the rendered beats into one 960-frame short (optional door-swing,
off by default), then hand off to the skill's finish.py
(bloom/vignette/grain, captions, audio mix, -12 LUFS).

  python shots/assemble.py                       # final renders in renders/beatN/
  python shots/assemble.py --preview             # uses renders/beatN_preview/
  python shots/assemble.py --voice voice.wav --words words.json --music bed.wav --sfx sfx.wav

Beat order and frame counts must match script.md:
  beat1 135, beat2 90, beat3 195, beat4 150, beat5 210, beat6 180 (beats 6+7)  = 960
"""
import argparse, glob, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINISH = os.path.join(os.environ.get("ZDF_SCRIPTS") or os.path.join(ROOT, "..", "..", "skills", "zack-d-short", "scripts"), "finish.py")
BEATS = [("beat1", 135), ("beat2", 90), ("beat3", 195), ("beat4", 150), ("beat5", 210), ("beat6", 180)]
SWING_INTO = None        # e.g. "beat6" to add a door-swing into that beat. Off: beat 5 -> 6 is a
                         # continuous dive into the sky-blue card (a door-swing from black space
                         # into the blue room read as a jarring flip).
SWING_N = 7              # frames out + frames in


def door_swing(S, N=SWING_N):
    """ffmpeg perspective filter: frames [S-N, S) swing away on a left hinge,
    frames [S, S+N) swing in on a right hinge. Outside the card is black."""
    p = f"((on-{S - N}+1)/{N})"            # 0->1 during swing-out
    q = f"(1-(on-{S}+1)/{N})"              # 1->0 during swing-in
    out_ = f"between(on,{S - N},{S - 1})"
    in_ = f"between(on,{S},{S + N - 1})"
    x0 = f"if({in_},W*0.92*{q},0)"
    y0 = f"if({in_},H*0.12*{q},0)"
    x2 = x0
    y2 = f"if({in_},H*(1-0.12*{q}),H)"
    x1 = f"if({out_},W*(1-0.92*{p}),W)"
    y1 = f"if({out_},H*0.12*{p},0)"
    x3 = x1
    y3 = f"if({out_},H*(1-0.12*{p}),H)"
    return (f"perspective=x0='{x0}':y0='{y0}':x1='{x1}':y1='{y1}':x2='{x2}':y2='{y2}':x3='{x3}':y3='{y3}'"
            f":sense=destination:eval=frame:interpolation=cubic")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "renders", "pembuluh_darah.mp4"))
    ap.add_argument("--voice"); ap.add_argument("--music"); ap.add_argument("--sfx")
    ap.add_argument("--words"); ap.add_argument("--text")
    a = ap.parse_args()

    seq = os.path.join(ROOT, "renders", "_assembled")
    shutil.rmtree(seq, ignore_errors=True)
    os.makedirs(seq)
    n, S = 0, None
    for beat, count in BEATS:
        d = os.path.join(ROOT, "renders", beat + ("_preview" if a.preview else ""))
        frames = sorted(glob.glob(os.path.join(d, "f_*.png")))
        if len(frames) != count:
            sys.exit(f"{beat}: expected {count} frames in {d}, found {len(frames)}")
        if beat == SWING_INTO:
            S = n
        for f in frames:
            n += 1
            dst = os.path.join(seq, f"f_{n:04d}.png")
            try:
                os.link(f, dst)
            except OSError:
                shutil.copy2(f, dst)
    print(f"{n} frames assembled; door-swing at frame {S}" if S else f"{n} frames assembled; no door-swing")

    joined = os.path.join(ROOT, "renders", "_joined.mp4")
    # perspective repeats edge pixels outside the card: a black border makes that black
    vf = (f"pad=1088:1928:4:4:black,{door_swing(S)},"
          f"crop=1080:1920:4:4,format=yuv420p") if S else "format=yuv420p"   # border cropped off after the warp
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-i", os.path.join(seq, "f_%04d.png"),
                    "-vf", vf, "-c:v", "libx264", "-crf", "10", "-preset", "slow", joined], check=True)
    cmd = [sys.executable, FINISH, "--frames", joined, "--out", a.out]
    for k in ("voice", "music", "sfx", "words", "text"):
        v = getattr(a, k)
        if v:
            cmd += [f"--{k}", v]
    subprocess.run(cmd, check=True)
    print("done:", a.out)


if __name__ == "__main__":
    main()

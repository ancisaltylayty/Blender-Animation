#!/usr/bin/env python3
"""
finish.py - turn rendered PNG frames + narration into a finished Zack-D-style short.

Steps: frames -> mp4 (30 fps) -> "real camera" post (bloom, vignette, grain)
       -> burned-in 1-3 word captions -> narration/music/SFX mix -> loudness to ~-12 LUFS.

Usage
  python finish.py --frames "renders/all/f_%04d.png" --out short.mp4 \
      --voice voice.wav [--music bed.wav] [--sfx sfx.wav] \
      (--words words.json | --text script.txt) [--lang id|en] [--no-post]

--lang id (default) uses Indonesian phrase rules for captions and syllable timing;
--lang en uses the English rules the style was measured on.

words.json : [{"word": "If", "start": 0.12, "end": 0.30}, ...]  (Whisper word timestamps)
script.txt : plain narration; timings are spread over the voice length by syllables
             (use only when no word timestamps exist; Whisper gives better sync).

Captions measured from the references:
  font Verdana Bold, white, thin black outline + soft drop shadow, centred,
  baseline at ~80% of frame height, cap height ~2.7% of frame height,
  1-3 words per caption, phrase-aligned, as spoken (lower case except sentence starts),
  no full stops/commas; keep '?' on questions. One caption replaces the next with no fade.
"""
import argparse, json, os, re, subprocess, sys, tempfile, shutil

W, H, FPS = 1080, 1920, 30
FONT = "Verdana"
FONT_SIZE = 80          # ASS size at 1080x1920 (measured: ~3.4% of width per character)
MARGIN_V = 360          # baseline ~ 80% down the frame
OUTLINE, SHADOW = 3, 3
TARGET_LUFS = -12       # refs: -7 .. -15, median about -12

# Per-language caption rules.
#   break: a caption may close BEFORE these function words (once it holds a content word)
#   keep:  these stick to the word before them ("laid them", "darah kamu", "tubuh ini")
#   lead:  always start a new caption (quantifiers that open a noun phrase)
#   trail: never leave these at the END of a caption; they move to the next one
#          ("all of the | blood" -> "all of | the blood", "dari | rambut" not "dari rambut" split)
LANG = {
    "en": dict(
        brk=set("""and but or so that which who when where if as then because
to into onto from with without of for by at in on over under across through
until after before while is are was were would could should will can
all the a an your my his her their them it you this these those every some
about not just very than like even also only out up down off away back they we he she i""".split()),
        keep=set("them it him her me us".split()),
        lead=set(),
        trail=set("the a an your my his her their its our this these those every some".split())),
    "id": dict(
        brk=set("""yang dan atau tapi tetapi namun karena sebab untuk dari ke di dengan pada dalam
bahwa jika kalau kalo seperti hingga sampai lalu kemudian agar supaya saat ketika sekitar
hampir kurang setiap semua seluruh para juga hanya cuma bisa akan sudah sedang masih
tidak bukan adalah ialah maka sehingga sebelum sesudah setelah selama antara menuju melalui
lewat tanpa oleh bagi tentang jadi makin semakin terus""".split()),
        keep=set("ini itu kamu kita saja pun lagi sekali banget".split()),
        lead=set("semua setiap seluruh para".split()),     # always open a caption: "Kalau | semua pembuluh darahmu"
        trail=set("""yang dan atau tapi di ke dari untuk dengan pada dalam seperti sampai hingga
para setiap semua seluruh sekitar lebih jadi""".split())),
}


def sh(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return float(out.strip())


def syllables(w, lang="id"):
    digits = re.sub(r"\D", "", w)
    if digits:                               # "100.000" is spoken "seratus ribu"
        return 2 + len(digits) // 2
    w = re.sub(r"[^a-z]", "", w.lower())
    if not w:
        return 1
    if lang == "id":                         # Indonesian: one syllable per vowel, diphthongs count once
        return max(1, len(re.findall(r"ai|au|oi|ei|[aeiou]", w)))
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1:
        n -= 1
    return max(1, n)


def words_from_text(text, total, lang="id", t0=0.12):
    toks = text.split()
    weights = [syllables(t, lang) + 0.6 for t in toks]
    # pause after sentence ends
    for i, t in enumerate(toks):
        if re.search(r"[.?!]$", t):
            weights[i] += 1.2
        elif t.endswith(","):
            weights[i] += 0.5
    scale = (total - t0 - 0.13) / sum(weights)
    out = []
    for tok, wgt in zip(toks, weights):
        d = wgt * scale
        out.append({"word": tok, "start": t0, "end": t0 + d * 0.85})
        t0 += d
    return out


def chunk(words, lang="id"):
    """Group into 1-3 word captions the way the references do:
    'If you somehow | removed | all of | the blood vessels | in your body | and tied | them together'.
    A caption closes at punctuation, at 3 words, or before a function word once it
    already holds a content word."""
    def bare(t):
        return re.sub(r"[^\w'-]", "", t).lower()
    R = LANG[lang]
    groups, cur = [], []
    for w in words:
        b = bare(w["word"])
        has_content = any(bare(x["word"]) not in R["brk"] for x in cur)
        keep = (b in R["keep"] and len(cur) < 3) or (lang == "en" and b in ("to", "of") and len(cur) == 1)   # "end to end", "out of"
        if cur and (len(cur) == 3 or b in R["lead"] or (b in R["brk"] and has_content and not keep)):
            groups.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.?!,;:]$", w["word"]):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    # lone word with no punctuation joins a short following caption: "branch | into smaller"
    i = 0
    while i < len(groups) - 1:
        g, n = groups[i], groups[i + 1]
        if len(g) == 1 and len(n) <= 2 and not re.search(r"[.?!,;:]$", g[0]["word"]):
            groups[i:i + 2] = [g + n]
        i += 1
    # sentence-final orphan borrows a word: "untuk satu putaran | penuh." -> "untuk satu | putaran penuh."
    for i in range(1, len(groups)):
        g, p = groups[i], groups[i - 1]
        if len(g) == 1 and len(p) == 3 and re.search(r"[.?!]$", g[0]["word"])                 and not re.search(r"[.?!,;:]$", p[-1]["word"]):
            g.insert(0, p.pop())
    # "all of the | blood vessels" -> "all of | the blood vessels"; "pipa yang | makin kecil" -> "pipa | yang makin kecil"
    for i in range(len(groups) - 1):
        g, n = groups[i], groups[i + 1]
        if len(g) > 1 and len(n) < 3 and bare(g[-1]["word"]) in R["trail"] and not re.search(r"[.?!,;:]$", g[-1]["word"]):
            n.insert(0, g.pop())
    return groups


def ts(sec):
    sec = max(0, sec)
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(groups, path, total):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ZDF,{FONT},{FONT_SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,{OUTLINE},{SHADOW},2,60,60,{MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    prev_end_punct = True
    for i, g in enumerate(groups):
        start = g[0]["start"]
        end = groups[i + 1][0]["start"] if i + 1 < len(groups) else min(total, g[-1]["end"] + 0.6)
        raw = " ".join(w["word"] for w in g)
        txt = re.sub(r"[.,;:!]", "", raw).replace("?", "")
        if prev_end_punct:
            txt = txt[:1].upper() + txt[1:]
        if raw.rstrip().endswith("?"):
            txt += "?"
        prev_end_punct = bool(re.search(r"[.?!]$", raw.strip()))
        lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},ZDF,,0,0,0,,{txt}")
    open(path, "w", encoding="utf-8").write(head + "\n".join(lines) + "\n")
    return path


def ff_path(p):
    """Escape a Windows path for use inside an ffmpeg filter argument."""
    return p.replace("\\", "/").replace(":", "\\:")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True, help='e.g. "renders/all/f_%%04d.png" or an .mp4')
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice")
    ap.add_argument("--music")
    ap.add_argument("--sfx")
    ap.add_argument("--words")
    ap.add_argument("--text")
    ap.add_argument("--lang", default="id", choices=sorted(LANG), help="caption language rules (default: id)")
    ap.add_argument("--no-post", action="store_true")
    ap.add_argument("--start", type=int, default=1)
    a = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="zdf_")
    vin = ["-i", a.frames] if a.frames.endswith(".mp4") else ["-framerate", str(FPS), "-start_number", str(a.start), "-i", a.frames]

    # 1) post: bloom (screen-blended blurred copy), vignette, fine animated grain
    post = (f"[0:v]scale={W}:{H}:flags=lanczos,format=gbrp,split[a][b];"
            f"[b]scale={W // 4}:{H // 4},gblur=sigma=10,scale={W}:{H}[g];"
            f"[a][g]blend=all_mode=screen:all_opacity=0.16,"
            f"vignette=angle=PI/9,noise=alls=3:allf=t,format=yuv420p[v]")
    if a.no_post:
        post = f"[0:v]scale={W}:{H},format=yuv420p[v]"

    total = None
    if a.voice:
        total = probe_duration(a.voice)
    graph = post
    if a.words or a.text:
        if a.words:
            words = json.load(open(a.words, encoding="utf-8"))
        else:
            if total is None:
                sys.exit("--text needs --voice to know the timing")
            words = words_from_text(open(a.text, encoding="utf-8").read(), total, a.lang)
        if total is None:
            total = words[-1]["end"] + 0.6
        ass = write_ass(chunk(words, a.lang), os.path.join(tmp, "caps.ass"), total)
        fontsdir = "C:/Windows/Fonts" if os.name == "nt" else "/usr/share/fonts"
        graph = post.replace("[v]", "[p]") + f";[p]subtitles='{ff_path(ass)}':fontsdir='{ff_path(fontsdir)}'[v]"

    cmd = ["ffmpeg", "-y", *vin]
    audio_inputs = [x for x in (a.voice, a.music, a.sfx) if x]
    for x in audio_inputs:
        cmd += ["-i", x]
    fc = graph
    if audio_inputs:
        # voice 0 dB, music -16 dB under voice (+3 dB vs "quiet bed"), SFX -6 dB; then loudnorm
        idx = 1
        labels = []
        for x, g in ((a.voice, 0), (a.music, -16), (a.sfx, -6)):
            if not x:
                continue
            fc += f";[{idx}:a]volume={g}dB[a{idx}]"
            labels.append(f"[a{idx}]")
            idx += 1
        fc += f";{''.join(labels)}amix=inputs={len(labels)}:normalize=0,loudnorm=I={TARGET_LUFS}:TP=-1:LRA=5[aout]"
        cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    else:
        cmd += ["-filter_complex", fc, "-map", "[v]"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-r", str(FPS), "-movflags", "+faststart", a.out]
    sh(cmd)
    shutil.rmtree(tmp, ignore_errors=True)
    print("done:", a.out)


if __name__ == "__main__":
    main()

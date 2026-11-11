#!/usr/bin/env python3
"""
transcribe.py - narration audio -> words.json (word timestamps) for finish.py captions.

    python transcribe.py voice.wav words.json            # Indonesian (default)
    python transcribe.py voice.wav words.json --lang en
    python transcribe.py voice.wav words.json --model large-v3 --script narasi.txt

Needs:  pip install faster-whisper   (the model downloads on first run)

--script narasi.txt  replaces Whisper's spelling with your script's words when the counts
                     match (keeps your punctuation, "100.000", names), timing stays Whisper's.
Output format (what finish.py --words expects):
    [{"word": "Kalau", "start": 0.12, "end": 0.40}, ...]
"""
import argparse, json, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--lang", default="id")
    ap.add_argument("--model", default="small", help="tiny/base/small/medium/large-v3")
    ap.add_argument("--script", help="narration text; its words replace Whisper's when counts match")
    a = ap.parse_args()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("pip install faster-whisper")
    model = WhisperModel(a.model, device="auto", compute_type="auto")
    segs, _ = model.transcribe(a.audio, language=a.lang, word_timestamps=True, vad_filter=True)
    words = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
             for s in segs for w in (s.words or []) if w.word.strip()]
    if a.script:
        mine = open(a.script, encoding="utf-8").read().split()
        if len(mine) == len(words):
            for w, m in zip(words, mine):
                w["word"] = m
        else:
            print(f"note: script has {len(mine)} words, Whisper heard {len(words)}; kept Whisper's text."
                  " Fix words.json by hand if a caption is misspelled.")
    json.dump(words, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(words)} words -> {a.out}")


if __name__ == "__main__":
    main()

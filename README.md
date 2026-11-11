# Short 3D Gaya Zack D: Skill Claude Code (Bahasa Indonesia)

Skill [Claude Code](https://claude.com/claude-code) untuk membuat video pendek 3D vertikal bergaya penjelas sains: latar biru langit, satu subjek realistis, kamera yang terus bergerak halus, overlay merah/hijau/magenta yang datar dan mencolok, dan caption 1–3 kata. Semuanya dibangun dengan **Blender + Python + ffmpeg**. Narasi dan caption dalam **Bahasa Indonesia**.

Gaya ini dibedah frame per frame dari 9 short Zack D. Films (113–256 juta views): kecepatan narasi, jumlah cut, warna latar, posisi caption, dan loudness diukur, bukan ditebak. Hasil ukurnya ada di [`skills/zack-d-short/references/video_breakdowns.md`](skills/zack-d-short/references/video_breakdowns.md).

> Proyek komunitas, **tidak berafiliasi** dengan Zack D. Films. Pakai untuk belajar gaya, lalu buat cerita dan identitas channel kamu sendiri. Jangan menyalin video, karakter, atau nama channel mereka.

## Isi repo

```
skills/zack-d-short/          skill-nya
  SKILL.md                    style bible, alur kerja, checklist audit, pelajaran dari feedback
  references/                 tabel beat per video referensi (data ukur)
  scripts/
    zdf.py                    library Blender: scene, latar, karakter Mixamo, kamera, overlay
    finish.py                 frame + suara -> mp4: bloom, vignette, grain, caption, mix -12 LUFS
    transcribe.py             rekaman narasi -> words.json (Whisper, Bahasa Indonesia)
    fetch_space_textures.py   peta Bumi/Bulan NASA
    analyze_reference.py      analisis short referensi baru (contact sheet, cut, LUFS, kata/detik)
examples/pembuluh-darah/      satu short lengkap: "Seberapa Panjang Pembuluh Darahmu?" (32 detik)
  script.md                   naskah, shot list, cek fakta
  narasi.txt                  teks narasi untuk rekaman
  shots/                      6 skrip shot Blender + assembly + render batch
  words_placeholder.json      timing caption perkiraan (sebelum ada rekaman)
```

## Kebutuhan

- [Blender](https://www.blender.org/download/) 5.x (diuji di 5.2 LTS), GPU NVIDIA disarankan untuk Cycles
- [ffmpeg](https://ffmpeg.org/) di PATH
- Python 3.10+ dengan `pip install pillow`
- Opsional: `pip install faster-whisper` (timestamp caption dari rekaman), `yt-dlp` (analisis referensi)
- Claude Code

## Pasang skill

**Sebagai plugin** (di Claude Code):

```
/plugin marketplace add ancisaltylayty/Blender-Animation
/plugin install zack-d-short@zackd-style-shorts
```

**Atau salin manual** ke folder skill:

```bash
git clone https://github.com/ancisaltylayty/Blender-Animation
cp -r Blender-Animation/skills/zack-d-short ~/.claude/skills/
```

Lalu di Claude Code, minta saja, misalnya:

> Buat short gaya Zack D tentang kenapa jari keriput kalau lama di air. Tulis naskah dan storyboard dulu.

Claude akan menulis naskah Bahasa Indonesia, mengauditnya terhadap gaya, membuat storyboard, dan **baru me-render setelah kamu setuju** (render memakan waktu berjam-jam).

## Coba contoh pembuluh darah

```bash
cd examples/pembuluh-darah
python shots/gen_tape.py
python ../../skills/zack-d-short/scripts/fetch_space_textures.py assets
# taruh dua karakter Mixamo di assets/hero.fbx dan assets/xray.fbx (lihat assets/README.md)
blender -b --python shots/shot3_branch.py -- --check      # bangun scene + cek framing, tanpa render
```

Render semua beat lalu gabungkan (sekitar 3,5–4 jam di RTX 5060, 64 sample):

```bash
BLENDER="/path/ke/blender" bash shots/render_all.sh
```

Setelah merekam narasi:

```bash
python ../../skills/zack-d-short/scripts/transcribe.py voice.wav words.json --script narasi.txt
python shots/assemble.py --voice voice.wav --words words.json --music musik.wav
```

## Lisensi

Kode dan dokumen: [MIT](LICENSE). Tekstur NASA domain publik (cantumkan "NASA" di deskripsi video). Karakter Mixamo tidak disertakan; unduh sendiri dari akun Adobe kamu.

---

### English summary

A Claude Code skill for making vertical 3D explainer shorts in the Zack D. Films style with Blender, Python and ffmpeg, set up for **Indonesian** narration and captions (`finish.py --lang en` switches the caption rules back to English). The style rules come from frame-by-frame measurement of 9 reference shorts. `examples/pembuluh-darah` is a complete 32-second short (script, six Blender shot scripts, assembly). Not affiliated with Zack D. Films.

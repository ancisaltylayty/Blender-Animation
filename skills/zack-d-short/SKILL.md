---
name: zack-d-short
description: Bikin video pendek 3D vertikal bergaya penjelas ala Zack D. Films (latar biru langit, satu subjek realistis, kamera bergerak terus dengan easing, overlay "sains" datar dan saturasi tinggi, caption 1-3 kata) memakai Blender 5.x + Python + ffmpeg, dengan narasi dan caption Bahasa Indonesia. Pakai saat user ingin menulis naskah, storyboard, membangun shot, me-render atau finishing short "gaya Zack D", mengaudit naskah/shot list terhadap gaya itu, atau menganalisis short referensi baru. Also triggers on English requests for a "Zack D style" short.
---

# Short 3D gaya Zack D (versi Bahasa Indonesia)

Gaya ini dibedah dari analisis frame-per-frame 9 short referensi (113 juta sampai 256 juta views). Tabel beat per video ada di `references/video_breakdowns.md` (bahasa Inggris, berisi data ukur). Baca file itu sebelum membuat storyboard topik baru, karena semua aturan di bawah berasal dari sana.

**Bahasa output:** narasi, naskah (`script.md`), caption, dan judul ditulis dalam **Bahasa Indonesia**, kecuali user minta bahasa lain. Kode dan komentar kode tetap bahasa Inggris.

Alat di `scripts/` (folder di sebelah file ini):
- `zdf.py`: library Blender: scene, latar biru, import karakter, grammar kamera, overlay, helper render. Diuji di Blender 5.2 LTS.
- `finish.py`: frame + suara jadi mp4 jadi: bloom, vignette, grain, caption terbakar (`--lang id` default), mix audio, normalisasi -12 LUFS.
- `transcribe.py`: rekaman narasi menjadi `words.json` (timestamp per kata, Whisper, `--lang id`).
- `fetch_space_textures.py`: unduh peta Bumi/Bulan NASA (domain publik).
- `analyze_reference.py`: unduh short referensi, buat contact sheet, ukur cut, loudness, kata/detik, dan warna.

Lingkungan: tanyakan ke user path Blender kalau `blender` tidak ada di PATH (Windows biasanya `C:/Program Files/Blender Foundation/Blender 5.x/blender.exe`). Butuh ffmpeg dan Python 3 dengan Pillow; yt-dlp dan faster-whisper opsional.

Contoh lengkap satu short (naskah, 6 skrip shot, assembly) ada di repo: `examples/pembuluh-darah/`. Pakai sebagai pola untuk topik baru.

---

## 1. Style bible (hasil ukur)

### Format
- 1080×1920, 30 fps, 28–40 detik, biasanya 30 detik.
- Referensi berbahasa Inggris berjalan sekitar **2,5 kata/detik**. Kata Bahasa Indonesia lebih panjang (rata-rata 2,5–3 suku kata), jadi targetnya sekitar **2,1–2,3 kata/detik ≈ 60–75 kata per 30 detik**, atau **5–6 suku kata/detik**. Ini perkiraan: ukur ulang dari rekaman suara yang sebenarnya. Nada tenang, tidak heboh.
- Loudness sekitar **-12 LUFS** integrated (rentang -7 sampai -15), mix padat dan terkompresi.

### Formula naskah
1. **Hook = hipotesis orang kedua** dalam 2 detik pertama. Di referensi, "If you…" membuka 7 dari 9 short. Padanannya: "Kalau kamu…", "Bayangkan kalau…", "Apa jadinya kalau…". Pakai "kamu", bukan "Anda" (gaya short santai).
2. **Intuisi keliru lalu pembalikan.** "Mungkin kamu kira… Tapi…" (5 dari 9 short).
3. **Proses urut sebab-akibat.** Satu kalimat = satu aksi yang terlihat di layar.
4. **Skala lewat patokan, bukan angka di layar.** Lapangan bola, Jakarta ke Surabaya, keliling Bumi, "10× Monas".
5. **Akhiri di payoff atau pertanyaan menggantung.** Tanpa outro, ajakan subscribe, atau kartu logo. Frame terakhir menuntaskan aksi.
6. Fakta yang belum pasti diberi pagar di kalimatnya: "Ilmuwan memperkirakan…".
7. Angka ditulis gaya Indonesia: `100.000`, `2,5`. Satuan ditulis lengkap di narasi ("kilometer"), karena itu yang muncul di caption.

### Tampilan
- **Latar**: gradien radial biru langit. Tepi sekitar `#4DC0FF`, tengah `#87D1FF`, pusat terang `#B8E0FF`. Tanpa horizon. Varian: biru datar `#53A4DF` (makro kulit) dan putih `#F7F7F7` (dental/medis). Lingkungan nyata (lapangan, laut, jalan) hanya kalau cerita butuh tempat.
- **Lantai**: shadow catcher tak terlihat (subjek melayang di biru dengan bayangan lembut) atau lantai stilasi (lapangan hijau bergaris, tile peta low-poly).
- **Satu subjek utama, di tengah,** mengisi 60–90% tinggi frame. Manusia scan/PBR realistis dengan kulit matte + SSS, tidak seperti lilin.
- **Cahaya**: satu matahari hangat dengan bayangan jelas agak lembut, plus fill biru dari langit. Terang, high-key, tanpa frame gelap.
- **Overlay sains datar, saturasi tinggi, glossy, tidak pernah sadis:**
  - darah, pembuluh, luka: merah datar `#D9070A`, glossy
  - sifat khusus (mis. "tak bisa hancur"): seluruh objek berubah **hijau toksik** menyala
  - gaya/energi: glow **magenta/ungu**, atau **riak merah konsentris** di permukaan yang kena
  - tekanan/arah: **panah 3D** tebal merah atau putih, glossy, ber-bevel
  - sel dan nanah: partikel **kuning** menyala. Listrik: kilat biru-putih.
  - jaringan sembuh: isian kuning jadi pink lalu warna bekas luka
  - bau: pita berliku warna pink
- **Cut-away**: blok potongan melintang dan **reveal X-ray** (material luar memudar jadi transparan).
- **Branding**: nama channel di properti (pintu mobil, perisai, kapal, lapangan) dalam sans tebal abu gelap. Pakai nama channel user sendiri, jangan nama channel lain.
- **Realisme kamera**: motion blur di setiap gerak cepat, DOF tipis di shot makro, bloom, vignette ringan, grain halus. View transform **Khronos PBR Neutral** (Standard memotong highlight, AgX membuat biru jadi abu).

### Grammar kamera
- **Median satu hard cut per short.** Kebanyakan satu kamera kontinu, atau transisi lewat gerak:
  1. **Dolly lurus** maju untuk menjelaskan dan **pull-out ber-easing** untuk menutup. Satu sumbu, tanpa orbit, tanpa geser samping.
  2. **Whip pan / whip zoom** dengan motion blur berat yang mendarat di scene berikutnya.
  3. **Fly-through**: dorong masuk ke objek dan keluar di dunia berikutnya.
  4. **Hand-off lewat warna bersama**: shot A berakhir memenuhi frame dengan satu warna (atmosfer, awan, darah, kulit), shot B mulai dari warna yang sama. Lihat `zdf.fill_card`.
  5. **Naik ke top-down** untuk panjang/luas, dan **tracking rendah cepat** sepanjang garis.
  6. **Door-swing** (frame berputar seperti kartu di atas hitam): **hanya** antara dua shot dengan palet dan latar yang sama, maksimal sekali. Lihat pelajaran di bagian 5.
- Semua keyframe di-ease (Bezier auto-clamped). Momen "diam" tetap creep pelan, bukan berhenti mati.
- Tangan POV (orang pertama) untuk hook "kalau kamu menyentuh / menusuk / menembak…".

### Caption (terbakar di video)
- Verdana Bold, putih, outline hitam tipis, drop shadow lembut, **di tengah, baseline sekitar 80% tinggi frame**.
- **1–3 kata** per caption, mengikuti frasa, persis seperti diucapkan. Contoh Indonesia dari `finish.py --lang id`:
  `Kalau | semua pembuluh darahmu | ditarik keluar | dan disambung | jadi satu`
- Aturan frasa Bahasa Indonesia (sudah di `finish.py`):
  - jangan memisah frasa benda: "pembuluh darah", "satu ruangan"
  - kata depan dan sambung (`di ke dari yang dan untuk dengan pada dalam`) tidak boleh di akhir caption, selalu ikut kata sesudahnya
  - `ini itu kamu` menempel ke kata sebelumnya ("darah kamu", "tubuh ini")
  - `semua setiap seluruh para` selalu membuka caption baru
  - kata yatim di akhir kalimat meminjam satu kata dari caption sebelumnya
- Huruf kecil kecuali awal kalimat dan nama (Bumi, Bulan). Tanpa titik dan koma. "?" dipertahankan.
- Caption berganti keras tanpa animasi. Caption terakhir ditahan sekitar 0,6 detik.
- Short paling populer **tanpa caption sama sekali**: caption opsional kalau visual sudah bercerita.

### Suara
- Room tone atau ambience per dunia (udara lapangan, bawah air, dengung luar angkasa).
- Hit atau whoosh tepat di frame setiap aksi dan setiap transisi whip.
- Musik di bawah suara. Efek ada tapi di bawah suara.

---

## 2. Alur kerja

Jalankan berurutan. Setelah tiap langkah, tunjukkan hasilnya ke user.

**Aturan render:** jangan me-render apa pun (still, preview, atau final) tanpa izin user. Render lama di GPU kelas menengah (contoh: 960 frame 1080p 64 sample ≈ 3,5–4 jam di RTX 5060). Tunjukkan storyboard semua beat dulu, minta persetujuan, lalu render semua beat sekaligus dalam satu batch. Menjalankan skrip shot dengan `--check` (hanya membangun scene, cek framing, simpan .blend) boleh tanpa izin.

1. **Naskah.** Sekitar 60–75 kata Bahasa Indonesia mengikuti formula. Cek fakta setiap angka dan taruh pagar di kalimatnya. Satu aksi terlihat per kalimat.
2. **Beat sheet.** Untuk tiap frasa seukuran caption: waktu, aksi di layar, gerak kamera, transisi ke beat berikutnya. Beat 2–5 detik, gabungkan jadi gerak kamera kontinu sebisa mungkin. Maksimal 2 hard cut.
3. **Audit** dengan checklist di bagian 4.
4. **Storyboard** untuk persetujuan user: sketsa atau still per beat, dengan caption di atasnya.
5. **Aset.** Kalau ada aset nyata, unduh (Poly Haven, NASA lewat `fetch_space_textures.py`, scan anatomi, Mixamo). Jangan modeling manual yang bisa diunduh. Cek lisensi; jangan commit file yang lisensinya melarang distribusi ulang (karakter Mixamo mentah).
6. **Bangun tiap shot** sebagai file Python sendiri, dijalankan dengan `blender -b --python shotN.py -- --check`. Shot dengan subjek sama memakai satu fungsi builder bersama (lihat `examples/pembuluh-darah/shots/common.py`).
7. **Cek framing tanpa render**: proyeksikan titik penting dengan `world_to_camera_view` di frame kunci (`common.check`). Semua titik harus di dalam 0..1.
8. **Look-dev still** (setelah izin): `--preview --stills 1,60,120`. Bandingkan berdampingan dengan contact sheet referensi.
9. **Render final** (setelah izin): 1080×1920, 64–128 sample Cycles + denoise. Skrip batch yang bisa dilanjutkan: `examples/pembuluh-darah/shots/render_all.sh`.
10. **Rekam narasi**, lalu buat timestamp kata:
    ```bash
    python scripts/transcribe.py voice.wav words.json --lang id --script narasi.txt
    ```
11. **Finishing**:
    ```bash
    python scripts/finish.py --frames "renders/all/f_%04d.png" --out short.mp4 --voice voice.wav --music bed.wav --sfx sfx.wav --words words.json --lang id
    ```
    - `--text narasi.txt` kalau belum ada timestamp kata (timing diperkirakan dari suku kata; Whisper lebih akurat).
    - Tanpa `--words` dan `--text` = versi tanpa caption.

### Template shot minimal
```python
import sys; sys.path.append(r"<path ke skill>/scripts")
import zdf
zdf.new_scene(seconds=4, preview=True)              # preview=False untuk final
man = zdf.import_character(r"assets/hero.fbx")
zdf.relax_arms(man)                                   # T-pose -> tangan turun
h = zdf.head_height(man)
cam = zdf.camera(loc=(0, -5.2, h*0.55), target=(0, 0, h*0.5), lens=40)
zdf.blue_backdrop()            # shader world; varian 'flat' atau 'white'
zdf.ground("catcher")          # atau "field"
zdf.sun(); zdf.area_fill()
zdf.dolly(cam, dist=1.5)       # dolly maju lurus ber-easing sepanjang shot
# zdf.render_frames(r"//renders/shot1/")   # hanya setelah user setuju render
```

### Helper zdf
| Kebutuhan | Panggilan |
|---|---|
| Scene, Cycles GPU, motion blur, PBR Neutral | `new_scene(seconds, samples, preview)` |
| World gradien biru / datar / putih | `blue_backdrop(style=)` |
| Lantai bayangan tak terlihat / lapangan hijau | `ground("catcher" / "field")` |
| FBX Mixamo dengan material spec/gloss→PBR, SSS di kulit | `import_character(path)` |
| Tangan turun dari T-pose | `relax_arms(arm, down_deg=72)` |
| Akses bone (prefix `mixamorigN:` apa pun) | `bone(arm, "LeftForeArm")` |
| Pose akting (angguk, angkat bahu) | `rotate_bone_world(arm, name, axis, deg)` + `key_bone` |
| Kamera + DOF | `camera(loc, target, lens, dof_target, fstop)` |
| Dolly lurus ber-easing | `dolly(cam, dist, f0, f1)` |
| Jalur multi-key ber-easing | `keyframe_path(cam, [(f,(x,y,z)),...], target)` |
| Pasangan transisi whip | `whip_out(cam, f0)` di akhir shot, `whip_in(cam)` di awal shot berikutnya |
| Hand-off lewat warna bersama | `fill_card(cam, BLUE_MID, [(f, alpha), ...])` di kedua shot |
| Getar handheld halus | `handheld(cam, amount=0.004)` |
| Glow "sifat khusus" | `glow_overlay(obj, GLOW_GREEN/GLOW_MAGENTA, f_on, f_off)` |
| X-ray / tembus pandang | `set_alpha(obj, 1.0, frame=a); set_alpha(obj, 0.2, frame=b)` |
| Garis atau benang menggambar dirinya | `tube_curve(points, radius, mat_blood())` + `grow_curve(obj, f0, f1)` |
| Jaringan pembuluh di dalam tubuh | `vessel_network(arm, body_mesh)` + `heart(loc)` |
| Sehelai rambut manusia (makro) | `hair_strand(p0, p1, radius, color)` |
| Panah 3D | `red_arrow(loc, rot_deg, scale)` |
| Nama channel di properti | `brand_text("NAMA CHANNEL", loc, size)` |
| Material | `mat_principled`, `mat_emission`, `mat_blood` |

---

## 3. Menganalisis referensi baru
```bash
python scripts/analyze_reference.py refs https://youtube.com/shorts/XXXX https://youtube.com/shorts/YYYY
```
Lalu **Read setiap `refs/sheets/*.jpg`**. Tiap sel 0,5 detik, tiap sheet 16 detik. Tulis tabel beat per video dengan format `references/video_breakdowns.md`. Jalankan pengukuran yang sama pada render sendiri: selisih kedua angka itu adalah daftar perbaikan. Untuk referensi berbahasa Indonesia, tambahkan `--lang id` (bahasa subtitle otomatis).

---

## 4. Checklist audit (jalankan pada setiap naskah atau shot list)
- [ ] Hook hipotesis orang kedua ("Kalau kamu…"), terucap dalam 2 detik pertama
- [ ] 60–75 kata untuk 30 detik (sekitar 5–6 suku kata/detik), tiap kalimat aksi yang terlihat
- [ ] Ada belokan "Mungkin kamu kira… tapi…" atau reveal yang jelas
- [ ] Skala lewat patokan (lapangan, kota, Bumi), **tanpa counter, label, UI, atau teks infografis di layar**. Teks hanya caption, plus banner peringatan opsional.
- [ ] Maksimal 2 hard cut. Perpindahan lain lewat dolly, whip, fly-through, atau hand-off warna bersama
- [ ] Setiap transisi menjaga **palet dan arah gerak**. Tidak ada lompatan hitam→biru atau kartu yang berputar di antara dunia berbeda
- [ ] **Tidak ada shot yang diam total.** Setiap shot punya creep, push, atau pull ber-easing
- [ ] Satu subjek utama di tengah dan besar di latar biru (atau tempat nyata kalau cerita butuh)
- [ ] Overlay memakai kode warna (merah darah, hijau khusus, magenta gaya, kuning sel, panah 3D)
- [ ] Objek pembanding skala (rambut, koin, sel) **terbaca sebagai benda nyata** dan punya kedalaman (bagian 5)
- [ ] Berakhir di payoff visual atau pertanyaan, tanpa kartu outro
- [ ] Caption 1–3 kata, Verdana Bold, di 80% tinggi, frasa Indonesia tidak terpotong
- [ ] Mix sekitar -12 LUFS dengan hit di frame aksi

---

## 5. Pelajaran dari feedback penonton

Masukan nyata dari short contoh (`examples/pembuluh-darah`). Terapkan di setiap short baru.

### Objek pembanding skala harus terlihat seperti benda aslinya
Feedback: *"rambutnya tidak terlihat seperti rambut, tidak ada kedalamannya."* Versi pertama hanyalah tabung cokelat polos yang melintang datar di atas kapiler, sejajar bidang fokus.
- Pakai `zdf.hair_strand`: sisik kutikula (pita gigi gergaji sebagai bump, jarak sekitar 0,12× diameter), dua highlight (coat putih tajam + highlight hangat lebar), tepi amber tembus cahaya dengan inti melanin lebih gelap, sedikit bergelombang sepanjang helai.
- Kedalaman datang dari **komposisi**, bukan cuma shader: helai melintang **diagonal menembus bidang fokus**. Satu ujung naik ke arah lensa dan blur, ujung lain menyelam di bawah/di belakang subjek. Helai itu menimpa objek lain dan menjatuhkan bayangan ke atasnya.
- Prinsip ini berlaku untuk semua pembanding skala (koin, sel, butir pasir): beri detail permukaan khas benda itu dan tumpang-tindih kedalaman. Jangan objek polos sejajar layar.

### Transisi antar dunia harus menjaga warna dan gerak
Feedback: *"transisi dari Bulan ke orang di ruang biru tidak bagus, tidak mulus, bukan gaya yang tepat."* Versi pertama memakai door-swing (frame berputar seperti kartu di atas hitam) dari luar angkasa yang hitam langsung ke latar biru.
- Short referensi hampir tidak pernah memotong antara dua palet yang berlawanan. Transisinya mengikuti gerak kamera, dan warnanya menyambung.
- Perbaikan: kamera **menyelam kembali dari Bulan ke Bumi, masuk atmosfer**, sampai frame penuh biru langit (`fill_card(cam, BLUE_MID, …)` muncul di 6 frame terakhir). Shot berikutnya **mulai dari kartu biru yang sama** dan kamera jatuh/tilt turun dari langit ke subjek sementara kartu memudar. Sambungannya identik di level piksel, dan geraknya ("jatuh kembali ke Bumi") masuk akal secara cerita.
- Aturan umum: sebelum memilih transisi, tulis warna dominan frame terakhir shot A dan frame pertama shot B. Kalau beda jauh, jembatani dengan warna bersama (atmosfer, awan, cairan, kulit, cahaya putih) atau whip dengan arah gerak yang sama. Door-swing hanya untuk dua shot dengan latar yang sama.

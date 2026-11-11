# Short: Seberapa Panjang Pembuluh Darahmu?

Format: 1080x1920 vertikal, 30 fps, sekitar 32 detik, 7 beat, caption per frasa.
Tampilan: latar gradien biru langit, lantai shadow catcher tak terlihat, satu pria berdiri di tengah dan besar. Setiap shot bergerak dengan easing. Tanpa hard cut.
Aturan gaya: `skills/zack-d-short/SKILL.md`.

## Narasi (66 kata, sekitar 5–6 suku kata/detik)

Teks polos untuk rekaman dan `transcribe.py --script`: `narasi.txt`.

1. Kalau semua pembuluh darahmu ditarik keluar dan disambung jadi satu,
2. mungkin kamu kira cuma cukup untuk satu ruangan.
3. Tapi arteri terus bercabang jadi pipa yang makin kecil, sampai kapiler yang lebih tipis dari rambut.
4. Ilmuwan memperkirakan, kalau digabung, panjangnya sekitar 100.000 kilometer.
5. Itu lebih dari dua kali keliling Bumi, atau seperempat jalan ke Bulan.
6. Dan setetes darah cuma butuh sekitar satu menit untuk satu putaran penuh.

## Shot list

| Beat | Waktu | Narasi | Visual | Kamera | Ke beat berikut | File |
|---|---|---|---|---|---|---|
| 1 | 0–4,5 d | "Kalau semua pembuluh darahmu… jadi satu" | Pria berdiri di latar biru. Jas dan kulitnya memudar (x-ray) ke lapisan otot, lalu ke jaringan pembuluh merah. Pembuluh meluncur keluar dari ujung jari seperti benang dan menyatu jadi satu garis merah di lantai. | Push-in pelan dari seluruh badan ke tangan | Tilt turun mengikuti garis | `shot1_reveal.py` |
| 2 | 4,5–7,5 d | "mungkin kamu kira… satu ruangan" | Melewati sepatunya, garis masuk ke ruangan cut-away 5 m × 3,5 m (tiga dinding putih, lantai kayu, tanpa atap). Pita meteran kuning raksasa menempel di kedua dinding samping. Garis berhenti di dinding belakang, tepat di angka 5 m. | Whip-in, lalu tracking rendah dari pintu ke dinding belakang | Terbang ke ujung potongan garis | `shot2_room.py` |
| 3 | 7,5–14 d | "Tapi arteri… lebih tipis dari rambut" | Makro di dalam garis: arteri tebal merah glossy bercabang jadi pipa makin kecil, sampai kapiler. Sehelai rambut manusia (sisik kutikula, tembus cahaya) melintang diagonal menembus bidang fokus, menimpa kapiler dan menjatuhkan bayangan. | Satu dorongan kontinu sepanjang cabang, naik ke top-down | Pull-back cepat keluar dari makro | `shot3_branch.py` |
| 4 | 14–19 d | "Ilmuwan memperkirakan… 100.000 kilometer" | Kembali di ruangan, garis menjebol dinding belakang (serpihan plester terlempar) dan melesat ke cakrawala. Kamera naik, ruangan mengecil di bawah. | Naik lurus ke top-down, terus naik | Naik menembus lapisan awan (tanpa cut) | `shot4_stretch.py` |
| 5 | 19–26 d | "Itu lebih dari dua kali keliling Bumi… ke Bulan" | Bumi dari satelit. Garis merah melilit dua kali, lepas ke angkasa menuju Bulan dan berhenti di seperempat jalan. | Naik mengorbit, pull-back lebar sampai Bulan terlihat, tahan sebentar, lalu **menyelam kembali ke Bumi dan masuk atmosfer** sampai frame penuh biru langit | Kartu biru langit bersama (`fill_card`) | `shot5_space.py` |
| 6 | 26–30,5 d | "Dan setetes darah… satu putaran penuh" | Mulai dari kartu biru yang sama, kamera jatuh dari langit dan tilt turun ke pria di latar biru. X-ray ke pembuluh. Tetes merah menyala keluar dari jantung, turun lewat lengan dan kaki, lalu kembali. Jantung berdenyut. | Jatuh dan mendarat setinggi pinggang, pull-back ke seluruh badan mengikuti tetes, lalu push-in lagi | Kontinu ke beat 7 | `shot6_loop.py` |
| 7 | 30,5–32 d | (selesai) | X-ray kembali ke pria berjas. Kepalanya menunduk cepat melihat dadanya, bahunya terangkat (reaksi tubuh; model tidak punya blend shape wajah). Tahan di reaksi, tanpa outro. | Creep pelan | Selesai | `shot6_loop.py` |

Hard cut: 0. Transisi: tilt, whip-in, fly-in, pull-back, naik menembus awan, dan hand-off lewat kartu biru langit (Bumi → ruang biru).

## Caption

1–3 kata, mengikuti frasa, Verdana Bold putih dengan outline hitam tipis dan drop shadow lembut, baseline di sekitar 80% tinggi frame. Dibuat oleh `finish.py --lang id` dari `words.json`:

`Kalau | semua pembuluh darahmu | ditarik keluar | dan disambung | jadi satu | mungkin kamu kira | cuma cukup | untuk satu ruangan | Tapi arteri | terus bercabang | jadi pipa | yang makin kecil | sampai kapiler | yang lebih tipis | dari rambut | …`

Tanpa teks lain di layar: tanpa label, counter, atau UI.

`words_placeholder.json` berisi timing perkiraan per beat (dari suku kata) sampai ada rekaman suara. Setelah merekam: `python ../../skills/zack-d-short/scripts/transcribe.py voice.wav words.json --script narasi.txt`.

## Fakta yang dicek

- 100.000 km (sekitar 60.000 mil) adalah angka total yang umum dikutip untuk orang dewasa, tapi sumber aslinya lemah. Karena itu kalimatnya "Ilmuwan memperkirakan".
- Keliling Bumi 40.075 km, jadi 100.000 km ≈ 2,5 putaran. "Lebih dari dua kali" aman.
- Jarak Bumi–Bulan rata-rata 384.400 km. 100.000 km = 26%, jadi "seperempat jalan" akurat.
- Waktu sirkulasi penuh saat istirahat sekitar 1 menit (umum dikutip 45–60 detik). "Sekitar satu menit" aman.
- Kapiler sekitar 5–10 µm, rambut manusia sekitar 50–100 µm. "Lebih tipis dari rambut" akurat.

## Aset

Lihat `assets/README.md`. Ringkasnya: dua karakter Mixamo (pria berpakaian + figur otot tanpa kulit), peta NASA (`fetch_space_textures.py`), dan tekstur meteran (`shots/gen_tape.py`).

- **Urutan x-ray (beat 1):** alpha pria 1 → 0 sementara figur otot tetap terlihat, lalu alpha otot 1 → sekitar 0,15 sementara pembuluh tetap merah penuh. Beat 7 membalik urutan.
- **Reaksi beat 7** adalah gerak tubuh (kepala dan leher menunduk, bahu terangkat), karena karakter tanpa blend shape wajah.
- **Bulan dicurangi** ke 24 jari-jari Bumi (aslinya 60,3) supaya Bumi dan Bulan terbaca di layar HP. Garis tetap berhenti di 26% jarak, jadi proporsi yang diucapkan narasi tetap benar.
- **Suara:** room tone biru, whoosh di tiap transisi, hit saat garis menjebol dinding (beat 4), dengung angkasa (beat 5), whoosh menyelam masuk atmosfer (akhir beat 5), detak jantung sinkron dengan denyut (beat 6), musik di bawah suara. Mix sekitar -12 LUFS.

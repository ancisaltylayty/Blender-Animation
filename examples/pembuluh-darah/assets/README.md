# Aset untuk contoh pembuluh darah

File di folder ini **tidak** ikut di-commit (lihat `.gitignore`). Siapkan sendiri:

| File | Isi | Cara dapat |
|---|---|---|
| `hero.fbx` | Pria berpakaian, rig Mixamo standar (65 bone, T-pose) | [mixamo.com](https://www.mixamo.com) → Characters → pilih karakter berjas → Download, format FBX, pose T-pose |
| `xray.fbx` | Figur otot tanpa kulit, tinggi mirip, rig Mixamo | Mixamo atau aset anatomi lain dengan rig Mixamo; harus pas di dalam `hero.fbx` di origin yang sama |
| `earth_day.jpg`, `earth_night.jpg`, `moon.jpg` | Peta NASA (domain publik) | `python ../../../skills/zack-d-short/scripts/fetch_space_textures.py .` |
| `tape_ltr.png`, `tape_rtl.png` | Tekstur pita meteran | `python ../shots/gen_tape.py` (dari folder `examples/pembuluh-darah`: `python shots/gen_tape.py`) |

Karakter Mixamo gratis dipakai di video, tapi file mentahnya tidak boleh dibagikan ulang. Jangan commit file `.fbx`.

Mau pakai FBX di tempat lain? Set environment variable:

```bash
export ZDF_HERO_FBX="/path/ke/pria.fbx"
export ZDF_XRAY_FBX="/path/ke/otot.fbx"
```

Tanpa tekstur NASA, beat 5 tetap jalan dengan Bumi dan Bulan prosedural (kurang realistis).

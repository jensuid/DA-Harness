# REPORT — WALK-UX-002

Walk-test end-to-end sebagai junior analyst baru, 27 Sep 2026.
Dataset mockup baru `coffee_shop_sales_2026.csv` (110 baris, 3 gerai kopi,
sengaja bermasalah: 1 date format campuran, 1 outlier revenue 99.000, 2 store
kosong, 1 transaction_id ganda).

Flow lengkap ditempuh: case → question → dataset → profile → plan → SQL run →
chart → draft finding → validate → decision → reopen. LLM aktif; 3 dari 4
call LLM timeout dan jatuh ke deterministic. Semua angka di bawah diukur dari
live DOM/JS, bukan kesan.

## Bukti kepadatan (yang dikata user "terlalu padat")

| Metrik | Angka |
|---|---|
| Panel (h2) | 18 |
| Sub-panel (h3) | 21 |
| Tombol interaktif | 23 |
| Item list | 85 |
| Kata | 2.258 |
| Tinggi halaman | 7.740 px = **13,1x viewport** (593 px) |
| Zone work saja | 7.600 px = 12,8x viewport |
| Progressive disclosure | **0** (`<details>` = 0) |
| Panel dengan empty state saat case baru | **12 dari 18** |

Keluhan "semua step di 1 halaman, terlalu padat" **terkonfirmasi secara
terukur**. Akar masalahnya ada dua: (1) volume, (2) semuanya flat — tidak ada
panel yang mengecil, tidak ada yang disembunyikan saat stage belum dicapai,
tidak ada yang disembunyikan saat kosong.

## Yang sudah baik (jangan dipecah)

1. **Workflow rail 7 step** — satu-satunya alasan halaman ini bisa dinavigasi.
   Stage terjawab jelas, `⚠ data` muncul saat ada peringatan kualitas.
2. **Profiler dan peringatan kualitas** — sangat spesifik dan tepat
   ("99000.0 is 758.6x the next-largest value", "1 of 110 date values do not
   read as the type the other 109 hold"). Bagian terbaik di app.
3. **Chart control + recharts** — cepat, axis/series bisa dipilih, tooltip.
4. **Privacy log** — request body/response payload tidak pernah di-log
   (hanya method/path/status/durasi). Sesuai desain.
5. **Evidence graph** — "1 dataset, 1 run, 1 finding, 1 chart, 1 plan",
   diturunkan dengan jelas.
6. **Fallback deterministic** — LLM gagal, app tetap menjawab. Arsitekturnya
   sehat; masalahnya presentasinya (W2X-001), bukan keberadaannya.

## Prioritas perbaikan

Urutan = dampak terhadap junior analyst ÷ effort.

### Prioritas 1 — perbaikan alur kerja (dampak besar, effort sedang)

| ID | Temuan | Dampak | Effort |
|---|---|---|---|
| **W2X-007** | Tidak ada editor SQL/Python; "Run an analysis" tidak punya UI | Inti app. Satu-satunya pintu ke `/runs` adalah codegen LLM yang tidak editable. | Sedang — satu textarea + tombol Run posting endpoint yang sudah ada |
| **W2X-006** | Kode LLM tidak bisa diedit padahal sering gagal jalan | Setiap error = 1 LLM call baru (2 menit). Loop frustrasi paling nyata. | Kecil — ganti `<pre>` dengan `<textarea>` |
| **W2X-002** | Submit form Dataset kosong = diam total | Pengguna baru berhenti di menit pertama. | Kecil — pesan inline + tanda wajib |
| **W2X-001** | LLM 120 detik tanpa progress/cancel | 3 dari 4 call timeout. Dua menit menunggu, lalu jawaban dari mesin lain. | Sedang — elapsed + cancel + banner fallback |
| **W2X-005** | "Next:" menampilkan `POST /cases/…/datasets` mentah | Jawaban developer, bukan pengguna; `{dataset_id}` tidak terisi. | Kecil — ganti string atau jadikan tombol |

### Prioritas 2 — kepadatan (temuan inti, effort lebih besar)

| ID | Temuan | Dampak | Effort |
|---|---|---|---|
| **W2X-008** | 13,1x viewport, 18 panel flat, 12 empty state di awal | Keluhan utama user. | Besar — butuh progressive disclosure + stage-aware hiding |

Saran terurut:
1. **Sembunyikan panel kosong** sampai ada data (kecuali yang menjadi next
   action). 12 empty state di detik pertama adalah kepadatan tanpa nilai.
2. **Zone orientation hanya rail + overview + next action.** Pindahkan Refine,
   Learn, History, Save-as-template ke tempat lain (tab "Notes"/"Timeline").
3. **Collapsible per stage**, auto-collapse saat stage selesai.

### Prioritas 3 — kualitas analisis

| ID | Temuan | Dampak | Effort |
|---|---|---|---|
| **W2X-009** | Fallback draft mempropagandakan outlier 758x sebagai finding | Loop trust menutup di atas angka palsu. | Sedang — drafter harus baca peringatan profil |

### Prioritas 4 — polish

| ID | Temuan | Effort |
|---|---|---|
| **W2X-003** | Chart hilang setelah reopen | Kecil |
| **W2X-004** | "unsaved edits" palsu di Context | Kecil |
| **W2X-011** | Klik baris case tidak membuka case | Kecil |
| **W2X-010** | Duplikat case tidak diberi peringatan | Kecil (opsional) |

## Yang TIDAK jadi temuan (dicek, tapi sehat)

- **Decision panel** — awalnya saya catat "tidak sinkron" (bilang "no finding
  validation has stood behind yet" padahal barusan divalidasi). **Tidak
  terkonfirmasi**: itu delay re-fetch setelah Validate; setelah reload,
  Decision menampilkan finding + uncertainty dengan benar. Saya keluarkan
  dari daftar temuan.
- **"working set" log** — `/logs` bekerja sempurna; request body tidak di-log.
- **Backend API** — semua endpoint 2xx/4xx sesuai kontrak; tidak ada 500.

## Keterbatasan sesi (honest)

- **Agent != naive human.** Saya membaca DOM, bukan layar; tidak punya
  kebingungan asli. Kepadatan saya ukur, bukan rasakan — angka di tabel atas
  adalah bukti, tapi "seberapa sulit dipahami" tetap pengalaman manusia.
- **LLM timing bukan representatif** — 3 dari 4 call timeout. Bisa jadi ini
  network provider hari ini, bukan kondisi normal. W2X-001 tentang *cara
  app menunggu*, bukan tentang kecepatan LLM itu sendiri.
- **Viewport 1256x593** — lebih kecil dari layar developer biasa. Rasio
  13,1x akan turun di layar besar, tapi 18 panel flat tetap 18 panel flat.
- **Satu dataset, satu case** — saya tidak menguji multi-dataset, template,
  chat cross-case, atau ekspor package.
- **Fase 2 (app riil) belum dijalankan.** Saya baru menyelesaikan fase 1
  (dev core + browser). Verifikasi temuan di `/Applications/DAH.app` masih
  perlu dilakukan.

## Fase 2 — SELESAI (app riil)

Dijalankan. Hasil di `walktest-w2/PHASE2.md`, temuan baru W2X-012 dan
W2X-013 di `FINDINGS.md`.

**Konfirmasi:** W2X-005 (endpoint mentah, muncul 2x), W2X-008 (5,8x
viewport), layout 3 zone, duplikasi Objective/Question.

**Temuan terbesar fase 2 — W2X-012 (BLOCKER):** app packaged
`/Applications/DAH.app` tidak punya kredensial LLM. `.env` tidak di-bundle
(`dah-core.spec` hanya menyertakan version stamp), shell tidak meng-inject
`DAH_LLM_API_KEY`. Bukti: `find /Applications/DAH.app -name ".env"` kosong,
dan POST `/generate-code` di app riil mengembalikan `"source":"template"`
(fase 1: "by llm"). Jadi seluruh lapisan cerdas (plan, draft, refine, chat,
agent) nonaktif di app yang user dapat — W2X-001 (timeout) bahkan tidak akan
terjadi karena LLM tidak dipanggil sama sekali.

W2X-013 (MINOR): zone orientasi hanya 232pt (18%) di window 1280pt —
pertanyaan panjang jadi blok 101pt tinggi yang nyaris tak terbaca.

## Langkah berikutnya (ditawarkan, bukan diasumsikan)

1. **Root-cause W2X-012** — bagaimana kredensial seharusnya sampai di
   sidecar. Pilihan: inject saat build (secret injection, bukan commit
   `.env`), first-run UI prompt di app data dir, atau status LLM tampil di
   UI. Ini memblokir seluruh fitur LLM untuk pengguna riil.
2. **Root-cause W2X-009** — apakah drafter membaca peringatan profil?
   (`server/app/drafter.py`, fallback deterministic path).
3. **Prototipe Prioritas 1** — editor SQL/Python + pesan form + tombol
   next-action, sebagai task terpisah dengan gate tes sendiri.

Walk-test ini selesai. Semua hasil ada di `walktest-w2/`:
PLAN.md, CAPTURE-SHEET.md, FINDINGS.md (13 temuan), REPORT.md, PHASE2.md,
coffee_shop_sales_2026.csv, evidence/case-page-final.png, data/, logs/.

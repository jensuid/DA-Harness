# WALK-UX-005 — Walk-test kelima (validasi W3X-001: filename ganda di Data panel)

Walk-test kelima. Tujuan: **satu pertanyaan** — apakah W3X-001 (Data panel
menerima filename yang sama dua kali, menciptakan dua dataset row yang tidak
dapat dibedakan) bisa dijangkau oleh cara kerja manusia, atau hanya artifact
dari cara harness membuat `File` lewat `DataTransfer`?

Karena W3 dan W4 sama-sama membuat dataset secara sintetis, W5 berbeda:
dataset disiapkan sebagai **file sungguhan di disk**, dan analyst
menyelesaikan loop penuh dengan domain baru, tanpa membaca FINDINGS lama.

## 0. Peran dan batas

- Saya berperan ganda: naive analyst yang baru pertama kali pakai app ini DAN
  facilitator yang mencatat. Jawaban participant selalu fresh dari state app
  saat ini.
- **Keterbatasan yang jujur:** agent != naive human. Saya bisa melihat DOM,
  teks, state, network — tapi tidak punya kebingungan asli. Temuan harus
  didasarkan pada bukti terukur, bukan perasaan.
- Tidak ada coaching mid-run. Penjelasan baru muncul di debrief.
- Dataset W5 = file sungguhan di `walktest-w5/`, bukan `DataTransfer` sintetis
  — inilah perbedaan kunci dari W3/W4.

## 1. Mekanisme akses

- Port core hard-coded **8123**. Core dijalankan manual dengan
  `DAH_DATA_DIR=walktest-w5/data` (dev venv yang baca `server/.env`, LLM
  aktif), frontend via Vite dev server (port 5273) di Chromium nyata.
  Alasan: Tauri WKWebView tidak punya CDP; bundle web dan bundle Tauri adalah
  kode React yang sama.
- Isolated data dir: `walktest-w5/data/` (gitignored), mulai dari kosong
  (`GET /cases` = `[]`).

## 2. Dataset mockup baru — domain baru, file sungguhan

`walktest-w5/retail_inventory_2026_h1.csv` — 2,800 baris inventory retail,
SKU × store × week, Jan–Jun 2026. Satu file di disk.

Enam anomalies ditanam (sama seperti W4 — profiler harus menemukannya):

1. 3 nilai `store_region` kosong
2. 1 outlier `revenue` (bulk order 40x di minggu normal)
3. 1 `week_start` format US (month-first) sedangkan lainnya ISO
4. 1 `sku_store_id` ganda
5. 1 `on_hand` = 0 untuk SKU yang tidak didiskontinu
6. `north` vs `North` (categorical split, region sama ditulis dua cara)

Narasi: out-of-stock untuk SKU elektronik di region North naik di Maret;
apakah lead time atau on_hand policy menjelaskannya? Outlier revenue adalah
row yang akan dimahkota average naive kalau tidak diberi flag.

**Kunci W5:** file ini di-attach **dua kali** sebagai bagian dari eksplorasi
naive analyst yang wajar: pertama untuk mencoba, lalu analyst kembali ke
panel Data dan attach file yang sama lagi untuk "memastikan" atau setelah
membaca guidance. Ini adalah pola penggunaan yang sah untuk manusia
penasaran — bukan upaya men-trigger bug. Jika panel menolak, itu fix
W3X-001 bekerja; jika menerima, itu temuan yang sekarang punya frekuensi.

## 3. Fokus pengukuran — F-DUP (validasi W3X-001)

Satu pengukuran wajib, selain loop penuh:

**F-DUP:**
- Saat file yang sama di-attach kedua kalinya: apakah panel menolak atau
  menerima?
- Kalau menerima: apakah `GET /cases/{id}/datasets` mengembalikan dua row
  dengan filename identik?
- Apakah ada konfirmasi visual (warning, notice, disable) sebelum attach
  kedua?
- Apakah permukaan lain (run/code/chart) jadi ambigu — mana `datasets[0]`?
- Kalau menolak: apakah kalimatnya menjelaskan dataset yang sudah ada
  (saran W3X-001 asli)?

**Loop penuh + regresi W2X/W3X/W4X:** attach (2x) → profile → plan → SQL →
Python → chart → interpret → draft → accept → validate → reviewer audit →
chat → implications → export → reopen. Setiap fix sebelumnya direkam
hold/regress.

## 4. Capture sheet

`walktest-w5/CAPTURE-SHEET.md`, setiap baris `*(to be recorded)*` sebelum
sesi. Id stabil: V (pre-flight), L (think-aloud per step), F (pengukuran
facilitator), D (debrief). Exit criterion: nol `to be recorded` tersisa.

## 5. Langkah walk (L-rows)

1. Landing: case list kosong. Apa ini? Apa yang harus saya lakukan?
2. New Analysis Case: field Question + Dataset.
3. Attach dataset (1st) → profile. Enam anomalies muncul?
4. **Attach file yang sama (2nd).** F-DUP: ditolak atau diterima?
5. Generate plan (LLM). Berapa lama? (regresi W3X-003-PROMPT)
6. Run SQL.
7. Run Python. (regresi W3X-004) Refusal pertama atau langsung kontrak?
8. Chart dari run.
9. Interpret (LLM).
10. Draft finding → accept → validate.
11. Reviewer agent audit (approve).
12. Ask the case (chat, LLM).
13. Implications → decision.
14. Back to list, reopen. (regresi W4X-001) State bertahan?
15. Export → round-trip.
16. Debrief.

Evidence per step: DOM snapshot + response API + core request log di
`walktest-w5/evidence/` dan `walktest-w5/logs/`.

## 6. Setelah run

1. Sweep capture sheet, pastikan nol yang tersisa.
2. `walktest-w5/FINDINGS.md` — append-only, satu blok per temuan: severity,
   area, lokasi kode, observasi, bukti terukur, mengapa penting, saran.
3. `walktest-w5/REPORT.md` — ringkasan + tabel journey + prioritas.
4. **Verdict F-DUP: HOLD (W3X-001 manusia bisa capai — perlu fix) atau NOT
   HOLD (hanya artifact harness — tutup observasi).**

## 7. Yang TIDAK saya lakukan

- Tidak mengubah kode app selama walk-test.
- Tidak commit selesai run; ini menghasilkan temuan.
- Tidak menyentuh `.env`, tidak mencetak isi `DAH_LLM_API_KEY`.

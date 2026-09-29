# WALK-UX-004 — Walk-test end-to-end DAH (validasi fix W3X di tangan naive analyst)

Walk-test keempat. Tujuan: **validasi** dua fix W3X yang sudah di-comm di
master tapi belum pernah dilewati analyst sungguhan di provider yang gagal:

1. **W3X-003-PROMPT (plan LLM tidak timeout di ~10 tok/s).** W3 mengukur plan
   call menghabiskan seluruh budget 120s lalu fallback deterministik. Root
   cause: prompt meminta 1785 token output; provider generate ~13 tok/s →
   ~137s. Fix: prompt kini meminta maks 4 sub-questions / 3 hypotheses /
   4 steps / 3 data requirements, satu clause pendek per string. Satu
   pengukuran live (52.3s, 508 token, `finish_reason: stop`) menunjukkan ini
   di dalam budget. Pertanyaan W4: apakah ini terjadi di tangan analyst,
   di provider yang sama?
2. **W3X-004 (panel Python mengurangi refusal).** W3 mengukur tiga refusal
   berturut-turut (`import pandas`, `import csv`, `path`) tanpa jawaban di
   halaman. Fix: panel menampilkan kontrak sandbox (`dataset.rows`, daftar
   module importable, contoh kanonik) sebelum run pertama. Pertanyaan W4:
   apakah interaksi Python pertama analyst menggunakan kontrak di halaman,
   dan berapa refusal sebelum run sukses?

Mode: naive analyst + facilitator, LLM nyata (Atria-Dawn-Preview, provider
yang SAMA seperti W3 — titik terkuat), dataset mockup baru, browser Chromium.

Laporan temuan W3 (`walktest-w3/FINDINGS.md`) **diabaikan** saat berperan —
saya tidak membaca isinya saat menjalankan analyst; yang dibawa hanya
"bagaimana cara pakai app ini secara umum", tidak lebih.

## 0. Peran dan batas

- Saya berperan ganda: analyst yang baru pertama kali pakai app ini DAN
  facilitator yang mencatat. Jawaban participant selalu fresh dari state app
  saat ini.
- **Keterbatasan yang jujur:** agent != naive human. Saya bisa melihat DOM,
  teks, state, network — tapi tidak punya kebingungan asli. Jadi temuan
  "sulit dipahami" harus didasarkan pada bukti terukur, bukan perasaan.
- Tidak ada coaching mid-run. Penjelasan baru muncul di debrief.

## 1. Mekanisme akses

- Port core hard-coded **8123**. Core dijalankan manual (dev venv yang baca
  `server/.env`, LLM aktif), frontend via Vite dev server (port 5273) di
  Chromium nyata. Alasan: Tauri WKWebView tidak punya CDP; bundle web dan
  bundle Tauri adalah kode React yang sama.
- Isolated data dir: `walktest-w4/data/` (gitignored).

## 2. Dataset mockup baru

`walktest-w4/saas_renewals_2026.csv` — 3,000 baris subscription SaaS B2B,
Jan–Des 2026, 4 plan (Solo/Team/Business/Enterprise) × 5 segment.

Enam anomalies ditanam (sama seperti W3 — profiler harus menemukannya):

1. 3 nilai `segment` kosong
2. 1 outlier `revenue_usd` (annual prepay 499,500 di baris monthly)
3. 1 `renewed_on` format US (month-first) sedangkan lainnya ISO
4. 1 `subscription_id` ganda
5. 1 `seats` = 0 (plan Solo minimum 1)
6. `scaleup` vs `ScaleUp` (categorical split, segment sama ditulis dua cara)

Narasi: renewal segment ScaleUp turun di Q3; apakah seat utilisation
(active_users/seats) menjelaskannya? Outlier revenue adalah row yang akan
dimahkotai average naive kalau tidak diberi flag.

## 3. Fokus pengukuran (pertanyaan inti sesi ini)

Selain loop penuh, dua pengukuran wajib:

**F-PLAN (validasi W3X-003-PROMPT):**
- Berapa lama `POST /plan` elapsed? Apakah < 120s dengan source LLM?
- `finish_reason` di log core? (stop = objek lengkap; length = truncated)
- Berapa token output? Berapa rate tok/s provider sesi ini?
- Kalau LLM plan sukses: sub-questions/hypotheses/steps/data_requirements
  berapa jumlahnya? (prompt minta maks 4/3/4/3)
- Kalau fallback: apakah announcement-nya terbaca sebagai kalimat utuh
  (validasi W3X-002 sekaligus)?

**F-PY (validasi W3X-004):**
- Saat engine Python dipilih, apakah kontrak tampil di panel sebelum run?
- Apakah analyst menjalankan `import pandas`/`import csv`/`path` lebih dulu
  (refusal), atau langsung memakai `dataset.rows` dari kontrak?
- Berapa refusal sebelum run Python sukses? Target: 0.
- Placeholder: apakah berupa script runnable, bukan `# python`?

**Loop penuh + regresi W2X/W3X:** attach → profile → plan → SQL → Python →
chart → interpret → draft → accept → validate → reviewer audit → chat →
implications → export → reopen. Setiap fix sebelumnya direkam hold/regress.

## 4. Capture sheet

`walktest-w4/CAPTURE-SHEET.md`, setiap baris `*(to be recorded)*` sebelum
sesi. Id stabil: V (pre-flight), L (think-aloud per step), F (pengukuran
facilitator), D (debrief). Exit criterion: nol `to be recorded` tersisa.

## 5. Langkah walk (L-rows)

1. Landing: case list kosong. Apa ini? Apa yang harus saya lakukan pertama?
2. New Analysis Case: field Question + Dataset.
3. Attach dataset → profile. Apakah enam anomalies muncul sebagai quality
   findings?
4. **Generate plan (LLM).** F-PLAN: berapa lama? Sukses LLM atau fallback?
5. Run SQL (SQL engine).
6. **Run Python.** F-PY: kontrak tampil? Refusal pertama atau langsung pakai
   `dataset.rows`?
7. Chart dari run.
8. Interpret (LLM).
9. Draft finding → accept → validate.
10. Reviewer agent audit (approve).
11. Ask the case (chat, LLM).
12. Implications → decision (loop closed?).
13. Back to list, reopen: state bertahan?
14. Export → round-trip.
15. Debrief.

Evidence per step: DOM snapshot + response API + screenshot di
`walktest-w4/evidence/`.

## 6. Setelah run

1. Sweep capture sheet, pastikan nol yang tersisa.
2. `walktest-w4/FINDINGS.md` — append-only, satu blok per temuan: severity,
   area, lokasi kode, observasi, bukti terukur, mengapa penting, saran.
3. `walktest-w4/REPORT.md` — ringkasan + tabel journey + prioritas.
4. Verdict untuk dua fix: HOLD atau NOT HOLD, dengan angka.

## 7. Yang TIDAK saya lakukan

- Tidak mengubah kode app selama walk-test.
- Tidak commit selesai run; ini menghasilkan temuan.
- Tidak menyentuh `.env`, tidak mencetak isi `DAH_LLM_API_KEY`.

# WALK-UX-002 — Walk-test end-to-end DAH (junior analyst, fokus case page)

Tujuan: input perbaikan UX/UI, khususnya case page (CaseWorkspace) yang
sekarang menampilkan **semua step di satu halaman** dan terasa terlalu padat.
Bukan lulus gate. Mode: naive junior analyst + think-aloud, LLM nyata,
dataset mockup baru.

Laporan temuan lama (`walktest/FINDINGS.md`, W-001..W-018) **diabaikan** — saya
tidak tahu isinya saat berperan; 19 temuan itu sudah resolved. Sesi ini
mengukur dari nol.

## 0. Peran dan batas

- Saya berperan ganda: junior analyst yang baru pertama kali pakai app ini
  (belum pernah lihat DAH, belum baca kode) DAN facilitator yang mencatat.
  Jawaban participant selalu fresh dari state app saat ini, tidak disalin dari
  dokumen manapun.
- **Keterbatasan yang jujur:** agent != naive human. Saya bisa melihat DOM,
  teks, state, network, dan — kali ini — screenshot (path browser), yang
  walktest lama tidak bisa. Tapi saya tidak punya kebingungan asli, tidak
  salah klik secara organik, dan membaca lebih cepat dari manusia. Jadi
  temuan "sulit dipahami" harus didasarkan pada **bukti terukur** (jumlah
  panel, volume teks, kedalaman scroll, urutan vs alur kerja), bukan perasaan.
  Setiap klaim padat/ramai saya sandarkan ke angka.
- Tidak ada coaching mid-run. Penjelasan baru muncul di debrief.

## 1. Mekanisme akses (dua fase)

Fakta arsitektur (dari source, bukan asumsi):

- Port core hard-coded **8123**. Dua core tidak bisa berbagi port; app kedua
  gagal bind dan terlihat mati.
- `resolve_server_command` (`desktop/src-tauri/src/core_server.rs:110`):
  sidecar `dah-core` di `shell_dir` (release) atau `server/.venv/bin/python`
  (dev). `DAH_DEV_CORE=1` memaksa dev venv meski sidecar ada.
- App packaged TIDAK membaca `server/.env` — hanya sidecar build yang
  melakukannya. Jadi tanpa langkah tambahan, LLM nonaktif di app riil.

**Fase 1 — dev core + browser (otoritatif untuk UX master).**
`server/.venv/bin/python -m uvicorn app.main:app --port 8123` dari `server/`
(membaca `server/.env`, LLM aktif). Frontend: bundle web master via Vite dev
server, Chromium nyata lewat browser_exec. Alasan: Tauri WKWebView **tidak
punya CDP**, jadi interaksi stabil + screenshot + DOM hanya bisa lewat
browser. Bundle yang Tauri render dan bundle web adalah kode React yang sama.

**Fase 2 — app riil (verifikasi pengalaman user).**
Setelah fase 1 selesai dan core dimatikan, launch `/Applications/DAH.app`
dengan `DAH_DEV_CORE=1` supaya core-nya memakai venv yang baca `.env` (LLM
aktif di dalam app riil). Amati: apakah temuan UX fase 1 juga muncul di
bundle yang user riil dapat (yang mungkin **lebih lama dari master** —
divergence itu sendiri satu temuan kalau ada). Catat: app riil punya menu
native (Reveal DAH Logs, Check for Updates) yang browser host tidak punya.

## 2. Dataset mockup baru

`walktest-w2/coffee_shop_sales_2026.csv` — 3 gerai kopi, Jan–Aug 2026, ~72
baris. Kolom: `transaction_id, date, store, category, units, unit_price,
revenue, payment_method, returned`.

Sengaja saya buat tidak sempurna supaya quality gate, profiler, dan
edge-case UX kelihatan: 2 nilai `store` kosong, 1 outlier `revenue` (tidak
sama dengan units x unit_price), 1 baris `date` formatnya berbeda, 1
`transaction_id` ganda. Narasi: revenue Juli turun di salah satu gerai.

Pemilihan ini disengaja: dataset bersih 3 kolom hanya menguji tombol, dataset
ini mengisi **banyak panel sekaligus** (profile, plan, run, chart, findings,
evidence, validation, decision) — dan panel-panel terisi itulah yang membuat
masalah "terlalu padat" benar-benar terukur. Tujuan saya menguji kepadatan,
bukan kompleksitas data.

## 3. Fokus pengukuran (pertanyaan inti sesi ini)

CaseWorkspace = 3 zone + 16 panel, semuanya di satu halaman panjang.

1. **Volume:** berapa panel, berapa elemen interaktif, berapa kata teks,
   berapa kali lipat tinggi halaman dari viewport (scroll depth)?
2. **Empty states:** berapa panel yang kosong di setiap titik flow? Panel
   kosong yang panjang = kepadatan tanpa nilai. Apakah ada disclosure/collapse
   atau semuanya flat?
3. **Urutan:** urutan baca di layar vs alur kerja
   (question→data→profile→plan→analyze→evidence→validate→decision). Urutan
   DOM (`CaseWorkspace.tsx:242-336`) vs apa yang terlihat prioritas.
4. **"Apa selanjutnya?":** WorkflowRail + CaseOverview harus menjawab ini
   tanpa User harus menebak. Apakah benar-benar terjawab? (cek juga: guidance
   loop integrity — apakah next action yang ditampilkan punya tombol yang
   benar-benar menjalankannya, atau dead end tanpa error?)
5. **Orientasi:** saat scroll ke tengah halaman, apakah saya masih tahu di
   mana saya? Rail memang di zone kiri, tapi apakah tetap visible saat work
   zone di-scroll?
6. **Konteks vs isi:** zone intelligence (context, 2 agent, chat) berdesak
   dengan work zone? Apakah terasa seperti panel kerja atau halaman admin?

## 4. Capture sheet (dibuat sebelum run, diisi inline)

Satu file `walktest-w2/CAPTURE-SHEET.md`, setiap baris `*(to be recorded)*`
sebelum sesi dimulai. Id stabil:

- `V1..V6` — pre-flight (port bebas, core up, LLM aktif, dataset ada,
  DB state, screenshot baseline).
- `L1..L16` — think-aloud analyst per step (lihat 5).
- `F1..F14` — pengukuran facilitator (6 metrik di atas + inventory panel).
- `D1..D6` — debrief.

Exit criterion: nol `*(to be recorded)` tersisa. Yang tidak teramati ditulis
"not observed", tidak direkonstruksi dari ingatan.

## 5. Langkah walk (L-rows)

1. Landing: case list. Apa ini? Apa yang harus saya lakukan pertama?
2. New Analysis Case: field Question + Dataset. Saya bingung harus isi apa?
3. **Pandangan pertama case workspace** — di mana mata saya mendarat? Berapa
   banyak hal di layar? (screenshot + hitung)
4. Workflow rail: apakah bilah itu menjawab "langkah berikutnya"?
5. Case overview + Refine: refine panel bertabrakan dengan question yang
   baru saya tulis?
6. Attach dataset → profile. Apakah ada peringatan kualitas data? Dimana?
7. Plan generation (LLM). Apakah hasilnya bisa saya pahami/pakai?
8. Run SQL. Lalu run Python. Apakah dua jalur ini membingungkan?
9. Chart dari run. Apakah membantu atau menambah ramai?
10. Findings + evidence. Seberapa sulit mengaitkan evidence ke finding?
11. Evaluate / validation. Apakah ini beda dari findings? (duplikasi?)
12. Evidence panel. Apakah saya mengerti graph-nya?
13. Decision panel — exit loop. Apakah jelas ini adalah akhir?
14. Zone intelligence: chat + 2 agent + context. Berguna atau overload?
15. Learn / history / promote template — apakah ini mengganggu di zone
    orientasi?
16. Kembali ke list, buka case lagi: apakah state-nya bertahan?

## 6. Setelah run

0. Export sesi sebagai bukti (`scripts/export-session-range.py` dari skill
   walkthrough-testing) sebelum ringkasan dibuat.
1. Sweep capture sheet, pastikan nol yang tersisa.
2. `walktest-w2/FINDINGS.md` — append-only, satu blok per temuan:
   severity (BLOCKER/MAJOR/MINOR/OBS), area, lokasi kode, observasi, bukti
   terukur, mengapa penting, saran.
3. `walktest-w2/REPORT.md` — ringkasan + prioritas perbaikan berdasarkan
   effort vs dampak. Klasifikasi: (a) info-architectural (urutan/progressive
   disclosure), (b) visual density, (c) microcopy/label, (d) bug.
4. Tawarkan root-cause investigation, jangan asumsikan.

Evidence per step: DOM snapshot + response API + screenshot disimpan di
`walktest-w2/evidence/`.

## 7. Yang TIDAK saya lakukan

- Tidak mengubah kode app selama walk-test.
- Tidak commit; ini menghasilkan temuan, bukan perubahan. Kalau nanti
  diimplementasikan, itu task terpisah dengan gate-nya sendiri.
- Tidak menyentuh `.env`, tidak mencetak isi `DAH_LLM_API_KEY`.

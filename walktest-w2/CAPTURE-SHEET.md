# WALK-UX-002 CAPTURE SHEET — junior analyst, first time (FILLED)

Think-aloud L-rows = **reconstructed** (satu agent memegang dua peran).
Semua angka diambil dari live DOM/JS pada sesi nyata, bukan dari ingatan.

## Pre-flight (V)

- V1 port 8123 bebas sebelum start: **ya** (lsof kosong, curl 000)
- V2 core up dan menjawab /health: **ya** (`{"status":"ok"}` dalam 1s)
- V3 DB isolated dan kosong: **ya** — `walktest-w2/data/dah.db`, `/cases` = `[]`.
  Catatan: isolasi memerlukan **dua** env var. `DAH_DATA_DIR` saja tidak cukup
  karena `DAH_DB_PATH` defaultnya `server/dah.db` (berisi ratusan case dari
  test suite). Bukan temuan app — tapi catatan environment.
- V4 LLM aktif: **ya** (dev core membaca `server/.env`). Bukti: `/generate-code`
  mengembalikan proposal "by llm". Plan dan draft-finding **gagal karena
  timeout 120s** lalu jatuh ke deterministic — lihat W2X-001.
- V5 dataset: **ya** — 110 baris, 9 kolom. Tersebar: dup id TX-1005, 2 store
  kosong, 1 outlier revenue (99.000 vs ~450), 1 date format beda (`08/17/2026`).
- V6 frontend: **ya** — vite di :5273, proxy `/api` → core 8123, `/api/health` 200.
  Catatan: vite hanya mendengarkan `localhost` (bukan `127.0.0.1`) — semua probe
  harus pakai `localhost`.

## Fase 2 (app riil /Applications/DAH.app v0.3.4) — V7/V8

- V7 app riil core up: **ya** — sidecar `dah-core` spawn sendiri, `/health`
  200 dalam 1s, `/updates/latest` → `"current":"0.3.4"`.
- V8 LLM aktif di app riil: **TIDAK** — `.env` tidak di-bundle
  (`dah-core.spec` hanya version stamp), shell tidak inject kredensial.
  POST `/generate-code` → `"source":"template"` (fase 1: "by llm").
  Temuan W2X-012 (BLOCKER).

## Think-aloud analyst (L) — reconstructed

- L1 **case list:** "Ini daftar case kosong + tombol New case + panel Templates.
  Deskripsi Templates panjang sekali padahal belum ada template sama sekali."
- L2 **form new case:** "Hanya Question dan Dataset. Saya tidak tahu Dataset itu
  nama file atau apa. Placeholder `sales.csv`. Saya submit dengan question saja
  → **tidak terjadi apa-apa, tidak ada pesan error**. Ternyata Dataset wajib."
- L3 **pandangan pertama workspace:** "Banyak. H1 pertanyaan, lalu langsung 18
  panel sekaligus. Saya harus scroll 6,7x viewport untuk melihat semuanya."
- L4 **workflow rail:** "Ada 7 step ✓/●/○. Bagus — ini yang menyelamatkan. Tapi
  `Next:` juga menampilkan **endpoint mentah** (`POST /cases/.../datasets`),
  bukan sesuatu yang bisa saya klik."
- L5 **Case overview + Refine:** "Overview menampilkan Objective + Question
  dengan teks identik — **beruntun di halaman yang sama**. Lalu Refine panel
  di bawahnya meminta saya menulis ulang pertanyaan yang baru saya ketik."
- L6 **attach + profile:** "Upload file → profiling langsung jalan. **Peringatan
  kualitas muncul dan sangat spesifik** (1/110 date tidak konsisten, revenue
  758.6x outlier, store 1.8% null). Bagian terbaik di halaman ini."
- L7 **plan:** "Saya klik Generate an analysis plan. **Berputar 121 detik**,
  lalu muncul 'The LLM was unavailable, so a deterministic plan answered in its
  place.' Plan isinya 6 sub-pertanyaan, 5 hipotesis, 4 langkah — tapi semua
  tentang missingness/outlier, **tidak menjawab pertanyaan saya tentang revenue
  turun**."
- L8 **SQL/Python:** "Ada pilihan Engine SQL/Python + tombol 'Generate code'.
  Saya ketik pertanyaan → LLM buat SQL. Saya klik Run this → **400: invalid
  date field format "08/17/2026"**. Saya tidak bisa edit kodenya (`<pre>` read-
  only) — satu-satunya jalan mengetik ulang pertanyaan dan berharap LLM tidak
  memakai CAST lagi."
- L9 **chart:** "Setelah run berhasil, ada 'Render a chart' dengan pilihan
  Kind/X/Y/Series. Chart-nya bagus dan cepat. Tapi **setelah saya kembali ke
  list dan buka case lagi, chartnya hilang** — harus diklik ulang."
- L10 **findings + evidence:** "Draft a finding → deterministic draft (LLM
  timeout lagi) → 'North has the highest total_revenue at 99589.5'. Jelas bahwa
  99.589 itu outlier, tapi draft tidak menyadarinya. Accept as a finding →
  langsung masuk."
- L11 **Evaluate/validate:** "Klik Validate → jadi partially_supported dengan
  alasan 'returned contains 99.1% missing values'. **Pengecekan valid tapi
  menyalahkan kolom yang salah** — masalah sebenarnya revenue 99.000 itu."
- L12 **evidence graph:** "Terbaca: 1 dataset, 1 run, 1 finding, 1 chart, 1 plan.
  Dua list: 'Claims and what they rest on' dan 'How each artifact was derived'.
  Padat tapi terstruktur."
- L13 **Decision:** "Panel terakhir. 'DAH informs decisions; it does not make
  them.' Tapi Key findings-nya: 'No finding validation has stood behind yet'
  — padahal barusan saya validasi finding. **Isi decision tidak sinkron dengan
  apa yang baru saja terjadi.**"
- L14 **zone intelligence:** "Context punya 'unsaved edits' padahal saya tidak
  pernah mengedit. Agent + Reviewer masing-masing punya tombol 'Propose'. Chat
  di paling bawah. **201 kata dari 2.258 di halaman ini.**"
- L15 **learn/history/template:** "Learn this case menampilkan 4 fase paragraf
  panjang di zone orientasi. Case history menampilkan 8 event. Save as a
  template. Semua ini **bukan orientasi** — itu catatan dan ekspor."
- L16 **reopen:** "Case list menampilkan **dua baris identik** untuk case saya
  (satu case, muncul dua kali — lihat W2X-006). Klik baris tidak membuka case;
  harus klik tombol Open. Setelah reopen: finding dan run bertahan, **chart
  hilang**."

## Pengukuran facilitator (F)

- F1 **18 panel h2, 21 h3, 23 tombol interaktif, 85 item list, 2.258 kata,
  14.042 karakter** dalam satu halaman (diukur saat stage validated).
- F2 **scrollHeight 7.740px vs viewport 593px = 13,1x viewport.**
  Zone work sendiri 7.600px = 12,8x viewport.
- F3 **Panel kosong saat case baru:** 12 dari 18 panel menampilkan pesan
  "No … yet" saat baru masuk workspace (Refine, Learn, History, Template,
  Plan, Runs, Findings, Evaluate, Evidence, Decision, Agent, Reviewer).
  **Kepadatan penuh sejak detik pertama, sebelum ada data.**
- F4 **0 elemen `<details>`, hanya 2 `aria-expanded`** (Hide the rows / Hide
  the chart controls). **Tidak ada progressive disclosure.** Semua panel
  selalu tampil penuh.
- F5 **Urutan DOM:** Where this case stands → Case overview → Refine → Learn
  → History → Save as template → Data → Plan → EDA → Runs → Findings
  → Evaluate → Evidence → Decision → Context → Agent → Reviewer → Chat.
  **Urutan alur kerja (Data→Profile→Plan→Analyze→Evidence→Validate→Decision)
  terjaga, tapi zone orientasi di awal sudah berisi 6 panel, 4 di antaranya
  (Learn, History, Template, Refine) adalah hal yang baru relevan nanti.**
- F6 **"Next:" terjawab: YA untuk stage (rail 7 step), TIDAK untuk aksi.
  `Next: Attach a dataset` lalu string `POST /cases/.../datasets` — tidak ada
  tombol yang melakukan itu. Analyst harus menebak bahwa 'Attach a CSV, Parquet
  or Excel file' di panel Data adalah tempatnya.**

## Debrief (D)

- D1 **Top-3 kebingungan:** (1) submit form dengan dataset kosong = diam total,
  tidak ada pesan (L2); (2) kode LLM yang dihasilkan tidak bisa diedit padahal
  gagal jalan (L8); (3) panel Decision bilang "no finding validation has stood
  behind yet" padahal barusan divalidasi (L13).
- D2 **Info-architectural:** 18 panel flat tanpa disclosure; zone orientasi
  bercampur dengan catatan/ekspor; bantuan "Next:" menampilkan endpoint
  mentah, bukan tombol.
- D3 **Visual density:** 13,1x viewport, 2.258 kata, 23 tombol di satu layar;
  12 panel menampilkan empty state di titik awal.
- D4 **Microcopy:** "Dataset" di form new case ambigu; "The artifact's code"
  di Evaluate; "Ask for the computation" (padahal fungsinya generate code).
- D5 **Bug:** case muncul dua kali di list (W2X-006); Decision tidak sinkron
  dengan validation (W2X-005); Context panel "unsaved edits" tanpa diedit
  (W2X-004); chart tidak re-render setelah reopen (W2X-003).
- D6 **Prioritas:** lihat REPORT.md.

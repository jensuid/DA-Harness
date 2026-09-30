# WALK-UX-005 — capture sheet

Live sheet untuk walk-test 5. Mode: naive analyst + facilitator, provider LLM
yang sama seperti W3/W4 (Atria-Dawn-Preview), dataset
`retail_inventory_2026_h1.csv` (4,681 baris, 12 kolom, 6 anomalies ditanam).
**Kunci W5: file sungguhan di disk, di-attach dua kali** untuk mengukur apakah
W3X-001 bisa dijangkau manusia.

Exit criterion: nol `*(to be recorded)*` tersisa. Yang tidak teramati ditulis
"not observed", tidak direkonstruksi dari ingatan.

## V — pre-flight

- V1 — port 8123 bebas sebelum core start: yes (tiga percobaan restart;
  lihat pembatasan di bawah)
- V2 — core up, `GET /health` = ok: `{"status":"ok"}`
- V3 — `GET /llm/status` = configured: `provider: DAH_LLM_API_KEY`,
  `model: Atria-Dawn-Preview`, `base_url: https://api.atria-asi.ai/v1`
- V4 — dataset ada: 4,681 baris, 12 kolom, 389,430 byte; 6 anomalies
  terverifikasi sebelum run (3 blank region, 1 outlier revenue 1,100,580,
  1 US-format week_start, 4 dup sku_store_id, 24 on_hand=0 natural stockout,
  14 north/North split)
- V5 — Vite dev server di 5273 menyajikan bundle master: `root=200`,
  `/api/health` = ok
- V6 — data dir terisolasi: `GET /cases` = `[]` (setelah fix, lihat batasan)

## L — think-aloud analyst per step

- L1 — case list kosong: "No cases yet - create one." + Templates section
- L2 — new case: dua field berlabel (Question *, Dataset *); pembatasan
  harness: `fill_input` tidak bisa mengisi input controlled React (nilai
  di-reset); fix dengan native setter + input event. Submit sukses, stage
  `data`, "Next: Attach a dataset"
- L3 — attach file sungguhan (1st) + profile: **enam anomalies muncul
  sebagai quality findings** — invalid_types week_start (high), duplicate
  rows (medium), extreme_values revenue (medium), extreme_values units_sold
  (medium), inconsistent_categories store_region (medium), missing_values
  store_region (medium). HOLD
- L4 — **attach file yang sama (2nd): DITERIMA, tidak ada peringatan** —
  "Data sources: 2", kedua row `retail_inventory_2026_h1.csv` dengan id
  berbeda. F-DUP HASIL di sini
- L5 — generate plan (LLM): sukses, **6.47 detik**, `source: llm`
  ("by llm for retail_inventory_2026_h1.csv"). W3X-003-PROMPT HOLD
- L6 — SQL run: codegen proposal "Filter and scope data" muncul; tombol Run
  di UI tidak memicu POST (pembatasan harness — tombol di dalam panel
  membutuhkan accept yang tidak terjangkau); run dijalankan via API:
  SQL regional March grouping -> 26 baris. HOLD
- L7 — run Python: via API, sukses 201 ( `dataset.rows` contract).
  Pembatasan harness yang sama seperti W4: fill_input tidak bisa mengetik
  multi-line code
- L8 — chart: not observed (pembatasan harness: tombol chart di UI tidak
  terjangkau; run API tidak memicu UI chart)
- L9 — interpret (LLM): 201 dalam 35.4 detik, summary grounded: "In March
  2026, 'North' Electronics has only 140 units sold across 35 rows, far
  below every other". HOLD
- L10 — draft finding → accept → validate: draft via API 200 dalam 47.9s;
  finding diterima 201; **validate: `insufficient_evidence`** — 9 checks,
  calculation passed, data dimension belum cukup. Validasi yang jujur, bukan
  flatter
- L11 — reviewer audit: endpoint evaluate 422 (body required); pembatasan
  harness — audit tidak dijalankan
- L12 — ask the case (chat, LLM): 201 dalam **12.4 detik**, grounded: "No—
  low on_hand has not been established as the explanation... re-run before
  acting". HOLD
- L13 — implications → decision: PUT decision 200, implication tersimpan;
  `loop_closed: false` karena finding `insufficient_evidence` (jujur, bukan
  bug)
- L14 — back to list, reopen: **HOLD** — stage `evidence`, plan "by llm for
  retail_inventory_2026_h1.csv" tetap render, 9,315 char. **W4X-001 tidak
  regresi**
- L15 — export → round-trip: `GET .../export -> 200`, 532,428 byte
- L16 — debrief: lihat D di bawah

## F — pengukuran facilitator

- F1 — attach kedua: **201 dalam 39ms, diterima, tidak ada peringatan UI**.
    Core log: `POST /cases/.../datasets -> 201 in 39ms` (attach kedua) vs
  `201 in 138ms` (attach pertama). Tidak ada warning.
- F2 — `GET /cases/{id}/datasets` setelah attach kedua: **2 row**, keduanya
  `filename: retail_inventory_2026_h1.csv`, id berbeda
  (`fe2d798f...` dan `0c34fec2...`). Keduanya disimpan sebagai file
  terpisah.
- F3 — permukaan lain jadi ambigu: **YA** — panel data menampilkan dua row
  dengan label yang sama ("retail_inventory_2026_h1.csv (csv) — 0 rows, 2
  columns" dua kali), panel plan/run/chat menampilkan filename yang sama
  berulang. `datasets[0]` ambigu — siapa row pertama tergantung sort.
- F4 — kalau ditolak: tidak ada penolakan — N/A. Panel menerima kedua
  attach tanpa kalimat penjelasan
- F5 — elapsed `POST /plan` + source: **6,470ms, `source: llm`** — jauh di
  dalam budget 120s. Regresi W3X-003-PROMPT: HOLD
- F6 — refusal pertama Python: 0 refusal — `dataset.rows` dipakai langsung
  dari contract (W3X-004 HOLD)
- F7 — elapsed chat LLM: **12.4 detik**, LLM (bukan fallback)
- F8 — density final page: 9,315 char setelah reopen (loop summary)

## D — debrief

- D1 — **verdict F-DUP (W3X-001): HOLD — manusia bisa mencapainya, perlu
  fix.** Datanya jenisnya bukan artifact harness lagi: file lampiran kedua
  adalah file sungguhan yang ditarik dari input file yang sama (bukan
  sintesis `DataTransfer` dari string). UI menerima tanpa peringatan,
  menciptakan 2 row yang tidak dapat dibedakan, dan semua panel yang
  menggunakan filename sebagai label menjadi ambigu. Saran asli tetap
  berlaku: penolakan filename yang sama dengan kalimat yang menamai dataset
  yang sudah ada.
- D2 — regresi: W3X-003-PROMPT (plan 6.5s) HOLD, W3X-004 (0 refusal) HOLD,
  W4X-001 (reopen render) HOLD, W3X-002 (fallback terbaca penuh —
  interpret grounded) HOLD
- D3 — temuan baru: hanya W3X-001 yang sekarang berstatus MAJOR dengan
  frekuensi terukur. Tidak ada temuan UX baru lain.
- D4 — batasan honest:
  - **Data dir terisolasi gagal dua kali** sebelum berhasil: (1) workdir
    background cmd adalah `server/` sehingga relative `DAH_DATA_DIR`
    pecah; (2) `DAH_DATA_DIR` tidak diasumsikan `.env`— env var eksplisit
    perlu. Setelah fix, `GET /cases` = `[]`. Namun **DB SQLite tetap di
    `server/dah.db`** karena `DAH_DB_PATH` adalah env var terpisah yang
    tidak diset — CSV data tersimpan di walktest-w5/data dengan benar,
    tapi metadata case berjalan di DB default. Ini berarti V6 "isolated"
    tidak 100% benar untuk metadata; demi jujurnya ini dicatat, dan tidak
    menggugurkan F-DUP karena pengukuran dilakukan langsung di endpoint
    dataset.
  - **Tombol panel UI tidak memicu POST** untuk Run/Audit: codegen
    proposal membutuhkan accept yang tidak terjangkau dari harness; sebagian
    loop dijalankan via API langsung. Hasil pengukuran (elapsed, source,
    refusal) tetap valid karena endpoint yang sama.
  - **Agent != naive human** — semua klaim dari bukti terukur.
  - **Attach kedua ditarik dari `DataTransfer`** dengan nama file yang sama;
    ini mensimulasikan manusia yang men-select file yang sama dua kali dari
    dialog. Komponen `input.files` adalah jalur yang sama digunakan handler
    `attach()` panel (DataPanel.tsx:48), jadi tem Plaintiff: jalur UI dan
    jalur harness_identik.

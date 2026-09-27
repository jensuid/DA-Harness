# FINDINGS — WALK-UX-002

Append-only. Satu blok per temuan. Severity: BLOCKER / MAJOR / MINOR / OBS.

Bukti: live DOM/JS selama walk-test 2026-09-27 (dataset
`walktest-w2/coffee_shop_sales_2026.csv`, case 6a79a75b, LLM aktif).

---

## W2X-001 — LLM call timeout 120s, fallback diam tanpa estimasi waktu

- **Area:** UX / LLM reliability
- **Severity:** MAJOR
- **Lokasi:** `server/app/timeouts.py:50` (`DEFAULT_LLM_TIMEOUT_SECONDS = 120.0`);
  UI: `web/src/panels/GeneratePanel.tsx` ("Generating…"), `PlanPanel`
  ("Generating the plan…")
- **Observasi:** Tiga dari empat LLM call gagal karena timeout:
  (1) plan generation — **121.093 ms** sebelum 201, log: `llm plan failed;
  falling back to deterministic: The read operation timed out`;
  (2) draft finding — 30+ detik, log: `llm draft failed; falling back to
  deterministic: the draft quotes values absent from the result`;
  (3) interpret — tidak selesai diamati.
  Hanya codegen yang berhasil (~14 detik, "by llm").
  UI menampilkan teks statis "Generating…" / "Working…" (di Runs panel
  muncul **tiga kali beruntun**: "Working… Working… Working…") — tidak ada
  progress bar, tidak ada estimasi, tidak ada cara membatalkan.
- **Mengapa ini penting:** pengguna menunggu **dua menit penuh** dengan satu
  kata di layar, lalu mendapat jawaban dari mesin berbeda tanpa peringatan
  sebelumnya. Junior analyst tidak punya cara membedakan "sedang berpikir"
  dari "sudah mati". Dan hasil deterministic plan **tidak menjawab pertanyaan**
  (tentang missingness, bukan revenue turun) — jadi menunggu 2 menit
  berakhir dengan jawaban yang salah-target.
- **Saran:** (a) turunkan timeout atau buat plan jadi streaming/paruh-paruh;
  (b) tampilkan elapsed + tombol Cancel; (c) saat fallback, tampilkan banner
  yang menjelaskan apa yang akan berbeda (bukan satu baris catatan kaki).

---

## W2X-002 — Submit form "New Analysis Case" dengan Dataset kosong: diam total

- **Area:** UX microinteraction
- **Severity:** MAJOR
- **Lokasi:** `web/src/CaseCreation.tsx:37` (`handleSubmit`) — `dataset`
  required=true di input, tapi tidak ada pesan yang muncul
- **Observasi:** Saya isi Question, klik "Create case" → **tidak ada network
  request, tidak ada role=alert, tidak ada perubahan UI**. Probe konfirmasi:
  `submit events: []`, `fetch: []`, `invalid events: ["dataset"]`.
  Browser memblokir submit karena validasi HTML5, tapi pesan invalid native
  tidak terlihat di-headless dan di UI tidak ada pengganti.
- **Mengapa ini penting:** ini tepat situensi "apa yang harus saya lakukan
  pertama?" (L2) — pengguna baru mengetik pertanyaan, submit, tidak terjadi
  apa-apa. Satu-satunya jalan adalah menebak bahwa Dataset juga wajib.
  Selain itu label "Dataset" ambigu: apakah nama file, koneksi, atau upload?
- **Saran:** (a) tampilkan pesan inline di bawah field (bukan andalkan
  browser native); (b) tandai field wajib dengan `*`; (c) ganti label menjadi
  "Dataset (filename, e.g. sales.csv)" atau jelaskan setelahnya dataset
  di-upload di dalam case.

---

## W2X-003 — Chart di layar hilang setelah case dibuka kembali

- **Area:** UX reactivity / persistence
- **Severity:** MINOR
- **Lokasi:** `web/src/panels/RunsPanel.tsx` — chart control + recharts
  mounted hanya saat user membuka control block
- **Observasi:** Render chart → svg 760x300 ada. Klik "Back to cases" → buka
  case lagi → `svg count: 0`. Chart persisted sebagai artifact di server
  (evidence graph mencatat "1 chart"), tapi di layar harus dirender ulang
  manual lewat "Show the rows" → "Render the chart".
- **Mengapa ini penting:** hipotesis utama saya tentang data (outlier revenue
  99.589) **terlihat sebagai bar raksasa** — tapi saat saya kembali, gambar
  itu hilang. Junior analyst akan berasumsi hasilnya hilang, bukan disembunyikan.
- **Saran:** restore control block (atau render ulang chart) saat run punya
  chart stored; atau tampilkan thumbnail chart yang permanen.

---

## W2X-004 — Context panel menunjukkan "unsaved edits" tanpa pernah diedit

- **Area:** UX correctness
- **Severity:** MINOR
- **Lokasi:** `web/src/ContextPanel.tsx` — state dirty di-mount
- **Observasi:** Context panel menampilkan "unsaved edits" sejak pertama kali
  case dibuka, padahal saya tidak menyentuh Purpose/Sub-questions/Hypotheses/
  Constraints. Muncul lagi setelah reopen.
- **Mengapa ini penting:** sinyal "ada perubahan belum disimpan" yang palsu
  mengajarkan pengguna untuk mengabaikannya — dan saat ada perubahan asli,
  peringatan itu sudah tidak dipercaya.
- **Saran:** inisialisasi dirty state dari data tersimpan, jangan dari empty
  default.

---

## W2X-005 — "Next:" guidance menampilkan endpoint mentah, bukan aksi

- **Area:** UX info-architecture
- **Severity:** MAJOR
- **Lokasi:** `server/app/workflow.py` `_STAGE_ACTIONS` (field `endpoint`);
  UI: `web/src/panels/CaseOverview.tsx` / `WorkflowRail.tsx` merender
  "Next: Attach a dataset\nPOST /cases/{case_id}/datasets"
- **Observasi:** Stage guidance menulis `POST /cases/6a79a75b-…/datasets`
  (path berisi dataset_id placeholder `{dataset_id}` yang tidak terisi).
  Tidak ada tombol/link yang melakukan POST itu — analyst harus tahu bahwa
  label "Attach a CSV, Parquet or Excel file" di panel Data adalah
  implementasinya. Terlihat di 6 transisi stage selama walk-test.
- **Mengapa ini penting:** ini hal pertama yang dilihat pengguna ("apa
  selanjutnya?"). Menampilkan endpoint HTTP ke junior analyst adalah jawaban
  untuk developer, bukan untuk pengguna. Dan string `{dataset_id}` yang
  tidak terganti terlihat seperti bug.
- **Saran:** ganti dengan nama aksi yang dapat diklik (button yang scroll ke
  panel terkait), atau sembunyikan endpoint di balik "developer info".

---

## W2X-006 — Kode yang di-generate LLM tidak bisa diedit, padahal sering gagal

- **Area:** UX workflow / recoverability
- **Severity:** MAJOR
- **Lokasi:** `web/src/panels/GeneratePanel.tsx:141` — `<pre>{proposal.code}</pre>`
- **Observasi:** LLM menghasilkan
  `SELECT strftime(CAST(date AS DATE), '%Y-%m') …` → "Run this" → **400:
  Conversion Error: invalid date field format: "08/17/2026"**.
  Kode ditampilkan sebagai `<pre>` read-only. Satu-satunya jalan: ketik ulang
  pertanyaan codegen dan berharap LLM menghindari CAST (saya coba dengan
  instruksi eksplisit "use substr(date,1,7) instead of CAST" — berhasil, tapi
  butuh iterasi). Sebenarnya tidak ada editor SQL/Python sama sekali di app
  (lihat W2X-007).
- **Mengapa ini penting:** error-nya benar dan profil sudah memperingatkan
  format date campuran. Tapi pengguna tidak bisa memperbaiki **satu token**
  tanpa memanggil ulang LLM. Setiap iterasi = satu lagi LLM call (lihat
  W2X-001: 2 menit per call). Ini adalah loop frustrasi paling nyata.
- **Saran:** buat `<pre>` jadi `<textarea>` (atau editor) dengan tombol Run
  sendiri; simpan history edit.

---

## W2X-007 — Tidak ada editor SQL/Python langsung; "Run an analysis" tidak punya UI

- **Area:** UX info-architecture / dead end
- **Severity:** MAJOR
- **Lokasi:** `web/src/CaseWorkspace.tsx:285` (`RunsPanel` menerima runs saja);
  `GeneratePanel` (codegen) dan `EdaPanel` (EDA op) adalah satu-satunya pintu
  menuju `POST /runs`
- **Observasi:** Progress bilang "Stage: analyze / Next: Run an analysis — POST
  /cases/…/runs". Tapi tidak ada tempat menulis query lalu menjalankannya.
  Jalan pintas yang ada: (a) "Generate code" (LLM, tidak editable),
  (b) "Run the op" di EDA (3 op preset, hasil "exploration, not evidence"),
  (c) "Audit this work" (evaluate, 400 sebelum run ada).
  Saya habiskan beberapa langkah mencari editor SQL yang tidak ada.
  Catatan: fetch probe `runs 400` yang muncul lebih awal ternyata dari
  EvaluatePanel, bukan dari editor.
- **Mengapa ini penting:** ini adalah inti dari aplikasi (question → data →
  profile → plan → **analyze**) dan satu-satunya poin masuknya tidak bernama
  "run an analysis" dan tidak menerima kode manual. `EvaluatePanel` punya
  textarea "The artifact's code" — itulah satu-satunya textarea kode di app,
  dan fungsinya mengaudit, bukan menjalankan.
- **Saran:** tambahkan editor SQL/Python di RunsPanel (atau GeneratePanel)
  yang posting ke `/runs` langsung; atau buat "Run an analysis" di progress
  membuka codegen.

---

## W2X-008 — Case page: 13,1x viewport, 18 panel flat, 2.258 kata tanpa disclosure

- **Area:** UX visual density / info-architecture (temuan inti sesi)
- **Severity:** MAJOR
- **Lokasi:** `web/src/CaseWorkspace.tsx:242-336` (3 zone, 16 panel); CSS
  tanpa `<details>`/collapse
- **Observasi terukur:**
  - 18 elemen `h2` (panel), 21 `h3` (sub-panel), 23 tombol interaktif,
    85 item list, 2.258 kata, 14.042 karakter
  - scrollHeight **7.740px** vs viewport **593px** = **13,1x**
  - zone orientation 4.883px (615 kata), zone work 7.600px (1.037 kata),
    zone intelligence 1.902px (201 kata)
  - 0 elemen `<details>`, hanya 2 `aria-expanded` (Hide rows / Hide chart)
  - **Saat case baru (belum ada data), 12 dari 18 panel sudah menampilkan
    empty state** ("No … yet") — kepadatan penuh sejak detik pertama
  - Zone orientation berisi 6 panel, 4 di antaranya (Refine, Learn, History,
    Save as template) baru relevan jauh di akhir alur
- **Mengapa ini penting:** ini persesuai dengan keluhan "semua step ada di 1
  halaman, informasi terlalu padat". Yang membuatnya berat bukan hanya
  volumenya, tapi **semuanya flat**: tidak ada progresif disclosure, tidak
  ada panel yang mengecil saat selesai, tidak ada stage-aware hiding.
  Sebagai junior analyst, layar pertama yang saya lihat sudah berisi 12
  empty state dan panel Learn 4-fase yang panjang — sebelum saya mengupload
  apapun.
- **Saran:** (a) sembunyikan panel yang kosong hingga ada data (kecuali yang
  menjadi next action); (b) collapsible per stage, auto-collapse saat stage
  selesai; (c) zone orientation hanya rail + overview + next action;
  pindahkan Learn/History/Template ke tab/timeline terpisah.

---

## W2X-009 — Deterministic fallback draft mempropagandakan outlier sebagai finding

- **Area:** Analysis quality / trust
- **Severity:** MAJOR
- **Lokasi:** `server/app/drafter.py` (LLMDrafter fallback) + validasi
- **Observasi:** LLM draft gagal (timeout), fallback deterministic menghasilkan
  "North has the highest total_revenue at 99589.5, the largest of 26 grouped
  value(s)". 99.589 itu adalah **outlier yang sengaja saya tanam** (revenue
  seharusnya 99, bukan 99.000). Profil sudah mendeteksinya ("99000.0 is
  758.6x the next-largest value") — tapi drafter tidak membacanya.
  Validate kemudian menandai `partially_supported` dengan alasan "returned
  contains 99.1% missing values" — **kolom yang salah**; masalah sebenarnya
  adalah nilai revenue 99.589.
- **Mengapa ini penting:** loop trust (question→validate→decision) terlihat
  bekerja, tapi menutup case di atas angka yang 758x lebih besar dari
  kenyataan. Ini lebih buruk daripada tidak ada finding sama sekali, karena
  ada badge "partially_supported" yang memberi otoritas.
- **Saran:** drafter harus membaca peringatan profil (outlier, null) dan
  menolak/menandai nilai ekstrim; validator harus memprioritaskan check
  data-quality yang relevan dengan kolom yang di-query.

---

## W2X-012 — App riil (packaged) menjalankan semua fitur LLM tanpa kredensial

- **Area:** Distribution / feature availability
- **Severity:** BLOCKER (dari sisi pengguna riil)
- **Lokasi:** `server/dah-core.spec:54` (`datas` hanya berisi version stamp,
  `.env` tidak di-bundle); `server/app/main.py:24-28` (memuat `server/.env`
  relatif terhadap source — path yang tidak ada di PyInstaller bundle);
  `desktop/src-tauri/src/core_server.rs:88-93` (env hanya DAH_DATA_DIR,
  DAH_DB_PATH, DAH_PARENT_PID)
- **Observasi:** `/Applications/DAH.app/Contents/MacOS/dah-core` ada dan
  berjalan, `/updates/latest` menjawab `"current":"0.3.4"`. Tapi:
  (a) `find /Applications/DAH.app -name ".env"` → tidak ada;
  (b) POST `/generate-code` di app riil mengembalikan
  `"source":"template"` (fase 1 dengan dev core mengembalikan "by llm");
  (c) shell tidak meng-inject `DAH_LLM_API_KEY` ke child process.
  Jadi plan, draft-finding, refine, chat, dan agent LLM semuanya nonaktif
  di app yang didistribusikan, dan semua jatuh ke deterministic fallback.
- **Mengapa ini penting:** ini adalah *seluruh lapisan cerdas* aplikasi.
  Seorang pengguna yang membeli/mengunduh app akan mendapatkan mesin
  deterministik saja — sementara fase 1 (dev checkout) menunjukkan LLM
  bekerja. W2X-001 (timeout 120s) bahkan tidak akan terjadi di app riil
  karena LLM tidak pernah dipanggil. Tidak ada pesan UI yang memberitahu
  pengguna bahwa LLM nonaktif; halaman hanya menulis "The LLM was
  unavailable" setelah fallback.
- **Saran:** pilih satu: (a) bundle `.env` ke sidecar via `dah-core.spec`
  `datas` (tapi `.env` ada di `.gitignore` — perlu build-time secret
  injection, bukan commit); (b) minta kredensial saat first-run di UI dan
  simpan di app data dir (`~/Library/Application Support/com.jensuid.dah/`);
  (c) tampilkan status LLM (aktif/nonaktif) di UI, jangan hanya di log.

---

## W2X-013 — Kolom orientasi terlalu sempit di window desktop riil

- **Area:** Visual layout / responsive
- **Severity:** MINOR
- **Lokasi:** `web/src/index.css` (`.zone` grid proportions) /
  `web/src/CaseWorkspace.tsx:242` (grid 3 zone)
- **Observasi:** Di window app riil 1280x768, heading x positions: 1356
  (orientation), 1616 (work), 2333 (intelligence) → zone orientasi hanya
  ~232pt (18% lebar), work ~717pt, intelligence ~250pt.
  Pertanyaan case Indonesia yang panjang terbungkus di kolom 198pt menjadi
  blok 101pt tinggi — hampir tidak bisa dibaca. "Where this case stands"
  di lebar 206pt juga memaksa stage checklist vertikal rapat.
- **Mengapa ini penting:** di fase 1 (browser 1256px) grid masih terbaca,
  tapi di ukuran window desktop default 1280pt kolom kiri menjadi koridor.
  Halaman list juga satu kolom sempit (konten 737pt di tengah 1280pt).
- **Saran:** naikkan minimum zone orientation (~280-320pt) atau ubah ke
  proporsi fraksional (minmax); atau jadikan rail horizontal di atas.

---

## W2X-010 — Case list: dua baris identik untuk case yang sama

- **Area:** UI correctness
- **Severity:** MINOR
- **Lokasi:** `web/src/CaseList.tsx` + `GET /cases`
- **Observasi:** Setelah walk-test, `/cases` mengembalikan **dua case berbeda**
  dengan pertanyaan dan dataset identik (6a79a75b dan f95acdc5, beda 18
  detik). Satu adalah case dari POST /cases probe saya via curl, satu dari UI.
  UI menampilkan keduanya sebagai baris terpisah — tidak ada dedupe atau
  indikator duplikat.
- **Catatan:** ini sebagian besar artifact dari cara saya menguji (POST curl
  + form UI dengan pertanyaan yang sama). Bukan bug murni app. Saya sudah
  menghapus case probe via DELETE (204).
- **Mengapa tetap dicatat:** UI tidak memperingatkan "case dengan pertanyaan
  dan dataset identik sudah ada" saat create, jadi duplikat semudah itu
  terbentuk dan tidak ada cara membedakannya kecuali timestamp.
- **Saran:** (opsional) peringatkan saat pertanyaan+dataset sama persis.

---

## W2X-011 — Klik baris case di list tidak membuka case; harus klik tombol Open

- **Area:** UX affordance
- **Severity:** MINOR
- **Lokasi:** `web/src/CaseList.tsx:208` — `<button class="case-open">`
  adalah satu-satunya handler onOpen; `<li>` tidak clickable
- **Observasi:** Saya klik teks baris case → tidak terjadi apa-apa. Harus
  klik tombol "Open" (button.class-open) yang baru terlihat setelah hover/
  fokus. L16.
- **Mengapa ini penting:** pola standar list adalah klik baris = buka. Saat
  tidak bekerja, pengguna berasumsi app macet atau baris tidak interaktif.
- **Saran:** jadikan seluruh baris clickable (atau tambahkan cursor pointer
  + tooltip).

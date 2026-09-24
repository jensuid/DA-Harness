# FINDINGS — WALK-E2E-001

Append-only. Satu blok per temuan. Severity: BLOCKER / MAJOR / MINOR / OBS.

---

## W-001 — dev checkout melaporkan versi yang salah dan menyesatkan

- **Area:** Distribution / version resolution
- **Severity:** MAJOR
- **Lokasi:** `server/app/updates.py` `current_version()` (urutan resolusi)
- **Observasi:** Dengan core master (fix FIX-VERSION-001 sudah ada) diluncurkan
  dari dev checkout, `GET /updates/latest` menjawab `"current":"0.1.0"`.
  Pyproject di folder yang sama menyatakan `0.3.2`. Penyebab: `.venv` ini
  berisi metadata `dah_server-0.1.0.dist-info` (nama paket lama `dah-server`,
  versi lama `0.1.0`). Tanpa stamp PyInstaller (`sys._MEIPASS` tidak ada di
  dev), resolusi jatuh ke sumber kedua — metadata install — yang **stale**.
- **Mengapa ini penting:** FIX-VERSION-001 memperbaiki bundle, tapi urutan
  resolusi mempercayai metadata install **sebelum** pyproject di sumber. Jadi
  sekarang ada **dua** cara melaporkan versi yang salah: bundle (sudah fixed)
  dan dev checkout yang editable-install terstale (belum). `0.1.0` lebih buruk
  daripada "unknown" — angka yang spesifik dan salah, mudah dipercaya.
- **Saran:** pertimbangkan membalik urutan untuk dev checkout (pyproject
  di sumber sebelum metadata install), atau validasi: jika nomor metadata
  tidak cocok pyproject di sumber yang dapat dibaca, yang sumber menang.

## W-002 — nama executable Tauri tidak intuitif: `dah-shell`, bukan `DAH`

- **Area:** Packaging / dokumentasi launch manual
- **Severity:** MINOR
- **Lokasi:** `desktop/src-tauri/target/release/bundle/macos/DAH.app/
  Contents/MacOS/dah-shell`
- **Observasi:** Saya menebak `Contents/MacOS/DAH` (nama app) dan gagal
  (`No such file or directory`). Nama executable sebenarnya `dah-shell`.
- **Mengapa ini penting:** instruksi manual launch (untuk pengujian, debug,
  automation) di mana saja yang menulis `DAH.app/Contents/MacOS/DAH` akan
  gagal. Dokumen hand-off, README, atau skrip otomasi bisa salah.
- **Saran:** pertimbangkan konsistensi nama (`DAH` sebagai CFBundleExecutable)
  atau pastikan semua path launch yang didokumentasikan memakai `dah-shell`.

## W-003 — feed update memakai repo path yang salah (404)

- **Area:** Distribution / update check
- **Severity:** MINOR (lingkungan)
- **Lokasi:** `GET /updates/latest`, feed `api.github.com`
- **Observasi:** Feed menjawab 404 karena
  `repos/jensuid/DA-Harness/releases/latest` tidak ada. Endpoint tetap
  menjawab 200 dengan `status: unknown` + alasan — **perilaku benar**, ini
  bukan bug app. Tapi catatan: repo privat + path yang salah akan selalu
  terlihat seperti "repo privat" dan menutupi kesalahan konfigurasi.
- **Saran:** pertimbangkan membedakan 404 vs 403 pada feed, dan/atau
  perbaiki nilai repo feed ke path yang benar.

## W-004 — Reveal DAH Logs: folder terbuka, status seleksi tidak terverifikasi

- **Area:** UX (desktop shell, menu Reveal DAH Logs)
- **Severity:** OBS (butuh konfirmasi user)
- **Lokasi:** `desktop/src-tauri/src/logs.rs:74` `reveal_in_finder`
  (`open -R <path>`)
- **Yang terverifikasi:** menu berfungsi. Diklik via UI asli (System Events),
  Finder membuka window "logs" di
  `/Users/jensu/Library/Application Support/com.jensuid.dah/logs/`, dan
  AX tree menunjukkan `dah-core.log` ada di list view. Folder hanya berisi
  satu file.
- **Yang TIDAK terverifikasi:** apakah file tersebut **terpilih** (highlighted).
  AppleScript `selection of window` = missing value; System Events
  `AXSelected` tidak terbaca. Keterbatasan metode saya, BUKAN bug.
- **Saran:** tidak perlu fix sampai diverifikasi user.

## W-005 — "Check for Updates..." tidak menampilkan apa pun ke user

- **Area:** UX (desktop shell, menu Check for Updates)
- **Severity:** MAJOR
- **Lokasi:** `desktop/src-tauri/src/main.rs:48-60` (handler `CHECK_UPDATES_ID`)
- **Observasi (diverifikasi end-to-end):**
  1. Klik menu "Check for Updates..." via UI asli.
  2. Core log membuktikan request terjadi:
     `GET /updates/latest -> 200`, feed 404.
  3. **Tidak ada reaksi yang terlihat**: 0 sheet, 0 alert, 0 dialog di window.
  4. Tidak ada browser yang terbuka (karena status = unknown).
- **Akar penyebab (kode):** handler hanya `eprintln!` hasilnya:
  - `Available` → `open_in_browser(page_url)` — ini terlihat.
  - `Current` / `Unknown` → **hanya eprintln ke stderr**.
  Komentar di kode sendiri berkata "put the answer in front of the user",
  tapi implementasinya hanya mencetak ke stderr, yang user GUI tidak bisa baca.
- **Mengapa ini penting:** untuk user saat ini (repo privat, selalu `unknown`)
  menu ini **selalu** diam. P6-UPDATE-005 sengaja membangun "honest check"
  dengan alasan untuk setiap UNKNOWN — tapi alasan itu tidak pernah sampai ke
  user. Item menu yang melakukan sesuatu tanpa feedback terlihat seperti
  rusak/dimatikan. Ini melanggar janji UX fitur sendiri.
- **Saran:** tampilkan hasil sebagai dialog (Tauri dialog plugin) atau notifikasi
  window: "Could not check: the release feed is not reachable; the repository
  may be private" — teksnya sudah ada di `update_summary()`, hanya perlu
  di-render, bukan di-stderr.

## W-007 — "Create case" awalnya disabled meski kedua field sudah terisi

- **Area:** UX (pembuatan case)
- **Severity:** MINOR
- **Lokasi:** `web/src/CaseList.tsx` (form New Analysis Case)
- **Observasi:** Setelah `fill_input` mengisi field Question + Dataset,
  `Create case` masih `disabled: true`. Setelah membaca ulang state (re-render
  berikutnya), tombol menjadi `enabled` dan klik berhasil membuat case.
- **Dugaan:** race antara pengisian programmatic dan state React — kemungkinan
  field `required` divalidasi sebelum React state ter-commit. Bisa juga
  perilaku asli pengisian manual manusia tidak terkena (manusia mengetik
  per karakter, state pasti ter-commit).
- **Status:** TIDAK dikonfirmasi sebagai bug user-facing. Bisa artefak metode
  headless. Butuh verifikasi: apakah user yang mengetik manual juga pernah
  melihat tombol disabled padahal field sudah terisi?

## W-009 — "Why these changes" tidak menampilkan rationale yang ada di API

- **Area:** UX (refinement, P8-REFINE-007)
- **Severity:** MAJOR
- **Lokasi:** `web/src/CaseWorkspace.tsx` (panel Refine the question),
  `GET /cases/{id}/refine` field `rationale` + `grounds`
- **Observasi (diverifikasi):** Klik "Why these changes" — **tidak ada apa pun
  yang muncul**. Tidak ada penjelasan, tidak ada error, tidak ada loading.
  Padahal API menjawab lengkap:
  - `rationale`: "The question is sharpened, not replaced: each addition is a
    measurement the profile already made... Splits the answer by channel,
    which has 3 distinct values, so the comparison is between groups rather
    than one total."
  - `grounds`: `[{"kind":"column","name":"channel","detail":"categorical
    column with 3 distinct values"}]`
  - Evidence: `walktest/evidence/refine-latest.json`
- **Mengapa ini penting:** P8-REFINE-007 membangun refinemen supaya
  "sharpened with what the profile measured - real columns, measured ranges".
  Seluruh nilainya adalah **mengapa** perubahan itu dipercaya — dasar
  terukurnya. Tanpa rationale, pengguna hanya melihat kalimat baru yang
  tampaknya diubah secara ajaib dan diminta menerimanya secara membabi buta.
  "Nothing is changed until you decide" adalah janji, tapi keputusan tanpa
  alasan bukan keputusan yang bermakna. Ini juga membuat "Accept" terlihat
  seperti menyetujui black box.
- **Saran:** render `rationale` (dan `grounds` sebagai daftar kolom/rentang
  terukur) di bawah tombol "Why these changes". Data sudah ada di endpoint,
  hanya perlu dirender.

## W-010 — guardrail LLM bekerja, tapi pengguna tidak diberi tahu alasannya

- **Area:** UX (refinement, LLM path)
- **Severity:** MINOR
- **Lokasi:** `server/app/refine.py` (fallback validation), log core
- **Observasi (dari core log):**
  ```
  POST https://api.atria-asi.ai/v1/chat/completions "HTTP/1.1 200 OK"
  WARNING app.refine llm refinement failed; falling back to deterministic:
    LLM refinement failed validation: the refined question loses the
    original's subject terms: kembali, padahal
  POST /cases/.../refine -> 200 in 41655ms
  ```
  LLM memang dipanggil dan menjawab, tapi **gagal validasi** (kehilangan
  subjek "kembali", "padahal"), lalu jatuh ke deterministic. UI hanya
  menampilkan "(deterministic)" tanpa alasan.
- **Mengapa ini penting (positif + negatif):**
  - **Positif:** guardrail AT-04 bekerja sempurna. Ini bukan bug — ini fitur
    yang berfungsi: LLM yang menulis ulang pertanyaan Indonesia dengan
    kehilangan nuansa ditolak.
  - **Negatif (UX):** pengguna tidak tahu bahwa LLM sudah dipanggil,
    memakan 41 detik, dan ditolak karena alasan tertentu. Label
    "(deterministic)" saja tidak menjelaskan apa-apa. Pengguna mungkin
    menunggu 41 detik bertanya-tanya apa yang terjadi (saya sendiri
    mengalaminya di walk-test ini).
- **Saran:** tampilkan alasan singkat saat fallback: "the AI proposal lost
  the original question's emphasis, so DAH kept your wording and sharpened
  it deterministically" — atau setidaknya "AI proposal rejected by
  validation; deterministic refinement used".

## W-008 — profil dataset otomatis di-POST setiap halaman case dibuka

- **Area:** Flow / arsitektur ( profiling )
- **Severity:** MAJOR (design smell, bukan crash)
- **Lokasi:** `web/src/CaseWorkspace.tsx:191-202` ( useEffect load() ),
  `web/src/api.ts:572` ( `profileDataset` = POST )
- **Observasi (bukti dari core log):** membuka case view memicu
  `POST .../profile -> 201` untuk setiap dataset, DUA KALI berturut-turut
  (23:33:49 dua request 440ms dan 401ms). Komentar kode di line 191-192
  berkata "Profiles are read-only context", tapi fungsi yang dipanggil adalah
  POST. Profil bersifat idempoten (`INSERT OR REPLACE`) jadi tidak ada
  korupsi data, DAN cacatnya memang tertangkap.
- **Mengapa ini penting:**
  1. **POST read-looking**: permintaan yang terlihat hanya membaca data ternyata
     menulis/memulai ulang profil. Pelanggaran prinsip keamanan dan REST.
  2. **Double-POST**: ada dua request untuk satu dataset — pemborosan komputasi
     profiling pada dataset besar (5 detik+ per profil).
  3. **"Stage: profile" menjadi ambigu**: UI menyatakan profil sebagai langkah
     manual ("Next: Profile every attached dataset") tapi sebenarnya sudah
     otomatis dijalankan saat membuka case. Instruksi dan kenyataan tidak
     cocok, membingungkan pengguna.
- **Saran:** profiling harus GET bila sudah ada profil (atau endpoint baca
  terpisah), POST hanya saat pengguna secara eksplisit meminta profiling
  ulang. Perbaiki double-invocation (lihat dependency array useEffect atau
  StrictMode double-render).

## W-006 — string literal di main.rs berisi puluhan spasi aneh

- **Area:** Code quality / log output
- **Severity:** MINOR
- **Lokasi:** `desktop/src-tauri/src/main.rs:41` dan `:43`
- **Observasi:** dua string log mengandung ~30 spasi kosong di tengah kalimat:
  `"DAH shell: the core reported file logging is off, so                          there is no log to reveal"`.
  Pola ini menunjukkan line-continuation yang di-join tanpa membersihkan
  indentasi.
- **Dampak:** hanya pesan stderr, tidak terlihat user. Tapi jika suatu saat
  log ini ditampilkan (misal saat W-005 diperbaiki), teksnya akan rusak.
- **Saran:** rapikan kedua string.

## W-011 — tombol "Generate an analysis plan" tidak ada: plan stage tidak bisa diselesaikan dari UI

- **Area:** UI/UX — orientation spine vs. permukaan kerja (loop terputus)
- **Severity:** MAJOR
- **Lokasi:** `web/src/CaseWorkspace.tsx` `PlanPanel` (hanya `getPlan`, tidak ada
  POST); rail `WorkflowRail` membaca `progress.next_action` dari
  `server/app/workflow.py:48` ("Generate an analysis plan",
  endpoint `POST /cases/{case_id}/datasets/{dataset_id}/plan`); tombol
  "Generate code" ada di `CaseWorkspace.tsx:753`
- **Observasi:** Case view menampilkan "Stage: plan / Next: Generate an analysis
  plan / POST /cases/.../plan" sebagai next action, tapi **tidak ada satu pun
  elemen UI yang melakukan POST itu**. `PlanPanel` hanya memanggil `getPlan`
  (GET) dan merender empty state "No plan for X yet - generate one to get
  sub-questions..." tanpa tombol apa pun. Tombol "Generate code" adalah
  `/generate-code` (endpoint lain, artifact lain). Analis harus membuka
  terminal dan `curl` untuk menyelesaikan stage ini.
- **Dampak:** loop panduan inti (orientation spine) menunjuk ke aksi yang tidak
  ada. Seluruh fase "What" dari LEARN walk dan stage plan tidak bisa
  diselesaikan dari shell yang dikirim. Setiap user baru akan terjebak di sini.
- **Reproduksi:** buat case + attach + profile (profil ter-POST otomatis),
  baca rail: "Next: Generate an analysis plan". Cari di seluruh DOM: tidak ada
  tombol/link yang memanggil endpoint plan. `grep -rn "POST.*plan" web/src`
  kosong.
- **Saran:** `PlanPanel` mendapat tombol "Generate the plan" yang POST ke
  `/cases/{id}/datasets/{id}/plan` (endpoint sudah ada, 201, schema-validated);
  setelah sukses reload plan + progress. Alternatif: plan di-generate saat
  pertama kali dibutuhkan oleh generate-code.

## W-012 — pertanyaan untuk generate-code tidak terisi dari pertanyaan case

- **Area:** UI/UX — usability
- **Severity:** MINOR
- **Lokasi:** `web/src/CaseWorkspace.tsx:744-755` (input "Question for code
  generation", placeholder "What would you like to know?")
- **Observasi:** Case sudah memiliki pertanyaan yang diterima (refined), tapi
  input untuk generate code **kosong** dan harus diketik ulang manual. Sumber
  LLM di backend (`generator.py:449`) menerima `question or '(none given)'`.
- **Dampak:** langkah yang seharusnya satu klik menjadi mengetik ulang
  pertanyaan panjang; juga mendorong pertanyaan generik yang tidak terkait.
- **Saran:** pra-isi dengan pertanyaan case (question atau refined question),
  tetap bisa diedit.

## W-013 — run SQL berhasil tapi panel Runs tidak berubah sampai reload manual

- **Area:** UI/UX — reactivity/state
- **Severity:** MINOR
- **Lokasi:** `web/src/CaseWorkspace.tsx` `CodegenPanel.run()` (sekitar 722-735)
  memanggil `runSql` lalu `setProposal(null)`; `RunsPanel` hanya render dari
  prop `runs` milik parent
- **Observasi:** Klik "Run this" -> POST `/runs` 201 (run tersimpan di core,
  terverifikasi via `GET /cases/.../runs`), tapi panel Runs masih "No analysis
  has run yet." sampai halaman dibuka ulang. Proposal memang dihapus, tapi
  `onChanged` (reload parent) **tidak dipanggil** di `CodegenPanel` (padahal
  `RunsPanel`, `DataPanel` dll semuanya memanggilnya).
- **Dampak:** analisis merasa runnya gagal; double-run (saya melakukannya dua
  kali, terlihat dari dua GET /runs di performance log) dan data duplikat di
  history meskipun hanya satu yang berguna.
- **Saran:** `CodegenPanel` menerima `onChanged` dan memanggil setelah `runSql`
  sukses, seperti panel lain.

## W-014 — interpret dan draft-finding LLM selalu timeout 30s, UI "Working…" lama tanpa sinyal

- **Area:** AI / reliability UX
- **Severity:** MAJOR
- **Lokasi:** `server/app/interpreter.py:239` (`timeout=30.0`),
  `server/app/drafter.py:312` (`timeout=30.0`), `server/app/assistant.py:576`
  (`timeout=30.0`); compare `server/app/planner.py:366` (`timeout=60.0`) dan
  `server/app/refine.py:595` (`timeout=60.0`) yang sukses
- **Observasi:** POST `/interpret` dan `/draft-finding` selalu gagal setelah
  tepat 30s ("The read operation timed out") dan fallback ke deterministic.
  Log core:
  `WARNING app.interpreter llm read failed; falling back to deterministic:
  The read operation timed out` (30133ms),
  `WARNING app.drafter llm draft failed ...` (30184ms).
  Profiler/generator (30s) dan refine (60s) bisa selesai; interpret dan draft
  yang prompt-nya lebih besar (kirim columns + rows) tidak.
- **Dampak:** dua dari tiga assistant slice "AI" selalu jawab deterministic di
  mesin ini — kualitas turun drastis (draft deterministic hanya mengulang
  range tanpa atribusi: "the result names no dimension to attribute the spread
  to"). UI menampilkan "Working…" sampai 30s tanpa indikasi bahwa LLM gagal dan
  fallback terjadi; pengguna tidak tahu hasilnya bukan LLM kecuali membaca
  label "by deterministic" yang kecil.
- **Saran:** naikkan timeout interpret/draft (mis. 60-90s, atau env-config),
  dan tampilkan secara eksplisit di UI ketika jawaban adalah fallback
  deterministik karena LLM gagal (bukan hanya label source yang kecil).

## W-015 — check evidence menolak finding yang benar: angka di dalam token tanggal/label dipotong oleh regex

- **Area:** Validation / trust machinery (9 dimensi, dimensi `evidence` HARD)
- **Severity:** MAJOR
- **Lokasi:** `server/app/evaluator.py` `_numbers_in()` (regex
  `-?\d[\d,]*\.?\d*`), dipakai oleh `server/app/validation.py:220`
  `check_evidence()`, juga `drafter.py:246` dan `evaluator.py:379`
- **Observasi:** Finding deterministic "2026-07 has the highest revenue at
  1526309.57, the largest of 44 grouped value(s)" divalidasi dengan verdict
  `insufficient_evidence` (HARD fail) karena "quotes values absent from its
  own result: -7.0, 2026.0". Regex `-?\d[\d,]*\.?\d*` memecah token "2026-07"
  menjadi **dua** angka: `2026` dan `-7`. String "2026-07" adalah nilai kolom
  `month` yang **memang ada di result** — tetapi tidak ada di himpunan
  `_allowed_numbers` (yang berisi cell values numerik saja, dan frekuensi).
  Diverifikasi langsung:
  `_numbers_in("2026-07 has ... 1526309.57 ... 44 ...") == [-7.0, 44.0, 2026.0, 1526309.57]`,
  dan `2026.0 not in _allowed_numbers(...)`.
- **Dampak:** false negative pada check HARD — finding yang 100% benar dan
  semua angkanya nyata ditolak total ("The verdict refuses this finding rather
  than passing it with a caveat"). Setiap analysis time-series dengan format
  `YYYY-MM` di statement akan gagal validasi. Ini adalah dimensi trust
  inti (AT evidence). Catatan: 44.0 juga dinyatakan invented meskipun "44
  grouped value(s)" = row_count result — frekuensi per nilai unik, bukan
  44 itu sendiri; ini batas kedua dari `_allowed_numbers`.
- **Reproduksi:** dataset B2B ini, run SQL `strftime('%Y-%m', order_date)`,
  Draft a finding (deterministic), Accept, Validate -> insufficient_evidence.
- **Saran:** `_numbers_in` harus mengabaikan angka yang adalah bagian dari
  token alfanumerik/date yang lebih besar (mis. guard agar `-` hanya angka
  jika diikuti digit dan didahului boundary/non-digit, atau strip token yang
  cocok pola tanggal `\d{4}-\d{2}`); dan `_allowed_numbers` sebaiknya juga
  menerima row_count dan jumlah group yang statement sebut sebagai "N grouped
  value(s)". Alternatif terbaik: allowed set memasukkan representasi string
  dari cell value (tanggal utuh), dan angka yang muncul sebagai substring
  token non-numerik tidak dihitung sebagai magnitude.

## W-016 — chart dan Python run tidak ada permukaan UI-nya (fitur backend tanpa shell)

- **Area:** UI/UX — fitur tak terjangkau
- **Severity:** MAJOR
- **Lokasi:** endpoint ada: `POST /cases/{id}/runs/{run_id}/charts`
  (`server/app/main.py:2884`), `POST /cases/{id}/datasets/{id}/runs/python`
  (`server/app/main.py:1778`); **tetapi** `grep -c chart web/src/api.ts` = 0,
  dan tidak ada satu pun `fetch`/`request<...>` ke `/runs/python` di
  `web/src/` (`grep -rn "runs/python" web/src` kosong). Satu-satunya render
  kata "chart" di shell adalah hitungan di evidence graph dan teks history.
- **Observasi:** Stage "evidence" rail menunjuk "Attach evidence to a finding"
  (`POST /findings`), tetapi P2-ANALYSIS-009 (chart) dan P2-ANALYSIS-008/
  P3-CHART-002 (Python + PNG) — yang dihitung lulus di P3/P4 — tidak punya
  tombol di shell yang dikirim. Chart hanya bisa dibuat via curl; PNG chart
  hanya bisa dilihat via file path.
- **Dampak:** dua kapabilitas inti tidak bisa dipakai pengguna tanpa terminal.
  Python sandbox (P3-SEC-001, fitur hardening utama) tidak teruji oleh user.
  Chart evidence artifact tidak bisa diproduksi sama sekali dari UI.
- **Saran:** `RunRow` mendapat "Render a chart" (pilih x/y/kind, POST charts,
  tampilkan SVG/PNG yang dikembalikan atau linknya); dan codegen panel mendukung
  `kind: 'python'` dengan tombol run ke `/runs/python` (endpoint + model
  `PythonRunCreate` sudah ada; generator sudah mendukung kind python).

## W-017 — EVALUATE "audit could not run" menampilkan detail backend mentah, tidak dinamis per penyebab

- **Area:** UI/UX — error taxonomy
- **Severity:** MINOR
- **Lokasi:** `web/src/CaseWorkspace.tsx:1841`
  (`The audit could not run: {error}`) vs `server/app/main.py:1895-1913`
- **Observasi:** Saat form EVALUATE dikirim dengan field kosong/salah, UI
  menampilkan detail backend mentah: "The audit could not run: the artifact is
  not a single read-only query, so it cannot be executed or audited (HTTP 400)".
  Tiga kemungkinan penyebab (code kosong / claim kosong / bukan read-only)
  tidak dibedakan di permukaan; pesan read-only muncul meski yang salah adalah
  field lain.
- **Dampak:** pengguna mengira SQL-nya yang ditolak padahal sebenarnya field
  kode kosong. Klasifikasi error 400 dipanggil dari satu tempat saja.
- **Saran:** pisahkan pesan per penyebab ("the artifact's code is empty",
  "no claim was submitted", "not a single read-only query") atau di UI, validasi
  non-empty field sebelum submit sehingga pesan yang muncul spesifik.

## W-018 — cross-case memory bekerja, tapi tidak ada permukaan yang menjelaskannya

- **Area:** UX / discoverability
- **Severity:** OBS
- **Lokasi:** chat endpoint `server/app/main.py:3060` (P6-MEMORY-001); UI
  hanya "Ask this case" (`web/src/CaseWorkspace.tsx` "Ask")
- **Observasi:** Di case baru, pertanyaan tentang temuan case lain dijawab
  dengan benar dan jujur ("answered by llm", grounds citing
  `finding:<id>` + `previous case: <question>`, plus "Tidak ada temuan yang
  membuktikan perbandingan langsung revenue September vs Juli"). Tidak ada
  label/hint di UI yang memberi tahu pengguna chat bisa mengingat case lain.
- **Dampak:** kapabilitas andal tetapi tidak terlihat; pengguna tidak akan
  mencobanya.
- **Saran:** teks hint di panel chat (mis. "may recall findings from your
  other cases") sudah cukup; tidak perlu UI baru.

## W-019 — UI tidak bisa memproduksi chart/Python run, tapi export membawanya hanya jika dibuat via API

- **Area:** konsistensi evidence chain
- **Severity:** OBS
- **Lokasi:** `POST /runs/python`, `POST /runs/{id}/charts` (tidak ada UI,
  W-016); evidence graph + export package membawa 7 runs + 1 chart + 1 python
- **Observasi:** Setelah saya buat python run dan chart via API, evidence graph
  ("1 dataset, 7 runs, 2 findings, 1 chart, 1 plan"), history ("7 runs
  executed, 1 chart rendered"), LEARN ("every phase is done") dan export
  package (13 struktur) semuanya membawanya dengan benar. Inti terverifikasi;
  hanya shell yang tidak menyajikannya.
- **Saran:** lihat W-016 — permukaan UI adalah satu-satunya celah.

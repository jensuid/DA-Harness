# WALK-E2E-001 — Walk-test end-to-end DAH (plan, tetap)

Tugas TIDAK tercatat di `ai/HANDOFF.md`. Tujuan: siapkan satu case + dataset,
jalankan app sungguh end-to-end, evaluasi **flow, UI, UX** untuk bahan
perbaikan. Bukan lulus gate. Mode: comprehensive (semua aspek), LLM nyata.

## 0. Peran dan batas

- Saya berperan ganda: naive learner/participant DAN facilitator yang mencatat.
  Catatan lama: eksekusi sungguh, jangan tawarkan opsi dulu, lapor hasil +
  keterbatasan honest (agent != naive human).
- **Saya tidak bisa melihat screenshot** (ikon pun dipilih blind). Evaluasi saya
  = struktur DOM, teks, alur, state, pesan error, kutipan, empty state.
  Screenshot tetap disimpan untuk dilihat user.
- Webview Tauri = WKWebView, **tidak ada CDP**. Karena itulah akses stabil
  dilakukan lewat browser nyata (Chromium) yang memuat **bundle web yang sama**
  Tauri render, plus core yang sama.

## 1. Mekanisme akses — yang dipelajari (valid, dari source)

Fakta arsitektur (bukan asumsi):

- Port core **hard-coded 8123** (`core_server.rs:19`, `web/package.json`
  `build:desktop` = `VITE_API_URL=http://127.0.0.1:8123`).
- App Tauri **selalu men-spawn core-nya sendiri**; `resolve_server_command`
  (`core_server.rs:110`) memilih: sidecar `dah-core` di `shell_dir` (release)
  atau `server/.venv/bin/python` (dev). **Tidak ada probe "core sudah jalan"**.
  Konsekuensi: dua core tidak bisa berbagi 8123; app kedua gagal bind dan terlihat
  mati (komentar di file sendiri, ~line 349).
- `DAH_DEV_CORE=1` memaksa resolve ke **venv checkout master** bahkan pada
  build release. Ini enabler (lihat 2).

Environment sekarang:

- `/Applications/DAH.app` = **v0.3.1**, sedang **berjalan** (pid 78247,
  `:8123`), core menjawab `"current":"unknown"` (pre-FIX-VERSION-001).
- `desktop/src-tauri/target/release/bundle/macos/DAH.app` = **v0.3.2** (build
  lokal, pre-fix version juga, tapi frontend == master).
- `server/.venv` Python 3.14.7 ada; checkout master (1ea112d) punya fix versi.
- `server/.env` berisi `DAH_LLM_API_KEY` / `DAH_LLM_BASE_URL` / `DAH_LLM_MODEL`
  (tidak pernah dibaca nilainya).
- `:5173` adalah project **BI-Mastery lain**, bukan DAH. Bukan sisa server dev.

## 2. Konfigurasi target — pilihan awal dan koreksinya

Pilihan awal (direkomendasikan, disetujui): "core master di background +
`.app` v0.3.2 untuk permukaan Tauri".

**Koreksi:** tidak bisa apa adanya — app Tauri selalu spawn core sendiri di
8123, jadi core master yang saya start duluan akan membuat app gagal bind.

Jalan keluar yang valid dan lebih baik (yang dipakai):

- Quit app 0.3.1 yang jalan, lalu launch `.app` v0.3.2 **dengan
  `DAH_DEV_CORE=1`** → shell Tauri asli (menu Updates / Reveal Logs, window)
  dengan core = **checkout master lewat venv** = fix version aktif.
  REPO_ROOT di-bake build v0.3.2 ke folder repo ini; `DAH_LLM_*` di-export di
  lingkungan launch.
- Catatan penyimpangan: startup jadi tanpa PyInstaller unpack (lebih cepat,
  ~40s lebih cepat). Tidak ada perubahan API/UX; hanya lokasi executable core.
- Deep DOM walk dilakukan di **browser Chromium** melawan core master yang sama
  (bundle `web/dist-desktop` identik dengan yang Tauri render).Permukaan khusus Tauri (menu Check for Updates, Reveal DAH Logs, window)
  diverifikasi terhadap `.app` itu.

## 3. Struktur resumable

```
walktest/HANDOFF.md   state mesin live: step terakhir, step berikutnya,
                      perintah start core, data dir, jumlah temuan, path
                      evidence. Dibaca dulu oleh session lanjutan.
walktest/FINDINGS.md  append-only: satu blok per temuan
                      (id, area, severity, lokasi, observasi, saran)
walktest/evidence/    export blob per milestone, store backup, screenshot
walktest/data/        dataset synthetic B2B
walktest/PLAN.md      file ini (statis)
walktest/REPORT.md    agregasi akhir
```

Aturan konteks: tiap step maksimal ~2 tool call, langsung tulis ke disk. Kapan
pun context habis, session baru baca `walktest/HANDOFF.md` dan lanjut tepat di
step itu. `ai/TASKS.md` juga mendapat entri open task supaya tidak hilang dari
backlog formal.

## 4. Daftar step (lintas session boleh)

**Fase A — belajar akses**
- A0 struktur + registrasi task + handoff
- A1 start core master (`DAH_DEV_CORE=1` via launch .app, atau venv langsung),
  cek `/health`, `/updates/latest`, `/schema-version`, `/logs`; catat
  mekanisme + waktu startup
- A2 browser: buka shell, buktikan bisa baca DOM + klik + isi input; catat
  gotcha (React-controlled input, `fill_input` vs js)
- A3 permukaan Tauri: menu Updates + Reveal Logs, window; catat

**Fase B — case & data** (B2B sales, ~400 baris, cacat sengaja: duplikat,
null customer, label kategori tidak konsisten, revenue != units x price di
beberapa baris, format tanggal campuran, unit outlier, kategori tak terkatalog)
- B1 generate dataset
- B2 buat case + attach + profile
- B3 refine question (LLM nyata)

**Fase C — analisis**: generate code SQL + run + EDA → Python + sandbox +
chart → interpret → draft finding → accept → validate (9 dimensi + causal
guard) → decision view + implications

**Fase D — mode lain**: EVALUATE → agent & multi-agent reviewer → LEARN →
history/memory/template/search → export/import round-trip

**Fase E — UX shell**: orientation spine, error taxonomy (400 vs 500
envelope), empty/loading state, rendering kutipan, permukaan Tauri

**Fase F — agregasi**: baca FINDINGS.md, klasifikasi severity
(blocker-flow / UX / polish), tulis REPORT.md berisi rekomendasi prioritas,
update `ai/`, commit

## 5. Severity yang dipakai

- `BLOCKER` aliran berhenti, tidak bisa lanjut
- `MAJOR` aliran jalan tapi hasil/konteks salah atau membingungkan
- `MINOR` polish, inkonsistensi kecil, teks
- `OBS` observasi UX (perlu konfirmasi user, bukan jelas-jelas bug)

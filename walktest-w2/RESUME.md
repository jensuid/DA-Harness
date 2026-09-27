# WALK-UX-002 RESUME — untuk session baru

Walk-test end-to-end DAH sebagai junior analyst. **Selesai** 27 Sep 2026.
Semua hasil ada di `walktest-w2/`. Tidak ada proses yang masih jalan
(port 8123 dan 5273 bersih, DAH.app dimatikan).

## Baca pertama (berurutan, kecil dulu)

1. `walktest-w2/REPORT.md` — ringkasan + bukti kepadatan + prioritas
   perbaikan. Ini dokumen utamanya.
2. `walktest-w2/FINDINGS.md` — 13 temuan (W2X-001..013), append-only,
   satu blok per temuan dengan severity + lokasi kode + observasi + saran.
3. `walktest-w2/PHASE2.md` — hasil verifikasi di app riil.
4. `walktest-w2/CAPTURE-SHEET.md` — V/L/F/D rows, semua terisi.

## 13 temuan, ringkas

**BLOCKER**
- W2X-012 — app packaged tidak punya kredensial LLM. `.env` tidak di-bundle
  (`server/dah-core.spec:54`), shell tidak inject `DAH_LLM_API_KEY`
  (`core_server.rs:88-93`). Bukti: `find /Applications/DAH.app -name .env`
  kosong; POST `/generate-code` → `"source":"template"` (dev core: "by
  llm"). Semua fitur LLM (plan/draft/refine/chat/agent) nonaktif untuk
  pengguna riil.

**MAJOR**
- W2X-001 — LLM timeout 120s, UI hanya "Generating… Working… Working…
  Working…" tanpa progress/cancel (3 dari 4 call timeout di fase 1)
- W2X-002 — submit form case dengan Dataset kosong = diam total (tidak ada
  alert, tidak ada request; HTML5 validation saja)
- W2X-005 — "Next:" menampilkan endpoint mentah
  `POST /cases/…/datasets/{dataset_id}/plan` (placeholder tidak terisi,
  muncul 2x). Tidak ada tombol yang melakukan aksi itu. **Konfirmasi fase 2.**
- W2X-006 — kode LLM ditampilkan `<pre>` read-only; saat gagal jalan
  (400 invalid date) tidak bisa diperbaiki tanpa generate ulang
- W2X-007 — tidak ada editor SQL/Python. "Run an analysis" tidak punya UI;
  satu-satunya pintu ke `/runs` adalah codegen LLM yang tidak editable
- W2X-008 — case page 13,1x viewport (browser) / 5,8x (app riil), 18 panel,
  0 progressive disclosure, 12/18 panel empty state saat case baru.
  **Konfirmasi fase 2.**
- W2X-009 — fallback deterministic draft mempropagandakan outlier 99.589
  (758x nilai normal) sebagai finding; profil sudah mendeteksi tapi drafter
  tidak membacanya; validate menyalahkan kolom yang salah

**MINOR**
- W2X-003 chart di layar hilang setelah reopen
- W2X-004 Context panel "unsaved edits" tanpa diedit
- W2X-010 case list menampilkan duplikat tanpa peringatan
- W2X-011 klik baris case tidak membuka case (harus tombol Open)
- W2X-013 zone orientation 232pt (18%) di window 1280pt — pertanyaan
  panjang jadi blok tak terbaca

## Yang ditarik kembali (bukan temuan)

- **Decision panel "tidak sinkron"** — awalnya saya catat. Tidak
  terkonfirmasi: itu delay re-fetch setelah Validate; setelah reload,
  Decision menampilkan finding + uncertainty dengan benar. Dicek via
  `GET /decision` (loop_closed=true, 1 finding) dan DOM. Tidak ada di
  FINDINGS.md.

## Keterbatasan (jujur)

- Agent != naive human. Kepadatan diukur dari DOM, bukan dirasakan.
- LLM timing fase 1 mungkin tidak representatif (bisa network provider).
- Viewport browser 1256x593; app riil 1280x768.
- Satu dataset, satu case. Multi-dataset, template, chat cross-case, dan
  export package belum diuji.
- Interaksi klik/scroll di app riil terbatas (WKWebView tanpa CDP;
  computer_use menemui window ambiguity pid 75492 punya 7 window).

## Cara reproduksi environment (jika perlu)

Fase 1 (LLM aktif, paling lengkap):
```
cd /Volumes/JensData/Jensu-Projects/DA-Harness/server && \
DAH_DATA_DIR=<tmp>/data DAH_DB_PATH=<tmp>/data/dah.db DAH_LOG_DIR=<tmp>/logs \
./.venv/bin/python -m uvicorn app.main:app --port 8123   # background
cd web && env -u CONDA_PREFIX PATH=/usr/local/bin:/usr/bin:/bin DAH_DEV_PORT=5273 npx vite
# browser: http://localhost:5273/  (localhost, BUKAN 127.0.0.1)
```
Catatan penting: DAH_DATA_DIR saja TIDAK cukup — DAH_DB_PATH defaultnya
`server/dah.db` (berisi ratusan case test suite). Keduanya harus di-set.

Fase 2 (app riil):
```
env -u CONDA_PREFIX PATH=/usr/local/bin:/usr/bin:/bin \
/Applications/DAH.app/Contents/MacOS/dah-shell   # background
```
LLM nonaktif (W2X-012). `DAH_DEV_CORE=1` TIDAK berfungsi di app packaged —
sidecar selalu ada di `/Applications/DAH.app/Contents/MacOS/dah-core`.

Dataset mockup: `walktest-w2/coffee_shop_sales_2026.csv` (110 baris, 3 gerai
kopi; 1 date format campuran `08/17/2026`, 1 outlier revenue 99000, 2 store
kosong, 1 transaction_id ganda TX-1005).

## Langkah berikutnya (tawarkan, jangan asumsikan)

1. Root-cause W2X-012 — kredensial LLM ke sidecar (blokir semua fitur LLM
   untuk pengguna riil). Pilihan: build-time secret injection, first-run UI
   prompt, atau status LLM di UI.
2. Root-cause W2X-009 — apakah drafter membaca peringatan profil?
   (`server/app/drafter.py` deterministic fallback path)
3. Prototipe Prioritas 1 — editor SQL/Python + pesan form + tombol
   next-action, task terpisah dengan gate tes sendiri.

Kalau user minta lanjut tanpa konteks, mulai dari "mau lanjut W2X mana?"
dan baca REPORT.md dulu.

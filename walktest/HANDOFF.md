# WALK-E2E-001 — hand-off live (dibaca pertama oleh session lanjutan)

Baca `walktest/PLAN.md` untuk rencana dan mekanisme akses (statis). File ini
hanya state mesin saat ini.

## Status: WALK-TEST SELESAI

- **Semua fase A-F selesai.** Laporan akhir: `walktest/REPORT.md`.
- 19 temuan dicatat (W-001..W-019): 8 MAJOR, 8 MINOR, 3 OBS. Detail di
  `walktest/FINDINGS.md` (append-only).
- Trust loop case utama tertutup: `loop_closed: true`, decision + implication
  tersimpan, export package lengkap.

## Yang selesai

Fase A (akses), B (case + dataset B2B 484 baris 8 cacat), C (plan via API,
codegen LLM, run SQL x2, interpret, draft, validate 9 dimensi, EDA, python
sandbox, chart SVG+PNG, decision), D (EVALUATE 9 axis, agent analyst +
reviewer approve/reject, LEARN, history, evidence graph, chat cross-case
memory, export 13 struktur, template round-trip), E (error taxonomy 400/404/
422/500, empty state, memory), F (REPORT.md ini).

## Temuan prioritas perbaikan (urutan)

1. **W-015 MAJOR** — `server/app/evaluator.py` `_numbers_in` regex
   `-?\d[\d,]*\.?\d*` memotong "2026-07" → `2026` + `-7`; check evidence HARD
   menolak finding yang benar (insufficient_evidence). W-011 MAJOR —
   `web/src/CaseWorkspace.tsx` `PlanPanel` tidak POST `/plan`; rail menunjuk
   aksi yang tak ada. W-016 MAJOR — chart + python run tak ada UI.
   W-014 MAJOR — interpret/draft LLM timeout 30s (`interpreter.py:239`,
   `drafter.py:312`). W-008, W-009, W-005, W-001.

## Yang sedang berjalan (background) — masih hidup

- **Core master di :8123** — pid 84940, `.app` v0.3.2 `DAH_DEV_CORE=1`,
  cwd `server/`, data dir
  `/Users/jensu/Library/Application Support/com.jensuid.dah`.
- **Window Tauri** — dah-shell pid 84919 (terlihat di layar).
- **Web dev server :5273** — pid 85367 (`cd web && npm run dev`), menjawab 200.
- Chrome remote debugging: approve sekali dengan
  `/Users/jensu/.local/share/uv/tools/browser-use/bin/browser-harness
  mac-approve` bila CDP timeout.

## Case yang dibuat (state live)

- Case utama: `23fd9c29-4eed-48ec-82eb-a8b8742ad4dc`
  - dataset `e93fe81d-555d-4c00-b565-0a67282da06c` (b2b_sales_q3_2026.csv)
  - 7 runs (2 SQL via UI + 1 python via API + audit runs), 2 findings
    (partially_supported + insufficient_evidence), 2 charts (svg+png),
    1 plan, decision dengan 1 implication, 19 history events.
  - Case turunan: `b1b13624-857e-4acb-b4e3-2772e30f4cfe` (dari template,
    stage data, hanya untuk verifikasi round-trip + memory).
- Case sampel dari import test: `74f2b9ca`, `32f7d5fc`, `8f715b78` (data
  kosong, bisa dibersihkan).
- Template: "B2B Q3 revenue mix-shift analysis" (+ 3 template auto-created
  dari percobaan sebelumnya; bisa di-retire).

## Cara melanjutkan (untuk session baru)

1. Baca file ini + `walktest/PLAN.md` + `walktest/REPORT.md`.
2. Cek core: `curl -s http://127.0.0.1:8123/health` (harus
   `{"status":"ok"}`).
3. Walk-test selesai; langkah berikutnya adalah **post-phase fix** per temuan
   MAJOR, prioritas W-015 → W-011 → W-016 → W-014. Satu fix per temuan,
   commit per task.
4. Browser: `new_tab("http://127.0.0.1:5273/")`.
   Catatan interaksi: `fill_input` tidak bekerja untuk textarea (pakai
   native React setter); select pakai native value setter + dispatch change.

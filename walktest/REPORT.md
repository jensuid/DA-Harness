# WALK-E2E-001 — Walk-test end-to-end DAH (laporan akhir)

Tanggal: 2026-09-24/25. Mode: comprehensive (flow, UI, UX), LLM nyata.
Akses: core master (checkout 1ea112d, fix FIX-VERSION-001 aktif) diluncurkan
via `.app` v0.3.2 dengan `DAH_DEV_CORE=1` di `:8123`; deep DOM walk di
Chromium memuat bundle web yang sama di `:5273`; permukaan Tauri (menu) diuji
langsung. Dataset: `walktest/b2b_sales_q3_2026.csv` (484 baris, 17 kolom, 8
cacat ditanam, `random.seed(20260924)` reproducible).

**Yang TIDAK bisa dievaluasi:** tampilan visual. Saya tidak bisa melihat
screenshot; evaluasi = struktur DOM, teks, alur, state, pesan error, kutipan,
empty state. Screenshot tetap ada di `walktest/evidence/` untuk dilihat user.

## Ringkasan eksekusi

Loop analisis lengkap dijalankan sungguh, dari refine sampai decision:

1. Refine question — LLM proposal gagal validasi (kehilangan subjek
   "kembali"/"padahal"), fallback deterministic di-accept. Guardrail AT-04
   bekerja.
2. Attach + profile (otomatis, lihat W-008) — 484 rows, 17 cols, 3 quality
   issues tertangkap (duplicate_rows, extreme_values, missing_values).
3. Plan — tidak bisa dari UI (W-011); dibuat via API. LLM timeout 60s →
   deterministic (W-014).
4. Generate code (LLM) — SQL agregasi bulanan tepat; `COUNT(DISTINCT
   order_id)` benar untuk B2B.
5. Run SQL — revenue per bulan: 6.11M / 1.03M / 6.30M; orders 190/120/170.
6. Interpret — LLM timeout → deterministic (W-014).
7. Draft finding + accept + validate (9 dimensi) — partially_supported dengan
   3 warning kontekstual. Validator menolak temuan kedua dengan
   insufficient_evidence — **namun alasannya keliru** (W-015).
8. EDA segment + correlate — benar (pearson r = -0.0147 terverifikasi manual).
9. Python run (sandbox seatbelt macOS) + chart SVG/PNG — via API saja (W-016).
10. Decision view + implication → `loop_closed: true`.
11. EVALUATE — 9 axis dengan verdict concern yang tepat untuk claim lemah.
12. Agent analyst + reviewer — propose/approve/reject loop bekerja; reviewer
    mengaudit finding dengan 9 axes.
13. LEARN — 4 fase complete. History 19 event. Evidence graph akurat.
14. Export package (13 struktur) + template → new case (fresh IDs).
15. Cross-case memory — chat di case baru mengutip finding case lama.

## Jawaban analisis yang muncul

Premis pertanyaan salah: **revenue September (6.30M) SUDAH melampaui Juli
(6.11M)**. Yang sebenarnya terjadi adalah mix shift:
- Hardware-family 33.6% → 41.5% revenue share (Juli → September)
- Software 58.8% → 46.6%
- Units 14.073 → 24.494 (naik 74%)
- Order hardware terbesar naik ~2.3x (median order 21.560 → 24.000)
- Diskon rata-rata turun 5.4% → 3.1% (bukan penyebab)

Kualitas data yang mengganggu: 41 label kategori tidak konsisten
(Hardware/HW, Service/Svc), 5 format tanggal campuran (`2026-07` vs
`2026/07`), 3 units=9999 outlier, 13 revenue ≠ units×price.

## Temuan: 19 total

### MAJOR (7) — aliran jalan tapi hasil/konteks salah atau membingungkan

| ID | Temuan | Lokasi |
|----|--------|--------|
| W-001 | dev checkout melaporkan versi 0.1.0 (metadata stale, lebih buruk dari "unknown") | `server/app/updates.py` urutan resolusi |
| W-005 | "Check for Updates..." hanya `eprintln!`, tidak menampilkan apa pun | `desktop/src-tauri/src/main.rs:48-60` |
| W-008 | profil di-POST otomatis 2x tiap buka case; "Stage: profile" ambigu | `web/src/api.ts:572` + `CaseWorkspace.tsx:191` |
| W-009 | "Why these changes" kosong; API punya rationale+grounds tapi tidak dirender | `web/src/RefinePanel.tsx` |
| W-011 | **rail menunjuk "Generate an analysis plan" tapi tombolnya tidak ada** — plan stage tidak bisa diselesaikan dari UI | `web/src/CaseWorkspace.tsx` PlanPanel |
| W-014 | interpret + draft-finding LLM **selalu** timeout 30s → fallback deterministic diam-diam; UI "Working…" tanpa sinyal | `interpreter.py:239`, `drafter.py:312` |
| W-015 | **check evidence menolak finding yang benar**: regex memotong "2026-07" → `2026` dan `-7` (false negative pada HARD check) | `server/app/evaluator.py` `_numbers_in` |
| W-016 | chart + Python run tidak ada UI-nya sama sekali (`grep -c chart web/src/api.ts` = 0) | endpoint ada, shell tak ada |
| W-017 | EVALUATE menampilkan detail backend mentah tanpa membedakan penyebab | `CaseWorkspace.tsx:1841` |

(Catatan: W-017 dimasukkan MINOR di FINDINGS.md; lihat detail di file itu.)

### MINOR / OBS (12)

W-002 (nama exec `dah-shell`), W-003 (feed 404), W-004 (seleksi Reveal Logs
tidak terverifikasi), W-006 (string spasi aneh di main.rs), W-007 (Create case
disabled sesaat), W-010 (guardrail bekerja tapi user tidak diberi tahu), W-012
(input codegen tidak terisi pertanyaan case), W-013 (panel Runs tidak refresh
sampai reload; menyebabkan double-run), W-017 (error taxonomy mentah), W-018
(cross-case memory bekerja tapi tidak dijelaskan UI), W-019 (core membawa
python/chart di export meski tak ada UI-nya).

## Prioritas perbaikan

1. **W-015** — trust machinery false negative. Regex memutus angka di dalam
   token tanggal/label; setiap analisis time-series `YYYY-MM` gagal validasi.
   Perbaikan terlokalisir di `_numbers_in` (+ `_allowed_numbers` untuk
   row_count/group count).
2. **W-011** — loop panduan terputus di stage plan. Tombol POST `/plan` di
   `PlanPanel`.
3. **W-016** — dua kapabilitas inti (chart, Python) tak terjangkau dari UI.
4. **W-014** — timeout 30s terlalu pendek untuk LLM di mesin ini; fallback
   harus disampaikan ke pengguna, bukan label kecil.
5. **W-008, W-009, W-005** — permukaan informasi yang ada tapi kosong/salah.
6. **W-001** — versi yang menyesatkan di dev checkout.

## Yang bekerja dengan baik (jangan rusak)

- Guardrail AT-04 (refinement LLM ditolak karena kehilangan subjek)
- Validasi 9 dimensi: verdict + alasan kontekstual per dimensi, carry-over
  uncertainty ke decision view
- Validator menolak finding (insufficient_evidence) — mekanisme penolakan
  bekerja, hanya criterianya yang salah (W-015)
- Profiler: 3 quality issues dengan dampak terhitung, bukan sekadar "ada
  duplikat"
- Sandbox Python: seatbelt macOS menolak kode tidak valid dengan 400 + pesan
  jujur; kode valid menghasilkan run yang masuk evidence graph
- EVALUATE: 9 axis, verdict concern untuk claim tak terfalsifikasi
- Agent approve/reject + reviewer audit — tidak ada write tanpa approval
- Cross-case memory + grounds citation + kejujuran analitis
- Error taxonomy: 400 detail engine, 404 bersih, 422 Pydantic, 500
  `request_id`; **tidak ada jalan input-user ke 500** (diverifikasi)
- Export 13 struktur + template round-trip dengan fresh IDs
- EDA numerik terverifikasi independen (pearson r cocok manual)

## Batasan evaluasi

- Saya tidak bisa melihat tampilan visual; layout, warna, kontras, jarak tidak
  dievaluasi.
- Agent berperan ganda (participant + facilitator); kecepatan/jeda
  pembelajaran manusia tidak terukur.
- LLM di mesin ini lambat (endpoint custom); W-014 sebagian adalah kondisi
  mesin, bukan murni kode — namun 30s hardcoded adalah keputusan kode.
- Case kedua dari template tidak dijalankan sampai selesai (tujuannya hanya
  verifikasi round-trip + memory).

## Evidence

`walktest/evidence/`: profile, refine, codegen-monthly, run-monthly,
run-breakdown, run-python, chart-1 (svg), evaluate-1, decision, plan,
export-package (134KB), findings, validate-1, python-payload.

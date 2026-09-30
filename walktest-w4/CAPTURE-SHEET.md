# WALK-UX-004 — capture sheet

Live sheet untuk walk-test 4. Mode: naive analyst + facilitator, provider
LLM yang sama seperti W3 (Atria-Dawn-Preview, ~10-13 tok/s), dataset
`saas_renewals_2026.csv` (3,000 baris, 6 anomalies ditanam). Berjalan di
atas tree v0.3.6 (master 0d15052) dengan fix W4X-001 diterapkan saat run
untuk verifikasi.

Exit criterion: nol `*(to be recorded)*` tersisa. Yang tidak teramati ditulis
"not observed", tidak direkonstruksi dari ingatan.

## V — pre-flight

- V1 — port 8123 bebas sebelum core start: yes, `lsof` kosong
- V2 — core up, `GET /health` = ok: `{"status":"ok"}`
- V3 — `GET /llm/status` = configured: `provider: DAH_LLM_API_KEY`,
  `model: Atria-Dawn-Preview`, `base_url: https://api.atria-asi.ai/v1`
- V4 — dataset ada: 3,000 baris, 10 kolom, 228,133 byte; 6 anomalies
  ditanam terverifikasi (3 blank segment, 1 outlier revenue 499,500,
  1 US-format date, 1 duplicate subscription_id, 1 seats=0, 3 lowercase
  `scaleup`)
- V5 — Vite dev server di 5273 menyajikan bundle master: `root=200`,
  `/api/health` = ok
- V6 — data dir terisolasi (walktest-w4/data): `GET /cases` = `[]`

## L — think-aloud analyst per step

- L1 — case list kosong: "No cases yet - create one." + Templates section
  yang menjelaskan dirinya sendiri; jelas harus klik New case
- L2 — new case: dua field berlabel (Question *, Dataset *) dengan
  placeholder yang mengajarkan ("Why did revenue decline?", "sales.csv");
  submit -> stage `data`, "Next: Attach a dataset"
- L3 — attach + profile: 6 anomalies muncul sebagai quality findings —
  `renewed_on` 1-of-3000 type inconsistency, segment 0.1% missing, segment
  spelling inconsistency (ScaleUp/scaleup), duplicate subscription_id,
  revenue outlier, seats=0; masing-masing dengan kalimat "Potential impact"
- L4 — generate plan (F-PLAN): attempt 1 kena provider 429, fallback 751ms
  terumumkan; setelah cooldown, **LLM menjawab 12.4 detik**, `source: llm`,
  4 sub-questions / 3 hypotheses / 4 steps / 3 data requirements
- L5 — SQL run: editor menerima query tulisan tangan, grouping
  segment/status, `read_csv_auto(?)` placeholder; stage -> analyze selesai
- L6 — Python run (F-PY): kontrak muncul saat engine Python dipilih;
  **attempt pertama langsung pakai `dataset.rows`, 0 refusal** (W3: 3
  refusal). Satu batasan harness: `fill_input` tidak bisa mengetik
  multi-line (newline ter-strip, sandbox jawab "'[' was never closed"),
  jadi run yang terukur adalah bentuk satu-ekspresi yang contoh panel
  sendiri ajarkan -> `POST .../runs/python -> 201`
- L7 — chart: not observed — batasan harness yang sama (L6): kolom numerik
  yang bisa di-chart butuh agregasi yang run satu-ekspresi tidak hasilkan.
  Tidak diasumsikan baik, tidak diasumsikan rusak
- L8 — interpret: provider 429 -> deterministic reading dalam 421ms,
  terumumkan sebagai kalimat utuh
- L9 — draft + accept + validate: provider 429 -> deterministic draft,
  terumumkan; accept mencatat finding; validate menjalankan 9 check dan
  secara jujur memberi verdict `insufficient_evidence` (dimensi yang
  tidak didukung evidence), finding tetap direkam
- L10 — reviewer audit: propose -> approve -> 9-axes EVALUATE verdict,
  per-axis sentence, `insufficient_evidence` dengan concern di axis data
- L11 — chat: LLM menjawab 20 detik, grounded di run sendiri: "Low
  active_users-to-seats utilisation predicts churned status."
- L12 — implications: editor terbuka dari "Add implication", satu baris
  diisi, Save tersimpan; `GET /decision` membawanya; `loop_closed: false`
  karena finding divalidasi `insufficient_evidence` (jujur, bukan bug)
- L13 — reopen: back to list -> klik baris -> semua state bertahan (stage
  evidence, objective, runs, finding). **Di sinilah W4X-001 tertangkap**:
  sebelum fix, workspace blank total dengan 3x TypeError; setelah fix,
  panel merender `by llm for saas_renewals_2026.csv`
- L14 — export: `GET .../export -> 200`, 337KB package

## F — pengukuran facilitator

- F1 — elapsed `POST /plan` + source: **12,420ms, `source: llm`** (attempt
  pertama 429 -> 751ms fallback deterministik)
- F2 — `finish_reason` plan: plan lengkap (tidak ada fallback warning di
  log; tidak ada token yang terpotong karena bukan respons terpotong)
- F3 — jumlah field di plan jawaban LLM: 4 sub_questions / 3 hypotheses /
  4 analysis_steps / 3 data_requirements (prompt minta maks 4/3/4/3) —
  tepat di cap
- F4 — fallback announcement terbaca sebagai kalimat utuh (W3X-002)?
  **HOLD** — "The LLM was unavailable, so a deterministic reading answered
  in its place." — kalimat period, tanpa fragment lowercase
- F5 — kontrak Python tampil saat engine dipilih? **HOLD** — 3 kalimat:
  handle (`dataset.rows`/`.columns`/`.query`, "no path variable, no
  open()"), daftar module importable (pandas/csv/numpy refused,
  statistics alternatif), bentuk `result` list-of-dicts
- F6 — refusal pertama: **0 refusal** — analyst langsung pakai
  `dataset.rows` dari kontrak. W3: 3 refusal (pandas, csv, path)
- F7 — placeholder Python = script runnable? **HOLD** —
  `totals = {}` / `for row in dataset.rows:` / ... (bukan `# python`)
- F8 — density final page: 19 panels, 3 collapsed disclosures, 1,715 kata
- F9 — outlier: profile memberi flag (severity: finding "may be inflated
  up to..."); drafter menamai segment split, bukan memahkota outlier
  499,500. **W2X-009 HOLD**
- F10 — wait surface: "Generating the plan… 5s elapsed" + Cancel.
  **W2X-001 HOLD**

## D — debrief

- D1 — verdict F-PLAN (W3X-003-PROMPT): **HOLD** — 12.4s vs 120s timeout
  di W3, provider yang sama. Satu batasan: provider rate-limiting (429 di
  interpret dan draft), jadi ini adalah satu observasi yang berhasil
  lewat, sama seperti W3 adalah satu observasi yang gagal
- D2 — verdict F-PY (W3X-004): **HOLD** — 0 refusal vs 3, kontrak dipakai
  saat percobaan pertama. Batasan harness: kode multi-line tidak bisa
  diketik (newline ter-strip)
- D3 — temuan baru: **W4X-001 (MAJOR)** — regression. Case dengan plan LLM
  tidak bisa dibuka kembali karena PlanPanel membaca `context_basis`
  tanpa guard; prompt yang dikecilkan tidak lagi meminta field itu dan
  validator menganggapnya opsional. Fixed + verified live + 1 test
- D4 — regresi fix sebelumnya: W3X-002, W2X-001, W2X-005, W2X-006,
  W2X-008/013, W2X-009, W2X-012, W2X-002 semua HOLD. W2X-003 (chart
  survives reopen) **not observed** — batasan harness (lihat L7), tidak
  diasumsikan
- D5 — batasan honest: agent != naive human (tidak ada kebingungan asli,
  semua klaim dari bukti terukur); satu provider satu sesi; harness
  tidak bisa mengetik multi-line code; W4X-001 hanya bisa ditemukan
  walk-test karena setiap fixture test menyuplai `context_basis`

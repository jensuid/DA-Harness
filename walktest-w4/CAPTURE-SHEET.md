# WALK-UX-004 — capture sheet

Live sheet untuk walk-test 4. Mode: naive analyst + facilitator, provider
LLM yang sama seperti W3 (Atria-Dawn-Preview, ~10-13 tok/s), dataset
`saas_renewals_2026.csv` (3,000 baris). Berjalan di atas tree v0.3.6.

Exit criterion: nol `*(to be recorded)*` tersisa. Yang tidak teramati ditulis
"not observed", tidak direkonstruksi dari ingatan.

## V — pre-flight

- V1 — port 8123 bebas sebelum core start: *(to be recorded)*
- V2 — core up, `GET /health` = ok: *(to be recorded)*
- V3 — `GET /llm/status` = configured (model, base_url; provider name only,
  never a key value): *(to be recorded)*
- V4 — dataset ada di walktest-w4/ (3,000 baris, 6 anomalies ditanam): *(to be recorded)*
- V5 — Vite dev server di 5273 menyajikan bundle master: *(to be recorded)*
- V6 — data dir terisolasi (walktest-w4/data, belum ada case): *(to be recorded)*

## L — think-aloud analyst per step

- L1 — case list kosong: apa yang pertama saya lakukan? *(to be recorded)*
- L2 — new case: field Question + Dataset, apakah jelas? *(to be recorded)*
- L3 — attach + profile: apakah 6 anomalies muncul? *(to be recorded)*
- L4 — generate plan (F-PLAN): *(to be recorded)*
- L5 — SQL run: *(to be recorded)*
- L6 — Python run (F-PY): *(to be recorded)*
- L7 — chart: *(to be recorded)*
- L8 — interpret: *(to be recorded)*
- L9 — draft + accept + validate: *(to be recorded)*
- L10 — reviewer audit: *(to be recorded)*
- L11 — chat: *(to be recorded)*
- L12 — implications (loop closed?): *(to be recorded)*
- L13 — reopen: state bertahan? *(to be recorded)*
- L14 — export: round-trip? *(to be recorded)*

## F — pengukuran facilitator

- F1 — elapsed `POST /plan` + source (llm|deterministic fallback): *(to be recorded)*
- F2 — `finish_reason` plan (stop|length) + token out + rate tok/s: *(to be recorded)*
- F3 — jumlah sub_questions / hypotheses / analysis_steps / data_requirements
  di plan jawaban LLM (prompt minta maks 4/3/4/3): *(to be recorded)*
- F4 — fallback announcement terbaca sebagai kalimat utuh (W3X-002)? *(to be recorded)*
- F5 — kontrak Python tampil saat engine Python dipilih (sebelum run)? *(to be recorded)*
- F6 — refusal Python pertama: `pandas`/`csv`/`path` atau langsung
  `dataset.rows`? Berapa refusal sebelum sukses? *(to be recorded)*
- F7 — placeholder Python = script runnable (bukan `# python`)? *(to be recorded)*
- F8 — density final page: panel count, collapsed disclosures, word count: *(to be recorded)*
- F9 — anomali outlier: apakah drafter menobatkannya atau memberi flag
  (W2X-009 hold check)? *(to be recorded)*
- F10 — wait surface: elapsed clock + Cancel di setiap LLM button (W2X-001): *(to be recorded)*

## D — debrief

- D1 — verdict F-PLAN (W3X-003-PROMPT): HOLD / NOT HOLD + angka: *(to be recorded)*
- D2 — verdict F-PY (W3X-004): HOLD / NOT HOLD + angka: *(to be recorded)*
- D3 — temuan baru (W4X-nnn) bila ada, severity: *(to be recorded)*
- D4 — regresi fix sebelumnya: *(to be recorded)*
- D5 — batasan honest: *(to be recorded)*

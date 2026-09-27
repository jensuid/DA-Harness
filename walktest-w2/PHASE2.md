# PHASE 2 — Verifikasi di app riil /Applications/DAH.app (v0.3.4)

Dijalankan 27 Sep 2026, setelah fase 1 (dev core + browser) selesai.
App riil diluncurkan langsung: `/Applications/DAH.app/Contents/MacOS/dah-shell`
(window 1280x768). Core sidecar `dah-core` spawn sendiri di port 8123.

## Yang diverifikasi

**Konfirmasi temuan fase 1 di app riil:**

1. **W2X-005 KONFIRMASI** — "Next: Generate an analysis plan" lalu string
   mentah `POST /cases/b1b13624-857e-4acb-b4e3-2772e30f4cfe/datasets/{dataset_id}/plan`
   (placeholder `{dataset_id}` tidak terisi) terlihat persis di app riil,
   muncul **dua kali** di zone orientasi (di "Where this case stands" dan di
   "Learn this case").
2. **W2X-008 KONFIRMASI** — case page di app riil: AXWebArea tinggi
   **4.459pt** vs window **768pt** = **5,8x viewport** (lebih kecil dari
   browser 13,1x karena window app 768pt dan konten lebih sempit, tapi
   tetap hampir 6 layar penuh scroll).
3. **Layout 3 zone KONFIRMASI ada di app** — heading x positions: 1356
   (orientation), 1616 (work), 2333 (intelligence). Tiga kolom menyamping.
4. **Duplikasi Objective/Question KONFIRMASI** — Case overview menampilkan
   "Objective:" dan "Question:" dengan teks identik, keduanya 101pt tinggi
   di kolom sempit.

**Temuan baru fase 2:**

5. **LLM TIDAK aktif di app riil** (lihat W2X-012). Sidecar `dah-core` tidak
   membaca `server/.env` (tidak di-bundle; `dah-core.spec` hanya menyertakan
   version stamp). Test codegen mengembalikan `"source":"template"` (bukan
   "llm"). Jadi: di app yang user dapat, plan/draft/refine/chat LLM semua
   nonaktif dan jatuh ke deterministic.
6. **Kolom orientasi terlalu sempit di window riil** (lihat W2X-013). Di
   1280pt lebar, zone orientasi hanya ~232pt (18%). Pertanyaan panjang
   Indonesia terbungkus menjadi kolom 101pt tinggi × 198pt lebar — nyaris
   tidak bisa dibaca.
7. **Case list riil sudah tercemar**: 3 case + **5 template**, 4 dari 5
   template punya nama Indonesia identik panjang, satu di antaranya
   "A question-only skeleton - no shape was captured." Bukan bug, tapi
   menunjukkan template tidak punya dedup dan nama panjang membuat list
   tidak bisa dibedakan.

## Yang TIDAK diverifikasi di fase 2

- Interaksi klik/scroll di app riil terbatas: WKWebView tidak ada CDP, dan
  computer_use menemui window ambiguity (pid 75492 punya 7 window; scroll
  ke coordinate kosong tidak berpindah, `cmd+down` berhasil tapi capture
  setelahnya terbatas). Verifikasi interaktif penuh lebih baik dilakukan
  lewat browser (bundle sama) seperti fase 1.
- Menu native (Reveal DAH Logs, Check for Updates) tidak diklik.

## Kesimpulan fase 2

Temuan UX fase 1 **semua konfirmasi** di app riil. Temuan yang paling penting
hanya muncul di fase 2: **LLM nonaktif di app yang user dapat** — jadi
W2X-001 (timeout 120s) tidak akan terjadi di app riil karena LLM tidak
dipanggil sama sekali; tapi *semua* fitur LLM (plan, draft, refine, chat,
agent) juga tidak berfungsi. Itu masalah distribusi yang terpisah dari UX.

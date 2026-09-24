# Walkthrough Capture Sheet — DAH first-run new-case loop

**Protocol:** DAH new-case UX walkthrough v1 (dual-role: naive analyst + facilitator)
**App under test:** /Applications/DAH.app 0.3.2 (Tauri native, installed build)
**Date:** 2026-09-24
**Target:** the full analytical loop on a brand-new case, from a fresh empty store:
  create case -> attach CSV -> profile -> plan -> generate code -> run -> interpret
  -> draft finding -> accept -> validate -> chart -> agent -> evidence graph ->
  history -> export. Pass 1 deterministic; Pass 2 LLM.
**Dataset:** walktest/orders_q3.csv (11 rows, subscription revenue).
**Business question:** "Why did revenue fall in September after July's peak?"
**Honest answer:** July's 9602 is inflated — order 1003 (enterprise 4800) is
  double-booked (one exact duplicate row); August has a NULL amount. Real
  recurring Sept revenue (5703) is the highest month, so the premise is false.

---

## Pre-session checklist

| # | Check | Result |
|---|---|---|
| V1 | App version + built state matches target | *(to be recorded)* |
| V2 | Empty baseline (fresh store, 0 cases, log reset) | *(to be recorded)* |
| V3 | Evidence capture live (screenshot + DB reads + log) | *(to be recorded)* |
| V4 | Protocol read, dataset + question fixed, no app knowledge leaking in | *(to be recorded)* |
| V5 | No instruction given before the run (naive stance from here) | *(to be recorded)* |
| V6 | Capture sheet open before the session starts | *(to be recorded)* |

---

## Pass 1 — DETERMINISTIC engine

### Link 0 — First launch (empty store)

| # | Question | Answer |
|---|---|---|
| F0.1 | Time from launch to window visible | *(to be recorded)* |
| F0.2 | Is the empty state clear and actionable? | *(to be recorded)* |
| F0.3 | Does the case list show 0 cases without error? | *(to be recorded)* |
| L0.1 | As a new user, is it obvious what to do first? | *(to be recorded)* |

### Link 1 — Create the case

| # | Question | Answer |
|---|---|---|
| F1.1 | Form fields, labels, placeholders readable? | *(to be recorded)* |
| F1.2 | Core status line shown and correct? | *(to be recorded)* |
| F1.3 | Does it open the workspace straight after create? | *(to be recorded)* |
| L1.1 | Is it clear the question is the analytical goal, not a title? | *(to be recorded)* |
| L1.2 | Is it clear the dataset field is a *label*, not a file? | *(to be recorded)* |

### Link 2 — Attach the dataset

| # | Question | Answer |
|---|---|---|
| F2.1 | File picker opens and accepts the CSV? | *(to be recorded)* |
| F2.2 | Attach auto-profiles; is profiling progress/feedback visible? | *(to be recorded)* |
| F2.3 | Profile shows rows/cols/nulls/duplicates the dataset actually has? | *(to be recorded)* |
| L2.1 | Does the profile surface the duplicate + NULL without hunting? | *(to be recorded)* |

### Link 3 — Orientation: where this case stands

| # | Question | Answer |
|---|---|---|
| F3.1 | Stage panel names the single next action? | *(to be recorded)* |
| F3.2 | Panel order matches the workflow's real next step? | *(to be recorded)* |
| L3.1 | As a naive analyst, do you know what to click next? | *(to be recorded)* |

### Link 4 — Plan

| # | Question | Answer |
|---|---|---|
| F4.1 | Plan generated; sub-questions + hypotheses shown? | *(to be recorded)* |
| F4.2 | Is `source` (deterministic) visible? | *(to be recorded)* |
| L4.1 | Does the plan actually advance the business question? | *(to be recorded)* |

### Link 5 — Generate code + run

| # | Question | Answer |
|---|---|---|
| F5.1 | Code proposal shown with explanation + columns read? | *(to be recorded)* |
| F5.2 | Run executes and shows result rows? | *(to be recorded)* |
| F5.3 | Is the read-only constraint communicated? | *(to be recorded)* |
| L5.1 | Does the generated query answer the business question? | *(to be recorded)* |
| L5.2 | Does the result reveal the double-booking / the false premise? | *(to be recorded)* |

### Link 6 — Interpret + draft a finding

| # | Question | Answer |
|---|---|---|
| F6.1 | Interpret summarises + states what it cannot conclude? | *(to be recorded)* |
| F6.2 | Draft finding shown with grounds chips? | *(to be recorded)* |
| L6.1 | Is the draft's naive claim (July highest) flagged as misleading? | *(to be recorded)* |
| L6.2 | Is it clear a draft writes nothing until accepted? | *(to be recorded)* |

### Link 7 — Accept + validate

| # | Question | Answer |
|---|---|---|
| F7.1 | Accept creates the finding; status visible? | *(to be recorded)* |
| F7.2 | Validate shows per-check verdicts, incl. the missing-data failure? | *(to be recorded)* |
| L7.1 | Does the verdict make the false premise visible? | *(to be recorded)* |

### Link 8 — Chart

| # | Question | Answer |
|---|---|---|
| F8.1 | Chart config usable (kind/x/y/series)? | *(to be recorded)* |
| F8.2 | Image renders and persists? | *(to be recorded)* |

### Link 9 — Agent / Reviewer

| # | Question | Answer |
|---|---|---|
| F9.1 | Agent proposes a next step; approve/reject work? | *(to be recorded)* |
| F9.2 | Reviewer's EVALUATE nine-axis verdict readable? | *(to be recorded)* |
| L9.1 | Is the human-in-the-loop contract obvious? | *(to be recorded)* |

### Link 10 — Evidence graph + history + export

| # | Question | Answer |
|---|---|---|
| F10.1 | Evidence graph traces finding -> run -> dataset? | *(to be recorded)* |
| F10.2 | History timeline complete and ordered? | *(to be recorded)* |
| F10.3 | Export round trip works (download + re-import)? | *(to be recorded)* |

### Link 11 — Shell-wide impressions (Pass 1)

| # | Question | Answer |
|---|---|---|
| L11.1 | The two look-alike boxes ("Ask for the computation" vs "Ask this case") — did they confuse? | *(to be recorded)* |
| L11.2 | Information density: too much / about right / too little? | *(to be recorded)* |
| L11.3 | Anything that looked broken, stale, or silently wrong? | *(to be recorded)* |
| L11.4 | Most valuable panel; least valuable panel | *(to be recorded)* |

---

## Pass 2 — LLM engine (UX comparison only)

| # | Question | Answer |
|---|---|---|
| P2.1 | LLM plan vs deterministic: richer, and still grounded? | *(to be recorded)* |
| P2.2 | LLM interpret/draft: does richer output help or overwhelm? | *(to be recorded)* |
| P2.3 | Is the `source` switch visible enough to tell which engine spoke? | *(to be recorded)* |
| P2.4 | Latency acceptable? | *(to be recorded)* |

---

## Debrief (asked only after behaviour is recorded)

| # | Question | Answer |
|---|---|---|
| D1 | Would this tool change how you trust a number on a dashboard? | *(to be recorded)* |
| D2 | What is the single most confusing thing about this product? | *(to be recorded)* |
| D3 | What would you remove? | *(to be recorded)* |
| D4 | What would you never remove? | *(to be recorded)* |

---

## Post-session: evidence cross-check

| Field | Expected | Result |
|---|---|---|
| Store case count | 1 after Pass 1 | *(to be recorded)* |
| Profile: duplicate + null reported | yes, by the core | *(to be recorded)* |
| Finding validation verdict | missing-data check fails | *(to be recorded)* |
| Log present, no user data in it | yes | *(to be recorded)* |
| Export blob round trips | yes | *(to be recorded)* |

Rule applied: a capture field empty where the session clearly produced data is a
**finding, not a blank**. Any field the blob cannot confirm is marked
**"not in export"** rather than reconstructed.

---

## Findings register

*(filled after the run; see final report)*

---

## Session summary

**Chain traversed:** *(to be recorded)*
**Verdict vs intended:** *(to be recorded)*
**Questions answered:** <N/M> — zero `*(to be recorded)*` remaining is the exit criterion
**Findings:** <count, one line each>

---

*Exit criterion: sweep this file for `to be recorded`. Zero remaining, or every
remaining row marked "not observed" / "not in export" with a reason.*

# DAH — Decisions

## DEC-001 — Web-first MVP, Tauri desktop shell post-MVP

**Date:** 2026-09-18

### Decision

Build the MVP as a browser-served web application: **React + Vite** frontend, **Python
(FastAPI)** backend. Adopt **Tauri** as the desktop shell only **after the MVP passes**,
wrapping the existing React bundle with the Python core running as a sidecar.

### Technology selections (confirmed)

| Concern       | Choice          | Rationale                                |
|---------------|-----------------|------------------------------------------|
| Backend       | Python + FastAPI| Typed, structured I/O — fits the "structured not prose" AI rule |
| Case state    | SQLite          | Reliable transactional persistence for Analysis Cases |
| Analytical    | DuckDB          | Embedded, file-based analytical engine; kept strictly separate from state |

### Architectural contract

**The frontend must never touch the filesystem or DuckDB directly — only through the
API.** This is the single rule that makes the later Tauri migration a host swap rather
than a rewrite: the browser host is replaced by the desktop shell, and the React bundle
stays unchanged.

### Reason

A browser-served MVP is faster to iterate on and avoids coupling early feature work to
desktop packaging, signing, and sidecar complexity. Deferring Tauri removes a whole
class of P0 risk (shell integration, native build tooling) without compromising the
local-first execution model — datasets, DuckDB, and Analysis Cases all remain local.

### Alternatives considered

- **Tauri from P0 (previous plan):** earlier desktop value, but pays packaging and
  shell-integration cost before the core analytical loop is even proven.
- **Electron:** larger bundle and heavier resource use; no advantage over Tauri for a
  local-first Python-backed app.

### Consequences

- P0 exit criteria change: "Tauri shell works" becomes "web frontend builds and serves".
- Browser file-access limits are acceptable for the MVP; datasets are selected via the
  API, not by direct frontend filesystem reads.
- Tauri adoption becomes a P3 task with its own exit criteria, not a P0 dependency.
- FastAPI + SQLite + DuckDB are now fixed platform decisions (recorded here, not
  re-debated per task).

---

## DEC-004: macOS app signing is deferred to P5

**Decision:** the packaged `.app` ships **unsigned** through P4. Signing and
notarization are P5 work, and the deferral is recorded formally rather than
just happening.

### Context

P3-SHELL-008 made DAH a double-clickable Tauri app. macOS Gatekeeper blocks an
unsigned app on first launch: the user must right-click and choose *Open*, then
confirm. That is a real but bounded friction - it never touches functionality,
and it applies once per machine.

### Reason

The cost of signing now is not the $99 developer-program fee; it is the
*pipeline* that fee implies, and none of it is a P4 concern:

- A signing identity must be provisioned, stored as a CI secret, and rotated
  when it expires. P4 has **no CI at all yet** (this task adds it), so the
  secret store does not exist to put the identity into.
- Notarization requires the finished, versioned, icon'd bundle - the exact
  artifacts P5 is about. Signing an in-flight bundle means re-signing on every
  merge, which is pure churn.
- Gatekeeper's first-launch prompt is a *single* user-visible cost, paid once.
  Every hour spent on signing before P5 buys one fewer hour on the P4 items
  that decide whether the app is worth signing: reliability, performance, and
  the desktop lifecycle actually being verified in CI.

The deferral is safe because it degrades *gracefully*: the app still launches,
and the workaround is documented rather than discovered. Signing is a
distribution concern; P4 is a *production candidate*, P5 is *production grade*
and distribution is its definition.

### Alternatives considered

- **Sign now, in P4.** Pays the full pipeline cost twice - once to sign the
  in-flight bundle, once again at P5 when the bundle is final. And there is no
  CI secret store to hold the identity yet.
- **Ad-hoc / self-signed certs.** Gatekeeper still prompts; the user gets the
  same friction plus a scarier dialog naming an unverified developer. Strictly
  worse than unsigned, which at least is honest about being unsigned.
- **Document a bypass (`xattr -cr`)** as the supported path. Technically
  removes the prompt, but it teaches users to disable a security control and
  reads as a hack. Right-click > *Open* is the legitimate, Apple-blessed path
  and is what the docs will say.

### Consequences

- **P4 ships unsigned.** The README and the release notes must state the
  first-launch workaround in plain language (right-click, *Open*, *Open anyway*
  - once, per machine). This is a documented user-facing behaviour, not an
  omission.
- The deferral is **formal**, not accidental: it is listed in the P4 checklist
  as DONE-by-deferral and in the P5 entry checklist as a required item, so it
  cannot be quietly forgotten.
- **Signing must not become load-bearing.** Nothing in P4 may depend on the app
  being signed - the CI added by this task proves the sidecar *builds and
  serves*, which is the property that actually matters before distribution.
- When P5 signs, the pipeline lands in one place: the `packaging` job in
  `.github/workflows/ci.yml` gains the identity secret and the notarization
  step, and the unsigned build stays available as a fallback target.

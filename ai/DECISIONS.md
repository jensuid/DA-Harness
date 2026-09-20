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

---

## DEC-005: the CI runner is macos-latest, not a pinned Ventura (Intel) runner

**Date:** 2026-09-20 · **Status:** ACCEPTED

### Context

P5-CI-004 pinned every CI and release job to `macos-13` (Ventura), for two
reasons: to build and test against the documented minimum supported macOS, and
because macos-13 was the last Intel hosted runner - matching the development
machine and the `x86_64-apple-darwin` sidecar triple, so a green run proved the
exact binary a local build produces.

That pin never ran. The commit that introduced it also referenced the label
through `${{ env.MACOS_RUNNER }}` in `runs-on`, and the `env` context is not
available there, so the whole workflow failed at parse time - zero seconds,
every job, reported only as "a workflow file issue". Three commits shipped with
no CI at all before it was caught.

Fixing the expression exposed the real problem: **GitHub has retired the
macos-13 hosted runner pool.** Verified empirically against this repository with
a throwaway probe workflow holding two identical jobs - the `macos-latest` job
completed in under a minute while the `macos-13` job sat *queued with zero
steps for eighteen minutes* and never picked up a runner. A label nothing
provisions is not a floor, it is a hang.

### Decision

All jobs in `.github/workflows/ci.yml` and `.github/workflows/release.yml` run
on `macos-latest`, as a literal `runs-on:` - never an env reference.

### Consequences

- **The Ventura floor is documented, not enforced.** The minimum supported
  macOS stays Ventura in the README; CI builds on whatever macos-latest
  resolves to (Apple Silicon today). A green run proves the code, the gates and
  the packaging path. It does **not** prove the Intel triple a local build
  produces.
- **The published build is arm64.** The first real release (v0.1.0) produced
  `DAH_0.1.0_macos_aarch64-apple-darwin.zip`. The release notes derive their
  architecture paragraph from the runner's actual triple rather than asserting
  Intel, so an arm64 or Intel lane both describe themselves correctly.
- **Restoring the Intel lane needs a self-hosted runner** (a spare Intel Mac
  with the actions runner) or an explicit cross-compile lane. Neither is
  current work; the Apple Silicon build covers the machines the user actually
  runs, and Rosetta covers the rest.
- **The `env`-in-`runs-on` lesson is recorded in both workflow headers** so the
  indirection is not reintroduced. Silent parse-time failures are the worst
  failure mode here: they report nothing and block every job at once.

### Alternatives considered

- **Keep pinning macos-13.** Not an option - the pool is gone; the jobs would
  queue forever and CI would never run again.
- **Pin macos-14 / macos-15.** Available, but pins CI to a version that will
  itself be retired, and reintroduces the exact maintenance burden this avoids.
  macos-latest moves with GitHub's pool; the architecture is recorded in the
  release artifact's name either way.
- **A self-hosted Intel runner now.** Correct in principle, and the only way to
  restore the Intel-in-CI property, but it is hardware provisioning - the same
  class of external dependency as the Apple Developer ID. Deferred.

---

## DEC-006: signing deferred indefinitely; DAH is single-user for now

**Date:** 2026-09-20 · **Status:** ACCEPTED · **Supersedes:** the "P5 required"
framing of DEC-004

### Context

DEC-004 deferred macOS code signing to P5 and listed it as a required P5
checklist item, blocked on a $99 Apple Developer ID. P5 has now delivered
everything else - the P4 gate, observability, the 500 envelope, release
automation, the Reveal-logs menu and the CI repair - and v0.1.0 is published
and checksum-verified. Signing is the sole remaining item, and the user has
decided **DAH is for their own use for the foreseeable future**, not for
distribution to others.

That decision dissolves the blocker rather than leaving it open. A
single-user, single-machine tool does not need a notarized identity: the
right-click > *Open* workaround is once per machine, the user is the only
person who pays it, and nobody is installing an unverified developer's build.

### Decision

Signing and notarization move from "P5 required, blocked" to **indefinitely
deferred, by intent**. P5 closes without them. The unsigned build is not a
defect or an oversight - it is the correct posture for a personal tool, and
the README plus the generated release notes still state the first-launch
workaround for the day someone else does want a copy.

### Consequences

- **P5 is COMPLETE.** The one open checklist item is retired by this decision,
  not by work. The phase closes on the evidence that exists: green CI, a
  published and checksum-verified v0.1.0, and three verification gates.
- **The pipeline slot stays.** `release.yml` keeps its gap between the build
  and the upload. If the user ever provisions a Developer ID, signing lands
  there in one place and `--prerelease` is the flag to revisit - unchanged
  from DEC-004's plan.
- **No P5 gate script.** Unlike P2/P3/P4, P5's content is distribution and
  observability rather than an in-process journey, so its evidence is the
  release run and the CI run, not a `verification/p5/verify_p5.py`. Recorded
  here so the absence is a decision and not a gap.
- **The unsigned first launch stays documented** in `README.md` and in the
  generated release notes.

### Alternatives considered

- **Keep P5 nominally open** until an ID appears. Leaves a phase that is
  finished in everything but name, and blocks the roadmap's stage marker on a
  purchase nobody needs to make. A blocked phase that will never unblock on
  its own is a bookkeeping lie.
- **Buy the ID anyway.** Real money and real pipeline work (identity, secret
  rotation, notarization stapling) for a user base of one. The ROI is negative
  until distribution is real.

## DEC-007: ship the update check, not the self-replacing updater

**Date:** 2026-09-20 · **Status:** ACCEPTED

### Context

P6-UPDATE-005 is the last P6 item: "an update flow for the packaged app." The
roadmap's framing assumed `tauri-plugin-updater` with a local release channel.

Two facts, both already recorded rather than open, constrain what is
verifiable:

- **The repository is private.** An unauthenticated request to the release feed
  answers 404 - verified empirically before designing, not assumed. No token can
  be shipped in an unsigned app to work around it, and shipping one would be a
  secret in a binary anyone can read.
- **The app is unsigned** (DEC-006). Tauri's updater validates a payload against
  a signature, and a build that cannot be signature-verified cannot verify an
  update either. A self-replacing updater could not be tested end to end even if
  the feed were reachable.

So the full updater is unverifiable code claiming a capability it cannot prove -
precisely the failure mode this project's verification discipline exists to
prevent.

### Decision

Ship the **check** and not the **install**. `GET /updates/latest` answers one of
three truths - `current`, `available` (with tag, page URL and notes), or
`unknown` with a reason - and the shell's **DAH > Check for Updates...** menu
item opens the release page or shows that sentence. The self-replacing install
is a documented slot: `tauri-plugin-updater` consumes exactly this check when
signing lands, and nothing built now has to be undone to add it.

The load-bearing design rule: **"could not check" is never reported as "is up to
date."** A 404, a 403, a 503, a timeout, a non-JSON body and a body without a
version are each `unknown` with their own reason. A check that silently claims
current when it could not reach the feed is worse than no check, because it
converts "I do not know" into a false assurance the user cannot inspect.

### Consequences

- The check works correctly against a private repository by design: it reports
  `unknown`, "the release feed is not reachable; the repository may be private".
  When the repository goes public it answers properly with **no code change**.
- The release notes now carry a "Checking for updates" section stating the
  private-repository behaviour, so the honest answer is documented where a user
  reads it rather than only in the codebase.
- No new runtime dependency: httpx was already in the tree, and the shell opens
  the browser through `open`, as the reveal-logs menu already opens Finder.
- The install path stays manual (download and replace), which the unsigned
  first-launch step already covers in the README and the generated notes.

### Alternatives considered

- **Ship `tauri-plugin-updater` anyway.** Unverifiable: the feed is unreachable
  and the payload cannot be signed. It would add a dependency nothing exercises
  and a capability nothing proves.
- **Ship no update surface until signing lands.** Leaves the one genuine
  distribution gap - "how do I know a new build exists" - closed by nothing, when
  the honest half of it is cheap and safe today.
- **Poll on a schedule in the background.** A single user does not need a
  poller burning battery and network, and a background check that reports nothing
  visible is a check nobody asked for. The menu item is the trigger.

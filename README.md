# DAH — Data Analysis Harness

A local-first analysis tool: attach data, profile it, run read-only SQL or
Python against it, chart the result, and record a finding whose evidence chain
is inspectable and reproducible.

An agent can also drive that loop itself: it proposes each step, a human
approves it, and the write runs through the endpoint that already owns it. It
holds no privilege a hand-written call lacks.

See `docs/` for the specification, the implementation roadmap, and the LLM
configuration. Engineering state (phase, tasks, handoff) lives in `ai/`.

## Layers

| Layer | Path | Test command |
|-------|------|--------------|
| Core — FastAPI + SQLite + DuckDB | `server/` | `cd server && .venv/bin/python -m pytest -q` |
| Shell — React + Vite | `web/` | `cd web && npm test` |
| Desktop — Tauri 2, hosts the same bundle | `desktop/` | `cd desktop/src-tauri && cargo test --features e2e` |

Verification gates (each walks one journey end to end and re-runs the suite):

```bash
server/.venv/bin/python verification/p1/verify_p1.py   # in-process
server/.venv/bin/python verification/p2/verify_p2.py   # in-process
server/.venv/bin/python verification/p3/verify_p3.py   # in-process
server/.venv/bin/python verification/p4/verify_p4.py   # in-process
python3 verification/p0/verify_p0.py                   # binds a port
```

The gates drive the app in-process, which is fast but never binds a port or
runs uvicorn itself. The end-to-end run is the complement - a real server:

```bash
server/.venv/bin/python verification/e2e/verify_e2e.py # a real server, ~3s
```

It starts uvicorn on a free port with an isolated data dir, builds one case by
hand (upload, profile, plan, generated SQL, a refused write, interpretation, a
finding accepted, validation, EVALUATE on nine axes), lets the reviewer agent
audit that finding through the shared approval gate, drives a second case
entirely with the analyst agent, and round-trips through export/import. The LLM
variables are emptied for the server, so the deterministic engines answer and
the run needs no network.

CI (`.github/workflows/ci.yml`) runs the server suite, the in-process gates and
the real-server end-to-end run, the web suite plus a build, the desktop shell's
lifecycle tests against a live core, and a sidecar packaging build.

## Installing the app

DAH requires **macOS 13 (Ventura) or later** - that is the oldest version CI
builds and tests against, on Intel hardware; newer versions and Apple Silicon
are exercised the same way.

The packaged app is **currently unsigned** (see `ai/DECISIONS.md`, DEC-004 —
signing and notarization are P5). macOS Gatekeeper will therefore block the
first launch. To open it:

1. Right-click (or Control-click) the app.
2. Choose **Open** from the menu.
3. Confirm with **Open anyway** in the dialog that appears.

This is needed **once per machine** and does not affect anything afterwards.
It is a documented behaviour of the pre-release build, not a defect.

## Checking for updates

The **DAH > Check for Updates...** menu item asks the release feed whether a
newer build exists, and either opens the release page in your browser or says
why it could not tell.

While the repository is private, an unauthenticated feed request cannot reach
it, so the item reports "could not check - the repository may be private". That
is the honest answer rather than a silent claim that the app is current, and it
answers properly the moment the repository is public, with no code change. The
reasoning and the deliberate scope - the *check* ships, the self-replacing
*install* waits on signing - are in `ai/DECISIONS.md` (DEC-007).

## When something goes wrong

The core keeps a log next to your cases, so a failure leaves something behind
instead of vanishing. It is at `<data dir>/logs/dah-core.log` — on macOS,
`~/Library/Application Support/DAH-Harness/logs/` — capped at 2 MB with three
rotating backups.

Read the last of it without leaving a terminal:

```bash
curl -s http://127.0.0.1:8123/logs | python3 -c "import json,sys; [print(l) for l in json.load(sys.stdin)['lines']]" | tail -40
```

`GET /logs` is read-only and returns the path, the size, the backup names and
the last lines (default 200, at most 1000). What it does **not** return is your
data: request bodies, the SQL you wrote and the values in your datasets are
never logged. See `docs/Observability.md` for the full boundary.

## Getting a build

Versioned builds are published from CI on a `v<x.y.z>` tag: look at the repo's
**Releases** page. Each carries the `.app` and its SHA-256.

These builds are **unsigned** (DEC-004) and currently **Intel** — they run on
Apple Silicon under Rosetta. The release notes carry the Gatekeeper steps and
the checksum; verify with `shasum -a 256` against the published `.sha256` file.

## Building the packaged app

```bash
cd server && ./build_sidecar.sh        # PyInstaller core -> desktop/src-tauri/binaries/
cd ../desktop && npm install && npm run build
```

The `packaging` CI job runs the same path on a clean machine, so a regression
in the sidecar spec fails CI rather than landing unnoticed.

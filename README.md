# DAH — Data Analysis Harness

A local-first analysis tool: attach data, profile it, run read-only SQL or
Python against it, chart the result, and record a finding whose evidence chain
is inspectable and reproducible.

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
python3 verification/p0/verify_p0.py                   # binds a port
```

CI (`.github/workflows/ci.yml`) runs the server suite plus both in-process
gates, the web suite plus a build, the desktop shell's lifecycle tests against
a live core, and a sidecar packaging build.

## Installing the app

The packaged app is **currently unsigned** (see `ai/DECISIONS.md`, DEC-004 —
signing and notarization are P5). macOS Gatekeeper will therefore block the
first launch. To open it:

1. Right-click (or Control-click) the app.
2. Choose **Open** from the menu.
3. Confirm with **Open anyway** in the dialog that appears.

This is needed **once per machine** and does not affect anything afterwards.
It is a documented behaviour of the pre-release build, not a defect.

## Building the packaged app

```bash
cd server && ./build_sidecar.sh        # PyInstaller core -> desktop/src-tauri/binaries/
cd ../desktop && npm install && npm run build
```

The `packaging` CI job runs the same path on a clean machine, so a regression
in the sidecar spec fails CI rather than landing unnoticed.

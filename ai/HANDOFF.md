# DAH - Handoff

## What was completed

- DEC-001 recorded: web-first MVP, Tauri desktop shell post-MVP
- FastAPI, SQLite, DuckDB locked as platform decisions
- Four master docs updated to reflect web-first delivery
- graphify skill installed for Codex; AGENTS.md guidance live
- P0-INFRA-001 DONE: git repo, repo scaffold, FastAPI skeleton, health endpoint, pytest
- P0-WEB-002 DONE: Vite + React + TS shell, case-creation screen, api client, Vitest
- P0-DATA-003 DONE: SQLite case persistence, DuckDB analytical engine, case endpoints
- P0 GATE PASSED: verification/p0/verify_p0.py runs the exit-test sequence, REPORT.md written

## What changed

- verification/p0/verify_p0.py: repeatable P0 gate (start -> backend op -> persist
  -> restart -> recover -> tests); DB wiped only on first start so recovery is real
- ai/: state updated to P1 phase

## Tests performed

- P0 exit-test sequence: all 6 steps PASS
- server pytest: 5 passed; web vitest: 2 passed

## Unresolved problems

- none. CSV profiling exists in the engine but has no endpoint yet - arrives in P1.

## Next action

Decompose P1 into tasks. Suggested first batch (one session each):
1. CSV ingest endpoint (upload/attach a dataset to a case) + golden test
2. Attach profile to a case (wire profile_csv into the case flow)
3. SQL analysis run against an attached dataset via DuckDB + result persistence
4. Finding + evidence link (finding -> result -> query -> dataset chain)
5. Validation checks (reproducibility, denominator, missing data)

Keep AI planning out of the first slices - prove the deterministic loop first.

## Important context

- server venv at server/.venv (Python 3.14); install with `uv pip install --python .venv/bin/python -e ".[dev]"`
- web deps installed; node_modules gitignored
- dev DB is server/dah.db (gitignored); tests use tmp_path
- graph is stale: corpus is still the four docs but the repo now has real code
  (Python + TypeScript). Rebuild before P1 so the AST pass maps call/import structure.

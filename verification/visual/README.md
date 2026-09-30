# Visual verification

The gates render nothing: jsdom and Starlette's `TestClient` prove the
contract, not the picture, so a restyle can be green and still look wrong.
This directory is the complement - the shell against a real core, in a real
browser, reading computed styles and capturing screenshots.

## Run

```sh
server/.venv/bin/python verification/visual/verify_visual.py shots    # PNGs
server/.venv/bin/python verification/visual/verify_visual.py verify    # computed styles
```

`shots` writes `shots/01-list.png`, `02-workspace.png`, `03-workspace-full.png`
(gitignored - they are output, not source). `verify` prints the browser's
resolved values as JSON; extend its block in `drive_chrome.js` whenever a new
surface lands, because that output is the record of what a pass changed.

Nothing is mocked and no LLM key is used: the LLM env vars are scrubbed from
the core's subprocess so the deterministic engines answer, which makes a run
reproducible offline.

## What it stands on, and why

- **An isolated core on 8124.** The running desktop app owns 8123 with the
  analyst's real case store. This core binds 8124 to an ephemeral data dir,
  and the dev server's `/api` proxy is pointed at it with `DAH_CORE_PORT`
  (the target defaults to 8123). Do not aim this at 8123 - a seeded case
  lands in the user's database, and deleting it through the API afterwards is
  how that mistake was cleaned up the first time.
- **No CORS on the core**, so the client reaches it through the Vite proxy
  rather than directly - hence the dev server rather than a static one.
- **Chrome over CDP, no dependency** (DEC-001): Node 24 has a WebSocket
  client, so `drive_chrome.js` speaks the protocol itself.
- **Chrome's debug port answers `localhost`, not `127.0.0.1`**, and a second
  Chrome needs its own `--user-data-dir` or it exits silently without binding
  the port. The port defaults to 9333 because a long-lived Chrome on this
  machine already holds 9222.

## Where this belongs in a task

A restyle is verified twice: the suite (the contract) and `verify` (the
picture). If a check belongs in the suite - an a11y invariant, a structural
assertion - it belongs there, not here. This is for what a test cannot see:
the weight of a heading, the fill of a primary button, the surface an anchor
panel sits on.

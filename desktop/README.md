# DAH desktop shell

The Tauri 2 shell that turns DAH into a double-clickable app. Per DEC-001 this is
a **host swap, not a rewrite**: Tauri serves the *same* React bundle the browser
host serves, and that bundle keeps talking to the *same* FastAPI core over HTTP.
No frontend code was changed to make this work - the shell only starts the core,
waits for it to answer, shows the window, and stops the core when the window
closes.

```
+-------------------+   spawns child    +-------------------+
|  DAH.app (Tauri)  | ----------------> | dah-core (Python) |
|  webview: React   |                   |  FastAPI + DuckDB |
|  bundle, unchngd  | <---------------- |  127.0.0.1:8123   |
+-------------------+   HTTP /api        +-------------------+
```

## Layout

```
desktop/
  package.json                 dev/build script wrappers (`npm run dev`, `dev:hmr`, `build`)
  src-tauri/
    tauri.conf.json            window, bundle, and the two host commands
    capabilities/default.json  grants only core:default - no FS/shell/net perms
    src/main.rs                window lifecycle: spawn, gate, show, stop
    src/core_server.rs         how to start the core + the health gate (tested)
    binaries/dah-core-<triple> the packaged Python core (built, not committed)
    icons/                     generated from icons/icon.png
```

## How the core is started

`resolve_server_command` picks one of two paths, purely on whether the sidecar
sits next to the shell executable:

| Host     | Condition                                | Command                                                   |
|----------|------------------------------------------|-----------------------------------------------------------|
| Release  | `dah-core` beside the executable         | `dah-core --port 8123` (PyInstaller one-file, no cwd)     |
| Dev      | no sidecar                               | `server/.venv/bin/python -m uvicorn app.main:app --port 8123`, cwd `server/` |

`DAH_DEV_CORE=1` overrides the check and forces the dev path - handy because
`tauri dev` copies a built sidecar next to the dev executable, and a 40s one-file
unpack is the last thing an iterating developer wants.

Before the window is shown, the shell polls
`GET http://127.0.0.1:8123/health` (`wait_for_health`) until it answers 200. The
budget is resolution-aware: 30s for the dev virtualenv, 180s for the packaged
sidecar, whose one-file unpack costs tens of seconds on a cold disk. If the core
never answers, the window is shown anyway and the error is logged - the bundle
renders its own unreachable state.

The shell points the core at a per-user data directory (`app_data_dir`) via
`DAH_DATA_DIR` and `DAH_DB_PATH`, so a packaged app keeps its cases in
`~/Library/Application Support/com.jensuid.dah` rather than next to the binary.
Closing the window kills the core, so a stopped DAH leaves no stray process.

## Running it

Dev (needs `server/.venv`, built once by the server setup):

```sh
cd desktop
npm install                 # once - fetches the Tauri CLI
npm run dev                 # builds the shell, starts the core, opens the window
```

There are two dev modes, and the difference is only *where the webview loads the
bundle from*:

| Script | Bundle source | Hot reload |
|--------|---------------|------------|
| `npm run dev` | the embedded `web/dist-desktop` (`frontendDist`) | full rebuild + webview reload on change |
| `npm run dev:hmr` | the vite dev server | true HMR |

The default (`npm run dev`, no `devUrl` in `tauri.conf.json`) serves exactly the
assets the packaged app serves - it cannot drift from what ships. It runs
`web`'s `build:desktop:watch` and reloads the webview when the bundle changes.

`npm run dev:hmr` points the webview at the vite dev server for true HMR. The
frontend dev server is pinned to **5273**, not vite's 5173 default, because 5173
collides with another dev server on this machine; `web/vite.config.ts` sets
`strictPort: true` so a taken port aborts loudly instead of silently hopping to
the next free one. A silent hop is what made the shell show an empty window: the
webview's URL and the actual dev server ended up on different ports. If 5273 is
taken, use `npm run dev:hmr:5274` (or 5275/5276), which pins both sides to the
same free port.

Either way the usual `/api` proxy to :8123 applies and no separate terminal is
needed - the shell starts the core itself.

Packaged app:

```sh
cd server && ./build_sidecar.sh      # builds dah-core and installs it into src-tauri/binaries/
cd desktop && npm run tauri build    # release shell + bundle, with the core embedded
open src-tauri/target/release/bundle/macos/DAH.app
```

The bundle is **unsigned**. macOS will gatekeep it on first launch: right-click
the app, choose *Open*, and confirm. Signing and notarization are P5 work.

## Why no remote-URL capability

The webview loads the bundle through Tauri's built-in asset protocol
(`frontendDist`), and the desktop bundle is built with an absolute API URL
(`VITE_API_URL=http://127.0.0.1:8123`, see `web`'s `build:desktop` script). The
webview therefore never loads a remote URL, so no `core:webview:allow-external-load`
or `dangerousUseHttpScheme` permission is needed, and the capability file grants
nothing but `core:default`. The frontend stays HTTP-only, exactly as DEC-001
requires.

## Tests

```sh
cd desktop/src-tauri
cargo test                 # 5 unit tests: resolution for both hosts, the dev
                           # override, the health URL, and a silent-port gate
cargo test --features e2e  # +1: actually starts server/.venv's uvicorn through
                           # the resolver and requires a live 200 from /health
```

The resolution and health logic is deliberately split out of `main`: both are
pure functions of paths and a URL, so they are testable without a window.

## Known limits

- The sidecar is a PyInstaller **one-file** build (~85MB). Every launch unpacks
  it to a temp directory, which costs tens of seconds of startup before the
  window appears. A one-dir build plus Tauri resources would cut this sharply;
  deferred because it changes how `externalBin` addresses the binary.
- The window stays hidden until the core answers, so a broken core means a
  wait (bounded by the health budget) before the window appears with its
  unreachable state.
- macOS only so far. Windows and Linux need their own icon set and a rebuilt
  sidecar for the matching target triple.

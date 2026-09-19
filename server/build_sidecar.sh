#!/usr/bin/env bash
# Build the `dah-core` sidecar (packaged Python core) and place it where the
# Tauri bundler looks for it.
#
# Tauri's `bundle.externalBin` expects the binary at
# desktop/src-tauri/binaries/dah-core-<target-triple>, so a packaged app gets the
# right one per architecture. In dev the shell does not use this file - it starts
# server/.venv's uvicorn instead - so building it is only needed to produce a
# distributable .app.
set -euo pipefail

cd "$(dirname "$0")"

TARGET="${1:-$(rustc -vV | awk '/^host:/ {print $2}')}"
OUT="dah-core-${TARGET}"

echo "Building dah-core sidecar for ${TARGET}..."
.venv/bin/pyinstaller dah-core.spec --noconfirm --clean --distpath /tmp/dah-core-dist

echo "Installing as desktop/src-tauri/binaries/${OUT}..."
mkdir -p ../desktop/src-tauri/binaries
cp /tmp/dah-core-dist/dah-core "../desktop/src-tauri/binaries/${OUT}"

echo "Done. \`cargo tauri build\` in desktop/ will now bundle the core."

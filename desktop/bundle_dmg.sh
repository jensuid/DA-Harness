#!/usr/bin/env bash
# Deterministic DMG bundling for DAH.
#
# Tauri's `cargo tauri build` shells out to the vendored create-dmg fork at
# target/release/bundle/dmg/bundle_dmg.sh. That script's Finder-prettifying
# AppleScript is the non-determinism: it fails when the build is invoked from
# a context without a GUI session (an npm-run subprocess, CI, a shell without
# a logged-in WindowServer) and succeeds when it has one, with no code change
# between. Its own `--sandbox-safe` flag skips the AppleScript, and the DMG it
# produces is then identical run to run - the cosmetic Finder layout is what
# the AppleScript adds, and a DMG without it still opens, mounts and installs.
#
# So the release step builds the .app with tauri (which is deterministic) and
# then calls this script for the DMG rather than letting `tauri build` reach
# the failing path. `--sandbox-safe` is not a workaround here; it is the
# correct mode for a headless or non-interactive build.
#
# Usage: ./bundle_dmg.sh <version> <target-triple>
#   e.g. ./bundle_dmg.sh 0.3.4 x86_64-apple-darwin
set -euo pipefail

VERSION="${1:?usage: bundle_dmg.sh <version> <target-triple>}"
ARCH="${2:?usage: bundle_dmg.sh <version> <target-triple>}"

cd "$(dirname "$0")"

APP="src-tauri/target/release/bundle/macos/DAH.app"
DMG_DIR="src-tauri/target/release/bundle/dmg"
DMG="$DMG_DIR/DAH_${VERSION}_x64.dmg"

test -d "$APP" || { echo "no built .app at $APP - run 'npm run tauri -- build' first" >&2; exit 1; }

# Tauri names its DMG *_x64.dmg regardless of the triple's direction (arm64
# builds ship as *-aarch64 but the bundler's own name uses x64 for x86_64),
# and the vendored script is regenerated per build, so the path is derived
# from the directory rather than trusting a previous run's filename.
SCRIPT="$DMG_DIR/bundle_dmg.sh"
test -x "$SCRIPT" || { echo "no bundle_dmg.sh at $SCRIPT - tauri generates it during the app build" >&2; exit 1; }

rm -f "$DMG"

"$SCRIPT" \
  --sandbox-safe \
  --volname "DAH $VERSION" \
  --window-size 500 300 \
  --icon-size 96 \
  --app-drop-link 360 205 \
  "$DMG" \
  "$APP"

hdiutil verify "$DMG" >/dev/null
shasum -a 256 "$DMG"
echo "Built $DMG"

# PyInstaller spec for the DAH Python core sidecar.
#
# Builds a self-contained one-file binary that serves the FastAPI app, so the
# desktop shell can start the core on a machine with no Python. Built with:
#
#     cd server && ../server/.venv/bin/pyinstaller dah-core.spec
#
# (see build_sidecar.sh, which also copies the result where Tauri expects it).
#
# The one-file build unpacks to a temp dir at startup, which costs roughly a
# second of startup time - acceptable, and it keeps the .app bundle small.

import re
import tempfile
import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# The version this bundle reports at `/updates/latest`. Neither the installed
# distribution's metadata nor `pyproject.toml` itself reaches a one-file
# PyInstaller bundle, so the spec reads the version here - from the same file
# the release workflow's tag check reads - and stamps it into the bundle root as
# `dah-build-version.txt`, where `app.updates.current_version` finds it through
# `sys._MEIPASS`. Without it a packaged core answers `current: unknown` and the
# Check for Updates item can never compare versions.


def _build_version() -> str:
    """The version in pyproject.toml, or fail the build loudly.

    A bundle that reports `unknown` is the failure this exists to prevent, so a
    spec that cannot read a version aborts the build instead of shipping one
    whose label the app cannot answer. tomllib is the interpreter's own, so the
    parse is the standard one rather than a hand-rolled line match.
    """
    with open("pyproject.toml", "rb") as project_file:
        version = tomllib.load(project_file)["project"]["version"]
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", str(version)):
        raise SystemExit(
            f"dah-core.spec: pyproject.toml's version is {version!r}, not a "
            "release number - app.updates cannot compare it"
        )
    return str(version)


BUILD_VERSION = _build_version()
_stamp = Path(tempfile.gettempdir()) / "dah-build-version.txt"
_stamp.write_text(BUILD_VERSION, encoding="utf-8")
print(f"dah-core.spec: stamping version {BUILD_VERSION} into the bundle")

datas = [(str(_stamp), ".")]
binaries = []
hiddenimports = []

# FastAPI/Starlette/Pydantic resolve a lot by name at runtime; PyInstaller's
# static analysis misses it, so collect each framework wholesale.
for package in ("fastapi", "starlette", "pydantic", "uvicorn", "anyio", "duckdb", "PIL"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# uvicorn's protocol/loop implementations are selected by string at runtime.
hiddenimports += [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "email.mime.multipart",
    "app.python_worker",
]

a = Analysis(
    ["dah_core_main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="dah-core",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

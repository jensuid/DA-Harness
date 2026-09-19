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

from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas = []
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

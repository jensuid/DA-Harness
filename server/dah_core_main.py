"""Entrypoint for the `dah-core` sidecar (the packaged Python core).

DAH's desktop shell runs the FastAPI core as a child process. In a packaged app
that child is a PyInstaller one-file binary built from this script, because a
user's machine has no reason to have Python installed.

A thin script rather than `python -m uvicorn app.main:app` because PyInstaller
bundles modules, not module invocations - and because the shell speaks a tiny
command line to the core (`--port`), which is parsed here.

The shell sets DAH_DATA_DIR and DAH_DB_PATH before starting the core, so a
packaged app keeps its cases in the user's application-support directory instead
of next to the binary.
"""

import argparse
import sys

import uvicorn

from app.main import app


def parse_port(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dah-core", description="DAH Python core")
    parser.add_argument("--port", type=int, default=8123, help="port to listen on")
    args, _unknown = parser.parse_known_args(argv)
    return args.port


def main(argv: list[str] | None = None) -> int:
    port = parse_port(sys.argv[1:] if argv is None else argv)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

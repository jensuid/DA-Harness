"""In-sandbox entrypoint for analysis Python runs (P3-SEC-001).

This module is executed as a separate process by python_exec.run_python, one
per run, under the OS-level sandbox (sandbox-exec on macOS) *and* the in-process
guards from python_exec. It never runs inside the API process.

Contract with the parent:

    argv[1]        path to a JSON job: dataset_path, code, timeout_seconds
    stdout         one JSON object: the tabulated result, or {"error": ...}
    exit code      0 in both cases; non-zero means the harness itself broke

Keeping the process alive on contract violations is what lets the parent answer
400 with a useful message instead of a bare "child crashed".
"""

import json
import os
import sys
import traceback

_MAX_RESULT_BYTES = 64 * 1024 * 1024


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload))
    sys.stdout.write("\n")
    sys.stdout.flush()


def _run(job: dict) -> dict:
    from app.python_exec import execute_user_code

    result = execute_user_code(
        job["dataset_path"],
        job["code"],
        job.get("timeout_seconds", 30),
    )
    encoded = json.dumps(result)
    if len(encoded) > _MAX_RESULT_BYTES:
        raise ValueError(
            "analysis result is too large to persist "
            f"({len(encoded)} bytes; limit {_MAX_RESULT_BYTES})"
        )
    return result


def main() -> int:
    job_path = sys.argv[1]
    with open(job_path, encoding="utf-8") as handle:
        job = json.load(handle)

    try:
        _emit(_run(job))
        return 0
    except Exception as error:
        # A rejected contract (bad import, no result, wrong shape, time limit)
        # is reported, not tracebacked; the parent turns it into a 400.
        sys.stderr.write(traceback.format_exc())
        sys.stderr.flush()
        _emit({"error": str(error)})
        return 0


if __name__ == "__main__":
    # The worker inherits a scrubbed environment; nothing here should need it,
    # but a missing PATH would surface as a confusing import error.
    os.environ.setdefault("PATH", "/usr/bin:/bin")
    sys.exit(main())

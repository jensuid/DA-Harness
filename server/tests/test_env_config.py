"""Environment configuration loading (LLM key setup follow-up).

The server loads server/.env at import time so a plain uvicorn start picks up
the LLM key. These tests call the loader directly - the import-time call itself
is deliberately skipped under pytest so a developer with a real key configured
never makes live calls from the suite.
"""

import os
from pathlib import Path

from app.main import load_env_config

MARKER = "DAH_TEST_ENV_MARKER"


def test_env_file_is_loaded(tmp_path) -> None:
    env = tmp_path / ".env"
    env.write_text(f'{MARKER}="quoted-value"\n{MARKER}_BARE=plain-value\n')
    try:
        assert load_env_config(env) is True
        assert os.environ[MARKER] == "quoted-value"
        assert os.environ[f"{MARKER}_BARE"] == "plain-value"
    finally:
        os.environ.pop(MARKER, None)
        os.environ.pop(f"{MARKER}_BARE", None)


def test_missing_env_file_is_a_no_op(tmp_path) -> None:
    """No file, no change, no error."""
    assert load_env_config(tmp_path / "no-such.env") is False


def test_real_environment_wins_over_file(tmp_path) -> None:
    """An exported variable is not clobbered by a value in the file."""
    os.environ[MARKER] = "exported-value"
    env = tmp_path / ".env"
    env.write_text(f'{MARKER}="file-value"\n')
    try:
        load_env_config(env)
        assert os.environ[MARKER] == "exported-value"
    finally:
        os.environ.pop(MARKER, None)

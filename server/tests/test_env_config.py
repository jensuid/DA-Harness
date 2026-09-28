"""Environment configuration loading (LLM key setup follow-up).

The server loads server/.env at import time so a plain uvicorn start picks up
the LLM key. These tests call the loader directly - the import-time call itself
is deliberately skipped under pytest so a developer with a real key configured
never makes live calls from the suite.
"""

import os
from pathlib import Path

import pytest

from app.main import load_env_config

MARKER = "DAH_TEST_ENV_MARKER"


@pytest.fixture(autouse=True)
def no_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    """The loader writes `os.environ`, so each test declares what it sets and
    monkeypatch restores it. A `try/finally` that pops by name restores the
    variable only when the test itself set it; `load_env_config` is another
    writer, and a variable it set that the `finally` did not name would outlive
    the test the way the settings suite's `apply_config` writes did."""
    for name in (MARKER, f"{MARKER}_BARE"):
        monkeypatch.delenv(name, raising=False)


def test_env_file_is_loaded(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(f'{MARKER}="quoted-value"\n{MARKER}_BARE=plain-value\n')
    assert load_env_config(env) is True
    assert os.environ[MARKER] == "quoted-value"
    assert os.environ[f"{MARKER}_BARE"] == "plain-value"


def test_missing_env_file_is_a_no_op(tmp_path: Path) -> None:
    """No file, no change, no error."""
    assert load_env_config(tmp_path / "no-such.env") is False


def test_real_environment_wins_over_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An exported variable is not clobbered by a value in the file."""
    monkeypatch.setenv(MARKER, "exported-value")
    env = tmp_path / ".env"
    env.write_text(f'{MARKER}="file-value"\n')
    load_env_config(env)
    assert os.environ[MARKER] == "exported-value"

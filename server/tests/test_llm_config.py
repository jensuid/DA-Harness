"""W2X-012 phase B: the settings surface that puts the credential where the
packaged core can read it.

Phase A named the state: the packaged app carries no credentials, every LLM
feature silently falls back to the deterministic engine, and the analyst is
told nothing. This suite covers the half that changes the state - a file in the
data directory the shell already points the core at, loaded into the
environment at boot and re-applied on write, so the six adapters read it
without a restart and without one of them being touched.

The properties that make this safe rather than convenient, and that this file
pins:

- The key never reaches a log line or a response the webview can read. The GET
  endpoint answers the file's own shape, but the write's answer is the status
  surface's - and that surface's contract, pinned in test_llm_status.py, is
  that the provider is a name and never a value.
- The file is advisory, not authoritative: an exported variable wins. A
  developer's exported key or a container's injected one is the deployment's
  own answer, and a settings surface that silently overrode it would be a
  surface that changes what the deployment was configured to do.
- A blank key is no key, the same way the adapters and the status endpoint
  treat it, so clearing the field is clearing the setting.
- A write that lands is atomic, so a crash mid-write cannot leave a
  half-written file the next boot reads as no key.
- No new dependency (DEC-001), and nothing is compiled into the distributable.
"""

from __future__ import annotations

import json
import logging
import os
import stat
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import LlmConfig
from app.llm import (
    SETTINGS_FILE_NAME,
    _configured,
    load_settings,
    read_settings_file,
    settings_path,
    write_settings,
)


@pytest.fixture(autouse=True)
def no_llm_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """The state phase A asserts as a baseline is the state this suite starts
    from too: a key in the developer's environment would make every test here
    observe a configuration it did not set."""
    for name in ("DAH_LLM_API_KEY", "OPENAI_API_KEY", "DAH_LLM_MODEL", "DAH_LLM_BASE_URL"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def settings_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the loader and the endpoints at a directory this suite owns.

    The endpoints resolve the path at call time through `settings_path`, so
    repointing `db.DATA_DIR` is enough - the same seam `resolve_log_dir`
    uses, and the same one the suite uses for the log.
    """
    from app import db as db_module

    data_dir = tmp_path / "dah-data"
    data_dir.mkdir()
    monkeypatch.setattr(db_module, "DATA_DIR", data_dir)
    return data_dir


# -- the file the shell writes -------------------------------------------------


def test_the_settings_file_sits_in_the_data_dir(settings_dir: Path) -> None:
    # The one place both the shell and the packaged core can reach: the data
    # directory the shell injects as DAH_DATA_DIR, beside the cases and the log.
    assert settings_path() == settings_dir / SETTINGS_FILE_NAME


def test_an_explicit_dir_wins_over_the_module_default(tmp_path: Path) -> None:
    # Tests call the loader against a directory they own rather than the one
    # the suite repointed, so the override has to be the first thing tried.
    assert settings_path(tmp_path) == tmp_path / SETTINGS_FILE_NAME


def test_a_file_nothing_wrote_yet_is_empty(settings_dir: Path) -> None:
    # The packaged app's first launch: the settings file does not exist, and
    # that is the unconfigured state, not an error to surface.
    assert read_settings_file(settings_path(settings_dir)) == {}


def test_the_round_trip_keeps_the_three_fields(settings_dir: Path) -> None:
    write_settings(settings_path(settings_dir), LlmConfig(api_key="***", model="m", base_url="https://e/v1"))

    assert read_settings_file(settings_path(settings_dir)) == {
        "api_key": "***",
        "model": "m",
        "base_url": "https://e/v1",
    }


def test_a_blank_key_is_written_as_blank_and_read_back(settings_dir: Path) -> None:
    # Clearing the field is clearing the setting: the value is stored, and the
    # loader treats a blank as absent, the same way the adapters do.
    write_settings(settings_path(settings_dir), LlmConfig())

    assert read_settings_file(settings_path(settings_dir)) == {
        "api_key": "",
        "model": "",
        "base_url": "",
    }


def test_the_settings_file_is_owner_readable_only(settings_dir: Path) -> None:
    # A credential in the user's data directory is still a credential. 600 is
    # the one thing that costs nothing and asks no dependency (DEC-001).
    write_settings(settings_path(settings_dir), LlmConfig(api_key="***"))

    mode = stat.S_IMODE(os.stat(settings_path(settings_dir)).st_mode)
    assert mode == 0o600


def test_the_write_is_atomic_so_a_crash_leaves_no_half_file(settings_dir: Path) -> None:
    # os.replace is the whole read: the file either is the new settings or is
    # the old one. A .tmp left behind by a crash is not a settings file the
    # loader reads, and the next boot sees the previous state intact.
    write_settings(settings_path(settings_dir), LlmConfig(model="first"))
    write_settings(settings_path(settings_dir), LlmConfig(model="second"))

    assert read_settings_file(settings_path(settings_dir))["model"] == "second"
    # The intermediate the atomic replace wrote through is gone.
    assert not (settings_dir / f"{SETTINGS_FILE_NAME}.tmp").exists()


def test_no_settings_tmp_is_left_when_the_parent_has_no_dir_yet(tmp_path: Path) -> None:
    # The endpoint writes into a directory that exists under the shell, but a
    # fresh data dir is the first-launch case the loader has to survive too.
    fresh = tmp_path / "fresh"
    write_settings(fresh / SETTINGS_FILE_NAME, LlmConfig(api_key="***"))

    assert read_settings_file(fresh / SETTINGS_FILE_NAME) == {"api_key": "***", "model": "", "base_url": ""}
    assert not (fresh / f"{SETTINGS_FILE_NAME}.tmp").exists()


# -- loading into the environment ----------------------------------------------


def test_a_written_key_reaches_the_environment(settings_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The six adapters read the environment at call time, so this is the whole
    # mechanism: the file becomes the environment, and no restart is needed.
    # `load_settings` writes to `os.environ`, so the variable it sets is
    # restored at teardown: leaking it would hand every later test in the
    # suite a configured LLM it did not ask for, and the refinement suite's
    # "without a key the deterministic engine answers" would answer through a
    # network call instead.
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    write_settings(settings_path(settings_dir), LlmConfig(api_key="from-file"))

    load_settings()

    assert os.environ["DAH_LLM_API_KEY"] == "from-file"


def test_an_exported_variable_wins_over_the_file(settings_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The file is advisory. A developer's exported key or a container's
    # injected one is the deployment's own answer, and a settings surface that
    # silently overrode it would change what the deployment was configured to do.
    monkeypatch.setenv("DAH_LLM_API_KEY", "exported")
    write_settings(settings_path(settings_dir), LlmConfig(api_key="from-file"))

    load_settings()

    assert os.environ["DAH_LLM_API_KEY"] == "exported"


def test_a_blank_key_in_the_file_is_absent(settings_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The same blank-is-absent contract the status endpoint and the adapters
    # hold: an empty field is the analyst clearing the setting, not an empty
    # key the core would try to authenticate with. `load_settings` honours it
    # by not writing the variable at all, so the assertion is the status
    # surface's own notion of configured - a variable set to an empty string
    # is still absent, and `is None` would be a claim about the dictionary
    # rather than about the product.
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    write_settings(settings_path(settings_dir), LlmConfig(api_key="   "))

    load_settings()

    assert _configured().configured is False


def test_model_and_base_url_reach_their_own_variables(settings_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The two values the status surface already reports are settings too: a
    # provider other than the default is a base URL change, and the model is
    # the one a deployment most often pins. Both are restored at teardown for
    # the same reason the key is.
    monkeypatch.delenv("DAH_LLM_MODEL", raising=False)
    monkeypatch.delenv("DAH_LLM_BASE_URL", raising=False)
    write_settings(settings_path(settings_dir), LlmConfig(model="the-model", base_url="https://e/v1"))

    load_settings()

    assert os.environ["DAH_LLM_MODEL"] == "the-model"
    assert os.environ["DAH_LLM_BASE_URL"] == "https://e/v1"


def test_the_key_does_not_write_the_openai_fallback_var(settings_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The settings surface writes the product's own name only. Writing the
    # fallback too would race a developer's exported OPENAI_API_KEY over which
    # variable is authoritative, and the status surface's provider field is
    # what would report the wrong one.
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    write_settings(settings_path(settings_dir), LlmConfig(api_key="***"))

    load_settings()

    assert os.environ.get("OPENAI_API_KEY") is None


def test_an_unreadable_file_is_absent_not_an_error(settings_dir: Path) -> None:
    # A file another build shaped differently, or one a user edited by hand,
    # is a state - and a loader that raised on it would make the app fail to
    # boot over a settings file.
    settings_path(settings_dir).write_text("{not json", encoding="utf-8")

    assert read_settings_file(settings_path(settings_dir)) == {}


def test_a_payload_that_is_not_an_object_is_absent(settings_dir: Path) -> None:
    settings_path(settings_dir).write_text('["api_key"]', encoding="utf-8")

    assert read_settings_file(settings_path(settings_dir)) == {}


def test_fields_that_are_not_strings_are_dropped(settings_dir: Path) -> None:
    # A hand-edited file with a number where a string belongs does not become
    # a TypeError at boot; the field is absent and the default applies.
    settings_path(settings_dir).write_text(
        json.dumps({"api_key": 12345, "model": None, "base_url": "https://e/v1"}),
        encoding="utf-8",
    )

    assert read_settings_file(settings_path(settings_dir)) == {"base_url": "https://e/v1"}


def test_unknown_keys_are_ignored(settings_dir: Path) -> None:
    # A field a newer build writes is not a reason for this build to fail; the
    # three this build knows are the three it reads. Absent fields are absent,
    # and the defaults the adapters hold are what answers for them.
    settings_path(settings_dir).write_text(
        json.dumps({"api_key": "***", "organization": "acme"}),
        encoding="utf-8",
    )

    assert read_settings_file(settings_path(settings_dir)) == {"api_key": "***"}


# -- the endpoints -------------------------------------------------------------


def test_the_read_endpoint_answers_the_files_shape(client: TestClient, settings_dir: Path) -> None:
    write_settings(settings_path(settings_dir), LlmConfig(api_key="***", model="m", base_url="https://e/v1"))

    body = client.get("/llm/config").json()

    assert body == {"api_key": "***", "model": "m", "base_url": "https://e/v1"}


def test_the_read_endpoint_answers_blanks_when_nothing_is_written(client: TestClient, settings_dir: Path) -> None:
    # The first-launch state the surface opens against: three empty fields,
    # not three defaults the surface would have to undo to write its own.
    assert client.get("/llm/config").json() == {"api_key": "", "model": "", "base_url": ""}


def test_the_write_endpoint_answers_the_status_the_banner_renders(
    client: TestClient, settings_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Writing is a state change on the deployment, so the answer is the status
    # surface's own shape - the surface says "configured" the moment it is,
    # and the shell does not have to refetch to learn it. The PUT applies to
    # `os.environ`, so the variables it touched are restored at teardown: a
    # leaked key makes later suites' "without a key" answers unreachable.
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    response = client.put("/llm/config", json={"api_key": "from-form", "model": "the-model", "base_url": "https://e/v1"})

    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is True
    # The provider names the env var, never its value - the one property a
    # CORS-permitted webview reading this response must not be able to break.
    assert body["provider"] == "DAH_LLM_API_KEY"
    assert body["model"] == "the-model"
    assert body["base_url"] == "https://e/v1"


def test_the_write_endpoint_persists_across_a_reread(client: TestClient, settings_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client.put("/llm/config", json={"api_key": "from-form", "model": "the-model"})

    assert client.get("/llm/config").json() == {
        "api_key": "from-form",
        "model": "the-model",
        "base_url": "",
    }


def test_a_blank_key_write_answers_unconfigured(client: TestClient, settings_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Clearing the field clears the setting, and the answer says so: the
    # banner renders the concern state again, which is how the analyst learns
    # the clearing landed.
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client.put("/llm/config", json={"api_key": "from-form"})
    response = client.put("/llm/config", json={"api_key": ""})

    assert response.json()["configured"] is False


def test_clearing_the_key_unsets_the_variable_not_blanks_it(client: TestClient, settings_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The bug this caught in the making: a first PUT sets the variable, and a
    # second PUT with a blank key has to *unset* it. Yielding to the
    # environment the way the boot loader does would leave the cleared key
    # live, and the banner would say unconfigured while the adapters still
    # authenticated with a key the analyst thinks they removed.
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client.put("/llm/config", json={"api_key": "from-form"})
    client.put("/llm/config", json={"api_key": ""})

    assert "DAH_LLM_API_KEY" not in os.environ


def test_a_written_key_does_not_shadow_an_exported_fallback(
    client: TestClient, settings_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The write path overwrites the product's own variable, but it leaves the
    # OpenAI fallback alone: a developer's exported key stays the deployment's
    # answer, and the status surface keeps reporting the variable that
    # actually supplied it.
    monkeypatch.setenv("OPENAI_API_KEY", "exported")
    client.put("/llm/config", json={"api_key": "from-form"})

    assert os.environ["OPENAI_API_KEY"] == "exported"
    assert os.environ["DAH_LLM_API_KEY"] == "from-form"


def test_the_written_key_reaches_the_environment_without_a_restart(
    client: TestClient, settings_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The whole point of re-applying on write: the six adapters read the
    # environment at call time, so the next plan or draft call sees the new
    # key in the same process.
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client.put("/llm/config", json={"api_key": "from-form"})

    assert os.environ["DAH_LLM_API_KEY"] == "from-form"


def test_the_write_is_atomic_through_the_endpoint(client: TestClient, settings_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client.put("/llm/config", json={"api_key": "from-form"})

    assert not (settings_dir / f"{SETTINGS_FILE_NAME}.tmp").exists()


def test_no_response_or_log_line_carries_the_key(
    client: TestClient, settings_dir: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The property phase A pinned for the status surface holds for the surface
    # that changes it: the key goes to the file, never to a body the webview
    # can read or a line the log can capture. The whole body is checked, and
    # the read endpoint's own body is the one that carries the key by design -
    # so that one is asserted separately, below, as the deliberate exception.
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with caplog.at_level(logging.INFO, logger="dah.core"):
        write_response = client.put("/llm/config", json={"api_key": "secret-key-value"})
        status_response = client.get("/llm/status")

    assert "secret-key-value" not in str(write_response.json())
    assert "secret-key-value" not in str(status_response.json())
    assert "secret-key-value" not in caplog.text


def test_the_read_endpoint_is_the_one_that_echoes_the_key_for_the_form(
    client: TestClient, settings_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The deliberate exception, and the reason it is safe: the read answers
    # the file's own contents so the form can pre-fill, and the shell's
    # webview is the CORS-permitted origin the allowlist already limits this
    # core to. The key never reaches the status surface, which is the one a
    # banner renders on every screen.
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client.put("/llm/config", json={"api_key": "secret-key-value"})

    body = client.get("/llm/config").json()

    assert body["api_key"] == "secret-key-value"


def test_an_unreadable_file_answers_blanks_without_raising(client: TestClient, settings_dir: Path) -> None:
    # The endpoint is what the settings surface opens against, so it answers
    # blanks rather than a 500 - the analyst still has to reach the form to
    # fix the file.
    settings_path(settings_dir).write_text("{not json", encoding="utf-8")

    assert client.get("/llm/config").json() == {"api_key": "", "model": "", "base_url": ""}


def test_an_exported_key_still_answers_configured(client: TestClient, settings_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The file is advisory, so a deployment that configured the key by
    # environment - the developer's own checkout - still reports the LLM is
    # there, and the banner stays silent rather than falsely offering to fix
    # a state that is not broken.
    monkeypatch.setenv("DAH_LLM_API_KEY", "exported")

    assert client.get("/llm/status").json()["configured"] is True


def test_write_settings_rejects_anything_that_is_not_the_model(settings_dir: Path) -> None:
    # A programming error, and the endpoint's 500 handler answers rather than
    # the loader silently storing nothing.
    with pytest.raises(TypeError):
        write_settings(settings_path(settings_dir), {"api_key": "not-a-model"})  # type: ignore[arg-type]

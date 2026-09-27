"""W2X-012: the core says, on a surface the shell can read, whether the LLM
features are actually configured.

The walk-test's BLOCKER was not a failure but a silence: the packaged app
carries no credentials, so every LLM feature fell back to the deterministic
engine and the analyst was told nothing. The `source` field that carried the
truth is a developer's field, and the analyst reads no part of it. This
endpoint is the answer the shell asks for on mount.

The suite's other job is the one the client cannot do for itself: pin the
field the component branches on. The web tests replace the whole api module
with mocks, so a fixture supplies `configured` whether the server emits it or
not - which is exactly how a status field ships dead while every test is
green. Here the server is the thing under test, so a response that dropped
`configured` is a response this file fails on.
"""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.llm import KEY_VARS, llm_status

#: The fields the shell reads. A change to the response model that drops or
#: renames one of these is a change to the client's branch, and the client's
#: own test cannot see it.
RESPONSE_FIELDS = frozenset({"configured", "provider", "model", "base_url"})


@pytest.fixture(autouse=True)
def no_llm_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """A key in the developer's environment would make `configured` true for
    every test in this file, so the state under test is asserted rather than
    inherited."""
    for name in (*KEY_VARS, "DAH_LLM_MODEL", "DAH_LLM_BASE_URL"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_reports_unconfigured_with_the_public_defaults(client: TestClient) -> None:
    response = client.get("/llm/status")

    assert response.status_code == 200
    # `configured` is the field the shell branches on: False is the packaged
    # app's actual state, and the one the whole surface exists to say.
    assert response.json() == {
        "configured": False,
        "provider": None,
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
    }


def test_reports_configured_with_the_provider_name_not_the_key(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The walk-test's own environment, and the developer's. The value is a
    # secret; the name is what the analyst sets.
    monkeypatch.setenv("DAH_LLM_API_KEY", "sk-not-a-real-key")
    monkeypatch.setenv("DAH_LLM_MODEL", "the-model")
    monkeypatch.setenv("DAH_LLM_BASE_URL", "https://example.invalid/v1")

    response = client.get("/llm/status")

    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is True
    # The provider names the env var, never its value - the one thing this
    # endpoint must never hand to a CORS-permitted webview or a log line.
    assert body["provider"] == "DAH_LLM_API_KEY"
    assert body["model"] == "the-model"
    assert body["base_url"] == "https://example.invalid/v1"


def test_the_openai_fallback_var_configures_the_same_way(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A developer with an exported OpenAI key gets the LLM without setting a
    # second variable, so the fallback is part of the contract, not a courtesy.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-not-a-real-key")

    response = client.get("/llm/status")

    assert response.status_code == 200
    assert response.json()["configured"] is True
    assert response.json()["provider"] == "OPENAI_API_KEY"


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_a_blank_key_is_no_key(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, blank: str
) -> None:
    # The adapters treat a blank value as absent; this endpoint must agree, or
    # the shell would promise an LLM the core never calls.
    monkeypatch.setenv("DAH_LLM_API_KEY", blank)

    response = client.get("/llm/status")

    assert response.status_code == 200
    assert response.json()["configured"] is False


def test_a_blank_key_does_not_shadow_the_fallback_var(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DAH_LLM_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-not-a-real-key")

    response = client.get("/llm/status")

    assert response.status_code == 200
    assert response.json()["configured"] is True
    assert response.json()["provider"] == "OPENAI_API_KEY"


def test_every_field_the_client_branches_on_is_emitted(client: TestClient) -> None:
    # The web suite mocks this response, so a field the model dropped would
    # be filled in by a fixture and the branch would ship dead (P9-F4's
    # `format` field failed exactly this way). This is the test that sees it.
    body = client.get("/llm/status").json()

    assert set(body) == RESPONSE_FIELDS


def test_the_response_never_contains_a_key_value(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A status that echoed any part of a credential would be a secret the
    # webview can read and a log line can capture. The whole body is checked,
    # because a key nested somewhere new is how this breaks.
    monkeypatch.setenv("DAH_LLM_API_KEY", "sk-not-a-real-key")

    body = str(client.get("/llm/status").json())

    assert "sk-not-a-real-key" not in body


def test_the_boot_line_states_the_engine_without_the_key(
    client: TestClient, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The log line is what `Reveal DAH Logs` shows, so it carries the same
    # property as the endpoint: the state, not the credential.
    monkeypatch.setenv("DAH_LLM_API_KEY", "sk-not-a-real-key")

    with caplog.at_level(logging.INFO, logger="dah.core"):
        from app import llm as llm_module

        llm_module.log_llm_status()

    assert "sk-not-a-real-key" not in caplog.text
    assert "llm configured" in caplog.text


def test_the_boot_line_names_the_fallback_engines_when_unconfigured(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="dah.core"):
        from app import llm as llm_module

        llm_module.log_llm_status()

    assert "deterministic" in caplog.text


def test_the_status_is_read_only(client: TestClient) -> None:
    # A GET with no body and no path parameters: nothing the caller supplies
    # can reach the environment the answer is computed from. A body sent to a
    # route that declares none is refused rather than read.
    response = client.request("GET", "/llm/status", content=b'{"configured": true}')

    # FastAPI refuses a body on a GET route that declares no body model, so
    # the answer is whatever the environment says, never the caller's.
    assert response.status_code != 200 or response.json()["configured"] is not True


def test_the_direct_helper_agrees_with_the_endpoint(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The six adapters each have their own read; this is the one the shell
    # asks, and it has to agree with the endpoint it backs.
    monkeypatch.setenv("DAH_LLM_API_KEY", "sk-not-a-real-key")

    assert llm_status().model_dump() == client.get("/llm/status").json()

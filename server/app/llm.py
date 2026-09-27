"""The one place the LLM's configuration is read (W2X-012).

Six adapters each read the same three environment variables through their own
`_configured_llm()`, so six places decide whether the analyst gets an LLM
answer or a deterministic one. That duplication is not this task's problem to
remove - but the *answer* to "is an LLM configured" has to be one place,
because it is now a question the shell asks the core on a surface the analyst
reads.

The endpoint and the component it serves answer a walk-test finding about a
silent degradation, not a slow one: the packaged app carries no credentials, so
every LLM feature fell back to the deterministic engine and the analyst was
told nothing. `source: template` in the response was the only evidence, and it
is the evidence a developer reads, not an analyst. The shell now asks this
endpoint once on mount and says, in a sentence, what the analyst is actually
getting - and, when the LLM is configured, says nothing at all, because a green
banner on every screen is noise the analyst learns to dismiss.

Phase B is the half that *fixes* the state phase A only named. A packaged app
cannot receive a credential the way a checkout does: `.env` is gitignored and
un-bundled, and a PyInstaller one-file build unpacks to a temp directory whose
path no source-relative `.env` resolves against. The credential has to come from
somewhere the packaged core can actually read, and the only place that is both
writable by the shell and readable by the core is the data directory the shell
already points the core at (`DAH_DATA_DIR`, injected in `core_server.rs`) - the
same directory the cases and the log already live in. So this module loads a
small JSON file from there into the environment, once at boot and again whenever
the settings surface writes it, and the six adapters keep reading the same
variables they always have. No adapter is touched, and no credential is compiled
into a binary that can be reversed.

What this reports deliberately excludes: the key. A status endpoint that echoed
any part of a credential would be a secret the CORS-permitted webview could
read and a log line could capture, so the answer carries only the *provider*
(which of the two env vars supplied it) and the two values that are already
public defaults: the model name and the base URL.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from app.models import LlmStatus

if TYPE_CHECKING:
    from app.models import LlmConfig

LOGGER = logging.getLogger("dah.core")

#: The env vars an OpenAI-compatible key can come from, in the order the six
#: adapters read them. `DAH_LLM_API_KEY` is the product's own name; the
#: fallback to the OpenAI one is so a developer with a key already exported
#: does not have to set a second.
KEY_VARS = ("DAH_LLM_API_KEY", "OPENAI_API_KEY")

#: The two values that are safe to report: the defaults are public constants
#: in every adapter, and a configured deployment overrode them deliberately.
MODEL_VAR = "DAH_LLM_MODEL"
BASE_URL_VAR = "DAH_LLM_BASE_URL"

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"

#: The settings file the shell's settings surface writes (W2X-012 phase B).
#: Sits in the data directory the shell already injects as `DAH_DATA_DIR` -
#: the one place both the shell and the packaged core can reach - and nowhere
#: else, so a credential is never compiled into the distributable and never
#: committed (`.env` is gitignored and un-bundled; this file is in the user's
#: application-support directory, which the repository never touches).
SETTINGS_FILE_NAME = "dah-llm.json"

#: The fields the settings file holds, and the variables they are applied to.
#: `api_key` is written to `DAH_LLM_API_KEY` only - never to the OpenAI
#: fallback var - so the settings surface and a developer's exported key do
#: not race over which one is authoritative.
SETTINGS_FIELDS = ("api_key", "model", "base_url")

_SETTINGS_TO_ENV = {
    "api_key": "DAH_LLM_API_KEY",
    "model": MODEL_VAR,
    "base_url": BASE_URL_VAR,
}


@dataclass(frozen=True)
class _Config:
    configured: bool
    provider: str | None
    model: str
    base_url: str


def settings_path(data_dir: Path | None = None) -> Path:
    """Where the settings file belongs (W2X-012 phase B).

    An explicit argument wins (tests use it against a tmp dir); then the data
    directory the shell already points at, which under the desktop shell is
    the user's application-support directory - the same place the cases and
    the log already live. Falls back to the module's data dir for a
    hand-started core, matching ``resolve_log_dir``'s convention.
    """
    if data_dir is not None:
        return data_dir / SETTINGS_FILE_NAME
    from app import db as db_module

    return Path(db_module.DATA_DIR) / SETTINGS_FILE_NAME


def read_settings_file(path: Path) -> dict[str, str]:
    """Read the settings file, as the loader and the GET endpoint both need.

    Anything that is not a JSON object, and any field that is not a string,
    is absent rather than an error: a file nothing writes yet, a file another
    build shapes differently and a file a user edited by hand are all states,
    and a settings surface that raised on them would be a surface that cannot
    open. ``nonlocal``-free - the caller decides what to do with ``{}``.
    """
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        # An unreadable file is reported as empty rather than raising: the
        # analyst still has to reach the settings surface to fix it.
        LOGGER.warning("the LLM settings file %s could not be read", path)
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        field: value
        for field in SETTINGS_FIELDS
        if isinstance((value := payload.get(field)), str)
    }


def load_settings(data_dir: Path | None = None) -> None:
    """Apply the settings file to the environment (W2X-012 phase B).

    The six adapters read the environment at call time, not at import, so
    setting the variables here is enough for the next adapter call to see
    them - no restart, and no adapter is touched. A variable already set in
    the environment wins: a developer's exported key or a container's
    injected one is the deployment's own answer, and a file written through
    the settings surface must not silently override it. Blank is absent, the
    same way ``_configured`` and the adapters treat it.

    No value here is logged. The privacy property the walk-test verified - no
    request body or response payload in the log, ever - holds because nothing
    in this function hands a value to a logger; the boot line that follows it
    names the engine, not the key.
    """
    path = settings_path(data_dir)
    for field, value in read_settings_file(path).items():
        if not value.strip():
            continue
        env_name = _SETTINGS_TO_ENV[field]
        if os.environ.get(env_name, "").strip():
            # The environment already answers. Keeping it is the property
            # that makes the file advisory rather than authoritative.
            continue
        os.environ[env_name] = value


def apply_config(config: "LlmConfig | object") -> None:
    """Apply a written config to the environment (W2X-012 phase B).

    The write path, as distinct from ``load_settings``: a value the analyst
    just submitted through the settings surface *is* the new answer, so it
    overwrites the variable rather than yielding to it, and a blank field
    unsets it - clearing the key is clearing the setting. ``load_settings``
    yields to an exported variable instead, because that is a variable the
    deployment itself set and a file written through a form must not silently
    override it; this one does not yield, because the form is the thing that
    just wrote it.

    Only the product's own variable is touched. The OpenAI fallback var is
    left alone: writing it too would race a developer's exported key over
    which one is authoritative, and the status surface's provider field is
    what would report the wrong one.
    """
    from app.models import LlmConfig

    if not isinstance(config, LlmConfig):
        raise TypeError("apply_config takes an LlmConfig")
    for field, env_name in _SETTINGS_TO_ENV.items():
        value = str(getattr(config, field, "") or "").strip()
        if value:
            os.environ[env_name] = value
        else:
            os.environ.pop(env_name, None)


def write_settings(path: Path, config: "LlmConfig | object") -> None:
    """Persist the settings the shell's surface collected (W2X-012 phase B).

    Typed loosely on purpose: the model lives in ``app.models`` and importing
    it at module scope would be an import cycle, so it is imported here and
    the fields are read by name. A caller passing anything else is a
    programming error this file does not paper over - it raises, and the
    endpoint's 500 handler answers.

    The file is created readable by the owner only: a credential in the
    user's data directory is still a credential, and 600 is the one thing
    that costs nothing and asks no dependency (DEC-001). Write is
    atomic-by-replace rather than in place, so a crash mid-write cannot leave
    a half-written settings file that the next boot reads as no key.

    Nothing here is logged: the value is written, never handed to a logger.
    """
    from app.models import LlmConfig

    if not isinstance(config, LlmConfig):
        raise TypeError("write_settings takes an LlmConfig")
    payload = {
        field: str(getattr(config, field, "") or "")
        for field in SETTINGS_FIELDS
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _configured() -> _Config:
    """Read the environment once, answering only what is safe to report.

    The provider names the variable rather than its value: `DAH_LLM_API_KEY`
    tells an analyst which setting to change, and a value would be a key. A
    blank value is treated as absent, the same way the adapters treat it, so
    this endpoint and the adapters cannot disagree about whether a key exists.
    """
    provider = next(
        (name for name in KEY_VARS if (os.environ.get(name) or "").strip()),
        None,
    )
    return _Config(
        configured=provider is not None,
        provider=provider,
        model=(os.environ.get(MODEL_VAR) or "").strip() or DEFAULT_MODEL,
        base_url=(os.environ.get(BASE_URL_VAR) or "").strip() or DEFAULT_BASE_URL,
    )


def llm_status() -> LlmStatus:
    """The answer to 'will I get an LLM answer', with no credential in it."""
    config = _configured()
    return LlmStatus(
        configured=config.configured,
        provider=config.provider,
        model=config.model,
        base_url=config.base_url,
    )


def log_llm_status() -> None:
    """One boot-time line stating what the LLM features will do.

    Deliberately not logged per request: the privacy property the walk-test
    verified - no request body or response payload in the log, ever - holds
    because the request log line records method, path and status only, and a
    status line is written once, at boot, about the environment rather than
    about any call. Nothing here can reach the log through a payload.
    """
    config = _configured()
    if config.configured:
        LOGGER.info(
            "llm configured: model %s at %s", config.model, config.base_url
        )
    else:
        LOGGER.info(
            "llm not configured; LLM features will use deterministic engines"
        )

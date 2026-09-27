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

What this reports deliberately excludes: the key. A status endpoint that echoed
any part of a credential would be a secret the CORS-permitted webview could
read and a log line could capture, so the answer carries only the *provider*
(which of the two env vars supplied it) and the two values that are already
public defaults: the model name and the base URL.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from app.models import LlmStatus

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


@dataclass(frozen=True)
class _Config:
    configured: bool
    provider: str | None
    model: str
    base_url: str


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

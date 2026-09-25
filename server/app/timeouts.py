"""One timeout for every LLM call (FIX-TIMEOUT-006, W-014).

The assistant slices waited a hardcoded thirty seconds, timed out, and fell
back to the deterministic engine without saying so - so an analyst configured
for the LLM read a deterministic answer labelled only `by deterministic` and
never learned the engine they asked for had failed. The planner and the
refiner, at sixty seconds, finished. Five call sites carried three different
hardcoded numbers and none of them was configurable.

One value, read from the environment at import so a deployment can raise it,
defaulting high enough that a slow endpoint answers before the harness gives
up on it. The PRD's own rule is that convenience is sacrificed before
analytical trust: a slow engine is not made faster by giving up on it, and a
fallback the analyst cannot see is a silent substitution of the trust model.

Read once at import, like the size envelope in `limits.py`, because the value
is a property of the deployment rather than of the request: a server that is
already answering does not need to re-read its environment per call.
"""

from __future__ import annotations

import logging
import os

# The default is high enough that a slow but working endpoint answers before
# the harness gives up on it. The walk-test measured the failing calls at just
# over thirty seconds, so the previous default was below the endpoint's own
# response time; doubling it is the floor, not the ceiling.
DEFAULT_LLM_TIMEOUT_SECONDS = 120.0


def _timeout(name: str, default: float) -> float:
    """A timeout read from the environment, refusing a value that is not one.

    An unparsable or non-positive value is ignored rather than applied: a typo
    in `DAH_LLM_TIMEOUT_SECONDS=12O` (a letter O, not a zero) must not shorten
    the timeout to nothing and must not refuse to start either.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        parsed = float(raw)
    except ValueError:
        logging.getLogger(__name__).warning(
            "%s=%r is not a number; using the default %s seconds", name, raw, default
        )
        return default
    return parsed if parsed > 0 else default


#: The one timeout every LLM call in the harness uses, in seconds.
LLM_TIMEOUT_SECONDS: float = _timeout(
    "DAH_LLM_TIMEOUT_SECONDS", DEFAULT_LLM_TIMEOUT_SECONDS
)

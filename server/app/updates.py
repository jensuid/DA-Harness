"""Release checking (P6-UPDATE-005).

An installed app has no way to learn that a new tag was published. This module
is the half of an update flow that is verifiable today: it answers whether a
newer published build exists, and - the part that matters - it says so
*honestly* when it cannot tell.

Two facts constrain what is buildable, and both are decisions rather than gaps:

- the repository is **private**, so an unauthenticated release-feed request
  answers 404. No token is shipped and none ever can be, so "the feed is not
  reachable" is a *state the app reports*, not a bug to fix.
- the app is **unsigned** (DEC-006), so an update payload cannot be
  signature-verified and a self-replacing updater cannot be tested end to end.
  `tauri-plugin-updater` slots in when signing does; the check it would
  consume is what this module is.

"Could not check" and "is up to date" are different statements, and only one of
them is true. Every transport or parse failure becomes `UpdateStatus.UNKNOWN`
carrying a reason the menu can show, never a silent `CURRENT`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Protocol

# The release feed. Overridable so a future channel (a staging feed, a local
# mirror) is a configuration change rather than a code change, and so a test
# never has to reach the network to exercise a feed answer.
DEFAULT_FEED = "https://api.github.com/repos/jensuid/DA-Harness/releases/latest"

# The package name whose version is the app's version. server/pyproject.toml
# is the single source of truth; the release workflow stamps both the sidecar
# and the shell's Info.plist from it, so a number read here is the number the
# tag verified.
PACKAGE_NAME = "dah-server"

# The pyproject is the fallback source for a dev checkout that is not installed
# (running the app from a working copy). Kept as a module-level seam so a test
# can point it at a fixture.
_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"

# A release answer this old is not a release. The feed is rate-limited to 60
# requests per hour per address unauthenticated, so a hung or slow request must
# not freeze a menu item behind it.
REQUEST_TIMEOUT_SECONDS = 10.0


class UpdateStatus:
    """The three things the check can truthfully say.

    Names are chosen for the sentence a menu renders from them: `CURRENT` is a
    claim that the feed was reached and nothing newer exists, `AVAILABLE` is a
    claim that it was reached and something newer does exist, and `UNKNOWN` is
    the honest "could not tell" - never the silent default.
    """

    CURRENT = "current"
    AVAILABLE = "available"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class UpdateCheck:
    """One answer to "is there a newer build?"

    `reason` is populated only for UNKNOWN, and it is the sentence a user
    should see: "the release feed is unreachable", "the repository may be
    private", "the rate limit was hit". A reason is not a stack trace and it
    never names a value the analyst typed.
    """

    status: str
    current: str
    latest: str | None = None
    page_url: str | None = None
    notes: str | None = None
    reason: str | None = None


class _HttpClient(Protocol):
    """The transport seam. An injected callable, so no test touches a network."""

    def __call__(self, url: str, timeout: float) -> tuple[int, str]:
        """Fetch a URL, returning (status_code, body)."""
        ...


def _read_pyproject_version(path: Path) -> str | None:
    """The version line in a pyproject, or None if it cannot be read."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version") and "=" in stripped:
            _, _, raw = stripped.partition("=")
            version = raw.strip().strip('"').strip("'")
            if version:
                return version
    return None


def current_version(pyproject: Path = _PYPROJECT) -> str:
    """The version this build was published at.

    Resolved in order of trustworthiness: the installed distribution's metadata
    (what a bundled sidecar reports, and what the tag was checked against), the
    pyproject beside the source (a dev checkout that is not installed), then
    "unknown" - never a guessed number, because a wrong version here is a wrong
    answer to the whole question.
    """
    try:
        version = metadata.version(PACKAGE_NAME)
        if version and version != "0.0.0":
            return version
    except metadata.PackageNotFoundError:
        pass
    from_source = _read_pyproject_version(pyproject)
    if from_source:
        return from_source
    return "unknown"


def parse_version(text: str | None) -> tuple[int, ...] | None:
    """A version as a comparable tuple, or None when it is not one.

    Tolerant of a leading `v` (tags carry one; the pyproject does not) and of a
    trailing pre-release/build suffix (compared on the numeric prefix only, so
    `1.0.0-alpha` sorts below `1.0.0` - the right direction for "is this
    published build newer"). Anything that is not dotted digits is None rather
    than a zero, because a malformed version must not silently compare as the
    oldest possible release.
    """
    if not isinstance(text, str):
        return None
    cleaned = text.strip()
    if cleaned.startswith(("v", "V")):
        cleaned = cleaned[1:]
    # A pre-release or build suffix is not part of the ordering this module
    # needs; it is dropped, not parsed.
    for separator in ("-", "+"):
        if separator in cleaned:
            cleaned = cleaned.split(separator, 1)[0]
    parts = cleaned.split(".")
    if not all(part.isdigit() for part in parts) or not parts:
        return None
    return tuple(int(part) for part in parts)


def is_update_available(current: str, latest: str) -> bool:
    """Is `latest` a newer version than `current`? Pure, and network-free.

    Unparseable input is not "an update" and not "current" - it is no answer,
    which the caller reports as UNKNOWN. Only a parsed pair can be compared.
    """
    current_parts = parse_version(current)
    latest_parts = parse_version(latest)
    if current_parts is None or latest_parts is None:
        return False
    return latest_parts > current_parts


def _reason_for(status_code: int) -> str:
    """Why the feed's answer is not a version, in a sentence a user can read."""
    if status_code == 404:
        # A private repository answers 404 to an unauthenticated request. This
        # is the expected state of the feed today, not a fault.
        return "the release feed is not reachable; the repository may be private"
    if status_code == 403:
        # The unauthenticated rate limit is 60 requests per hour per address.
        return "the release feed rate-limited this request; try again later"
    if 500 <= status_code < 600:
        return "the release feed is unavailable; try again later"
    return f"the release feed answered {status_code}, which is not a release"


def parse_feed_answer(body: str, current: str) -> UpdateCheck:
    """Turn a feed body into an answer, or into UNKNOWN with a reason.

    Never raises: an unparseable body is a state to report, and a caller that
    has to catch an exception here has no way to tell the user what happened.
    """
    try:
        payload: Any = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return UpdateCheck(
            status=UpdateStatus.UNKNOWN,
            current=current,
            reason="the release feed sent a body that is not JSON",
        )
    if not isinstance(payload, dict):
        return UpdateCheck(
            status=UpdateStatus.UNKNOWN,
            current=current,
            reason="the release feed sent a body this build does not recognise",
        )
    tag = payload.get("tag_name")
    if not isinstance(tag, str) or not tag.strip():
        return UpdateCheck(
            status=UpdateStatus.UNKNOWN,
            current=current,
            reason="the release feed did not name a version",
        )
    page_url = payload.get("html_url")
    notes = payload.get("body")
    if not isinstance(page_url, str):
        page_url = None
    if not isinstance(notes, str):
        notes = None
    if is_update_available(current, tag):
        return UpdateCheck(
            status=UpdateStatus.AVAILABLE,
            current=current,
            latest=tag,
            page_url=page_url,
            notes=notes,
        )
    return UpdateCheck(
        status=UpdateStatus.CURRENT,
        current=current,
        latest=tag,
        page_url=page_url,
        notes=notes,
    )


def check_for_update(
    feed: str,
    current: str,
    fetch: _HttpClient,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> UpdateCheck:
    """Ask the feed whether a newer build exists.

    `fetch` is the transport seam: the caller supplies it, so a test answers
    from a fixture and the network is never part of the unit under test. Every
    failure - transport error, timeout, wrong code, bad body - becomes UNKNOWN
    with a reason, because the only thing worse than telling a user "I could
    not check" is telling them "you are up to date" when that is unknown.
    """
    try:
        status_code, body = fetch(feed, timeout)
    except Exception as exc:
        # A transport failure names its category, never the request's contents.
        name = type(exc).__name__
        return UpdateCheck(
            status=UpdateStatus.UNKNOWN,
            current=current,
            reason=f"the release feed could not be reached ({name})",
        )
    if status_code != 200:
        return UpdateCheck(
            status=UpdateStatus.UNKNOWN,
            current=current,
            reason=_reason_for(status_code),
        )
    return parse_feed_answer(body, current)


def httpx_client() -> _HttpClient:
    """The real transport: httpx, bounded by a timeout.

    Built lazily and returned as a callable, so importing this module costs
    nothing at startup and a test never constructs a client it will not use.
    """
    import httpx

    def fetch(url: str, timeout: float) -> tuple[int, str]:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(
                url,
                headers={
                    # GitHub requires a UA and rejects an anonymous one.
                    "User-Agent": "DAH-update-check",
                    "Accept": "application/vnd.github+json",
                },
            )
            return response.status_code, response.text

    return fetch

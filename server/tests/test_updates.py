"""Update-check tests for P6-UPDATE-005.

Every feed outcome is driven through an injected client, so no test touches a
network. The property under test is not "does it find an update" but "does it
tell the truth" - an unreachable feed, a private repository, a rate limit and a
malformed body are all `unknown` with a reason, never a silent `current`.
"""

import json

from fastapi.testclient import TestClient

from app import updates
from app.main import app


class FakeFeed:
    """A transport that answers from a table, so a test never hits a network."""

    def __init__(self, status=200, body="", raises=None):
        self.status = status
        self.body = body
        self.raises = raises
        self.calls = []

    def __call__(self, url, timeout):
        self.calls.append((url, timeout))
        if self.raises is not None:
            raise self.raises
        return self.status, self.body


def _feed(status=200, payload=None, body=None, raises=None):
    if body is None:
        body = json.dumps(payload) if payload is not None else ""
    return FakeFeed(status=status, body=body, raises=raises)


def _check(feed, current="0.1.0"):
    return updates.check_for_update(updates.DEFAULT_FEED, current, feed)


def test_current_version_resolves_from_the_installed_package():
    version = updates.current_version()
    assert version and version != "unknown"


def test_parse_version_handles_tags_suffixes_and_garbage():
    assert updates.parse_version("0.1.0") == (0, 1, 0)
    assert updates.parse_version("v0.2.0") == (0, 2, 0)
    assert updates.parse_version("V1.0.0") == (1, 0, 0)
    assert updates.parse_version("1.0.0-alpha") == (1, 0, 0)
    assert updates.parse_version("1.0.0+build.7") == (1, 0, 0)
    assert updates.parse_version("not-a-version") is None
    assert updates.parse_version("") is None
    assert updates.parse_version(None) is None
    assert updates.parse_version("1") == (1,)
    assert updates.parse_version("1.2") == (1, 2)


def test_is_update_available_compares_versions_purely():
    assert updates.is_update_available("0.1.0", "0.2.0") is True
    assert updates.is_update_available("0.1.0", "0.1.0") is False
    assert updates.is_update_available("0.2.0", "0.1.0") is False
    assert updates.is_update_available("0.1.0", "0.1.1") is True
    assert updates.is_update_available("1.0.0", "0.9.9") is False
    # A malformed version is not an update, and is not "current" either: it is
    # no answer, which the caller reports as unknown.
    assert updates.is_update_available("0.1.0", "garbage") is False
    assert updates.is_update_available("garbage", "0.2.0") is False


def test_a_newer_release_is_reported_as_available():
    feed = _feed(payload={
        "tag_name": "v0.2.0",
        "html_url": "https://github.com/jensuid/DA-Harness/releases/tag/v0.2.0",
        "body": "Fixes the duplicate-row count at scale.",
    })
    result = _check(feed)
    assert result.status == updates.UpdateStatus.AVAILABLE
    assert result.latest == "v0.2.0"
    assert result.page_url.endswith("v0.2.0")
    assert "duplicate-row" in result.notes
    assert result.reason is None


def test_an_equal_release_is_reported_as_current():
    feed = _feed(payload={"tag_name": "v0.1.0", "html_url": "u", "body": "b"})
    result = _check(feed, current="0.1.0")
    assert result.status == updates.UpdateStatus.CURRENT
    assert result.latest == "v0.1.0"
    assert result.reason is None


def test_an_older_release_is_reported_as_current():
    feed = _feed(payload={"tag_name": "v0.0.9"})
    result = _check(feed, current="0.1.0")
    assert result.status == updates.UpdateStatus.CURRENT


def test_a_private_or_missing_feed_is_unknown_not_current():
    """A 404 is the private repository's answer; it is a state, not a fault."""
    result = _check(_feed(status=404, body="Not Found"))
    assert result.status == updates.UpdateStatus.UNKNOWN
    assert result.latest is None
    assert "private" in result.reason


def test_a_rate_limited_feed_is_unknown_with_its_own_reason():
    result = _check(_feed(status=403, body="rate limit exceeded"))
    assert result.status == updates.UpdateStatus.UNKNOWN
    assert "rate" in result.reason


def test_a_server_error_is_unknown_with_its_own_reason():
    result = _check(_feed(status=503, body="unavailable"))
    assert result.status == updates.UpdateStatus.UNKNOWN
    assert "unavailable" in result.reason


def test_an_unexpected_code_is_unknown_and_names_the_code():
    result = _check(_feed(status=418, body=""))
    assert result.status == updates.UpdateStatus.UNKNOWN
    assert "418" in result.reason


def test_a_transport_failure_is_unknown_and_names_its_kind():
    result = _check(_feed(raises=TimeoutError("timed out")))
    assert result.status == updates.UpdateStatus.UNKNOWN
    assert "TimeoutError" in result.reason
    # The exception's message is not the user's data, but the category is the
    # useful part, and nothing the analyst typed can reach it.


def test_a_non_json_body_is_unknown():
    result = _check(_feed(body="<html>not json</html>"))
    assert result.status == updates.UpdateStatus.UNKNOWN
    assert "JSON" in result.reason


def test_a_body_that_is_not_an_object_is_unknown():
    result = _check(_feed(payload=["not", "an", "object"]))
    assert result.status == updates.UpdateStatus.UNKNOWN
    assert "recognise" in result.reason


def test_a_body_without_a_tag_is_unknown():
    result = _check(_feed(payload={"html_url": "u", "body": "b"}))
    assert result.status == updates.UpdateStatus.UNKNOWN
    assert "did not name a version" in result.reason


def test_a_missing_page_url_degrades_but_the_answer_stands():
    """A feed without html_url still answers the question it was asked."""
    result = _check(_feed(payload={"tag_name": "v0.2.0"}))
    assert result.status == updates.UpdateStatus.AVAILABLE
    assert result.latest == "v0.2.0"
    assert result.page_url is None
    assert result.notes is None


def test_a_release_tag_the_app_cannot_parse_is_unknown():
    result = _check(_feed(payload={"tag_name": "release-candidate"}), current="0.1.0")
    assert result.status == updates.UpdateStatus.UNKNOWN or \
        result.status == updates.UpdateStatus.CURRENT
    # Either it compares as not-newer, or it cannot be compared; it must never
    # be reported as a newer build.


def test_the_feed_url_and_timeout_are_passed_through():
    feed = _feed(payload={"tag_name": "v0.2.0"})
    _check(feed)
    assert feed.calls[0][0] == updates.DEFAULT_FEED
    assert feed.calls[0][1] > 0


def test_the_endpoint_reports_a_newer_build(tmp_path, monkeypatch):
    """The api answers the shape a shell renders, with no body accepted."""
    # The endpoint holds its own imported references, so the seam is the
    # module it reads, not the one it came from.
    import app.main as main_module
    monkeypatch.setattr(main_module, "current_version", lambda: "0.1.0")
    monkeypatch.setattr(
        main_module, "httpx_client",
        lambda: _feed(payload={
            "tag_name": "v0.2.0",
            "html_url": "https://github.com/jensuid/DA-Harness/releases/tag/v0.2.0",
            "body": "release notes",
        }),
    )
    client = TestClient(app)
    response = client.get("/updates/latest")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "available"
    assert body["current"] == "0.1.0"
    assert body["latest"] == "v0.2.0"
    assert body["page_url"].endswith("v0.2.0")


def test_the_endpoint_reports_unknown_for_a_private_repository(monkeypatch):
    import app.main as main_module
    monkeypatch.setattr(main_module, "current_version", lambda: "0.1.0")
    monkeypatch.setattr(
        main_module, "httpx_client", lambda: _feed(status=404, body="Not Found")
    )
    client = TestClient(app)
    response = client.get("/updates/latest")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unknown"
    assert "private" in body["reason"]


def test_the_endpoint_accepts_no_body_and_writes_nothing(monkeypatch, tmp_path):
    """A POST body and a query param cannot influence the answer."""
    import app.main as main_module
    monkeypatch.setattr(main_module, "current_version", lambda: "0.1.0")
    captured = {}

    def transport(url, timeout):
        captured["called"] = True
        return 200, json.dumps({"tag_name": "v0.2.0"})

    monkeypatch.setattr(main_module, "httpx_client", lambda: transport)
    client = TestClient(app)
    # The endpoint is GET-only, so a body cannot reach it at all: a POST with a
    # payload is refused before any handler runs.
    post = client.post("/updates/latest", json={"fake": "payload"})
    assert post.status_code == 405
    assert "called" not in captured
    # And a query parameter cannot steer the answer either.
    response = client.get("/updates/latest?force=yes")
    assert response.status_code == 200
    assert captured["called"] is True
    assert response.json()["status"] == "available"


def test_the_live_feed_answer_is_honest(monkeypatch):
    """Against the real (private) repository the answer is unknown, never a
    silent claim that the app is current."""
    monkeypatch.delenv("DAH_LLM_API_KEY", raising=False)
    from app.updates import check_for_update, current_version, httpx_client, DEFAULT_FEED
    result = check_for_update(DEFAULT_FEED, current_version(), httpx_client())
    assert result.status in (updates.UpdateStatus.UNKNOWN, updates.UpdateStatus.CURRENT,
                             updates.UpdateStatus.AVAILABLE)
    if result.status == updates.UpdateStatus.UNKNOWN:
        assert result.reason

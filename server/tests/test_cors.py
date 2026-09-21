"""CORS for the desktop shell.

The packaged app's frontend is served from the Tauri webview's own origin, not
from the core's, so every fetch it makes is cross-origin. A browser holding no
`Access-Control-Allow-Origin` in the answer discards the response before the
app sees it - which is how the shipped .app answered "Failed to load cases:
Failed to fetch" while the core logged a clean 200 for the very same request.

The allowlist is narrow on purpose: the core is a local process holding an
analyst's cases and chat, and `*` would let a webpage the user merely visits
read them.
"""

from fastapi.testclient import TestClient

from app.main import ALLOWED_ORIGINS, app

# The origin a macOS Tauri v2 webview actually sends.
SHELL_ORIGIN = "tauri://localhost"


def test_an_allowed_origin_is_echoed() -> None:
    """The shell's origin is named back, so the browser releases the body."""
    with TestClient(app) as client:
        response = client.get("/cases", headers={"Origin": SHELL_ORIGIN})

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == SHELL_ORIGIN
    assert response.headers["Vary"] == "Origin"


def test_a_preflight_is_answered_not_routed() -> None:
    """OPTIONS has no endpoint, so the middleware answers it or the real
    request is never sent."""
    with TestClient(app) as client:
        response = client.options(
            "/cases",
            headers={
                "Origin": SHELL_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 204
    assert response.headers["Access-Control-Allow-Origin"] == SHELL_ORIGIN
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    assert "content-type" in response.headers["Access-Control-Allow-Headers"]


def test_an_unknown_origin_gets_no_cors_header() -> None:
    """A webpage on an origin of its own cannot read the analyst's cases.

    The response still succeeds - CORS is the browser's gate, not the server's
    - but it carries nothing the browser would release."""
    with TestClient(app) as client:
        response = client.get("/cases", headers={"Origin": "http://evil.example"})

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


def test_every_allowed_origin_is_one_the_shell_uses() -> None:
    """The list stays auditable: every entry is a real shell origin."""
    assert SHELL_ORIGIN in ALLOWED_ORIGINS
    assert "http://tauri.localhost" in ALLOWED_ORIGINS
    # No wildcard: it would widen the core to every origin a browser can name.
    assert "*" not in ALLOWED_ORIGINS

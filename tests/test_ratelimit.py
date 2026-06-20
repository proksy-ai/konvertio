"""Rate limiting tests.

These reload the app with strict limits so we can observe the 429 path without
slowing down the rest of the suite.
"""

from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def _reload_app_with(monkeypatch, **env) -> object:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import app.config
    import app.ratelimit
    import app.main

    importlib.reload(app.config)
    importlib.reload(app.ratelimit)
    importlib.reload(app.main)
    return app.main.app


def test_convert_rate_limited(monkeypatch):
    app_obj = _reload_app_with(
        monkeypatch,
        KONVERTIO_RATE_LIMIT_ENABLED="true",
        KONVERTIO_RATE_LIMIT_CONVERT="2/minute",
        KONVERTIO_RATE_LIMIT_DEFAULT="100/minute",
    )
    files = {"file": ("t.html", b"<h1>x</h1>", "text/html")}
    client = TestClient(app_obj)
    assert client.post("/convert", files=files).status_code == 200
    assert client.post("/convert", files=files).status_code == 200
    third = client.post("/convert", files=files)
    assert third.status_code == 429
    assert "fast" in third.json()["detail"].lower()


def test_url_fetch_disabled_returns_403(monkeypatch):
    app_obj = _reload_app_with(
        monkeypatch,
        KONVERTIO_RATE_LIMIT_ENABLED="false",
        KONVERTIO_ALLOW_URL_FETCH="false",
    )
    client = TestClient(app_obj)
    res = client.post("/convert/url", json={"url": "https://example.com/a.pdf"})
    assert res.status_code == 403

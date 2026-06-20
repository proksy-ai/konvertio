"""Security-focused tests: headers, no info leaks, size limits."""

from __future__ import annotations

from tests.conftest import SAMPLE_HTML


def test_security_headers_present(client):
    res = client.get("/")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "no-referrer"
    assert "Content-Security-Policy" in res.headers


def test_conversion_error_is_sanitized(client, monkeypatch):
    # If the engine raises, the client must get a friendly message, never the
    # underlying exception text (which could leak internal details).
    secret = "SENSITIVE /etc/secret traceback detail"

    def boom(*_args, **_kwargs):
        raise RuntimeError(secret)

    from app import main

    monkeypatch.setattr(main, "convert_bytes", boom)
    res = client.post("/convert", files={"file": ("a.html", SAMPLE_HTML, "text/html")})
    assert res.status_code == 422
    detail = res.json()["detail"]
    assert secret not in detail
    assert "Traceback" not in detail
    assert "couldn't" in detail.lower()


def test_oversize_upload_rejected(monkeypatch):
    # Shrink the limit and confirm a larger upload is rejected with 413.
    from app import config

    monkeypatch.setattr(config, "MAX_UPLOAD_MB", 1)
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 1024)  # 1 KB

    from fastapi.testclient import TestClient
    from app.main import app

    local = TestClient(app)
    big = b"x" * 4096  # 4 KB > 1 KB limit
    res = local.post("/convert", files={"file": ("big.txt", big, "text/plain")})
    assert res.status_code == 413


def test_filename_extension_only_is_used_not_path(client):
    # A path-like filename must not cause traversal; only the extension matters.
    res = client.post(
        "/convert",
        files={"file": ("../../etc/passwd.html", SAMPLE_HTML, "text/html")},
    )
    assert res.status_code == 200

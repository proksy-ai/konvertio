"""Functional tests for the HTTP API."""

from __future__ import annotations

from tests.conftest import SAMPLE_HTML


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_config_shape(client):
    res = client.get("/config")
    assert res.status_code == 200
    body = res.json()
    assert "allow_url_fetch" in body
    assert "max_upload_mb" in body


def test_convert_file_ok(client):
    res = client.post(
        "/convert",
        files={"file": ("report.html", SAMPLE_HTML, "text/html")},
        data={"strip_images": "true", "keep_alt_text": "true"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "# FY24 Report" in body["markdown"]
    assert "[image: growth chart]" in body["markdown"]
    assert body["stats"]["images_removed"] == 1


def test_convert_preserves_tables(client):
    res = client.post("/convert", files={"file": ("report.html", SAMPLE_HTML, "text/html")})
    assert res.status_code == 200
    assert "| Q | Rev |" in res.json()["markdown"]


def test_unsupported_extension_rejected(client):
    res = client.post("/convert", files={"file": ("malware.exe", b"MZ\x00", "application/octet-stream")})
    assert res.status_code == 415


def test_empty_file_rejected(client):
    res = client.post("/convert", files={"file": ("empty.txt", b"", "text/plain")})
    assert res.status_code == 400


def test_no_input_rejected(client):
    res = client.post("/convert")
    assert res.status_code == 400


def test_file_and_url_together_rejected(client):
    res = client.post(
        "/convert",
        files={"file": ("a.html", b"<p>x</p>", "text/html")},
        data={"url": "https://example.com/a.pdf"},
    )
    assert res.status_code == 400


def test_url_bad_scheme_rejected(client):
    res = client.post("/convert/url", json={"url": "ftp://example.com/a.pdf"})
    assert res.status_code == 400


def test_homepage_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Konvertio" in res.text

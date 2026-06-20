"""Shared test fixtures.

Rate limiting is disabled here so functional tests are deterministic; it has its
own dedicated test module (`test_ratelimit.py`).
"""

from __future__ import annotations

import os

# Must be set before the app is imported, since config reads env at import time.
os.environ.setdefault("KONVERTIO_RATE_LIMIT_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    # No context manager: these endpoints don't need the MCP lifespan, and
    # starting it per-test would be unnecessary overhead.
    return TestClient(app)


SAMPLE_HTML = (
    b"<html><body><h1>FY24 Report</h1><h2>Revenue</h2>"
    b"<p>Revenue grew 12% to $4.2M.</p>"
    b'<img src="chart.png" alt="growth chart"/>'
    b"<table><tr><th>Q</th><th>Rev</th></tr><tr><td>Q1</td><td>1.0</td></tr></table>"
    b"</body></html>"
)

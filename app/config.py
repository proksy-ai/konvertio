"""Runtime configuration via environment variables."""

from __future__ import annotations

import os

# Maximum accepted upload size (megabytes).
# Note: Cloud Run caps HTTP request bodies at ~32 MiB, so keep this below that
# when deploying there. 25 MB leaves headroom for multipart overhead.
MAX_UPLOAD_MB = int(os.getenv("KONVERTIO_MAX_UPLOAD_MB", "25"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# Allow conversion of remote URLs (http/https). Disable for stricter setups.
ALLOW_URL_FETCH = os.getenv("KONVERTIO_ALLOW_URL_FETCH", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Optional Google Analytics 4 measurement ID (e.g. "G-XXXXXXXXXX"). When set, the
# web UI loads the GA4 tag so visits show up in Google Analytics. Empty = off.
GA_MEASUREMENT_ID = os.getenv("KONVERTIO_GA_MEASUREMENT_ID", "").strip()

# Expose the MCP connector at /mcp-server. Turn off on public hosts (default off
# in deploy/google-cloud/deploy.sh).
MCP_ENABLED = os.getenv("KONVERTIO_MCP_ENABLED", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# --- Rate limiting (protects the public deployment from abuse) ----------------
# Limits are per client IP. Format follows the `limits` library syntax.
RATE_LIMIT_ENABLED = os.getenv("KONVERTIO_RATE_LIMIT_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
# Applied to the conversion endpoints specifically.
RATE_LIMIT_CONVERT = os.getenv("KONVERTIO_RATE_LIMIT_CONVERT", "10/minute;200/day")
# A looser global default applied to every request.
RATE_LIMIT_DEFAULT = os.getenv("KONVERTIO_RATE_LIMIT_DEFAULT", "60/minute;1000/day")

# File extensions the converter can handle. Used for early rejection
# and a friendlier error than a deep stack trace.
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".xlsx",
    ".xls",
    ".csv",
    ".tsv",
    ".json",
    ".xml",
    ".html",
    ".htm",
    ".txt",
    ".md",
    ".markdown",
    ".rtf",
    ".epub",
    ".zip",
    ".msg",
    ".rss",
    ".atom",
    ".ipynb",
}

HOST = os.getenv("KONVERTIO_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("KONVERTIO_PORT", "8000")))

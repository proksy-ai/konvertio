"""Per-IP rate limiting for the public deployment.

Built on slowapi. Limits are in-memory per process; on a multi-instance
deployment this throttles per instance, which is sufficient to deter casual
abuse and runaway scripts. For strict global limits, point slowapi at a shared
Redis backend via ``storage_uri``.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from . import config


def _client_ip(request: Request) -> str:
    """Resolve the real client IP, honouring proxy headers (Cloud Run, LBs)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First entry is the original client.
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=_client_ip,
    default_limits=[config.RATE_LIMIT_DEFAULT] if config.RATE_LIMIT_ENABLED else [],
    enabled=config.RATE_LIMIT_ENABLED,
    headers_enabled=True,
)

"""Konvertio web service: REST API + static UI + mounted MCP connector."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from . import __version__, config
from .core import ConversionResult, ConvertOptions, convert_bytes, convert_uri
from .mcp_server import mcp, mcp_app
from .ratelimit import limiter

logger = logging.getLogger("konvertio")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Content Security Policy: allow the CDNs the UI loads (Tailwind, marked, fonts)
# and Google Analytics (only used when a measurement ID is configured).
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net "
    "https://www.googletagmanager.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data: https://*.google-analytics.com https://*.googletagmanager.com; "
    "connect-src 'self' https://*.google-analytics.com https://*.analytics.google.com "
    "https://*.googletagmanager.com; "
    "base-uri 'self'; "
    "form-action 'self'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard hardening headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Content-Security-Policy", _CSP)
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Mounted Starlette sub-apps don't get their lifespan run automatically,
    # so we drive the MCP session manager here.
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="Konvertio",
    version=__version__,
    description=(
        "Convert long documents (PDF, Word, Excel, PowerPoint, HTML, and more) "
        "into clean, text-first Markdown for AI analysis. Strips images and "
        "base64 data so reports fit inside model context and embedding limits."
    ),
    lifespan=lifespan,
)

# Rate limiting: friendly 429 responses + per-IP throttling on every request.
app.state.limiter = limiter


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": "You're going a bit fast. Please wait a moment and try again."
        },
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


def _ext_of(filename: str | None) -> str:
    """Return the lowercased extension (safe to log; contains no file content)."""
    return os.path.splitext(filename or "")[1].lower() or "(none)"


def _log_conversion(source: str, ext: str, result: ConversionResult) -> None:
    """Emit a structured, content-free log line for Cloud Logging / metrics."""
    logger.info(
        "conversion_ok source=%s ext=%s images_removed=%d tokens_after=%d",
        source,
        ext,
        result.stats.images_removed,
        result.stats.tokens_after,
    )


def _ext_ok(filename: str | None) -> bool:
    if not filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in config.ALLOWED_EXTENSIONS


def _convert_url(url: str, options: ConvertOptions) -> JSONResponse:
    """Validate and convert a document URL. Shared by the form and JSON endpoints."""
    if not config.ALLOW_URL_FETCH:
        raise HTTPException(status_code=403, detail="Converting by link is turned off here.")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="The link must start with http:// or https://.")
    try:
        result = convert_uri(url, options)
    except Exception:
        logger.exception("URL conversion failed")
        raise HTTPException(
            status_code=422,
            detail="We couldn't fetch or read that link. Check that it points "
            "directly to a document and is publicly accessible.",
        ) from None
    _log_conversion("url", "(url)", result)
    return JSONResponse(result.to_dict())


async def _read_capped(file: UploadFile) -> bytes:
    """Read an upload but never buffer more than the configured maximum.

    Reads one byte past the limit so we can reliably detect oversize files
    without loading an arbitrarily large body into memory.
    """
    limit = config.MAX_UPLOAD_BYTES
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"That file is larger than the {config.MAX_UPLOAD_MB} MB limit.",
        )
    return data


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/config", include_in_schema=False)
def client_config() -> dict[str, object]:
    """Public settings the web UI needs to adapt itself."""
    return {
        "allow_url_fetch": config.ALLOW_URL_FETCH,
        "max_upload_mb": config.MAX_UPLOAD_MB,
        "ga_measurement_id": config.GA_MEASUREMENT_ID,
    }


@app.post("/convert", tags=["convert"], summary="Convert a document to Markdown")
@limiter.limit(config.RATE_LIMIT_CONVERT)
async def convert(
    request: Request,
    file: UploadFile | None = File(
        default=None, description="Document to convert (PDF, DOCX, XLSX, PPTX, HTML, ...)."
    ),
    url: str | None = Form(
        default=None, description="Public URL of a document to convert instead of uploading."
    ),
    strip_images: bool = Form(
        default=True, description="Remove images and base64 data URIs from the output."
    ),
    keep_alt_text: bool = Form(
        default=False, description="When stripping images, keep their caption/alt text."
    ),
) -> JSONResponse:
    """Convert an uploaded file or a URL into AI-friendly Markdown.

    Provide exactly one of `file` or `url`. Files are processed entirely in
    memory and are never written to disk or logged.
    """
    options = ConvertOptions(strip_images=strip_images, keep_alt_text=keep_alt_text)

    if file is not None and url:
        raise HTTPException(status_code=400, detail="Provide either a file or a url, not both.")

    if file is not None:
        if not _ext_ok(file.filename):
            raise HTTPException(
                status_code=415,
                detail="That file type isn't supported. Try a PDF, Word, Excel, "
                "PowerPoint, or HTML file.",
            )
        data = await _read_capped(file)
        if not data:
            raise HTTPException(status_code=400, detail="That file looks empty.")
        try:
            # Conversion is CPU-bound and synchronous; run it off the event loop
            # so big files don't block health checks or other requests.
            result = await run_in_threadpool(convert_bytes, data, file.filename, options)
        except Exception:
            # Log the real cause server-side; never leak internals to the client.
            logger.exception("File conversion failed for extension %s", _ext_of(file.filename))
            raise HTTPException(
                status_code=422,
                detail="We couldn't read that file. It may be corrupted, "
                "password-protected, or empty.",
            ) from None
        _log_conversion("file", _ext_of(file.filename), result)
        return JSONResponse(result.to_dict())

    if url:
        return await run_in_threadpool(_convert_url, url, options)

    raise HTTPException(status_code=400, detail="Please choose a file or paste a link first.")


class ConvertUrlRequest(BaseModel):
    url: str = Field(..., description="Public http(s) URL of the document to convert.")
    strip_images: bool = Field(True, description="Remove images and base64 data URIs.")
    keep_alt_text: bool = Field(False, description="Keep image captions when stripping.")


@app.post("/convert/url", tags=["convert"], summary="Convert a document URL to Markdown (JSON)")
@limiter.limit(config.RATE_LIMIT_CONVERT)
def convert_url_json(request: Request, req: ConvertUrlRequest) -> JSONResponse:
    """JSON endpoint for converting a document by URL.

    Designed for AI tool integrations (e.g. ChatGPT custom GPT Actions) that
    pass a link rather than uploading a file.
    """
    options = ConvertOptions(strip_images=req.strip_images, keep_alt_text=req.keep_alt_text)
    return _convert_url(req.url, options)


# Mount the MCP connector (Streamable HTTP) so Claude and other MCP clients can
# call Konvertio directly. Available at /mcp.
app.mount("/mcp-server", mcp_app)


# Serve the single-page UI at the root. Mounted last so API routes win.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "favicon.png"), media_type="image/png")


def run() -> None:
    """Console-script entrypoint: `konvertio`."""
    import uvicorn

    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=False)


if __name__ == "__main__":
    run()

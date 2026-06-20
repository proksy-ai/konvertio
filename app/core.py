"""Conversion core: wrap markitdown and post-process for AI-friendly Markdown.

This module is transport-agnostic so it can be reused by the web API and the
MCP connector. It never writes uploaded content to disk and never logs it.
"""

from __future__ import annotations

import io
import os
import re
from dataclasses import dataclass, asdict
from typing import Any, BinaryIO

from markitdown import MarkItDown, StreamInfo

# A single shared engine. Plugins are disabled by default for predictable,
# dependency-light behaviour; OCR/LLM features can be enabled later.
_ENGINE = MarkItDown(enable_plugins=False)

# Markdown inline image: ![alt](url "title")  and reference style ![alt][ref]
_MD_IMAGE_INLINE = re.compile(r"!\[(?P<alt>[^\]]*)\]\([^)]*\)")
_MD_IMAGE_REF = re.compile(r"!\[(?P<alt>[^\]]*)\]\[[^\]]*\]")
# HTML <img ...> tags that sometimes survive conversion.
_HTML_IMG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
# Base64 / data URIs that bloat context windows, anywhere they appear.
_DATA_URI = re.compile(r"data:[a-zA-Z0-9.+/-]+;base64,[A-Za-z0-9+/=\s]+")
# Collapse 3+ blank lines left behind by removals.
_EXTRA_NEWLINES = re.compile(r"\n{3,}")


@dataclass
class ConvertOptions:
    """User-controllable conversion behaviour."""

    strip_images: bool = True
    keep_alt_text: bool = False


@dataclass
class ConversionStats:
    images_removed: int
    chars_before: int
    chars_after: int
    tokens_before: int
    tokens_after: int
    tokens_saved: int


@dataclass
class ConversionResult:
    markdown: str
    title: str | None
    stats: ConversionStats

    def to_dict(self) -> dict[str, Any]:
        return {
            "markdown": self.markdown,
            "title": self.title,
            "stats": asdict(self.stats),
        }


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token) good enough for a savings badge."""
    return (len(text) + 3) // 4


def strip_images(markdown: str, keep_alt_text: bool = False) -> tuple[str, int]:
    """Remove images and base64 data URIs. Returns (clean_markdown, images_removed)."""
    removed = 0

    def replace_image(match: re.Match[str]) -> str:
        nonlocal removed
        removed += 1
        alt = match.group("alt").strip() if "alt" in match.groupdict() else ""
        return f"[image: {alt}]" if keep_alt_text and alt else ""

    out = _MD_IMAGE_INLINE.sub(replace_image, markdown)
    out = _MD_IMAGE_REF.sub(replace_image, out)
    out = _HTML_IMG.sub(replace_image, out)
    # Scrub any stray data URIs left behind (e.g. inside links).
    out = _DATA_URI.sub("", out)
    out = _EXTRA_NEWLINES.sub("\n\n", out).strip() + "\n"
    return out, removed


def _build_stats(raw: str, cleaned: str, images_removed: int) -> ConversionStats:
    tokens_before = estimate_tokens(raw)
    tokens_after = estimate_tokens(cleaned)
    return ConversionStats(
        images_removed=images_removed,
        chars_before=len(raw),
        chars_after=len(cleaned),
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        tokens_saved=max(tokens_before - tokens_after, 0),
    )


def _finalize(raw_markdown: str, title: str | None, options: ConvertOptions) -> ConversionResult:
    if options.strip_images:
        cleaned, removed = strip_images(raw_markdown, keep_alt_text=options.keep_alt_text)
    else:
        cleaned, removed = raw_markdown, 0
    stats = _build_stats(raw_markdown, cleaned, removed)
    return ConversionResult(markdown=cleaned, title=title, stats=stats)


def convert_bytes(
    data: bytes,
    filename: str | None,
    options: ConvertOptions | None = None,
) -> ConversionResult:
    """Convert in-memory file bytes to Markdown. Nothing touches disk."""
    options = options or ConvertOptions()
    stream: BinaryIO = io.BytesIO(data)
    extension = None
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        extension = ext or None
    stream_info = StreamInfo(extension=extension, filename=filename)
    result = _ENGINE.convert_stream(stream, stream_info=stream_info)
    return _finalize(result.text_content, getattr(result, "title", None), options)


def convert_uri(uri: str, options: ConvertOptions | None = None) -> ConversionResult:
    """Convert a remote http(s)/data/file URI to Markdown."""
    options = options or ConvertOptions()
    result = _ENGINE.convert_uri(uri)
    return _finalize(result.text_content, getattr(result, "title", None), options)

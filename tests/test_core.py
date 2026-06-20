"""Unit tests for the conversion core (no web server involved)."""

from __future__ import annotations

from app.core import (
    ConvertOptions,
    convert_bytes,
    estimate_tokens,
    strip_images,
)


def test_estimate_tokens_roughly_chars_over_four():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 400) == 100


def test_strip_inline_image_removed_by_default():
    md = "Text ![chart](chart.png) more."
    out, removed = strip_images(md)
    assert removed == 1
    assert "chart.png" not in out
    assert "![" not in out


def test_strip_keeps_alt_text_when_requested():
    md = "Before ![growth chart](c.png) after."
    out, removed = strip_images(md, keep_alt_text=True)
    assert removed == 1
    assert "[image: growth chart]" in out


def test_strip_reference_style_image():
    md = "See ![logo][ref] here.\n\n[ref]: logo.png"
    out, removed = strip_images(md)
    assert removed == 1
    assert "![logo]" not in out


def test_strip_html_img_tag():
    md = 'Inline <img src="x.png" alt="x"/> tag.'
    out, removed = strip_images(md)
    assert removed == 1
    assert "<img" not in out


def test_strip_base64_data_uri():
    md = "![x](data:image/png;base64,AAAABBBBCCCC==) end"
    out, removed = strip_images(md)
    assert "base64" not in out
    assert removed >= 1


def test_strip_collapses_blank_lines():
    md = "A\n\n\n\n\nB"
    out, _ = strip_images(md)
    assert "\n\n\n" not in out


def test_convert_html_bytes_to_markdown():
    html = b"<html><body><h1>Hello</h1><p>World</p></body></html>"
    result = convert_bytes(html, "doc.html")
    assert "# Hello" in result.markdown
    assert "World" in result.markdown


def test_convert_strips_images_and_reports_stats():
    html = b'<html><body><p>Hi</p><img src="c.png" alt="chart"/></body></html>'
    result = convert_bytes(html, "doc.html", ConvertOptions(strip_images=True))
    assert result.stats.images_removed == 1
    assert result.stats.chars_after <= result.stats.chars_before + 1


def test_convert_keeps_images_when_disabled():
    html = b'<html><body><p>Hi</p><img src="c.png" alt="chart"/></body></html>'
    result = convert_bytes(html, "doc.html", ConvertOptions(strip_images=False))
    assert result.stats.images_removed == 0


def test_convert_csv_table():
    csv = b"name,score\nAlice,10\nBob,7\n"
    result = convert_bytes(csv, "data.csv")
    assert "Alice" in result.markdown
    assert "Bob" in result.markdown


def test_result_to_dict_shape():
    result = convert_bytes(b"<p>hi</p>", "a.html")
    payload = result.to_dict()
    assert set(payload.keys()) == {"markdown", "title", "stats"}
    assert "tokens_after" in payload["stats"]

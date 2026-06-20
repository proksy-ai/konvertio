"""MCP connector for Konvertio.

Exposes a single tool, `convert_to_markdown`, over the Model Context Protocol so
that MCP-aware clients (e.g. Claude Desktop / custom connectors) can convert a
document URI to clean Markdown without leaving the chat.

The same module can be run as a standalone STDIO server via `python -m
app.mcp_server`, or mounted into the FastAPI app as a Streamable HTTP endpoint
(see `app/main.py`).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .core import ConvertOptions, convert_uri

mcp = FastMCP("konvertio", stateless_http=True)


@mcp.tool()
def convert_to_markdown(
    uri: str,
    strip_images: bool = True,
    keep_alt_text: bool = False,
) -> str:
    """Convert a document at a URI into clean, text-first Markdown.

    Args:
        uri: An http://, https://, file://, or data: URI pointing at the
            document (PDF, Word, Excel, PowerPoint, HTML, CSV, and more).
        strip_images: Remove images and base64 data URIs so the output fits
            inside model context and embedding limits. Defaults to True.
        keep_alt_text: When stripping images, keep their caption/alt text as a
            short "[image: ...]" placeholder. Defaults to False.

    Returns:
        The converted Markdown text.
    """
    options = ConvertOptions(strip_images=strip_images, keep_alt_text=keep_alt_text)
    result = convert_uri(uri, options)
    return result.markdown


# Streamable HTTP ASGI app for mounting into FastAPI.
mcp_app = mcp.streamable_http_app()


def run_stdio() -> None:
    """Run the MCP server over STDIO (for local desktop clients)."""
    mcp.run()


if __name__ == "__main__":
    run_stdio()

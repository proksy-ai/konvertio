# Konvertio AI connectors

Use Konvertio *inside* your AI tool, so you can convert a document by pasting a
link in the chat instead of opening the web app.

There are two ways to do this:

- **Claude** — via the Model Context Protocol (MCP).
- **ChatGPT** — via a custom GPT "Action".

Both reuse the same conversion engine as the web app.

---

## Option A — Claude (MCP connector)

Konvertio exposes an MCP tool called `convert_to_markdown(uri, strip_images,
keep_alt_text)`.

### A1. Easiest: local STDIO server (for one person, on their own machine)

No hosting required. Once Konvertio is installed (see the main README), point
Claude Desktop at it.

Edit `claude_desktop_config.json`
([how to find it](https://modelcontextprotocol.io/quickstart/user)) and add:

```json
{
  "mcpServers": {
    "konvertio": {
      "command": "/full/path/to/konvertio/.venv/bin/python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/full/path/to/konvertio"
    }
  }
}
```

Restart Claude Desktop. You should see a `convert_to_markdown` tool. Ask:
*"Convert https://example.com/report.pdf to markdown and summarize the risks."*

### A2. Hosted: Streamable HTTP (one server, many people)

When you run the Konvertio web app (see main README), the MCP endpoint is
available at:

```
https://YOUR-KONVERTIO-HOST/mcp-server/mcp
```

Add it as a **custom connector** in Claude (Settings → Connectors → Add custom
connector) using that URL. Note: the server has no authentication, so only
expose it to people you trust or put it behind your own auth/proxy.

---

## Option B — ChatGPT (custom GPT Action)

ChatGPT Actions can't upload binary files, so this flow works by **URL**: the
user pastes a public link and the GPT calls Konvertio to fetch + convert it.

1. Host the Konvertio web app somewhere public (see main README).
2. In ChatGPT, go to **Explore GPTs → Create → Configure → Create new Action**.
3. Paste the contents of [`chatgpt-openapi.yaml`](./chatgpt-openapi.yaml) into
   the schema box.
4. Change the `servers.url` value to your Konvertio host
   (e.g. `https://konvertio.yourdomain.com`).
5. Save. Add instructions to the GPT like:

   > When the user shares a link to a report or document, call
   > `convertDocumentUrl` to get clean Markdown, then analyze the text.

Now users can say: *"Analyze this filing: https://…/10-K.pdf"* and the GPT will
convert it to lean Markdown first.

---

## Tip: keeping it lean for embeddings

Leave `strip_images` on (the default). The response includes `stats.tokens_saved`
so you can see how much context you reclaimed by dropping images and base64 data.

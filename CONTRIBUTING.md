# Contributing to Konvertio

First off, thank you for taking the time to contribute! Konvertio is built for
non-technical people who need clean text for AI analysis, and every improvement
helps them. This guide explains how to get set up and how to propose changes.

By participating in this project, you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

- **Report bugs** — open an [issue](https://github.com/proksy-ai/konvertio/issues) using the bug template.
- **Suggest features** — open an issue using the feature template.
- **Improve docs** — fixes to the README, comments, or guides are always welcome.
- **Write code** — pick up an open issue, or propose a change first so we can align.

If you are planning a larger change, please open an issue to discuss it **before**
writing a lot of code, so we can agree on the approach.

## Development setup

You need **Python 3.10+**. We recommend [uv](https://github.com/astral-sh/uv).

```bash
# 1. Fork and clone
git clone https://github.com/<your-username>/konvertio.git
cd konvertio

# 2. Create a virtual environment and install dependencies
uv venv --python=3.12 .venv
uv pip install -r requirements.txt

# 3. Run the app locally
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Open <http://localhost:8000>. The web UI is in `app/static/` and reloads on refresh;
the Python code reloads automatically with `--reload`.

### Project layout

| Path | What it does |
|------|--------------|
| `app/core.py` | Conversion engine + image stripping + stats (transport-agnostic). |
| `app/main.py` | FastAPI app: REST API, static UI, mounted MCP connector. |
| `app/ratelimit.py` | Per-IP rate limiting. |
| `app/mcp_server.py` | MCP server exposing `convert_to_markdown`. |
| `app/config.py` | Environment-based configuration. |
| `app/static/` | Single-page web UI. |
| `connectors/` | Claude (MCP) and ChatGPT (GPT Action) setup. |
| `deploy/` | Cloud deployment configs. |

## Coding conventions

- **Style:** follow standard Python style (PEP 8). Keep functions small and focused.
- **Type hints:** add them to new functions and public APIs.
- **Comments:** explain *why*, not *what*. Don't add comments that just restate the code.
- **Keep the core transport-agnostic:** conversion logic lives in `app/core.py` so it can
  be reused by the web API and the MCP connector. Don't couple it to FastAPI.
- **Privacy:** never write uploaded content to disk and never log document contents.
- **Dependencies:** keep them minimal. Discuss adding a new dependency in an issue first.

We recommend running a formatter/linter such as [ruff](https://docs.astral.sh/ruff/)
before submitting:

```bash
uv pip install ruff
ruff check app
ruff format app
```

## Commit messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add EPUB chunking option
fix: handle empty PDF pages without crashing
docs: clarify Cloud Run cost section
refactor: extract image stripper into helper
test: add cases for reference-style images
chore: bump markitdown to 0.1.2
```

Reference issues where relevant, e.g. `fix: reject oversized uploads (#42)`.

## Pull request process

1. Create a branch from `main`: `git checkout -b feat/short-description`.
2. Make your change. Keep PRs small and focused on one thing.
3. Test it locally (convert a few real documents; check the UI still works).
4. Update docs if behavior changed.
5. Push and open a pull request against `main`, filling in the PR template.
6. A maintainer will review. Please respond to feedback; we aim to be quick and kind.

By submitting a contribution, you agree that it will be licensed under the project's
[MIT License](LICENSE).

## Questions

Open a [discussion or issue](https://github.com/proksy-ai/konvertio/issues), or email
the maintainers at **piyush@proksy.ai**.

Thank you for helping make document analysis easier for everyone!

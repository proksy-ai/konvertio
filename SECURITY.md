# Security Policy

We take the security of Konvertio and its users seriously. Because the tool
processes documents that may contain sensitive financial information, we
appreciate responsible disclosure of any vulnerabilities.

## Reporting a vulnerability

**Please do not report security issues through public GitHub issues.**

Instead, email **piyush@proksy.ai** with:

- A description of the vulnerability and its potential impact.
- Steps to reproduce, or a proof of concept.
- Any suggested mitigation, if you have one.

We will acknowledge your report as soon as possible, keep you updated on our
progress, and credit you once the issue is resolved (unless you prefer to remain
anonymous).

## Scope and design notes

A few things that are important to understand about how Konvertio handles data:

- **No persistence:** uploaded files are processed entirely in memory and are
  never written to disk or logged.
- **Conversion privileges:** the underlying engine ([MarkItDown](https://github.com/microsoft/markitdown))
  reads with the privileges of the server process. On public deployments we
  recommend running in a container (as our Docker image does) and **disabling URL
  fetching** (`KONVERTIO_ALLOW_URL_FETCH=false`) to avoid server-side request
  forgery (SSRF) against internal resources.
- **Rate limiting:** the conversion endpoints are rate-limited per IP to reduce
  the impact of abuse. Limits are configurable (see the README).
- **The MCP endpoint is unauthenticated.** Only expose it to trusted users/
  networks, or place it behind your own authentication/proxy.

## Supported versions

Konvertio is under active development. Security fixes are applied to the latest
version on the `main` branch.

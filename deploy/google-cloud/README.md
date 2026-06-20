# Deploy Konvertio to Google Cloud Run

Cloud Run runs the app as a container that **scales to zero** when nobody is
using it, so for a small team this is typically **free or a few dollars a
month** — easily covered by Google Cloud / YC student credits.

You only need to do this once. After that, re-running the deploy command ships
updates.

## What you'll need

1. A Google account with **Google Cloud credits** applied.
2. A **Google Cloud project** (e.g. `konvertio`) with billing enabled.
3. The [`gcloud` CLI](https://cloud.google.com/sdk/docs/install) installed and
   `gcloud auth login` completed.

## Deploy in one command

From the project root:

```bash
PROJECT_ID=konvertio ./deploy/google-cloud/deploy.sh
```

For users in India, use Mumbai:

```bash
REGION=asia-south1 PROJECT_ID=konvertio ./deploy/google-cloud/deploy.sh
```

With Google Analytics (after you create a GA4 property):

```bash
KONVERTIO_GA_MEASUREMENT_ID=G-XXXXXXXXXX \
  REGION=asia-south1 PROJECT_ID=konvertio \
  ./deploy/google-cloud/deploy.sh
```

The script enables APIs, builds the Docker image, deploys with HTTP/2 (for files
up to 100 MB), and prints your public URL.

## Default production settings

| Setting | Value | Why |
|---------|-------|-----|
| Memory | 2 GiB | Large PDFs and textbooks need headroom |
| CPU | 2 | Faster conversion for big files |
| Timeout | 600 s | Long documents can take minutes |
| Max upload | 100 MB | Student case files and books |
| URL fetch | **off** | Safer on a public host |
| MCP connector | **off** | Not exposed publicly by default |
| HTTP/2 | on | Required for uploads &gt; 32 MB |
| Scale | 0 → 3 instances | Cheap when idle, capped under abuse |

Override via env vars when calling the script, e.g.
`MEMORY=4Gi MAX_INSTANCES=5 PROJECT_ID=konvertio ./deploy/google-cloud/deploy.sh`.

## Analytics and usage

See **[analytics.md](./analytics.md)** for:

- Setting up **Google Analytics 4** (visitors, geography, conversions).
- **Cloud Run metrics** (requests, latency, memory).
- **Logs Explorer** queries to count conversions.
- **Billing budget** alerts.

## App environment variables

| Variable | Deploy default | Description |
|----------|----------------|-------------|
| `KONVERTIO_MAX_UPLOAD_MB` | `100` | Max upload size (MB). |
| `KONVERTIO_ALLOW_URL_FETCH` | `false` | Allow converting by link (SSRF risk if public). |
| `KONVERTIO_GA_MEASUREMENT_ID` | _(empty)_ | GA4 measurement ID for visitor analytics. |
| `KONVERTIO_MCP_ENABLED` | `false` | Expose `/mcp-server` for Claude MCP clients. |
| `KONVERTIO_RATE_LIMIT_ENABLED` | `true` | Per-IP rate limiting. |

## Optional: lock it down

By default the service is public (`--allow-unauthenticated`). To restrict
access, redeploy without that flag and grant specific users the
`roles/run.invoker` role, or put it behind
[Identity-Aware Proxy](https://cloud.google.com/iap).

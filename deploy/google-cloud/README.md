# Deploy Konvertio to Google Cloud Run

Cloud Run runs the app as a container that **scales to zero** when nobody is
using it, so for a small team this is typically **free or a few dollars a
month** — easily covered by Google Cloud / YC student credits.

You only need to do this once. After that, re-running the deploy command ships
updates.

## What you'll need to give me / have ready

1. A Google account with **Google Cloud credits applied** (from YC Startup
   School).
2. A **Google Cloud project** — create one at
   <https://console.cloud.google.com/projectcreate> and note its **Project ID**
   (e.g. `konvertio-prod`).
3. The [`gcloud` CLI](https://cloud.google.com/sdk/docs/install) installed, and
   you've run `gcloud auth login` once.

That's everything. No servers, Docker, or DevOps knowledge required.

## Deploy in one command

From the project root:

```bash
PROJECT_ID=your-project-id ./deploy/google-cloud/deploy.sh
```

Pick a region closer to your users for speed, e.g. India:

```bash
REGION=asia-south1 PROJECT_ID=your-project-id ./deploy/google-cloud/deploy.sh
```

The script will:
1. Enable the needed Google APIs.
2. Build the container from the included `Dockerfile`.
3. Deploy it to Cloud Run with sensible defaults (1 GB RAM, scales 0→3).
4. Print your public URL at the end.

Share that URL with your users — they just open it and start converting.

## Cost & settings

- **Scales to zero**: you pay nothing while idle (first request after idle has a
  ~2–4s cold start).
- Defaults: `1Gi` memory, `1` CPU, `300s` timeout, max `3` instances.
- Override any of them via environment variables, e.g.
  `MEMORY=2Gi MAX_INSTANCES=5 PROJECT_ID=... ./deploy/google-cloud/deploy.sh`.

## App settings

| Variable | Default | Description |
|----------|---------|-------------|
| `KONVERTIO_MAX_UPLOAD_MB` | `50` | Max upload size (MB). |
| `KONVERTIO_ALLOW_URL_FETCH` | `true` | Allow converting documents by link. |

## Optional: lock it down

By default the service is public (`--allow-unauthenticated`). To restrict
access, redeploy without that flag and grant specific users the
`roles/run.invoker` role, or put it behind
[Identity-Aware Proxy](https://cloud.google.com/iap).

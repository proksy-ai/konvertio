#!/usr/bin/env bash
#
# Deploy Konvertio to Google Cloud Run.
#
# Prerequisites (one-time):
#   1. Install the gcloud CLI:  https://cloud.google.com/sdk/docs/install
#   2. Log in:                  gcloud auth login
#   3. Create / pick a project: https://console.cloud.google.com/projectcreate
#      (apply your YC / student Google Cloud credits to this project)
#
# Usage:
#   PROJECT_ID=your-project-id ./deploy/google-cloud/deploy.sh
#
# Optional overrides:
#   REGION=asia-south1 PROJECT_ID=... ./deploy/google-cloud/deploy.sh
#
set -euo pipefail

# ---- Configuration -----------------------------------------------------------
SERVICE_NAME="${SERVICE_NAME:-konvertio}"
REGION="${REGION:-us-central1}"
MEMORY="${MEMORY:-2Gi}"
CPU="${CPU:-2}"
# Request timeout (seconds). Large files can take a while to convert.
TIMEOUT="${TIMEOUT:-600}"
# Concurrent requests per instance. Kept modest so big files don't exhaust RAM.
CONCURRENCY="${CONCURRENCY:-8}"
# Scale to zero when idle (no cost), up to a small ceiling.
MIN_INSTANCES="${MIN_INSTANCES:-0}"
MAX_INSTANCES="${MAX_INSTANCES:-3}"
MAX_UPLOAD_MB="${KONVERTIO_MAX_UPLOAD_MB:-100}"
ALLOW_URL_FETCH="${KONVERTIO_ALLOW_URL_FETCH:-false}"
GA_MEASUREMENT_ID="${KONVERTIO_GA_MEASUREMENT_ID:-}"
MCP_ENABLED="${KONVERTIO_MCP_ENABLED:-false}"

if [[ -z "${PROJECT_ID:-}" ]]; then
  echo "ERROR: set PROJECT_ID, e.g.  PROJECT_ID=my-project ./deploy/google-cloud/deploy.sh" >&2
  exit 1
fi

# Repo root (this script lives in deploy/google-cloud/).
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "==> Project:  $PROJECT_ID"
echo "==> Service:  $SERVICE_NAME"
echo "==> Region:   $REGION"
echo

gcloud config set project "$PROJECT_ID"

echo "==> Enabling required APIs (run, cloudbuild, artifactregistry)..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

echo "==> Building from source (uses the Dockerfile) and deploying..."
# --use-http2 lets Cloud Run accept request bodies larger than 32 MiB (big files).
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --use-http2 \
  --memory "$MEMORY" \
  --cpu "$CPU" \
  --timeout "$TIMEOUT" \
  --concurrency "$CONCURRENCY" \
  --min-instances "$MIN_INSTANCES" \
  --max-instances "$MAX_INSTANCES" \
  --set-env-vars "KONVERTIO_MAX_UPLOAD_MB=${MAX_UPLOAD_MB},KONVERTIO_ALLOW_URL_FETCH=${ALLOW_URL_FETCH},KONVERTIO_GA_MEASUREMENT_ID=${GA_MEASUREMENT_ID},KONVERTIO_MCP_ENABLED=${MCP_ENABLED}"

echo
echo "==> Done. Your app URL:"
gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)'

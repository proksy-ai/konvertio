# Konvertio analytics on Google Cloud

Two layers work together:

1. **Google Analytics 4 (GA4)** — visitors, sessions, geography, real-time traffic.
2. **Google Cloud (built-in)** — request volume, latency, errors, and conversion counts from logs.

No document content is ever sent to analytics. Conversion logs record only file type
and token counts.

---

## 1. Google Analytics 4 (website visitors)

### Set up (one time, ~5 minutes)

1. Go to [Google Analytics](https://analytics.google.com/) and sign in with the same
   Google account that owns the Cloud project.
2. **Admin** (gear icon) → **Create** → **Property**.
   - Name it `Konvertio`, set your timezone and currency.
3. Under the property, **Data streams** → **Add stream** → **Web**.
   - URL: `https://konvertio-812098809765.asia-south1.run.app` (or your custom domain).
   - Stream name: `Konvertio web`.
4. Copy the **Measurement ID** (format `G-XXXXXXXXXX`).

### Enable on the live app

Redeploy with the measurement ID:

```bash
KONVERTIO_GA_MEASUREMENT_ID=G-XXXXXXXXXX \
  REGION=asia-south1 PROJECT_ID=konvertio \
  ./deploy/google-cloud/deploy.sh
```

Or update only the env var without a full rebuild:

```bash
gcloud run services update konvertio \
  --region asia-south1 \
  --update-env-vars KONVERTIO_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

### What you can see in GA4

| Report | Where in GA4 |
|--------|----------------|
| Active users right now | **Reports → Realtime** |
| Users / sessions over time | **Reports → Acquisition** |
| Geography | **Reports → User → Demographics → Country** |
| Conversions (uploads) | **Reports → Engagement → Events** → `convert_document` |

The UI fires `convert_document` with `images_removed` and `tokens_after` only (no file names or content).

---

## 2. Google Cloud metrics (no extra setup)

### Cloud Run dashboard (requests and performance)

1. Open [Cloud Run](https://console.cloud.google.com/run).
2. Select service **`konvertio`**, region **`asia-south1`**.
3. Open the **Metrics** tab.

Useful charts:

- **Request count** — how busy the app is.
- **Request latencies** — how long conversions take (large files spike here).
- **Container instance count** — how many instances are running (0 when idle).
- **Container memory utilization** — watch this if you upload many 100 MB files.

Direct link (replace project if needed):

`https://console.cloud.google.com/run/detail/asia-south1/konvertio/metrics?project=konvertio`

### Conversion counts (Logs Explorer)

Each successful conversion writes one line like:

```text
conversion_ok source=file ext=.pdf images_removed=3 tokens_after=4521
```

**View recent conversions:**

1. Open [Logs Explorer](https://console.cloud.google.com/logs/query?project=konvertio).
2. Paste this query and click **Run query**:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="konvertio"
textPayload:"conversion_ok"
```

3. Use the **time range** picker (last 24 hours, 7 days, etc.).

**Count conversions per day** (Logs Explorer → **Create chart** from query results, or use this in **Log Analytics**):

```text
resource.type="cloud_run_revision"
resource.labels.service_name="konvertio"
textPayload:"conversion_ok"
```

Group by time bucket in the chart builder to see conversions over time.

### Billing and cost alerts

1. [Billing → Budgets & alerts](https://console.cloud.google.com/billing/budgets).
2. **Create budget** → link to your billing account → set amount (e.g. **$10/month**).
3. Add email alerts at 50%, 90%, and 100%.

For light student/team use you will usually stay near **$0** (free tier + scale to zero).

---

## Quick reference

| Question | Where to look |
|----------|----------------|
| How many people visited? | GA4 → Realtime / Acquisition |
| How many files were converted? | Logs Explorer → `conversion_ok` |
| Is the app slow or erroring? | Cloud Run → Metrics |
| What will this cost? | Billing → Reports / Budgets |

Questions: [piyush@proksy.ai](mailto:piyush@proksy.ai)

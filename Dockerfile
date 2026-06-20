FROM python:3.12-slim

# System deps some markitdown extractors benefit from (e.g. PDF/zip handling).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# Run as a non-root user for safety.
RUN useradd --create-home --uid 10001 konvertio
USER konvertio

# Hypercorn speaks HTTP/2 cleartext (h2c), which lets Cloud Run (with --use-http2)
# accept request bodies larger than the 32 MiB HTTP/1 cap, needed for big files.
# Shell form so $PORT (injected by Cloud Run, default 8000 elsewhere) expands.
CMD exec hypercorn app.main:app --bind 0.0.0.0:${PORT:-8000} --workers 1

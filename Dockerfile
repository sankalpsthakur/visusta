# ── Stage 1: Frontend builder ─────────────────────────────────────────────────
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend

ENV NEXT_TELEMETRY_DISABLED=1

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# ── Stage 2: Python deps ──────────────────────────────────────────────────────
FROM python:3.12-slim AS python-deps

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements-runtime.txt .
RUN pip install --no-cache-dir --no-compile -r requirements-runtime.txt


# ── Stage 3: Final image ──────────────────────────────────────────────────────
FROM python:3.12-slim AS final

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOFFICE_PATH=/usr/bin/soffice \
    SAL_USE_VCLPLUGIN=svp \
    NO_AT_BRIDGE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install headless LibreOffice only.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-core-nogui \
    libreoffice-writer-nogui \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from python-deps stage.
COPY --from=python-deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy only the Node runtime needed for the Next.js standalone server.
COPY --from=frontend-builder /usr/local/bin/node /usr/local/bin/node

# Copy Next.js standalone build from frontend-builder stage
COPY --from=frontend-builder /app/frontend/.next/standalone /app/frontend-server
COPY --from=frontend-builder /app/frontend/.next/static /app/frontend-server/.next/static
COPY --from=frontend-builder /app/frontend/public /app/frontend-server/public

# Copy backend source
COPY api/ ./api/
COPY agents/ ./agents/
COPY mars/ ./mars/
COPY config/ ./config/
COPY db/ ./db/
COPY regulatory_data/ ./regulatory_data/
COPY scripts/ ./scripts/
COPY build_monthly_report.py ./build_monthly_report.py
COPY build_quarterly_brief.py ./build_quarterly_brief.py
COPY gap_analysis.py ./gap_analysis.py
COPY models.py ./models.py
COPY pipeline.py ./pipeline.py
COPY quarterly_consolidator.py ./quarterly_consolidator.py
COPY regulatory_screening.py ./regulatory_screening.py
COPY report_engine.py ./report_engine.py
COPY templates/ ./templates/

# Render assigns $PORT (typically 10000); EXPOSE must match
EXPOSE 10000

# Startup script runs migrations then starts both servers
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python3 -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).status == 200 else 1)"

ENTRYPOINT ["/docker-entrypoint.sh"]

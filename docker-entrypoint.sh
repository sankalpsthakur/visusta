#!/bin/sh
set -e

# Render assigns $PORT; default to 10000 for local Docker
FRONTEND_PORT="${PORT:-10000}"
API_PORT=8000

# Run database migrations
echo "Running database migrations..."
python3 -m db.migrate

# Seed default report templates (idempotent — no-op when templates exist)
python3 scripts/seed_templates.py || echo "seed_templates: skipped or failed (non-fatal)"

# Start FastAPI backend in background on internal port
echo "Starting API server on port $API_PORT..."
python3 -m uvicorn api.main:app --host 127.0.0.1 --port "$API_PORT" &

# Start Next.js frontend (foreground) on Render's $PORT
echo "Starting frontend server on port $FRONTEND_PORT..."
PORT="$FRONTEND_PORT" HOSTNAME="0.0.0.0" exec node /app/frontend-server/server.js

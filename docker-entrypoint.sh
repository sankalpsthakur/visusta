#!/bin/sh
set -e

# Render assigns $PORT; default to 3000 for local Docker
FRONTEND_PORT="${PORT:-3000}"
API_PORT=8000

# Run database migrations
echo "Running database migrations..."
python3 -m db.migrate

# Start FastAPI backend in background on internal port
echo "Starting API server on port $API_PORT..."
python3 -m uvicorn api.main:app --host 0.0.0.0 --port "$API_PORT" &

# Start Next.js frontend (foreground) on Render's $PORT
# Next.js reads PORT env var automatically in standalone mode
echo "Starting frontend server on port $FRONTEND_PORT..."
PORT="$FRONTEND_PORT" exec node /app/frontend-server/server.js

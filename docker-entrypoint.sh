#!/bin/sh
set -e

# Run database migrations
echo "Running database migrations..."
python3 -m db.migrate

# Start Next.js frontend server in background
echo "Starting frontend server on port 3000..."
node /app/frontend-server/server.js &

# Start FastAPI backend (foreground, so container stays alive)
echo "Starting API server on port 8000..."
exec python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000

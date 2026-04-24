#!/usr/bin/env bash
# run_dev.sh — start all services locally (no Docker required)
# Usage: bash run_dev.sh
# Press Ctrl+C once to stop all services.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$REPO_ROOT"

# Load .env if present
if [ -f "$REPO_ROOT/.env" ]; then
  set -a
  source "$REPO_ROOT/.env"
  set +a
fi

# Install deps for all services into the current Python env
echo "▶ Installing dependencies..."
pip install -q fastapi[standard] sqlalchemy aiosqlite pydantic-settings httpx uvicorn

echo ""
echo "▶ Starting services..."
echo "  Gateway   → http://localhost:8000  (docs: http://localhost:8000/docs)"
echo "  Shortener → http://localhost:8001  (internal)"
echo "  Redirect  → http://localhost:8002  (internal)"
echo "  Cleanup   → http://localhost:8003  (internal)"
echo ""

# Run each service in the background; trap Ctrl+C to kill them all
cleanup() {
  echo ""
  echo "▶ Stopping all services..."
  kill "$PID_SHORTENER" "$PID_REDIRECT" "$PID_CLEANUP" "$PID_GATEWAY" 2>/dev/null || true
  wait
  echo "▶ All services stopped."
}
trap cleanup INT TERM

uvicorn shortener.app.main:app --host 0.0.0.0 --port 8001 --reload &
PID_SHORTENER=$!

uvicorn redirect.app.main:app  --host 0.0.0.0 --port 8002 --reload &
PID_REDIRECT=$!

uvicorn cleanup.app.main:app   --host 0.0.0.0 --port 8003 --reload &
PID_CLEANUP=$!

# Give upstream services a moment before gateway starts
sleep 1

uvicorn gateway.app.main:app   --host 0.0.0.0 --port 8000 --reload &
PID_GATEWAY=$!

wait

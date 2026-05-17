#!/bin/bash
# ───────────────────────────────────────────────
#  AETERNA Dashboard Starter
#  Usage: bash start_dashboard.sh
#         (from gumroad.auto/ directory)
# ───────────────────────────────────────────────

cd "$(dirname "$0")"
PYTHON="$(dirname "$0")/venv/bin/python3"

# Fallback to system python if venv not found
if [ ! -f "$PYTHON" ]; then
  PYTHON="python3"
fi

# Kill any existing server on port 8001
lsof -ti:8001 | xargs kill -9 2>/dev/null
sleep 0.5

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   AETERNA Product Dashboard          ║"
echo "  ║   http://localhost:8001              ║"
echo "  ╚══════════════════════════════════════╝"
echo ""
echo "  Approve  → instantly published to Gumroad"
echo "  Reject   → saved as feedback for AI"
echo "  Press Ctrl+C to stop"
echo ""

# Start server, open browser
$PYTHON local_server.py &
SERVER_PID=$!

sleep 1.5
open http://localhost:8001 2>/dev/null || xdg-open http://localhost:8001 2>/dev/null

wait $SERVER_PID

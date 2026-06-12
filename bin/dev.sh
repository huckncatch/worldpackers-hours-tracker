#!/bin/bash
# Run a throwaway dev instance for manual testing in a detached tmux session.
# Separate port and separate SQLite DB from the live tmux-managed instance
# ("worldpackers" on port 5050) — safe to run alongside it without touching
# production data.
#
# An empty dev DB is auto-seeded with sample packers (see bin/seed_dev_data.py).
#
# Usage:
#   bin/dev.sh           # start (reuses instance/dev.db across runs)
#   bin/dev.sh --reset   # stop, wipe instance/dev.db, and restart fresh (re-seeds)
#   bin/dev.sh --stop    # stop the dev session
#
# Override port or admin password: PORT=5052 OPS_PASSWORD=foo bin/dev.sh
set -euo pipefail

if [ -x /opt/homebrew/bin/tmux ]; then
  TMUX=/opt/homebrew/bin/tmux
elif [ -x /usr/local/bin/tmux ]; then
  TMUX=/usr/local/bin/tmux
else
  TMUX=tmux
fi

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SESSION=worldpackers-dev
PORT="${PORT:-5051}"
DEV_DB="$APP_DIR/instance/dev.db"
OPS_PASSWORD="${OPS_PASSWORD:-devpass}"

cd "$APP_DIR"
mkdir -p instance

stop_session() {
  $TMUX kill-session -t "$SESSION" 2>/dev/null || true
  # Werkzeug's reloader spawns a second process; make sure both are gone.
  for pid in $(lsof -ti tcp:"$PORT" 2>/dev/null || true); do
    kill "$pid" 2>/dev/null || true
  done
}

case "${1:-}" in
  --stop)
    stop_session
    echo "Stopped $SESSION"
    exit 0
    ;;
  --reset)
    stop_session
    rm -f "$DEV_DB"
    echo "Reset $DEV_DB"
    ;;
  *)
    if $TMUX has-session -t "$SESSION" 2>/dev/null; then
      echo "Dev instance already running: http://127.0.0.1:$PORT  (ops login: $OPS_PASSWORD)"
      echo "Attach: $TMUX attach -t $SESSION   |   Stop: bin/dev.sh --stop"
      exit 0
    fi
    ;;
esac

$TMUX new-session -d -s "$SESSION" -x 220 -y 50 \
  "cd '$APP_DIR' && PORT='$PORT' DEV_DB='$DEV_DB' OPS_PASSWORD='$OPS_PASSWORD' .venv/bin/python3 bin/dev_server.py"

echo "Dev instance: http://127.0.0.1:$PORT  (ops login: $OPS_PASSWORD)"
echo "Database: $DEV_DB"
echo "Attach: $TMUX attach -t $SESSION   |   Stop: bin/dev.sh --stop"

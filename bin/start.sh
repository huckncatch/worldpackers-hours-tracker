#!/bin/sh
# Start WorldPackers Hours Tracker in a dedicated tmux session.
# Idempotent — does nothing if session already exists.
if [ -x /opt/homebrew/bin/tmux ]; then
  TMUX=/opt/homebrew/bin/tmux
elif [ -x /usr/local/bin/tmux ]; then
  TMUX=/usr/local/bin/tmux
else
  TMUX=tmux
fi
PYTHON=/Users/soob/Developer/worldpackers-hours-tracker/.venv/bin/python3
APP_DIR=/Users/soob/Developer/worldpackers-hours-tracker
LOG=/Users/soob/Library/Logs/worldpackers-tracker.log

[ -f "$APP_DIR/.env" ] && . "$APP_DIR/.env"

$TMUX has-session -t worldpackers 2>/dev/null && exit 0

$TMUX new-session -d -s worldpackers -x 220 -y 50 \
  "cd '$APP_DIR' && OPS_PASSWORD='$OPS_PASSWORD' '$PYTHON' app.py >> '$LOG' 2>&1"

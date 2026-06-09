#!/bin/sh
# Start WorldPackers Hours Tracker in a dedicated tmux session.
# Idempotent — does nothing if session already exists.
TMUX=/opt/homebrew/bin/tmux
PYTHON=/Users/soob/Developer/worldpackers-hours-tracker/.venv/bin/python3
APP_DIR=/Users/soob/Developer/worldpackers-hours-tracker
LOG=/Users/soob/Library/Logs/worldpackers-tracker.log

$TMUX has-session -t worldpackers 2>/dev/null && exit 0

$TMUX new-session -d -s worldpackers -x 220 -y 50 \
  "cd '$APP_DIR' && '$PYTHON' app.py >> '$LOG' 2>&1"

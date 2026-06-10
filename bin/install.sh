#!/bin/bash
# Self-contained setup: provisions .env, creates venv + deps,
# installs the LaunchAgent, and starts the server.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_NAME=com.local.worldpackers-tracker.plist
PLIST_SRC="$APP_DIR/launchagents/$PLIST_NAME"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

cd "$APP_DIR"

if [ ! -f .env ]; then
  while [ -z "${OPS_PASSWORD:-}" ]; do
    read -rsp "Set admin (ops) password: " OPS_PASSWORD
    echo
  done
  printf 'OPS_PASSWORD=%s\n' "$OPS_PASSWORD" > .env
  chmod 600 .env
fi

echo "Setting up Python environment..."
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

echo "Installing LaunchAgent..."
mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST_SRC" "$PLIST_DEST"
launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo "Starting server..."
"$APP_DIR/bin/start.sh"

echo "Done. Open http://localhost:5050"

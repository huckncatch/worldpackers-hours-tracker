# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup (development)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

Serves on `0.0.0.0:5050`. On startup, `create_app()` ensures `instance/` exists and `database.init_db()` runs the schema (`CREATE TABLE IF NOT EXISTS`), so the SQLite DB at `instance/worldpackers.db` is created/upgraded automatically.

### Test

```bash
pytest                                  # full suite
pytest tests/test_balance.py            # one file
pytest tests/test_balance.py::test_name -v   # single test
```

Tests run against an in-memory SQLite DB (see `tests/conftest.py`) — no setup needed beyond the venv. Use the `authed_client` fixture for routes under `/ops` (it logs in with `OPS_PASSWORD=testpass`).

### Deploy / auto-start (macOS)

```bash
bin/install.sh   # one-time: provisions .env (prompts for OPS_PASSWORD), creates venv, installs LaunchAgent, starts server
bin/start.sh     # idempotent: starts the tmux session if not already running (called by the LaunchAgent at login)
```

The app runs inside a detached tmux session named `worldpackers`. `bin/start.sh` resolves the `tmux` binary at runtime (checks `/opt/homebrew/bin` then `/usr/local/bin`) since this repo is deployed on both Apple Silicon and Intel Macs.

## Architecture

**Layering:** `routes/*.py` (Flask Blueprints) → `models.py` (all SQL, plain functions, no ORM) → `db.py` (raw `sqlite3` connection via Flask's `g`, schema in the `SCHEMA` constant). `balance.py` is the one layer with no Flask/DB dependency — pure functions over plain dicts, which is why it's the most heavily unit-tested module.

**Schema** (`db.py`): four tables — `packers`, `work_entries` (FK to `packers`), `excused_days` (FK to `packers`, nullable `packer_id` means it applies to all packers), `audit_log` (FK-less, retained even after a packer is deleted).

**Balance model** (`balance.py`): each packer has their own `tracking_start_date`; weeks are rolling 7-day windows from that date (`get_week_number`/`get_week_boundaries`), not calendar weeks. `compute_balance()` walks all of a packer's entries to get `cumulative_balance` (surplus/deficit vs. each completed week's target), then derives `adjusted_target_this_week` = `current_week_target - cumulative_balance` (floored at 0). A week's target is normally 25h but is pro-rated down via `_week_target_hours()` by `25 × (7 − N) / 7` for each of the `N` excused days (from `excused_days`, global or per-packer) that fall in that week. `routes/dashboard.py` and `routes/api.py` (consumed by Chart.js client-side) both call `compute_balance()` via `parse_entries_for_balance()` and `parse_excused_days()` — keep them in sync if the return shape or inputs change.

**Time picker** (`routes/log.py`): forms submit hour/minute/AM-PM as three separate selects (`HOUR_OPTIONS`/`MINUTE_OPTIONS`/`AMPM_OPTIONS`). `_to_24h`/`_from_24h` convert between this and the `"HH:MM"` 24h strings stored in `work_entries`. `_calc_duration` raises `ValueError` if end <= start; both `entry()` and `edit_entry()` catch this and re-render the form with an error rather than redirecting.

**Auth** (`routes/admin.py`): the `/ops` blueprint is gated by a single shared `OPS_PASSWORD` (no per-user accounts). `before_request` checks `session["ops_authed"]`; login compares via `hmac.compare_digest`. The `next` redirect target is validated to start with `/ops` and have no scheme/netloc, to prevent open-redirect.

**Audit log**: `models.log_audit()` is called only from `routes/log.py` (create/update/delete of `work_entries`) — admin operations on `packers` (create/edit/lock/hide/delete) are not audited.

**Frontend**: server-rendered Jinja2 templates extending `templates/base.html`, styled with the Tailwind CDN build and charted with Chart.js CDN — no JS build step, no `node_modules`. `routes/api.py` (`/api/packer/<id>/stats`) is the JSON source for per-packer Chart.js widgets and accepts an optional `?today=` override for testing/debugging a specific date.

**Secrets**: `OPS_PASSWORD` lives in `.env` (gitignored), sourced by `bin/start.sh` and passed as an env var to the `python app.py` process. There is no `.env.example` — `bin/install.sh` prompts for the password on first run and writes `.env` itself.

## Feature Development Workflow (EPCT)

For TODO items, use `/epct` (global checkpoint/test-plan process defined in
`~/.config/claude/commands/epct.md`). Preview info for its Phase 1:

- App: http://localhost:5050 (tmux session `worldpackers`). Flask may not
  hot-reload — restart with `tmux kill-session -t worldpackers && bin/start.sh`
  before UX checkpoints/testing.
- Tests: `pytest`

## Cross-repo documentation

This app's LaunchAgent/tmux auto-start setup is also documented in `~/config/NOTES.md` under "WorldPackers Hours Tracker" (restore steps, verify/restart commands, log paths). If a change here affects `bin/install.sh`, `bin/start.sh`, the LaunchAgent plist (`launchagents/`), the tmux session name, the port (5050), or log file locations, update that section of `~/config/NOTES.md` too — it's the canonical "how to restore this on a fresh machine" reference and lives outside this repo.

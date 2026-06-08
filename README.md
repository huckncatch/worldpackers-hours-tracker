# WorldPackers Hours Tracker

A locally-hosted web app for tracking volunteer work hours for [WorldPackers](https://www.worldpackers.com) guests. Packers work 25 hours/week in exchange for accommodation and meals. This replaces a paper logbook with a mobile-friendly shared dashboard anyone on the home network can use.

## Features

- **Shared dashboard** — progress rings and weekly bar charts for each active packer
- **Rolling 7-day weeks** — each packer's week starts from their individual tracking start date
- **Cumulative balance** — surplus/deficit carries forward; adjusted weekly target reflects what's still owed
- **Hour logging** — select date (last 30 days), start/end time (15-minute intervals), optional task description
- **Multiple blocks per day** — log as many work sessions as needed
- **Admin panel** — manage the packer roster; lock (freeze entries) or hide (archive) packers; delete packers
- **Audit log** — every create/edit/delete is logged with IP, user-agent, and timestamp
- **Auto-start** — runs in a tmux session via a LaunchAgent at login

## Tech Stack

- **Python + Flask** — app server
- **SQLite** — database (no external dependencies)
- **Tailwind CSS** (CDN) — styling, no build step
- **Chart.js** (CDN) — dashboard progress rings and bar charts

## Requirements

- Python 3.10+
- [tmux](https://github.com/tmux/tmux) (for auto-start)
- macOS (LaunchAgent auto-start is macOS-specific; the app itself runs anywhere)

## Setup

```bash
git clone <repo-url>
cd worldpackers-hours-tracker

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the server:

```bash
python app.py
```

The app listens on `0.0.0.0:5050`. Open `http://<your-machine-ip>:5050` from any device on the same network.

## Auto-Start on macOS (LaunchAgent + tmux)

The app runs in a detached tmux session so it survives login and can be inspected in a terminal.

A self-contained `bin/start.sh` and `bin/install.sh` (to set up the LaunchAgent automatically after cloning) are on the roadmap. For now, create a start script and LaunchAgent plist manually — the pattern used here mirrors the tmux session approach in the [things-mcp](https://github.com/nicholasgasior/things-mcp) project.

To view the server log once running:

```bash
tail -f ~/Library/Logs/worldpackers-tracker.log
```

To attach to the tmux session:

```bash
tmux attach -t worldpackers
```

## Admin Panel

The admin panel is accessible to the host at a non-obvious URL — check `routes/admin.py` for the path. It is not linked from anywhere in the public UI. From admin you can add packers, lock/unlock entries, hide/show packers, and delete packers.

## Running Tests

```bash
source .venv/bin/activate
pytest
```

## License

MIT — see [LICENSE](LICENSE).

# WorldPackers Hours Tracker — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locally-hosted Flask web app that replaces a paper logbook for tracking WorldPackers volunteer hours, with a mobile-friendly shared dashboard showing per-packer progress rings and weekly charts.

**Architecture:** Server-side rendered Flask app with SQLite persistence. Balance logic lives in pure Python functions (testable without HTTP). Chart.js reads from lightweight JSON API endpoints. Routes are split into focused Blueprint files. The server auto-starts via LaunchAgent + tmux on login, same pattern as `things-mcp`.

**Tech Stack:** Python 3.11+, Flask 3.x, SQLite3 (stdlib), pytest, Chart.js (CDN), Tailwind CSS (CDN Play), python-dotenv

---

## File Structure

```
worldpackers-hours-tracker/
├── app.py                      # Flask app factory, blueprint registration
├── db.py                       # Schema init, get_db() connection helper
├── models.py                   # All SQL queries (packers, work_entries, audit_log)
├── balance.py                  # Pure functions: week calc, running balance
├── routes/
│   ├── __init__.py             # Empty
│   ├── dashboard.py            # GET / → shared dashboard
│   ├── log.py                  # Packer select, log entry, edit/delete entry
│   ├── admin.py                # Admin packer CRUD, lock/hide
│   └── api.py                  # JSON endpoints consumed by Chart.js
├── templates/
│   ├── base.html               # Layout shell: Tailwind CDN, Chart.js CDN, nav
│   ├── dashboard.html          # Per-packer cards with charts
│   ├── log_select.html         # Pick your name
│   ├── log_entry.html          # Log a work block + today's entries list
│   ├── admin_packers.html      # Packer list with lock/hide controls
│   └── admin_packer_form.html  # Add / edit packer form
├── tests/
│   ├── conftest.py             # App + DB fixture (in-memory SQLite)
│   ├── test_balance.py         # Balance calculation unit tests — most critical
│   ├── test_models.py          # Database layer tests
│   └── test_routes.py          # Route integration tests
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Chunk 1: Foundation — DB schema, models, balance logic

### Task 1: Project scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `app.py`
- Create: `db.py`

- [ ] **Step 1: Create `requirements.txt`**

```
flask>=3.0
python-dotenv>=1.0
pytest>=8.0
pytest-flask>=1.3
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
*.db
.venv/
venv/
```

- [ ] **Step 3: Create virtual environment and install deps**

```bash
cd ~/Developer/worldpackers-hours-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: Flask and pytest install without errors.

- [ ] **Step 4: Create `db.py` with schema init**

```python
import sqlite3
import click
from flask import g, current_app


SCHEMA = """
CREATE TABLE IF NOT EXISTS packers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    arrival_date        TEXT    NOT NULL,
    departure_date      TEXT    NOT NULL,
    tracking_start_date TEXT    NOT NULL,
    tracking_end_date   TEXT    NOT NULL,
    locked              INTEGER NOT NULL DEFAULT 0,
    hidden              INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS work_entries (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    packer_id           INTEGER NOT NULL REFERENCES packers(id),
    entry_date          TEXT    NOT NULL,
    start_time          TEXT    NOT NULL,
    end_time            TEXT    NOT NULL,
    duration_minutes    INTEGER NOT NULL,
    task_description    TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (packer_id) REFERENCES packers(id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    operation    TEXT NOT NULL,
    entity       TEXT NOT NULL,
    entity_id    INTEGER NOT NULL,
    packer_name  TEXT,
    user_agent   TEXT,
    ip_address   TEXT,
    timestamp    TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(_init_db_command)


@click.command("init-db")
def _init_db_command():
    init_db()
    click.echo("Database initialized.")
```

- [ ] **Step 5: Create minimal `app.py`**

```python
import os
from flask import Flask
from . import db as database


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        DATABASE=os.path.join(app.instance_path, "worldpackers.db"),
    )
    if config:
        app.config.from_mapping(config)

    os.makedirs(app.instance_path, exist_ok=True)
    database.init_app(app)

    return app
```

Wait — since this is a standalone script (not a package), avoid relative imports. Use this instead:

```python
import os
from flask import Flask
import db as database


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-key-change-me"),
        DATABASE=os.path.join(app.instance_path, "worldpackers.db"),
    )
    if config:
        app.config.from_mapping(config)

    os.makedirs(app.instance_path, exist_ok=True)
    database.init_app(app)

    from routes.dashboard import bp as dashboard_bp
    from routes.log import bp as log_bp
    from routes.admin import bp as admin_bp
    from routes.api import bp as api_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        database.init_db()
    app.run(host="0.0.0.0", port=5050, debug=False)
```

- [ ] **Step 6: Create stub Blueprint files so the app can start**

`routes/__init__.py` — empty file.

`routes/dashboard.py`:
```python
from flask import Blueprint, render_template
bp = Blueprint("dashboard", __name__)

@bp.route("/")
def index():
    return "Dashboard coming soon", 200
```

`routes/log.py`:
```python
from flask import Blueprint
bp = Blueprint("log", __name__, url_prefix="/log")

@bp.route("/")
def select():
    return "Log select coming soon", 200
```

`routes/admin.py`:
```python
from flask import Blueprint
bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
def index():
    return "Admin coming soon", 200
```

`routes/api.py`:
```python
from flask import Blueprint, jsonify
bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/health")
def health():
    return jsonify({"status": "ok"})
```

- [ ] **Step 7: Write the smoke test**

`tests/conftest.py`:
```python
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
import db as database


@pytest.fixture()
def app():
    test_app = create_app({
        "TESTING": True,
        "DATABASE": ":memory:",
    })
    with test_app.app_context():
        database.init_db()
    yield test_app


@pytest.fixture()
def client(app):
    return app.test_client()
```

`tests/test_routes.py` (initial smoke test):
```python
def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json["status"] == "ok"

def test_dashboard_stub(client):
    resp = client.get("/")
    assert resp.status_code == 200
```

- [ ] **Step 8: Run smoke tests**

```bash
cd ~/Developer/worldpackers-hours-tracker
source .venv/bin/activate
pytest tests/ -v
```

Expected: 2 tests pass.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: project scaffold — Flask app factory, DB schema, stub routes"
```

---

### Task 2: Models — data access layer

**Files:**
- Create: `models.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for packer CRUD**

`tests/test_models.py`:
```python
import pytest
from datetime import date
import models


def test_create_and_get_packer(app):
    with app.app_context():
        packer_id = models.create_packer(
            name="Maria",
            arrival_date=date(2026, 6, 1),
            departure_date=date(2026, 6, 28),
            tracking_start_date=date(2026, 6, 2),
            tracking_end_date=date(2026, 6, 27),
        )
        packer = models.get_packer(packer_id)
        assert packer["name"] == "Maria"
        assert packer["locked"] == 0
        assert packer["hidden"] == 0


def test_list_active_packers(app):
    with app.app_context():
        models.create_packer("Active", date(2026,6,1), date(2026,6,28),
                              date(2026,6,1), date(2026,6,28))
        hidden_id = models.create_packer("Hidden", date(2026,6,1), date(2026,6,28),
                                          date(2026,6,1), date(2026,6,28))
        models.set_packer_hidden(hidden_id, True)

        active = models.list_active_packers()
        names = [p["name"] for p in active]
        assert "Active" in names
        assert "Hidden" not in names


def test_create_work_entry(app):
    with app.app_context():
        packer_id = models.create_packer("Kai", date(2026,6,1), date(2026,6,28),
                                          date(2026,6,1), date(2026,6,28))
        entry_id = models.create_work_entry(
            packer_id=packer_id,
            entry_date=date(2026, 6, 5),
            start_time="09:00",
            end_time="12:00",
            duration_minutes=180,
            task_description="Garden work",
        )
        entries = models.get_entries_for_packer(packer_id)
        assert len(entries) == 1
        assert entries[0]["duration_minutes"] == 180
        assert entries[0]["task_description"] == "Garden work"


def test_delete_work_entry(app):
    with app.app_context():
        packer_id = models.create_packer("Dee", date(2026,6,1), date(2026,6,28),
                                          date(2026,6,1), date(2026,6,28))
        entry_id = models.create_work_entry(packer_id, date(2026,6,5),
                                             "10:00", "11:00", 60, None)
        models.delete_work_entry(entry_id)
        entries = models.get_entries_for_packer(packer_id)
        assert len(entries) == 0


def test_audit_log_records_operation(app):
    with app.app_context():
        models.log_audit(
            operation="CREATE",
            entity="entry",
            entity_id=1,
            packer_name="Maria",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.42",
        )
        log = models.get_recent_audit(limit=5)
        assert len(log) == 1
        assert log[0]["operation"] == "CREATE"
        assert log[0]["packer_name"] == "Maria"
```

- [ ] **Step 2: Run to verify all fail**

```bash
pytest tests/test_models.py -v
```

Expected: ImportError or AttributeError on `models`.

- [ ] **Step 3: Implement `models.py`**

```python
from datetime import date
from db import get_db


# ── Packers ──────────────────────────────────────────────────────────────────

def create_packer(name, arrival_date, departure_date,
                  tracking_start_date, tracking_end_date):
    db = get_db()
    cur = db.execute(
        """INSERT INTO packers
           (name, arrival_date, departure_date, tracking_start_date, tracking_end_date)
           VALUES (?, ?, ?, ?, ?)""",
        (name, str(arrival_date), str(departure_date),
         str(tracking_start_date), str(tracking_end_date)),
    )
    db.commit()
    return cur.lastrowid


def get_packer(packer_id):
    return get_db().execute(
        "SELECT * FROM packers WHERE id = ?", (packer_id,)
    ).fetchone()


def list_all_packers():
    return get_db().execute(
        "SELECT * FROM packers ORDER BY name"
    ).fetchall()


def list_active_packers():
    """Packers visible on the dashboard (not hidden)."""
    return get_db().execute(
        "SELECT * FROM packers WHERE hidden = 0 ORDER BY name"
    ).fetchall()


def update_packer(packer_id, name, arrival_date, departure_date,
                  tracking_start_date, tracking_end_date):
    db = get_db()
    db.execute(
        """UPDATE packers SET name=?, arrival_date=?, departure_date=?,
           tracking_start_date=?, tracking_end_date=?
           WHERE id=?""",
        (name, str(arrival_date), str(departure_date),
         str(tracking_start_date), str(tracking_end_date), packer_id),
    )
    db.commit()


def set_packer_locked(packer_id, locked: bool):
    db = get_db()
    db.execute("UPDATE packers SET locked=? WHERE id=?",
               (int(locked), packer_id))
    db.commit()


def set_packer_hidden(packer_id, hidden: bool):
    db = get_db()
    db.execute("UPDATE packers SET hidden=? WHERE id=?",
               (int(hidden), packer_id))
    db.commit()


def delete_packer(packer_id):
    db = get_db()
    db.execute("DELETE FROM work_entries WHERE packer_id=?", (packer_id,))
    db.execute("DELETE FROM packers WHERE id=?", (packer_id,))
    db.commit()


# ── Work Entries ──────────────────────────────────────────────────────────────

def create_work_entry(packer_id, entry_date, start_time,
                      end_time, duration_minutes, task_description):
    db = get_db()
    cur = db.execute(
        """INSERT INTO work_entries
           (packer_id, entry_date, start_time, end_time,
            duration_minutes, task_description)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (packer_id, str(entry_date), start_time, end_time,
         duration_minutes, task_description),
    )
    db.commit()
    return cur.lastrowid


def get_work_entry(entry_id):
    return get_db().execute(
        "SELECT * FROM work_entries WHERE id=?", (entry_id,)
    ).fetchone()


def get_entries_for_packer(packer_id):
    return get_db().execute(
        """SELECT * FROM work_entries WHERE packer_id=?
           ORDER BY entry_date, start_time""",
        (packer_id,),
    ).fetchall()


def update_work_entry(entry_id, entry_date, start_time,
                      end_time, duration_minutes, task_description):
    db = get_db()
    db.execute(
        """UPDATE work_entries SET entry_date=?, start_time=?, end_time=?,
           duration_minutes=?, task_description=? WHERE id=?""",
        (str(entry_date), start_time, end_time,
         duration_minutes, task_description, entry_id),
    )
    db.commit()


def delete_work_entry(entry_id):
    db = get_db()
    db.execute("DELETE FROM work_entries WHERE id=?", (entry_id,))
    db.commit()


# ── Audit Log ─────────────────────────────────────────────────────────────────

def log_audit(operation, entity, entity_id,
              packer_name=None, user_agent=None, ip_address=None):
    db = get_db()
    db.execute(
        """INSERT INTO audit_log
           (operation, entity, entity_id, packer_name, user_agent, ip_address)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (operation, entity, entity_id, packer_name, user_agent, ip_address),
    )
    db.commit()


def get_recent_audit(limit=50):
    return get_db().execute(
        "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_models.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add models.py tests/test_models.py
git commit -m "feat: data access layer — packers, work_entries, audit_log"
```

---

### Task 3: Balance calculation logic

This is the most important business logic. Test it exhaustively before wiring to routes.

**Files:**
- Create: `balance.py`
- Create: `tests/test_balance.py`

**Key formula:**
- Week N spans `tracking_start_date + (N-1)*7` to `tracking_start_date + N*7 - 1`
- `cumulative_balance` = hours worked in all **completed** weeks − (25 × completed_weeks)
- `adjusted_target_this_week` = max(0, 25 − cumulative_balance)
- Positive balance = ahead (surplus from past weeks)
- Negative balance = behind (deficit from past weeks)

- [ ] **Step 1: Write failing tests**

`tests/test_balance.py`:
```python
import pytest
from datetime import date
from balance import compute_balance, get_week_number, parse_entries_for_balance


# Helper: build fake entry list
def entry(d: date, minutes: int):
    return {"entry_date": d, "duration_minutes": minutes}


class TestWeekNumber:
    def test_day_1_is_week_1(self):
        start = date(2026, 6, 1)
        assert get_week_number(start, date(2026, 6, 1)) == 1

    def test_day_7_is_still_week_1(self):
        start = date(2026, 6, 1)
        assert get_week_number(start, date(2026, 6, 7)) == 1

    def test_day_8_is_week_2(self):
        start = date(2026, 6, 1)
        assert get_week_number(start, date(2026, 6, 8)) == 2

    def test_day_14_is_week_2(self):
        start = date(2026, 6, 1)
        assert get_week_number(start, date(2026, 6, 14)) == 2

    def test_day_15_is_week_3(self):
        start = date(2026, 6, 1)
        assert get_week_number(start, date(2026, 6, 15)) == 3


class TestBalance:
    def test_zero_hours_zero_balance(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Day 8 = week 2
        result = compute_balance([], start, today)
        assert result["completed_weeks"] == 1
        assert result["cumulative_balance"] == -25.0  # owed 25, worked 0
        assert result["adjusted_target_this_week"] == 50.0  # 25 + 25 catch-up

    def test_exactly_on_target_after_one_week(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Start of week 2
        entries = [entry(date(2026, 6, d), 300) for d in range(1, 6)]  # 5×5h = 25h
        result = compute_balance(entries, start, today)
        assert result["cumulative_balance"] == 0.0
        assert result["adjusted_target_this_week"] == 25.0

    def test_surplus_reduces_next_week_target(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Week 2, day 1
        # Worked 30h in week 1 (5h surplus)
        entries = [entry(date(2026, 6, d), 360) for d in range(1, 6)]  # 5×6h = 30h
        result = compute_balance(entries, start, today)
        assert result["cumulative_balance"] == 5.0
        assert result["adjusted_target_this_week"] == 20.0

    def test_deficit_increases_next_week_target(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)  # Week 2, day 1
        # Worked 20h in week 1 (5h deficit)
        entries = [entry(date(2026, 6, d), 240) for d in range(1, 6)]  # 5×4h = 20h
        result = compute_balance(entries, start, today)
        assert result["cumulative_balance"] == -5.0
        assert result["adjusted_target_this_week"] == 30.0

    def test_this_week_hours_counted_separately(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 10)  # Week 2, mid-week
        # Week 1: exactly 25h. Week 2 so far: 6h
        week1 = [entry(date(2026, 6, d), 300) for d in range(1, 6)]
        week2 = [entry(date(2026, 6, 9), 360)]  # 6h on day 9
        result = compute_balance(week1 + week2, start, today)
        assert result["cumulative_balance"] == 0.0      # week 1 was exactly 25
        assert result["this_week_hours"] == 6.0
        assert result["adjusted_target_this_week"] == 25.0
        assert result["this_week_remaining"] == 19.0

    def test_adjusted_target_never_goes_negative(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 8)
        # Worked 60h in week 1 (35h surplus — extreme case)
        entries = [entry(date(2026, 6, d), 720) for d in range(1, 6)]  # 5×12h
        result = compute_balance(entries, start, today)
        assert result["adjusted_target_this_week"] == 0.0

    def test_first_week_no_completed_weeks(self):
        start = date(2026, 6, 1)
        today = date(2026, 6, 5)  # Still in week 1
        entries = [entry(date(2026, 6, 3), 180)]  # 3h so far
        result = compute_balance(entries, start, today)
        assert result["completed_weeks"] == 0
        assert result["cumulative_balance"] == 0.0   # No completed weeks to evaluate
        assert result["this_week_hours"] == 3.0
        assert result["adjusted_target_this_week"] == 25.0


class TestParseEntries:
    def test_sqlite_row_dicts_converted(self):
        """parse_entries_for_balance converts SQLite Row objects to plain dicts."""
        # This is tested indirectly through model integration tests
        entries = [
            {"entry_date": "2026-06-03", "duration_minutes": 180},
        ]
        parsed = parse_entries_for_balance(entries)
        assert parsed[0]["entry_date"] == date(2026, 6, 3)
        assert parsed[0]["duration_minutes"] == 180
```

- [ ] **Step 2: Run to verify all fail**

```bash
pytest tests/test_balance.py -v
```

Expected: ImportError (balance.py doesn't exist yet).

- [ ] **Step 3: Implement `balance.py`**

```python
from datetime import date, timedelta


def get_week_number(tracking_start: date, target_date: date) -> int:
    """Return 1-based week number for target_date relative to tracking_start."""
    delta = (target_date - tracking_start).days
    return delta // 7 + 1


def get_week_boundaries(tracking_start: date, week_number: int) -> tuple:
    """Return (start_date, end_date) for the given 1-based week number."""
    start = tracking_start + timedelta(days=(week_number - 1) * 7)
    end = start + timedelta(days=6)
    return start, end


def parse_entries_for_balance(raw_entries) -> list:
    """Convert SQLite Row objects or string-date dicts to plain dicts with date objects."""
    result = []
    for e in raw_entries:
        d = e["entry_date"]
        if isinstance(d, str):
            d = date.fromisoformat(d)
        result.append({
            "entry_date": d,
            "duration_minutes": e["duration_minutes"],
        })
    return result


def compute_balance(entries: list, tracking_start: date, today: date) -> dict:
    """
    Compute hours balance for a packer.

    entries: list of dicts with 'entry_date' (date) and 'duration_minutes' (int).
             Use parse_entries_for_balance() to convert from SQLite rows.

    Returns:
        current_week (int)           — 1-based week containing today
        completed_weeks (int)        — weeks fully elapsed
        total_hours_worked (float)
        cumulative_balance (float)   — surplus/deficit from completed weeks only
                                       positive = ahead, negative = behind
        adjusted_target_this_week (float) — 25 adjusted by cumulative_balance
        this_week_hours (float)      — hours logged in the current week
        this_week_remaining (float)  — hours still needed this week
        hours_by_day (dict)          — {date_str: hours} for current week
    """
    current_week = get_week_number(tracking_start, today)
    completed_weeks = current_week - 1
    week_start, week_end = get_week_boundaries(tracking_start, current_week)

    total_minutes = 0
    this_week_minutes = 0
    hours_by_day: dict = {}

    for e in entries:
        total_minutes += e["duration_minutes"]
        if week_start <= e["entry_date"] <= week_end:
            this_week_minutes += e["duration_minutes"]
            day_str = str(e["entry_date"])
            hours_by_day[day_str] = hours_by_day.get(day_str, 0) + e["duration_minutes"] / 60

    total_hours = total_minutes / 60
    this_week_hours = this_week_minutes / 60
    completed_week_hours = total_hours - this_week_hours
    cumulative_balance = completed_week_hours - (25 * completed_weeks)
    adjusted_target = max(0.0, 25 - cumulative_balance)
    this_week_remaining = max(0.0, adjusted_target - this_week_hours)

    return {
        "current_week": current_week,
        "completed_weeks": completed_weeks,
        "total_hours_worked": round(total_hours, 2),
        "cumulative_balance": round(cumulative_balance, 2),
        "adjusted_target_this_week": round(adjusted_target, 2),
        "this_week_hours": round(this_week_hours, 2),
        "this_week_remaining": round(this_week_remaining, 2),
        "hours_by_day": {k: round(v, 2) for k, v in hours_by_day.items()},
        "week_start": str(week_start),
        "week_end": str(week_end),
    }
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_balance.py -v
```

Expected: All 11 tests pass.

- [ ] **Step 5: Commit**

```bash
git add balance.py tests/test_balance.py
git commit -m "feat: balance calculation — week detection, surplus/deficit carryover"
```

---

## Chunk 2: Routes — dashboard, logging, admin, API

### Task 4: Admin routes — packer management

**Files:**
- Modify: `routes/admin.py`
- Modify: `tests/test_routes.py`

- [ ] **Step 1: Add admin route tests**

Add to `tests/test_routes.py`:
```python
from datetime import date
import models


def _make_packer(app, name="TestPacker"):
    with app.app_context():
        return models.create_packer(
            name, date(2026,6,1), date(2026,6,28),
            date(2026,6,1), date(2026,6,28)
        )


def test_admin_list(client):
    resp = client.get("/admin/")
    assert resp.status_code == 200


def test_admin_create_packer(client):
    resp = client.post("/admin/packers/new", data={
        "name": "Maria",
        "arrival_date": "2026-06-01",
        "departure_date": "2026-06-28",
        "tracking_start_date": "2026-06-02",
        "tracking_end_date": "2026-06-27",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Maria" in resp.data


def test_admin_lock_packer(client, app):
    pid = _make_packer(app)
    resp = client.post(f"/admin/packers/{pid}/lock", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        packer = models.get_packer(pid)
        assert packer["locked"] == 1


def test_admin_hide_packer(client, app):
    pid = _make_packer(app)
    resp = client.post(f"/admin/packers/{pid}/hide", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        packer = models.get_packer(pid)
        assert packer["hidden"] == 1
```

- [ ] **Step 2: Run to verify new tests fail**

```bash
pytest tests/test_routes.py::test_admin_list tests/test_routes.py::test_admin_create_packer -v
```

Expected: 404 or assertion errors.

- [ ] **Step 3: Implement `routes/admin.py`**

```python
from flask import Blueprint, render_template, redirect, url_for, request
from datetime import date
import models

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
def index():
    packers = models.list_all_packers()
    return render_template("admin_packers.html", packers=packers)


@bp.route("/packers/new", methods=["GET", "POST"])
def new_packer():
    if request.method == "POST":
        models.create_packer(
            name=request.form["name"],
            arrival_date=date.fromisoformat(request.form["arrival_date"]),
            departure_date=date.fromisoformat(request.form["departure_date"]),
            tracking_start_date=date.fromisoformat(request.form["tracking_start_date"]),
            tracking_end_date=date.fromisoformat(request.form["tracking_end_date"]),
        )
        return redirect(url_for("admin.index"))
    return render_template("admin_packer_form.html", packer=None)


@bp.route("/packers/<int:packer_id>/edit", methods=["GET", "POST"])
def edit_packer(packer_id):
    packer = models.get_packer(packer_id)
    if request.method == "POST":
        models.update_packer(
            packer_id=packer_id,
            name=request.form["name"],
            arrival_date=date.fromisoformat(request.form["arrival_date"]),
            departure_date=date.fromisoformat(request.form["departure_date"]),
            tracking_start_date=date.fromisoformat(request.form["tracking_start_date"]),
            tracking_end_date=date.fromisoformat(request.form["tracking_end_date"]),
        )
        return redirect(url_for("admin.index"))
    return render_template("admin_packer_form.html", packer=packer)


@bp.route("/packers/<int:packer_id>/lock", methods=["POST"])
def lock_packer(packer_id):
    packer = models.get_packer(packer_id)
    models.set_packer_locked(packer_id, not packer["locked"])
    return redirect(url_for("admin.index"))


@bp.route("/packers/<int:packer_id>/hide", methods=["POST"])
def hide_packer(packer_id):
    packer = models.get_packer(packer_id)
    models.set_packer_hidden(packer_id, not packer["hidden"])
    return redirect(url_for("admin.index"))


@bp.route("/packers/<int:packer_id>/delete", methods=["POST"])
def delete_packer(packer_id):
    models.delete_packer(packer_id)
    return redirect(url_for("admin.index"))
```

Note: admin routes render templates that don't exist yet. Tests use `follow_redirects=True` and check for name in response, which requires stub templates. Create minimal stubs:

`templates/admin_packers.html`:
```html
<!doctype html>
<html>
<body>
{% for p in packers %}<p>{{ p.name }}</p>{% endfor %}
<a href="{{ url_for('admin.new_packer') }}">Add packer</a>
</body>
</html>
```

`templates/admin_packer_form.html`:
```html
<!doctype html>
<html>
<body>
<form method="post">
  <input name="name" value="{{ packer.name if packer else '' }}">
  <input name="arrival_date" type="date" value="{{ packer.arrival_date if packer else '' }}">
  <input name="departure_date" type="date" value="{{ packer.departure_date if packer else '' }}">
  <input name="tracking_start_date" type="date" value="{{ packer.tracking_start_date if packer else '' }}">
  <input name="tracking_end_date" type="date" value="{{ packer.tracking_end_date if packer else '' }}">
  <button type="submit">Save</button>
</form>
</body>
</html>
```

- [ ] **Step 4: Run admin route tests**

```bash
pytest tests/test_routes.py -k "admin" -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add routes/admin.py templates/admin_packers.html templates/admin_packer_form.html tests/test_routes.py
git commit -m "feat: admin routes — packer CRUD, lock/hide toggles"
```

---

### Task 5: Log entry routes

**Files:**
- Modify: `routes/log.py`
- Modify: `tests/test_routes.py`

The log flow: `GET /log/` → pick packer → `GET /log/<id>` → form + today's entries → `POST /log/<id>` → save entry → redirect back.

Edit/delete operate on existing entries with audit logging.

- [ ] **Step 1: Add log route tests**

Add to `tests/test_routes.py`:
```python
def test_log_select_shows_active_packers(client, app):
    _make_packer(app, "Visible")
    resp = client.get("/log/")
    assert resp.status_code == 200
    assert b"Visible" in resp.data


def test_log_entry_form_get(client, app):
    pid = _make_packer(app)
    resp = client.get(f"/log/{pid}")
    assert resp.status_code == 200


def test_log_entry_submit_creates_entry(client, app):
    pid = _make_packer(app)
    resp = client.post(f"/log/{pid}", data={
        "entry_date": "2026-06-07",
        "start_time": "09:00",
        "end_time": "12:00",
        "task_description": "Weeding",
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        entries = models.get_entries_for_packer(pid)
        assert len(entries) == 1
        assert entries[0]["duration_minutes"] == 180
        assert entries[0]["task_description"] == "Weeding"


def test_log_entry_delete(client, app):
    pid = _make_packer(app)
    with app.app_context():
        eid = models.create_work_entry(pid, date(2026,6,7), "09:00", "10:00", 60, None)
    resp = client.post(f"/log/{pid}/entries/{eid}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert len(models.get_entries_for_packer(pid)) == 0
```

- [ ] **Step 2: Implement `routes/log.py`**

```python
from flask import Blueprint, render_template, redirect, url_for, request
from datetime import date, datetime
import models

bp = Blueprint("log", __name__, url_prefix="/log")


def _calc_duration(start_time: str, end_time: str) -> int:
    """Return duration in minutes between HH:MM strings."""
    fmt = "%H:%M"
    delta = datetime.strptime(end_time, fmt) - datetime.strptime(start_time, fmt)
    return int(delta.total_seconds() // 60)


def _audit_context():
    return {
        "user_agent": request.headers.get("User-Agent"),
        "ip_address": request.remote_addr,
    }


@bp.route("/")
def select():
    packers = models.list_active_packers()
    return render_template("log_select.html", packers=packers)


@bp.route("/<int:packer_id>", methods=["GET", "POST"])
def entry(packer_id):
    packer = models.get_packer(packer_id)
    if request.method == "POST":
        start = request.form["start_time"]
        end = request.form["end_time"]
        entry_id = models.create_work_entry(
            packer_id=packer_id,
            entry_date=date.fromisoformat(request.form["entry_date"]),
            start_time=start,
            end_time=end,
            duration_minutes=_calc_duration(start, end),
            task_description=request.form.get("task_description") or None,
        )
        models.log_audit(
            operation="CREATE", entity="entry", entity_id=entry_id,
            packer_name=packer["name"], **_audit_context(),
        )
        return redirect(url_for("log.entry", packer_id=packer_id))

    today = date.today()
    entries = models.get_entries_for_packer(packer_id)
    return render_template("log_entry.html", packer=packer,
                           entries=entries, today=str(today))


@bp.route("/<int:packer_id>/entries/<int:entry_id>/delete", methods=["POST"])
def delete_entry(packer_id, entry_id):
    packer = models.get_packer(packer_id)
    models.delete_work_entry(entry_id)
    models.log_audit(
        operation="DELETE", entity="entry", entity_id=entry_id,
        packer_name=packer["name"], **_audit_context(),
    )
    return redirect(url_for("log.entry", packer_id=packer_id))


@bp.route("/<int:packer_id>/entries/<int:entry_id>/edit", methods=["GET", "POST"])
def edit_entry(packer_id, entry_id):
    packer = models.get_packer(packer_id)
    entry_row = models.get_work_entry(entry_id)
    if request.method == "POST":
        start = request.form["start_time"]
        end = request.form["end_time"]
        models.update_work_entry(
            entry_id=entry_id,
            entry_date=date.fromisoformat(request.form["entry_date"]),
            start_time=start,
            end_time=end,
            duration_minutes=_calc_duration(start, end),
            task_description=request.form.get("task_description") or None,
        )
        models.log_audit(
            operation="UPDATE", entity="entry", entity_id=entry_id,
            packer_name=packer["name"], **_audit_context(),
        )
        return redirect(url_for("log.entry", packer_id=packer_id))
    return render_template("log_entry.html", packer=packer,
                           edit_entry=entry_row,
                           entries=models.get_entries_for_packer(packer_id),
                           today=str(date.today()))
```

Create stub template `templates/log_select.html`:
```html
<!doctype html><html><body>
{% for p in packers %}<a href="{{ url_for('log.entry', packer_id=p.id) }}">{{ p.name }}</a>{% endfor %}
</body></html>
```

Create stub template `templates/log_entry.html`:
```html
<!doctype html><html><body>
<h1>{{ packer.name }}</h1>
<form method="post">
  <input name="entry_date" type="date" value="{{ today }}">
  <input name="start_time" type="time">
  <input name="end_time" type="time">
  <input name="task_description">
  <button type="submit">Log</button>
</form>
{% for e in entries %}
<p>{{ e.entry_date }} {{ e.start_time }}–{{ e.end_time }} {{ e.duration_minutes }}min
  <form method="post" action="{{ url_for('log.delete_entry', packer_id=packer.id, entry_id=e.id) }}" style="display:inline">
    <button>Delete</button>
  </form>
</p>
{% endfor %}
</body></html>
```

- [ ] **Step 3: Run log route tests**

```bash
pytest tests/test_routes.py -k "log" -v
```

Expected: 4 tests pass.

- [ ] **Step 4: Commit**

```bash
git add routes/log.py templates/log_select.html templates/log_entry.html tests/test_routes.py
git commit -m "feat: log entry routes — submit, edit, delete with audit logging"
```

---

### Task 6: Dashboard and JSON API routes

**Files:**
- Modify: `routes/dashboard.py`
- Modify: `routes/api.py`
- Modify: `tests/test_routes.py`

- [ ] **Step 1: Write API tests**

Add to `tests/test_routes.py`:
```python
def test_api_packer_stats(client, app):
    pid = _make_packer(app)
    with app.app_context():
        models.create_work_entry(pid, date(2026,6,1), "09:00", "12:00", 180, None)
    resp = client.get(f"/api/packer/{pid}/stats?today=2026-06-01")
    assert resp.status_code == 200
    data = resp.json
    assert "this_week_hours" in data
    assert "adjusted_target_this_week" in data
    assert "hours_by_day" in data
    assert data["this_week_hours"] == 3.0


def test_dashboard_shows_active_packers(client, app):
    _make_packer(app, "DashPacker")
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"DashPacker" in resp.data
```

- [ ] **Step 2: Implement `routes/api.py`**

```python
from flask import Blueprint, jsonify, request
from datetime import date
import models
from balance import compute_balance, parse_entries_for_balance

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/packer/<int:packer_id>/stats")
def packer_stats(packer_id):
    packer = models.get_packer(packer_id)
    today_param = request.args.get("today")
    today = date.fromisoformat(today_param) if today_param else date.today()

    raw_entries = models.get_entries_for_packer(packer_id)
    entries = parse_entries_for_balance(raw_entries)
    tracking_start = date.fromisoformat(packer["tracking_start_date"])

    balance = compute_balance(entries, tracking_start, today)
    return jsonify({
        "packer_id": packer_id,
        "packer_name": packer["name"],
        **balance,
    })
```

- [ ] **Step 3: Implement `routes/dashboard.py`**

```python
from flask import Blueprint, render_template
from datetime import date
import models
from balance import compute_balance, parse_entries_for_balance

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    packers = models.list_active_packers()
    today = date.today()

    packer_data = []
    for p in packers:
        raw = models.get_entries_for_packer(p["id"])
        entries = parse_entries_for_balance(raw)
        tracking_start = date.fromisoformat(p["tracking_start_date"])
        balance = compute_balance(entries, tracking_start, today)
        packer_data.append({"packer": p, "balance": balance})

    return render_template("dashboard.html", packer_data=packer_data, today=str(today))
```

Create stub template `templates/dashboard.html`:
```html
<!doctype html><html><body>
<h1>WorldPackers Dashboard</h1>
{% for item in packer_data %}
<div>
  <h2>{{ item.packer.name }}</h2>
  <p>This week: {{ item.balance.this_week_hours }}h / {{ item.balance.adjusted_target_this_week }}h target</p>
  <p>Balance: {{ item.balance.cumulative_balance }}h</p>
  <a href="{{ url_for('log.entry', packer_id=item.packer.id) }}">Log hours</a>
</div>
{% endfor %}
</body></html>
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add routes/dashboard.py routes/api.py templates/dashboard.html tests/test_routes.py
git commit -m "feat: dashboard and chart API routes with balance integration"
```

---

## Chunk 3: UI — Templates, Charts, Mobile Layout

### Task 7: Base layout + Tailwind + Chart.js

At this stage all functionality works — the templates are functional stubs. This task replaces them with a proper mobile-first UI.

**Files:**
- Create: `templates/base.html`
- Modify: All templates to extend base

- [ ] **Step 1: Create `templates/base.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}WorldPackers{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body class="bg-gray-50 text-gray-900 min-h-screen">
  <header class="bg-green-700 text-white px-4 py-3 flex items-center justify-between">
    <a href="{{ url_for('dashboard.index') }}" class="font-bold text-lg">🌍 WorldPackers</a>
    <nav class="flex gap-4 text-sm">
      <a href="{{ url_for('log.select') }}" class="hover:underline">Log Hours</a>
      <a href="{{ url_for('admin.index') }}" class="hover:underline">Admin</a>
    </nav>
  </header>
  <main class="max-w-2xl mx-auto px-4 py-6">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

- [ ] **Step 2: Rebuild `templates/dashboard.html` with charts**

```html
{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<h1 class="text-2xl font-bold mb-6">Hours Dashboard</h1>

{% if not packer_data %}
  <p class="text-gray-500">No active packers. <a href="{{ url_for('admin.new_packer') }}" class="text-green-700 underline">Add one</a>.</p>
{% endif %}

{% for item in packer_data %}
{% set b = item.balance %}
{% set packer = item.packer %}
<div class="bg-white rounded-2xl shadow p-5 mb-6" id="packer-{{ packer.id }}">
  <div class="flex items-center justify-between mb-3">
    <h2 class="text-xl font-semibold">{{ packer.name }}</h2>
    <span class="text-sm {% if b.cumulative_balance >= 0 %}text-green-600{% else %}text-red-500{% endif %} font-medium">
      {% if b.cumulative_balance >= 0 %}+{% endif %}{{ b.cumulative_balance }}h overall
    </span>
  </div>

  <div class="flex gap-6 items-center">
    <!-- Progress donut -->
    <div class="w-32 h-32 flex-shrink-0">
      <canvas id="donut-{{ packer.id }}"></canvas>
    </div>

    <!-- Stats -->
    <div class="flex-1 text-sm space-y-1">
      <p><span class="font-medium">{{ b.this_week_hours }}h</span> worked this week</p>
      <p>Target: <span class="font-medium">{{ b.adjusted_target_this_week }}h</span></p>
      <p class="{% if b.this_week_remaining == 0 %}text-green-600 font-semibold{% else %}text-gray-600{% endif %}">
        {% if b.this_week_remaining == 0 %}Week complete ✓
        {% else %}{{ b.this_week_remaining }}h remaining
        {% endif %}
      </p>
      <p class="text-gray-400">Week {{ b.current_week }}</p>
      <a href="{{ url_for('log.entry', packer_id=packer.id) }}"
         class="inline-block mt-2 bg-green-700 text-white text-xs px-3 py-1 rounded-full">
        Log hours →
      </a>
    </div>
  </div>

  <!-- Bar chart -->
  <div class="mt-4 h-28">
    <canvas id="bar-{{ packer.id }}"></canvas>
  </div>
</div>

<script>
(function() {
  const packerId = {{ packer.id }};
  fetch(`/api/packer/${packerId}/stats`)
    .then(r => r.json())
    .then(d => {
      // Donut
      const done = Math.min(d.this_week_hours, d.adjusted_target_this_week);
      const remaining = Math.max(0, d.adjusted_target_this_week - d.this_week_hours);
      new Chart(document.getElementById('donut-' + packerId), {
        type: 'doughnut',
        data: {
          datasets: [{
            data: [done, remaining],
            backgroundColor: ['#15803d', '#e5e7eb'],
            borderWidth: 0,
          }]
        },
        options: {
          cutout: '70%', plugins: { legend: { display: false } },
          responsive: true, maintainAspectRatio: true,
        }
      });

      // Bar chart — days of current week
      const weekStart = new Date(d.week_start);
      const labels = [];
      const values = [];
      for (let i = 0; i < 7; i++) {
        const day = new Date(weekStart);
        day.setDate(weekStart.getDate() + i);
        const key = day.toISOString().slice(0, 10);
        labels.push(['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][day.getDay()]);
        values.push(d.hours_by_day[key] || 0);
      }
      new Chart(document.getElementById('bar-' + packerId), {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            data: values,
            backgroundColor: '#16a34a',
            borderRadius: 4,
          }]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, ticks: { font: { size: 10 } } },
            x: { ticks: { font: { size: 10 } } }
          }
        }
      });
    });
})();
</script>
{% endfor %}
{% endblock %}
```

- [ ] **Step 3: Rebuild `templates/log_select.html`**

```html
{% extends "base.html" %}
{% block title %}Who are you?{% endblock %}
{% block content %}
<h1 class="text-2xl font-bold mb-6">Log Hours — Who are you?</h1>
{% if packers %}
  <ul class="space-y-3">
  {% for p in packers %}
    <li>
      <a href="{{ url_for('log.entry', packer_id=p.id) }}"
         class="block bg-white rounded-xl shadow px-5 py-4 text-lg font-medium hover:bg-green-50 transition">
        {{ p.name }}
      </a>
    </li>
  {% endfor %}
  </ul>
{% else %}
  <p class="text-gray-500">No active packers.</p>
{% endif %}
{% endblock %}
```

- [ ] **Step 4: Rebuild `templates/log_entry.html`**

```html
{% extends "base.html" %}
{% block title %}Log Hours — {{ packer.name }}{% endblock %}
{% block content %}
<div class="flex items-center justify-between mb-4">
  <h1 class="text-2xl font-bold">{{ packer.name }}</h1>
  <a href="{{ url_for('log.select') }}" class="text-sm text-gray-500 hover:underline">← Back</a>
</div>

<div class="bg-white rounded-2xl shadow p-5 mb-6">
  <h2 class="font-semibold mb-3">Log a Work Block</h2>
  <form method="post" class="space-y-3">
    <div>
      <label class="block text-sm text-gray-600 mb-1">Date</label>
      <input type="date" name="entry_date" value="{{ today }}" required
             class="w-full border rounded-lg px-3 py-2 text-sm">
    </div>
    <div class="flex gap-3">
      <div class="flex-1">
        <label class="block text-sm text-gray-600 mb-1">Start</label>
        <input type="time" name="start_time" required
               class="w-full border rounded-lg px-3 py-2 text-sm">
      </div>
      <div class="flex-1">
        <label class="block text-sm text-gray-600 mb-1">End</label>
        <input type="time" name="end_time" required
               class="w-full border rounded-lg px-3 py-2 text-sm">
      </div>
    </div>
    <div>
      <label class="block text-sm text-gray-600 mb-1">Task (optional)</label>
      <input type="text" name="task_description" placeholder="e.g. Garden, Cleaning"
             class="w-full border rounded-lg px-3 py-2 text-sm">
    </div>
    <button type="submit"
            class="w-full bg-green-700 text-white py-2 rounded-lg font-medium">
      Save Entry
    </button>
  </form>
</div>

{% if entries %}
<div class="bg-white rounded-2xl shadow p-5">
  <h2 class="font-semibold mb-3">All Entries</h2>
  <ul class="space-y-2 text-sm">
  {% for e in entries %}
  <li class="flex items-center justify-between border-b pb-2 last:border-0">
    <div>
      <span class="font-medium">{{ e.entry_date }}</span>
      <span class="text-gray-500 ml-2">{{ e.start_time }}–{{ e.end_time }}</span>
      <span class="text-green-700 ml-2">{{ "%.1f"|format(e.duration_minutes / 60) }}h</span>
      {% if e.task_description %}<span class="text-gray-400 ml-1">· {{ e.task_description }}</span>{% endif %}
    </div>
    <form method="post"
          action="{{ url_for('log.delete_entry', packer_id=packer.id, entry_id=e.id) }}"
          onsubmit="return confirm('Delete this entry?')">
      <button class="text-red-400 hover:text-red-600 text-xs">✕</button>
    </form>
  </li>
  {% endfor %}
  </ul>
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 5: Rebuild admin templates**

`templates/admin_packers.html`:
```html
{% extends "base.html" %}
{% block title %}Admin — Packers{% endblock %}
{% block content %}
<div class="flex justify-between items-center mb-6">
  <h1 class="text-2xl font-bold">Packer Management</h1>
  <a href="{{ url_for('admin.new_packer') }}"
     class="bg-green-700 text-white text-sm px-4 py-2 rounded-lg">+ Add Packer</a>
</div>

<div class="bg-white rounded-2xl shadow overflow-hidden">
<table class="w-full text-sm">
  <thead class="bg-gray-50 text-gray-500 uppercase text-xs">
    <tr>
      <th class="px-4 py-3 text-left">Name</th>
      <th class="px-4 py-3 text-left">Dates</th>
      <th class="px-4 py-3 text-left">Status</th>
      <th class="px-4 py-3 text-left">Actions</th>
    </tr>
  </thead>
  <tbody class="divide-y">
  {% for p in packers %}
  <tr class="{% if p.hidden %}opacity-50{% endif %}">
    <td class="px-4 py-3 font-medium">{{ p.name }}</td>
    <td class="px-4 py-3 text-gray-500 text-xs">
      {{ p.tracking_start_date }} → {{ p.tracking_end_date }}
    </td>
    <td class="px-4 py-3">
      {% if p.locked %}<span class="text-orange-500 text-xs font-medium">Locked</span>{% endif %}
      {% if p.hidden %}<span class="text-gray-400 text-xs font-medium ml-1">Hidden</span>{% endif %}
      {% if not p.locked and not p.hidden %}<span class="text-green-600 text-xs">Active</span>{% endif %}
    </td>
    <td class="px-4 py-3 flex gap-2">
      <a href="{{ url_for('admin.edit_packer', packer_id=p.id) }}"
         class="text-blue-600 text-xs hover:underline">Edit</a>
      <form method="post" action="{{ url_for('admin.lock_packer', packer_id=p.id) }}" class="inline">
        <button class="text-orange-500 text-xs hover:underline">
          {{ 'Unlock' if p.locked else 'Lock' }}
        </button>
      </form>
      <form method="post" action="{{ url_for('admin.hide_packer', packer_id=p.id) }}" class="inline">
        <button class="text-gray-500 text-xs hover:underline">
          {{ 'Show' if p.hidden else 'Hide' }}
        </button>
      </form>
    </td>
  </tr>
  {% endfor %}
  </tbody>
</table>
</div>
{% endblock %}
```

`templates/admin_packer_form.html`:
```html
{% extends "base.html" %}
{% block title %}{{ 'Edit' if packer else 'Add' }} Packer{% endblock %}
{% block content %}
<h1 class="text-2xl font-bold mb-6">{{ 'Edit' if packer else 'Add' }} Packer</h1>
<div class="bg-white rounded-2xl shadow p-5">
<form method="post" class="space-y-4">
  <div>
    <label class="block text-sm font-medium mb-1">Name</label>
    <input type="text" name="name" required value="{{ packer.name if packer else '' }}"
           class="w-full border rounded-lg px-3 py-2">
  </div>
  {% for field, label in [
      ('arrival_date','Arrival Date'),
      ('departure_date','Departure Date'),
      ('tracking_start_date','Tracking Start Date'),
      ('tracking_end_date','Tracking End Date')
  ] %}
  <div>
    <label class="block text-sm font-medium mb-1">{{ label }}</label>
    <input type="date" name="{{ field }}" required
           value="{{ packer[field] if packer else '' }}"
           class="w-full border rounded-lg px-3 py-2">
  </div>
  {% endfor %}
  <div class="flex gap-3 pt-2">
    <button type="submit" class="bg-green-700 text-white px-6 py-2 rounded-lg font-medium">
      Save
    </button>
    <a href="{{ url_for('admin.index') }}" class="px-6 py-2 text-gray-600 hover:underline">Cancel</a>
  </div>
</form>
</div>
{% endblock %}
```

- [ ] **Step 6: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests still pass (templates don't break routes).

- [ ] **Step 7: Commit**

```bash
git add templates/
git commit -m "feat: full Tailwind + Chart.js UI — dashboard, log entry, admin forms"
```

---

## Chunk 4: Server Setup — LaunchAgent + tmux

### Task 8: Start script and LaunchAgent

This follows the exact same pattern as `things-mcp`. The script is idempotent (checks for existing tmux session).

**Files:**
- Create: `~/config/bin/start-worldpackers.sh`
- Create: `~/Library/LaunchAgents/com.local.worldpackers-tracker.plist`

- [ ] **Step 1: Create `~/config/bin/start-worldpackers.sh`**

```bash
#!/bin/zsh
# Start WorldPackers Hours Tracker in a dedicated tmux session.
# Idempotent — does nothing if session already exists.

SESSION="worldpackers"
APP_DIR="$HOME/Developer/worldpackers-hours-tracker"
VENV="$APP_DIR/.venv/bin/python3"
LOG="$HOME/Library/Logs/worldpackers-tracker.log"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  exit 0
fi

tmux new-session -d -s "$SESSION" -x 220 -y 50
tmux send-keys -t "$SESSION" \
  "cd '$APP_DIR' && '$VENV' app.py >> '$LOG' 2>&1" Enter
```

```bash
chmod +x ~/config/bin/start-worldpackers.sh
```

- [ ] **Step 2: Test the start script manually**

```bash
~/config/bin/start-worldpackers.sh
tmux attach -t worldpackers
```

Expected: Flask server starts on port 5050. Detach with `Ctrl+B d`.

- [ ] **Step 3: Create `~/Library/LaunchAgents/com.local.worldpackers-tracker.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.local.worldpackers-tracker</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>/Users/soob/config/bin/start-worldpackers.sh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
  <key>StandardOutPath</key>
  <string>/Users/soob/Library/Logs/worldpackers-launchagent.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/soob/Library/Logs/worldpackers-launchagent.log</string>
</dict>
</plist>
```

- [ ] **Step 4: Load the LaunchAgent**

```bash
launchctl load ~/Library/LaunchAgents/com.local.worldpackers-tracker.plist
```

- [ ] **Step 5: Verify it's running**

```bash
tmux ls | grep worldpackers
curl http://localhost:5050/api/health
```

Expected: `{"status": "ok"}`.

- [ ] **Step 6: Commit start script and plist**

```bash
cd ~/config
git add bin/start-worldpackers.sh
git commit -m "feat: add worldpackers start script (LaunchAgent + tmux)"
```

Note: The LaunchAgent plist lives in `~/Library/LaunchAgents/` (not tracked in config repo — document in NOTES.md).

- [ ] **Step 7: Update `~/config/NOTES.md`** with restore steps for the LaunchAgent (same section as things-mcp).

---

## Final Checklist

- [ ] All pytest tests pass: `pytest tests/ -v`
- [ ] App starts: `python3 app.py` (or via tmux session)
- [ ] Dashboard loads on mobile browser at `http://<local-ip>:5050`
- [ ] Can add a packer via `/admin`
- [ ] Can log hours via `/log`
- [ ] Balance updates correctly after logging
- [ ] Chart.js progress ring and bar chart render
- [ ] LaunchAgent auto-starts on login
- [ ] NOTES.md updated with LaunchAgent restore steps

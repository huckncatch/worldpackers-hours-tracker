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

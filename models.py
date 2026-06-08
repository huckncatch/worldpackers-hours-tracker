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
    # audit_log rows are intentionally retained after packer deletion


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

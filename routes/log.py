from flask import Blueprint, render_template, redirect, url_for, request
from datetime import date, datetime, timedelta
import models

bp = Blueprint("log", __name__, url_prefix="/log")

def _time_options():
    """All 'HH:MM' 24h values in 15-minute increments, paired with a 12h display label."""
    options = []
    for total_minutes in range(0, 24 * 60, 15):
        h, m = divmod(total_minutes, 60)
        ampm = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        options.append((f"{h:02d}:{m:02d}", f"{h12}:{m:02d} {ampm}"))
    return options


TIME_OPTIONS = _time_options()


def _time_from_form(prefix: str) -> str:
    return request.form[f"{prefix}_time"]


def _picker_options():
    return {"time_options": TIME_OPTIONS}


def _date_slots(anchor=None, days=30):
    today = anchor or date.today()
    slots = []
    for i in range(days):
        d = today - timedelta(days=i)
        if i == 0:
            label = f"Today — {d.strftime('%b %-d')}"
        elif i == 1:
            label = f"Yesterday — {d.strftime('%b %-d')}"
        else:
            label = d.strftime('%A, %b %-d')
        slots.append((str(d), label))
    return slots


def _calc_duration(start_time: str, end_time: str) -> int:
    """Return duration in minutes between HH:MM strings. Raises ValueError if not positive."""
    fmt = "%H:%M"
    delta = datetime.strptime(end_time, fmt) - datetime.strptime(start_time, fmt)
    minutes = int(delta.total_seconds() // 60)
    if minutes <= 0:
        raise ValueError(f"end_time {end_time!r} must be after start_time {start_time!r}")
    return minutes


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
        start = _time_from_form("start")
        end = _time_from_form("end")
        try:
            duration = _calc_duration(start, end)
        except ValueError:
            entries = models.get_entries_for_packer(packer_id)
            return render_template("log_entry.html", packer=packer, entries=entries,
                                   date_slots=_date_slots(), **_picker_options(),
                                   error="End time must be after start time.")
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
                           entries=entries, date_slots=_date_slots(), **_picker_options())


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
        start = _time_from_form("start")
        end = _time_from_form("end")
        try:
            duration = _calc_duration(start, end)
        except ValueError:
            return render_template("log_entry.html", packer=packer, edit_entry=entry_row,
                                   entries=models.get_entries_for_packer(packer_id),
                                   date_slots=_date_slots(), **_picker_options(),
                                   error="End time must be after start time.")
        models.update_work_entry(
            entry_id=entry_id,
            entry_date=date.fromisoformat(request.form["entry_date"]),
            start_time=start,
            end_time=end,
            duration_minutes=duration,
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
                           date_slots=_date_slots(), **_picker_options())

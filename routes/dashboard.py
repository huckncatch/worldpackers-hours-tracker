from flask import Blueprint, render_template
from datetime import date
import models
from balance import compute_balance, parse_entries_for_balance, parse_excused_days

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    packers = models.list_active_packers()
    today = date.today()

    packer_data = []
    for p in packers:
        raw = models.get_entries_for_packer(p["id"])
        entries = parse_entries_for_balance(raw)
        excused_dates = parse_excused_days(models.get_excused_days_for_packer(p["id"]))
        tracking_start = date.fromisoformat(p["tracking_start_date"])
        balance = compute_balance(entries, tracking_start, today, excused_dates)
        packer_data.append({"packer": p, "balance": balance})

    return render_template("dashboard.html", packer_data=packer_data, today=str(today))

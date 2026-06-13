from flask import Blueprint, jsonify, request
from datetime import date
import models
from balance import compute_balance, parse_entries_for_balance, parse_excused_days

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/packer/<int:packer_id>/stats")
def packer_stats(packer_id):
    packer = models.get_packer(packer_id)
    if packer is None:
        return jsonify({"error": "not found"}), 404
    today_param = request.args.get("today")
    today = date.fromisoformat(today_param) if today_param else date.today()

    raw_entries = models.get_entries_for_packer(packer_id)
    entries = parse_entries_for_balance(raw_entries)
    excused_dates = parse_excused_days(models.get_excused_days_for_packer(packer_id))
    tracking_start = date.fromisoformat(packer["tracking_start_date"])

    balance = compute_balance(entries, tracking_start, today, excused_dates)
    return jsonify({
        "packer_id": packer_id,
        "packer_name": packer["name"],
        **balance,
    })

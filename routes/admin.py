import hmac
import logging
from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, request, session, current_app
from datetime import date
import models

bp = Blueprint("admin", __name__, url_prefix="/ops")


@bp.before_request
def require_auth():
    if request.endpoint == "admin.login":
        return
    if not session.get("ops_authed"):
        return redirect(url_for("admin.login", next=request.path))


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        submitted = request.form.get("password", "")
        expected = current_app.config["OPS_PASSWORD"]
        if hmac.compare_digest(submitted, expected):
            session["ops_authed"] = True
            next_url = request.form.get("next") or request.args.get("next") or "/ops"
            parsed = urlparse(next_url)
            if parsed.scheme or parsed.netloc or not next_url.startswith("/ops"):
                next_url = "/ops"
            return redirect(next_url)
        error = "Wrong password"
    next_val = request.args.get("next", "")
    return render_template("admin_login.html", error=error, next=next_val)


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


@bp.route("/excused-days")
def excused_days():
    days = models.list_all_excused_days()
    packers = models.list_all_packers()
    return render_template("admin_excused_days.html", days=days, packers=packers)


@bp.route("/excused-days/new", methods=["POST"])
def new_excused_day():
    packer_id = request.form.get("packer_id") or None
    models.create_excused_day(
        packer_id=int(packer_id) if packer_id else None,
        excused_date=date.fromisoformat(request.form["excused_date"]),
        reason=request.form.get("reason") or None,
    )
    return redirect(url_for("admin.excused_days"))


@bp.route("/excused-days/<int:excused_day_id>/delete", methods=["POST"])
def delete_excused_day(excused_day_id):
    models.delete_excused_day(excused_day_id)
    return redirect(url_for("admin.excused_days"))

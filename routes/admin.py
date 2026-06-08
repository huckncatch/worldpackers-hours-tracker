from flask import Blueprint, render_template, redirect, url_for, request
from datetime import date
import models

bp = Blueprint("admin", __name__, url_prefix="/ops")


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

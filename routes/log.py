from flask import Blueprint
bp = Blueprint("log", __name__, url_prefix="/log")

@bp.route("/")
def select():
    return "Log select coming soon", 200

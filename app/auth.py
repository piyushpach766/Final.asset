from functools import wraps

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return

    g.user = get_db().execute(
        "SELECT id, name, email, role FROM users WHERE id = ? AND is_active = 1", (user_id,)
    ).fetchone()


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = get_db().execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

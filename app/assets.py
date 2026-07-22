from sqlite3 import IntegrityError

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .auth import login_required
from .db import get_db
from .status_rules import VALID_STATUSES, assert_transition_allowed, normalize_status

bp = Blueprint("assets", __name__, url_prefix="/assets")


@bp.route("/")
@login_required
def index():
    db = get_db()
    status = request.args.get("status", "").strip()
    category = request.args.get("category", "").strip()

    query = ["SELECT * FROM assets WHERE is_active = 1"]
    params = []
    if status in VALID_STATUSES:
        query.append("AND status = ?")
        params.append(status)
    if category:
        query.append("AND category = ?")
        params.append(category)
    query.append("ORDER BY created_at DESC")

    assets = db.execute(" ".join(query), params).fetchall()
    categories = db.execute(
        "SELECT DISTINCT category FROM assets WHERE is_active = 1 ORDER BY category"
    ).fetchall()
    return render_template(
        "assets/index.html",
        assets=assets,
        categories=categories,
        statuses=VALID_STATUSES,
        selected_status=status,
        selected_category=category,
    )


@bp.route("/save", methods=("POST",))
@login_required
def save():
    db = get_db()
    asset_id = request.form.get("asset_id")
    status = normalize_status(request.form.get("status", "storage"))

    payload = {
        "asset_tag": request.form["asset_tag"].strip(),
        "serial_number": request.form["serial_number"].strip(),
        "category": request.form["category"].strip(),
        "model": request.form["model"].strip(),
        "purchase_date": request.form.get("purchase_date") or None,
        "purchase_value": request.form.get("purchase_value") or None,
        "status": status,
    }

    try:
        if asset_id:
            existing = db.execute("SELECT status FROM assets WHERE id = ?", (asset_id,)).fetchone()
            if existing is None:
                flash("Asset not found.", "danger")
                return redirect(url_for("assets.index"))
            assert_transition_allowed(existing["status"], status)
            db.execute(
                """
                UPDATE assets
                SET asset_tag = ?, serial_number = ?, category = ?, model = ?,
                    purchase_date = ?, purchase_value = ?, status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (*payload.values(), asset_id),
            )
            flash("Asset updated successfully.", "success")
        else:
            db.execute(
                """
                INSERT INTO assets
                    (asset_tag, serial_number, category, model, purchase_date, purchase_value, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(payload.values()),
            )
            flash("Asset created successfully.", "success")
        db.commit()
    except IntegrityError:
        flash("Asset tag or serial number already exists.", "danger")
    except ValueError as error:
        flash(str(error), "danger")

    return redirect(url_for("assets.index", status=request.args.get("status", ""), category=request.args.get("category", "")))


@bp.route("/<int:asset_id>")
@login_required
def detail(asset_id):
    db = get_db()
    asset = db.execute("SELECT * FROM assets WHERE id = ? AND is_active = 1", (asset_id,)).fetchone()
    if asset is None:
        flash("Asset not found.", "danger")
        return redirect(url_for("assets.index"))

    assignments = db.execute(
        """
        SELECT aa.*, e.name AS employee_name, d.name AS department_name, u.name AS assigned_by_name
        FROM asset_assignments aa
        LEFT JOIN employees e ON e.id = aa.employee_id
        LEFT JOIN departments d ON d.id = aa.department_id
        LEFT JOIN users u ON u.id = aa.assigned_by_user_id
        WHERE aa.asset_id = ?
        ORDER BY aa.assigned_date DESC, aa.id DESC
        """,
        (asset_id,),
    ).fetchall()
    maintenance_logs = db.execute(
        """
        SELECT *
        FROM maintenance_logs
        WHERE asset_id = ?
        ORDER BY sent_out_date DESC, id DESC
        """,
        (asset_id,),
    ).fetchall()
    current_assignment = next((row for row in assignments if row["returned_date"] is None), None)
    return render_template(
        "assets/detail.html",
        asset=asset,
        assignments=assignments,
        current_assignment=current_assignment,
        maintenance_logs=maintenance_logs,
        statuses=VALID_STATUSES,
    )


@bp.route("/<int:asset_id>/delete", methods=("POST",))
@login_required
def delete(asset_id):
    db = get_db()
    asset = db.execute("SELECT status FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if asset is None:
        flash("Asset not found.", "danger")
    else:
        db.execute(
            """
            UPDATE assets
            SET is_active = 0, deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (asset_id,),
        )
        db.commit()
        flash("Asset deleted safely.", "success")
    return redirect(url_for("assets.index"))

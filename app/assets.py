from sqlite3 import IntegrityError

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .auth import login_required
from .db import get_db
from .status_rules import VALID_STATUSES, assert_assignable, assert_transition_allowed, normalize_status

bp = Blueprint("assets", __name__, url_prefix="/assets")


def _get_asset_or_none(db, asset_id):
    return db.execute("SELECT * FROM assets WHERE id = ? AND is_active = 1", (asset_id,)).fetchone()


def _get_active_assignment(db, asset_id):
    return db.execute(
        """
        SELECT *
        FROM asset_assignments
        WHERE asset_id = ? AND returned_date IS NULL
        ORDER BY assigned_date DESC, id DESC
        LIMIT 1
        """,
        (asset_id,),
    ).fetchone()


def _resolve_assignment_target(form):
    employee_id = form.get("employee_id") or None
    department_id = form.get("department_id") or None
    if bool(employee_id) == bool(department_id):
        raise ValueError("Choose exactly one employee or department for the assignment.")
    return employee_id, department_id


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

    return redirect(
        url_for(
            "assets.index",
            status=request.args.get("status", ""),
            category=request.args.get("category", ""),
        )
    )


@bp.route("/<int:asset_id>")
@login_required
def detail(asset_id):
    db = get_db()
    asset = _get_asset_or_none(db, asset_id)
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
    active_employees = db.execute(
        """
        SELECT e.id, e.name, d.name AS department_name
        FROM employees e
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE e.is_active = 1
        ORDER BY e.name
        """
    ).fetchall()
    active_departments = db.execute(
        "SELECT id, name FROM departments WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    open_repair_log = next((row for row in maintenance_logs if row["returned_date"] is None), None)
    return render_template(
        "assets/detail.html",
        asset=asset,
        assignments=assignments,
        current_assignment=current_assignment,
        maintenance_logs=maintenance_logs,
        open_repair_log=open_repair_log,
        active_employees=active_employees,
        active_departments=active_departments,
        statuses=VALID_STATUSES,
    )


@bp.route("/<int:asset_id>/assign", methods=("POST",))
@login_required
def assign(asset_id):
    db = get_db()
    asset = _get_asset_or_none(db, asset_id)
    if asset is None:
        flash("Asset not found.", "danger")
        return redirect(url_for("assets.index"))

    try:
        assert_assignable(asset["status"])
        employee_id, department_id = _resolve_assignment_target(request.form)
        note = request.form.get("note", "").strip() or None
        with db:
            active_assignment = _get_active_assignment(db, asset_id)
            if active_assignment is not None:
                db.execute(
                    "UPDATE asset_assignments SET returned_date = CURRENT_DATE WHERE id = ?",
                    (active_assignment["id"],),
                )
            db.execute(
                """
                INSERT INTO asset_assignments
                    (asset_id, employee_id, department_id, assigned_date, returned_date, assigned_by_user_id, note)
                VALUES (?, ?, ?, CURRENT_DATE, NULL, ?, ?)
                """,
                (asset_id, employee_id, department_id, g.user["id"], note),
            )
            db.execute(
                """
                UPDATE assets
                SET status = 'in_use', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (asset_id,),
            )
        flash("Assignment saved successfully.", "success")
    except ValueError as error:
        flash(str(error), "danger")

    return redirect(url_for("assets.detail", asset_id=asset_id))


@bp.route("/<int:asset_id>/repair", methods=("POST",))
@login_required
def repair(asset_id):
    db = get_db()
    asset = _get_asset_or_none(db, asset_id)
    if asset is None:
        flash("Asset not found.", "danger")
        return redirect(url_for("assets.index"))

    try:
        if asset["status"] == "retired":
            raise ValueError("Retired assets cannot be sent for repair.")
        if asset["status"] == "in_repair":
            raise ValueError("This asset is already in repair.")

        issue_description = request.form["issue_description"].strip()
        vendor = request.form.get("vendor", "").strip() or None
        cost = request.form.get("cost") or None

        with db:
            active_assignment = _get_active_assignment(db, asset_id)
            if active_assignment is not None:
                db.execute(
                    "UPDATE asset_assignments SET returned_date = CURRENT_DATE WHERE id = ?",
                    (active_assignment["id"],),
                )
            db.execute(
                """
                INSERT INTO maintenance_logs
                    (asset_id, issue_description, sent_out_date, returned_date, vendor, cost)
                VALUES (?, ?, CURRENT_DATE, NULL, ?, ?)
                """,
                (asset_id, issue_description, vendor, cost),
            )
            db.execute(
                """
                UPDATE assets
                SET status = 'in_repair', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (asset_id,),
            )
        flash("Asset marked in repair.", "success")
    except ValueError as error:
        flash(str(error), "danger")

    return redirect(url_for("assets.detail", asset_id=asset_id))


@bp.route("/<int:asset_id>/maintenance/<int:log_id>/return", methods=("POST",))
@login_required
def return_from_repair(asset_id, log_id):
    db = get_db()
    asset = _get_asset_or_none(db, asset_id)
    if asset is None:
        flash("Asset not found.", "danger")
        return redirect(url_for("assets.index"))

    log = db.execute(
        "SELECT * FROM maintenance_logs WHERE id = ? AND asset_id = ?",
        (log_id, asset_id),
    ).fetchone()
    if log is None:
        flash("Repair record not found.", "danger")
        return redirect(url_for("assets.detail", asset_id=asset_id))
    if log["returned_date"] is not None:
        flash("Repair record is already closed.", "warning")
        return redirect(url_for("assets.detail", asset_id=asset_id))

    db.execute(
        """
        UPDATE maintenance_logs
        SET returned_date = CURRENT_DATE
        WHERE id = ?
        """,
        (log_id,),
    )
    db.execute(
        """
        UPDATE assets
        SET status = 'storage', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (asset_id,),
    )
    db.commit()
    flash("Asset returned from repair.", "success")
    return redirect(url_for("assets.detail", asset_id=asset_id))


@bp.route("/<int:asset_id>/retire", methods=("POST",))
@login_required
def retire(asset_id):
    db = get_db()
    asset = _get_asset_or_none(db, asset_id)
    if asset is None:
        flash("Asset not found.", "danger")
        return redirect(url_for("assets.index"))

    try:
        retirement_reason = request.form["retirement_reason"].strip()
        if not retirement_reason:
            raise ValueError("Retirement reason is required.")
        if asset["status"] == "retired":
            raise ValueError("This asset is already retired.")

        with db:
            active_assignment = _get_active_assignment(db, asset_id)
            if active_assignment is not None:
                db.execute(
                    "UPDATE asset_assignments SET returned_date = CURRENT_DATE WHERE id = ?",
                    (active_assignment["id"],),
                )
            open_repair_log = db.execute(
                """
                SELECT id
                FROM maintenance_logs
                WHERE asset_id = ? AND returned_date IS NULL
                ORDER BY sent_out_date DESC, id DESC
                LIMIT 1
                """,
                (asset_id,),
            ).fetchone()
            if open_repair_log is not None:
                db.execute(
                    "UPDATE maintenance_logs SET returned_date = CURRENT_DATE WHERE id = ?",
                    (open_repair_log["id"],),
                )
            db.execute(
                """
                UPDATE assets
                SET status = 'retired',
                    retirement_reason = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (retirement_reason, asset_id),
            )
        flash("Asset retired successfully.", "success")
    except ValueError as error:
        flash(str(error), "danger")

    return redirect(url_for("assets.detail", asset_id=asset_id))


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

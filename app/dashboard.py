from flask import Blueprint, render_template

from .auth import login_required
from .db import get_db

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    db = get_db()
    status_counts = db.execute(
        """
        SELECT status, COUNT(*) AS total
        FROM assets
        WHERE is_active = 1
        GROUP BY status
        ORDER BY status
        """
    ).fetchall()
    category_counts = db.execute(
        """
        SELECT category, COUNT(*) AS total
        FROM assets
        WHERE is_active = 1
        GROUP BY category
        ORDER BY category
        """
    ).fetchall()
    in_repair = db.execute(
        "SELECT * FROM assets WHERE is_active = 1 AND status = 'in_repair' ORDER BY updated_at DESC"
    ).fetchall()
    unassigned = db.execute(
        """
        SELECT a.*
        FROM assets a
        LEFT JOIN asset_assignments aa
            ON aa.asset_id = a.id AND aa.returned_date IS NULL
        WHERE a.is_active = 1
            AND a.status != 'retired'
            AND aa.id IS NULL
        ORDER BY a.created_at DESC
        """
    ).fetchall()
    recent_assignments = db.execute(
        """
        SELECT aa.*, a.asset_tag, a.model, e.name AS employee_name, d.name AS department_name
        FROM asset_assignments aa
        JOIN assets a ON a.id = aa.asset_id
        LEFT JOIN employees e ON e.id = aa.employee_id
        LEFT JOIN departments d ON d.id = aa.department_id
        WHERE a.is_active = 1
        ORDER BY aa.assigned_date DESC, aa.id DESC
        LIMIT 5
        """
    ).fetchall()
    return render_template(
        "dashboard/index.html",
        status_counts=status_counts,
        category_counts=category_counts,
        in_repair=in_repair,
        unassigned=unassigned,
        recent_assignments=recent_assignments,
    )

from sqlite3 import IntegrityError

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .auth import login_required
from .db import get_db

bp = Blueprint("directory", __name__)


@bp.route("/employees")
@login_required
def employees():
    db = get_db()
    employees = db.execute(
        """
        SELECT e.*, d.name AS department_name
        FROM employees e
        LEFT JOIN departments d ON d.id = e.department_id
        ORDER BY e.is_active DESC, e.name ASC
        """
    ).fetchall()
    departments = db.execute(
        "SELECT id, name FROM departments WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    return render_template(
        "directory/employees.html",
        employees=employees,
        departments=departments,
    )


@bp.route("/employees/save", methods=("POST",))
@login_required
def save_employee():
    db = get_db()
    employee_id = request.form.get("employee_id")
    payload = {
        "name": request.form["name"].strip(),
        "department_id": request.form.get("department_id") or None,
        "contact": request.form.get("contact", "").strip() or None,
        "is_active": 1 if request.form.get("is_active") else 0,
    }

    try:
        if employee_id:
            db.execute(
                """
                UPDATE employees
                SET name = ?, department_id = ?, contact = ?, is_active = ?
                WHERE id = ?
                """,
                (*payload.values(), employee_id),
            )
            flash("Employee updated successfully.", "success")
        else:
            db.execute(
                """
                INSERT INTO employees (name, department_id, contact, is_active)
                VALUES (?, ?, ?, ?)
                """,
                tuple(payload.values()),
            )
            flash("Employee created successfully.", "success")
        db.commit()
    except IntegrityError:
        flash("Unable to save employee.", "danger")

    return redirect(url_for("directory.employees"))


@bp.route("/employees/<int:employee_id>/delete", methods=("POST",))
@login_required
def delete_employee(employee_id):
    db = get_db()
    db.execute("UPDATE employees SET is_active = 0 WHERE id = ?", (employee_id,))
    db.commit()
    flash("Employee archived.", "success")
    return redirect(url_for("directory.employees"))


@bp.route("/departments")
@login_required
def departments():
    db = get_db()
    departments = db.execute(
        """
        SELECT d.*, COUNT(e.id) AS employee_count
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.id
        GROUP BY d.id
        ORDER BY d.is_active DESC, d.name ASC
        """
    ).fetchall()
    return render_template(
        "directory/departments.html",
        departments=departments,
    )


@bp.route("/departments/save", methods=("POST",))
@login_required
def save_department():
    db = get_db()
    department_id = request.form.get("department_id")
    payload = {
        "name": request.form["name"].strip(),
        "cost_center": request.form.get("cost_center", "").strip() or None,
        "is_active": 1 if request.form.get("is_active") else 0,
    }

    try:
        if department_id:
            db.execute(
                """
                UPDATE departments
                SET name = ?, cost_center = ?, is_active = ?
                WHERE id = ?
                """,
                (*payload.values(), department_id),
            )
            flash("Department updated successfully.", "success")
        else:
            db.execute(
                """
                INSERT INTO departments (name, cost_center, is_active)
                VALUES (?, ?, ?)
                """,
                tuple(payload.values()),
            )
            flash("Department created successfully.", "success")
        db.commit()
    except IntegrityError:
        flash("Department name already exists.", "danger")

    return redirect(url_for("directory.departments"))


@bp.route("/departments/<int:department_id>/delete", methods=("POST",))
@login_required
def delete_department(department_id):
    db = get_db()
    db.execute("UPDATE departments SET is_active = 0 WHERE id = ?", (department_id,))
    db.commit()
    flash("Department archived.", "success")
    return redirect(url_for("directory.departments"))

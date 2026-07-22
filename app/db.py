import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


def get_db():
    if "db" not in g:
        database_path = current_app.config["DATABASE"]
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    schema_path = Path(current_app.root_path) / "schema.sql"
    db.executescript(schema_path.read_text())
    seed_demo_data(db)
    db.commit()


def init_app(app):
    with app.app_context():
        init_db()


def seed_demo_data(db):
    user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count:
        return

    db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        ("Piyush Admin", "admin@example.com", generate_password_hash("admin123"), "admin"),
    )
    db.executemany(
        "INSERT INTO departments (name, cost_center) VALUES (?, ?)",
        [("IT", "CC-100"), ("Finance", "CC-200"), ("Operations", "CC-300")],
    )
    db.executemany(
        "INSERT INTO employees (name, department_id, contact, is_active) VALUES (?, ?, ?, 1)",
        [
            ("Aarav Sharma", 1, "aarav@example.com"),
            ("Neha Patel", 2, "neha@example.com"),
            ("Rohan Mehta", 3, "rohan@example.com"),
        ],
    )
    db.executemany(
        """
        INSERT INTO assets
            (asset_tag, serial_number, category, model, purchase_date, purchase_value, status, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """,
        [
            ("LAP-001", "SN-LAP-001", "Laptop", "Dell Latitude 5440", "2025-01-15", 78000, "in_use"),
            ("MON-002", "SN-MON-002", "Monitor", "LG 24MP400", "2025-02-05", 12500, "storage"),
            ("PHN-003", "SN-PHN-003", "Phone", "Samsung Galaxy A35", "2025-03-12", 32000, "in_repair"),
        ],
    )
    db.executemany(
        """
        INSERT INTO asset_assignments
            (asset_id, employee_id, department_id, assigned_date, returned_date, assigned_by_user_id, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, 1, 1, "2025-04-01", "2025-08-10", 1, "Initial laptop assignment"),
            (1, 2, 2, "2025-08-10", None, 1, "Reassigned after team transfer"),
            (3, 3, 3, "2025-06-12", None, 1, "Phone assigned before repair"),
        ],
    )
    db.execute(
        """
        INSERT INTO maintenance_logs
            (asset_id, issue_description, sent_out_date, returned_date, vendor, cost)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (3, "Screen replacement", "2025-09-01", None, "TechCare Repairs", 4500),
    )

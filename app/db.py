import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


def get_db():
    if "db" not in g:
        database_path = Path(current_app.config["DATABASE"])
        if not database_path.is_absolute():
            database_path = Path(current_app.instance_path) / database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
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
    apply_migrations(db)
    seed_demo_data(db)
    db.commit()


def init_app(app):
    with app.app_context():
        init_db()


def apply_migrations(db):
    migrations_dir = Path(current_app.root_path) / "migrations"
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    applied = {
        row["name"]
        for row in db.execute("SELECT name FROM schema_migrations ORDER BY name").fetchall()
    }
    if not migrations_dir.exists():
        return

    for migration_file in sorted(migrations_dir.glob("*.sql")):
        if migration_file.name in applied:
            continue
        db.executescript(migration_file.read_text(encoding="utf-8"))
        db.execute(
            "INSERT INTO schema_migrations (name) VALUES (?)",
            (migration_file.name,),
        )


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
            ("FUR-004", "SN-FUR-004", "Furniture", "Steelcase Chair", "2024-11-18", 18500, "retired"),
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
            (1, 2, 2, "2025-08-10", "2025-09-01", 1, "Reassigned after team transfer"),
            (1, 1, 1, "2025-09-11", None, 1, "Returned after repair and reassigned"),
            (3, 3, 3, "2025-06-12", "2025-09-01", 1, "Phone assigned before repair"),
            (4, 2, 2, "2025-01-08", "2025-11-01", 1, "Retired chair assignment history"),
        ],
    )
    db.execute(
        """
        INSERT INTO maintenance_logs
            (asset_id, issue_description, sent_out_date, returned_date, vendor, cost)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (1, "Battery replacement", "2025-09-01", "2025-09-10", "TechCare Repairs", 4500),
    )
    db.execute(
        """
        INSERT INTO maintenance_logs
            (asset_id, issue_description, sent_out_date, returned_date, vendor, cost)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (3, "Screen replacement", "2025-09-01", None, "TechCare Repairs", 4500),
    )
    db.execute(
        """
        UPDATE assets
        SET retirement_reason = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        ("Disposed after long service life", 4),
    )

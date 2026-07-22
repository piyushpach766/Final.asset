# Final Asset

Flask asset management capstone app for tracking assets, custody history, status rules, and dashboard reporting.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app run.py run
```

Open `http://127.0.0.1:5000`.

Demo login:

```text
Email: admin@example.com
Password: admin123
```

## Shared UI Standard

Theme palette:

- 60% background: `#f4f7fb`
- 30% surface/sidebar: `#101827`
- 10% accent: `#2563eb`

All app pages use:

- Persistent collapsible sidebar and header.
- Card container for module pages.
- Bootstrap Icons only.
- jQuery DataTables for list screens.
- One Add/Edit modal per object where practical.
- Confirmation before delete.
- Soft-delete for audit or relationship-important records.

## Piyush Issues Implemented

- #1 Flask app foundation.
- #3 Authentication and access control.
- #5 Asset CRUD workflows.
- #7 Filtered asset list and detail shell.
- #9 Asset custody history display.
- #11 Asset status transition rules.
- #12 Dashboard reporting widgets.

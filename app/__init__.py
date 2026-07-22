import os
from pathlib import Path
from secrets import token_hex

from flask import Flask

from . import assets, auth, dashboard, directory
from .db import close_db, init_app


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.from_mapping(
        DATABASE="asset_management.sqlite",
    )

    app.config.from_prefixed_env()
    if not app.config.get("SECRET_KEY"):
        secret_file = Path(app.instance_path) / "secret_key.txt"
        if secret_file.exists():
            app.config["SECRET_KEY"] = secret_file.read_text(encoding="utf-8").strip()
        else:
            secret_key = os.environ.get("SECRET_KEY") or token_hex(32)
            secret_file.write_text(secret_key, encoding="utf-8")
            app.config["SECRET_KEY"] = secret_key

    init_app(app)
    app.teardown_appcontext(close_db)

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(assets.bp)
    app.register_blueprint(directory.bp)

    return app

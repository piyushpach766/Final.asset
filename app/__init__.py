from flask import Flask

from . import assets, auth, dashboard
from .db import close_db, init_app


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev-change-me",
        DATABASE="asset_management.sqlite",
    )

    app.config.from_prefixed_env()

    init_app(app)
    app.teardown_appcontext(close_db)

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(assets.bp)

    return app

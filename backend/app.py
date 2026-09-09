import os
from pathlib import Path

from flask import Flask

from .extensions import db
from .routes.api import api, auth


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "development-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///transactions.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
        MERKLE_ANCHOR_PATH=os.environ.get("MERKLE_ANCHOR_PATH", "instance/merkle-anchor.json"),
        MERKLE_ANCHOR_SECRET=os.environ.get("MERKLE_ANCHOR_SECRET", "development-anchor-secret"),
    )
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    app.register_blueprint(auth)
    app.register_blueprint(api)
    with app.app_context():
        db.create_all()
    return app

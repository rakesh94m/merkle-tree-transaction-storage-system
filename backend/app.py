import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from backend.extensions import db
from backend.routes.api import api, auth

load_dotenv()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "development-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///transactions.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=os.environ.get("SESSION_COOKIE_SAMESITE", "Lax"),
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
        MERKLE_ANCHOR_PATH=os.environ.get("MERKLE_ANCHOR_PATH", "instance/merkle-anchor.json"),
        MERKLE_ANCHOR_SECRET=os.environ.get("MERKLE_ANCHOR_SECRET", "development-anchor-secret"),
        CORS_ORIGINS=[
            origin.strip()
            for origin in os.environ.get(
                "CORS_ORIGINS",
                "http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://127.0.0.1:8080",
            ).split(",")
            if origin.strip()
        ],
    )
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )
    app.register_blueprint(auth)
    app.register_blueprint(api)
    with app.app_context():
        db.create_all()
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))

import os
from pathlib import Path
from flask import Flask
from backend.db import init_db
from backend.routes.auth import auth_bp
from backend.routes.home import home_bp

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # ✅ caminho absoluto (sempre o mesmo Users.db)
    project_root = Path(__file__).resolve().parent.parent  # .../VENDRAME - NEW FRONTEND
    default_db = project_root / "database" / "Users.db"
    app.config["DATABASE"] = os.getenv("DATABASE_PATH", str(default_db))

    init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)

    return app

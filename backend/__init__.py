import os
from flask import Flask

from backend.db import init_db
from backend.routes.auth import auth_bp
from backend.routes.home import home_bp

# ✅ novo arquivo de rotas
from backend.routes.solicitacao_agendamento import sol_agendamento_bp

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["DATABASE"] = os.getenv("DATABASE_PATH", "database/Users.db")

    init_db(app)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(sol_agendamento_bp)

    return app

from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from backend.db import get_db
from datetime import timedelta

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        db = get_db()
        user = db.execute(
            'SELECT user, password, type, name, email FROM "user" WHERE user = ?',
            (username,)
        ).fetchone()

        if not user or (user["password"] or "") != password:
            erro = "Usuário ou senha não existem."
        else:
            remember = request.form.get("remember") == "on"
            session.permanent = remember
            if remember:
                current_app.permanent_session_lifetime = timedelta(days=15)

            session.clear()
            session["user"] = user["user"]
            session["type"] = user["type"]
            session["name"] = user["name"]
            session["email"] = user["email"]

            return redirect(url_for("home_router.dashboard"))

    return render_template("auth/login.html", erro=erro)


@auth_bp.route("/esqueci-senha", methods=["GET", "POST"])
def esqueci_senha():
    erro = None
    sucesso = None

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        new_password = (request.form.get("password") or "").strip()

        db = get_db()
        user = db.execute(
            'SELECT user FROM "user" WHERE user = ?',
            (username,)
        ).fetchone()

        if not user:
            erro = "Usuário não encontrado."
        else:
            db.execute(
                'UPDATE "user" SET password = ? WHERE user = ?',
                (new_password, username)
            )
            db.commit()
            sucesso = "Senha alterada com sucesso!"


    return render_template("auth/forgot_password.html", erro=erro, sucesso=sucesso)

from flask import Blueprint, render_template, session, redirect, url_for

home_admin_bp = Blueprint("home_admin", __name__)

def _is_logged():
    return session.get("user") is not None

def _tipo():
    return (session.get("type") or "").strip().lower()

@home_admin_bp.route("/home-admin", methods=["GET"])
def home_admin():
    if not _is_logged():
        return redirect(url_for("auth.login"))

    # ✅ só administrador
    if _tipo() != "administrador":
        return redirect(url_for("home_router.home"))

    return render_template(
        "home_admin.html",
        nome=session.get("name", "Administrador")
    )

@home_admin_bp.route("/controle-acessos", methods=["GET"])
def controle_acessos():
    if not _is_logged():
        return redirect(url_for("auth.login"))

    # ✅ só administrador
    if _tipo() != "administrador":
        return redirect(url_for("home_router.home"))

    return render_template("controle_usuarios.html")

@home_admin_bp.route("/solicitacoes-em-andamento-admin", methods=["GET"])
def solicitacoes_em_andamento_admin():
    if not _is_logged():
        return redirect(url_for("auth.login"))

    # ✅ só administrador
    if _tipo() != "administrador":
        return redirect(url_for("home_router.home"))

    return "<h1>Solicitações em andamento (em construção)</h1>"


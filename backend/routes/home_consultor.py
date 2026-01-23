from flask import Blueprint, render_template, session, redirect, url_for

home_consultor_bp = Blueprint("home_consultor", __name__)

def _is_logged():
    return session.get("user") is not None

def _tipo():
    return (session.get("type") or "").strip().lower()

@home_consultor_bp.route("/home-consultor", methods=["GET"])
def home_consultor():
    if not _is_logged():
        return redirect(url_for("auth.login"))

    # ✅ só consultor
    if _tipo() != "consultor":
        return redirect(url_for("home_router.home"))

    return render_template(
        "home_consultor.html",
        nome=session.get("name", "Consultor")
    )

@home_consultor_bp.route("/solicitacoes-em-andamento", methods=["GET"])
def solicitacoes_em_andamento():
    if not _is_logged():
        return redirect(url_for("auth.login"))

    # ✅ só consultor (recomendado manter)
    if _tipo() != "consultor":
        return redirect(url_for("home_router.home"))

    return "<h1>Solicitações em andamento (em construção)</h1>"

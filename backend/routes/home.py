from flask import Blueprint, render_template, session, redirect, url_for

home_cliente_bp = Blueprint("home_cliente", __name__)

def _is_logged():
    return "user" in session

def _tipo():
    return (session.get("type") or "").strip().lower()

@home_cliente_bp.route("/home-cliente")
def home_cliente():
    if not _is_logged():
        return redirect(url_for("auth.login"))

    # ✅ garante que só cliente abre a home normal
    if _tipo() != "cliente":
        return redirect(url_for("home_router.dashboard"))

    return render_template("home.html", nome=session.get("name", "Cliente"))

@home_cliente_bp.route("/nova-solicitacao")
def nova_solicitacao():
    if not _is_logged():
        return redirect(url_for("auth.login"))

    # (opcional) se quiser que só consultor possa criar solicitação, bloqueie:
    # if _tipo() != "consultor":
    #     return redirect(url_for("home_router.dashboard"))

    return render_template("tipos_solicitacao.html")

@home_cliente_bp.route("/confirmacao-comparecimento")
def confirmacao_comparecimento():
    if not _is_logged():
        return redirect(url_for("auth.login"))
    return "TODO: tela/form de confirmação"


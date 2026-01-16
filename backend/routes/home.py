from flask import Blueprint, render_template, session, redirect, url_for

home_bp = Blueprint("home", __name__)

@home_bp.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    return render_template("home.html", nome=session.get("name", "Usuário"))

@home_bp.route("/nova-solicitacao")
def nova_solicitacao():
    return render_template("tipos_solicitacao.html")


@home_bp.route("/confirmacao-comparecimento")
def confirmacao_comparecimento():
    return "TODO: tela/form de confirmação"


@home_bp.route("/minhas-solicitacoes")
def minhas_solicitacoes():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    return "<h1>Minhas Solicitações (em construção)</h1>"

# backend/routes/home_router.py
from flask import Blueprint, session, redirect, url_for

home_router_bp = Blueprint("home_router", __name__)

def _is_logged():
    return session.get("user") is not None

def _user_type():
    return (session.get("type") or "").strip().lower()

@home_router_bp.route("/dashboard", methods=["GET"])
def dashboard():
    if not _is_logged():
        return redirect(url_for("auth.login"))

    tipo = _user_type()

    if tipo == "consultor":
        return redirect(url_for("home_consultor.home_consultor"))

    if tipo == "cliente":
        return redirect(url_for("home_cliente.home_cliente"))
    
    if tipo == "administrador":
        return redirect(url_for("home_admin.home_admin"))


    # fallback seguro
    return redirect(url_for("auth.login"))

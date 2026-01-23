# backend/routes/users_admin.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from backend.db import get_db
from flask import Blueprint, session, redirect, url_for, jsonify

users_admin_bp = Blueprint("users_admin", __name__)

def _is_logged():
    return session.get("user") is not None

def _tipo():
    return (session.get("type") or "").strip().lower()

def _only_admin():
    """Garante que apenas administrador acesse."""
    if not _is_logged():
        return redirect(url_for("auth.login"))
    if _tipo() != "administrador":
        return redirect(url_for("home_router.dashboard"))
    return None

# ===========================
# TELA (GET)
# ===========================
@users_admin_bp.route("/controle-acessos", methods=["GET"])
def controle_acessos():
    guard = _only_admin()
    if guard:
        return guard

    return render_template("controle_usuarios.html")

# ===========================
# CRIAR USUÁRIO (POST)
# ===========================
@users_admin_bp.route("/controle-acessos/criar-usuario", methods=["POST"])
def criar_usuario():
    guard = _only_admin()
    if guard:
        return guard

    username = (request.form.get("user") or "").strip()
    password = (request.form.get("password") or "").strip()
    email = (request.form.get("email") or "").strip()
    name = (request.form.get("name") or "").strip()
    user_type = (request.form.get("type") or "").strip().lower()

    # validações mínimas
    if not username or not password or not user_type:
        flash("❌ Preencha Usuário, Senha e Tipo de Usuário.", "error")
        return redirect(url_for("users_admin.controle_acessos"))

    if user_type not in ("administrador", "consultor", "cliente"):
        flash("❌ Tipo de usuário inválido.", "error")
        return redirect(url_for("users_admin.controle_acessos"))

    db = get_db()

    # verifica se já existe
    existente = db.execute(
        'SELECT user FROM "user" WHERE user = ?',
        (username,)
    ).fetchone()

    if existente:
        flash("❌ Já existe um usuário com esse login.", "error")
        return redirect(url_for("users_admin.controle_acessos"))

    # insere
    db.execute(
        'INSERT INTO "user" (user, password, type, name, email) VALUES (?, ?, ?, ?, ?)',
        (username, password, user_type, name or None, email or None)
    )
    db.commit()

    flash("✅ Usuário criado com sucesso!", "success")
    return redirect(url_for("users_admin.controle_acessos"))

@users_admin_bp.route("/admin/usuarios/editar", methods=["POST"])
def editar_usuario():
    if not _is_logged():
        return redirect(url_for("auth.login"))
    if _tipo() != "administrador":
        return redirect(url_for("home_router.dashboard"))

    username = (request.form.get("user") or "").strip()
    new_password = (request.form.get("password") or "").strip()

    if not username or not new_password:
        flash("❌ Preencha Usuário e Nova Senha.", "error")
        return redirect(url_for("home_admin.controle_acessos"))

    db = get_db()

    existente = db.execute('SELECT user FROM "user" WHERE user = ?', (username,)).fetchone()
    if not existente:
        flash("❌ Usuário não encontrado.", "error")
        return redirect(url_for("home_admin.controle_acessos"))

    db.execute(
        'UPDATE "user" SET password = ? WHERE user = ?',
        (new_password, username),
    )
    db.commit()

    flash("✅ Senha atualizada com sucesso!", "success")
    return redirect(url_for("home_admin.controle_acessos"))


@users_admin_bp.route("/admin/usuarios/remover", methods=["POST"])
def remover_usuario():
    if not _is_logged():
        return redirect(url_for("auth.login"))
    if _tipo() != "administrador":
        return redirect(url_for("home_router.dashboard"))

    username = (request.form.get("user") or "").strip()
    if not username:
        flash("❌ Informe o usuário para remover.", "error")
        return redirect(url_for("home_admin.controle_acessos"))

    # (opcional, mas recomendado) impedir deletar a si mesmo
    usuario_logado = (session.get("user") or "").strip()
    if usuario_logado and username.lower() == usuario_logado.lower():
        flash("❌ Você não pode remover o usuário logado.", "error")
        return redirect(url_for("home_admin.controle_acessos"))

    db = get_db()

    existente = db.execute('SELECT user FROM "user" WHERE user = ?', (username,)).fetchone()
    if not existente:
        flash("❌ Usuário não encontrado.", "error")
        return redirect(url_for("home_admin.controle_acessos"))

    db.execute('DELETE FROM "user" WHERE user = ?', (username,))
    db.commit()

    flash("✅ Usuário removido com sucesso!", "success")
    return redirect(url_for("home_admin.controle_acessos"))

@users_admin_bp.route("/admin/usuarios/listar", methods=["GET"])
def listar_usuarios_json():
    if not _is_logged():
        return redirect(url_for("auth.login"))
    if _tipo() != "administrador":
        return redirect(url_for("home_router.dashboard"))

    db = get_db()
    rows = db.execute(
        'SELECT user, email, name, type FROM "user" ORDER BY user'
    ).fetchall()

    usuarios = []
    for r in rows:
        # se seu get_db já usa row_factory, r["user"] funciona.
        # se não, use índices: r[0], r[1], r[2], r[3]
        try:
            usuarios.append({
                "user": r["user"],
                "email": r["email"],
                "name": r["name"],
                "type": r["type"],
            })
        except TypeError:
            usuarios.append({
                "user": r[0],
                "email": r[1],
                "name": r[2],
                "type": r[3],
            })

    return jsonify(usuarios)
import os
import io
import mimetypes
import sqlite3
from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    current_app,
    send_from_directory,
    send_file,
    abort,
)

minhas_solicitacoes_bp = Blueprint("minhas_solicitacoes", __name__)

# =========================
# Helpers
# =========================
def _is_logged():
    return session.get("user") is not None


def _tipo():
    return (session.get("type") or "").strip().lower()


def _db_path():
    return os.path.abspath(current_app.config.get("DATABASE", "database/Users.db"))


def _get_db():
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _list_tables(db):
    rows = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return [r["name"] for r in rows]


def _table_columns(db, table_name):
    cols = db.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return [c["name"] for c in cols]


def _first_existing(col_list, candidates):
    for c in candidates:
        if c in col_list:
            return c
    return None


def _infer_tipo_exame(table_name, row, cols):
    if "tipo_exame" in cols:
        val = row["tipo_exame"]
        if val:
            return val

    mapa = {
        "solicitacoes_admissional": "Admissional",
        "solicitacoes_periodico": "Periódico",
        "solicitacoes_demissional": "Demissional",
        "solicitacoes_retorno_trabalho": "Retorno ao Trabalho",
        "solicitacoes_avaliacao_medica": "Avaliação Médica",
        "solicitacoes_mudanca_riscos": "Mudança de Riscos",
    }
    return mapa.get(table_name, table_name.replace("solicitacoes_", "").replace("_", " ").title())


def _safe_filename(name: str) -> bool:
    if not name:
        return False
    if "/" in name or "\\" in name:
        return False
    if ".." in name:
        return False
    return True


def _allowed_doc(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    allowed = {
        "pdf", "png", "jpg", "jpeg", "webp",
        "doc", "docx", "xls", "xlsx", "txt", "csv",
    }
    return ext in allowed


def _table_has_all_columns(cols, required_set):
    return required_set.issubset(set(cols))


def _doc_base_dirs():
    """
    Pastas base onde podem existir diretórios por protocolo.
    OBS: mantenho seus nomes "Documentos_Retorno", "Documentos_Avaliacao", "Documentos_Mudanca"
    conforme seu código atual.
    """
    dirs = []

    uploads_dir = os.path.abspath(current_app.config.get("UPLOADS_DIR", "uploads"))
    dirs.append(uploads_dir)

    defaults = [
        "database/Documentos_Admissional",
        "database/Documentos_Periodico",
        "database/Documentos_Demissional",
        "database/Documentos_Retorno",
        "database/Documentos_Avaliacao",
        "database/Documentos_Mudanca",
    ]
    for d in defaults:
        dirs.append(os.path.abspath(d))

    out = []
    seen = set()
    for d in dirs:
        if d and os.path.isdir(d) and d not in seen:
            out.append(d)
            seen.add(d)
    return out


def _resolve_doc_dir(protocolo: str, stored_name: str):
    if not protocolo or not stored_name:
        return None
    if not _safe_filename(protocolo) or not _safe_filename(stored_name):
        return None
    if not _allowed_doc(stored_name):
        return None

    for base in _doc_base_dirs():
        pasta_protocolo = os.path.join(base, protocolo)
        if not os.path.isdir(pasta_protocolo):
            continue
        full = os.path.join(pasta_protocolo, stored_name)
        if os.path.isfile(full):
            return pasta_protocolo
    return None


def _get_docs(db, protocolo):
    """
    Retorna lista de documentos do protocolo (pasta do protocolo e/ou tabela solicitacao_docs).
    Ajuste importante: dedupe case-insensitive e por stored_name.
    """
    documentos = []
    if not protocolo:
        return documentos

    tables = _list_tables(db)

    # Opção A: tabela de docs (se existir)
    if "solicitacao_docs" in tables:
        docs = db.execute(
            """
            SELECT filename, stored_name
            FROM solicitacao_docs
            WHERE protocolo = ?
            ORDER BY rowid DESC
            """,
            (protocolo,),
        ).fetchall()

        # dedupe por stored_name (case-insensitive)
        seen = set()
        for d in docs:
            stored = (d["stored_name"] or "").strip()
            fname = (d["filename"] or "").strip() or stored

            if not (_safe_filename(stored) and _allowed_doc(stored)):
                continue

            key = stored.casefold()
            if key in seen:
                continue
            seen.add(key)

            documentos.append({"filename": fname, "stored_name": stored})

        return documentos

    # Opção B: sem tabela -> lista arquivos em qualquer base_dir/<protocolo>/
    encontrados = set()  # case-insensitive
    for base in _doc_base_dirs():
        pasta_protocolo = os.path.join(base, protocolo)
        if not os.path.isdir(pasta_protocolo):
            continue

        for fname in sorted(os.listdir(pasta_protocolo)):
            full = os.path.join(pasta_protocolo, fname)
            if not os.path.isfile(full):
                continue
            if not _safe_filename(fname):
                continue
            if not _allowed_doc(fname):
                continue

            key = fname.casefold()
            if key in encontrados:
                continue

            encontrados.add(key)
            documentos.append({"filename": fname, "stored_name": fname})

    return documentos


def _doc_exists_in_list(docs, name_or_stored: str) -> bool:
    """
    Verifica se já existe na lista:
    - por stored_name
    - OU por filename
    (case-insensitive)
    """
    v = (name_or_stored or "").strip()
    if not v:
        return False

    vcf = v.casefold()
    for d in docs:
        stored = (d.get("stored_name") or "").strip().casefold()
        fname = (d.get("filename") or "").strip().casefold()
        if stored == vcf or fname == vcf:
            return True
    return False


def _is_owner(row, cpf_cliente: str, user_login: str) -> bool:
    """
    True se o registro pertence ao cliente (por cpf ou user).
    """
    row_cpf = (row["cpf"] or "").strip() if "cpf" in row.keys() else ""
    row_user = (row["user"] or "").strip() if "user" in row.keys() else ""

    if cpf_cliente and row_cpf and cpf_cliente == row_cpf:
        return True
    if user_login and row_user and user_login == row_user:
        return True
    return False


# =========================
# Routes
# =========================
@minhas_solicitacoes_bp.route("/minhas-solicitacoes", methods=["GET"])
def minhas_solicitacoes():
    if not _is_logged():
        return redirect(url_for("auth.login"))

    if _tipo() != "cliente":
        return redirect(url_for("home_router.dashboard"))

    cpf_cliente = (session.get("cpf") or "").strip()
    user_login = (session.get("user") or "").strip()

    db = _get_db()

    all_tables = _list_tables(db)
    tabelas_solic = [t for t in all_tables if t.startswith("solicitacoes_")]

    solicitacoes = []

    admissional_required = {
        "protocolo", "cnpj", "unidade", "empresa", "centro_custo", "codigo_rh",
        "data_preferencia", "local_agendar", "funcionario", "rg", "cpf",
        "nascimento", "admissao", "funcao", "setor",
    }

    for tabela in tabelas_solic:
        cols = _table_columns(db, tabela)

        if tabela == "solicitacoes_admissional":
            if not _table_has_all_columns(cols, admissional_required):
                continue

        col_protocolo = _first_existing(cols, ["protocolo", "protocol", "codigo", "id_protocolo"])
        col_status = _first_existing(cols, ["status_final", "status", "situacao"])
        col_cpf = _first_existing(cols, ["cpf", "cpf_cliente"])
        col_user = _first_existing(cols, ["user", "usuario", "login"])

        # ✅ NOVO: coluna resposta_consultor (se existir em qualquer tabela)
        col_resposta = _first_existing(cols, ["resposta_consultor"])

        if not col_protocolo:
            continue

        if cpf_cliente and col_cpf:
            where_sql = f'WHERE "{col_cpf}" = ?'
            params = (cpf_cliente,)
        elif user_login and col_user:
            where_sql = f'WHERE "{col_user}" = ?'
            params = (user_login,)
        else:
            continue

        col_data = _first_existing(cols, ["criado_em", "created_at", "data_criacao", "data", "timestamp"])
        order_sql = f'ORDER BY "{col_data}" DESC' if col_data else "ORDER BY rowid DESC"

        sql = f'SELECT * FROM "{tabela}" {where_sql} {order_sql}'
        rows = db.execute(sql, params).fetchall()

        def get_any(r, *names):
            for n in names:
                if n in cols:
                    return r[n]
            return None

        for r in rows:
            protocolo_raw = r[col_protocolo]
            protocolo = (str(protocolo_raw).strip() if protocolo_raw is not None else "")

            status = ""
            if col_status and r[col_status]:
                status = str(r[col_status]).strip()

            # documentos padrão (pasta do protocolo / solicitacao_docs)
            docs = _get_docs(db, protocolo)

            # ========= AVALIAÇÃO MÉDICA (arquivo em BLOB) =========
            am_forma_just = get_any(r, "forma_justificativa")
            am_just_texto = get_any(r, "justificativa_texto")
            am_nome_arquivo = get_any(r, "nome_arquivo")
            am_blob = get_any(r, "arquivo")
            tem_blob_am = bool(am_blob) and bool(am_nome_arquivo)

            if tabela == "solicitacoes_avaliacao_medica" and tem_blob_am:
                nome = str(am_nome_arquivo).strip()
                # evita duplicar se já existe na pasta (ou na lista)
                if nome and not _doc_exists_in_list(docs, nome):
                    docs.insert(0, {"filename": nome, "stored_name": "__avaliacao_db__"})

            # ========= RETORNO AO TRABALHO (arquivo em BLOB) =========
            rt_nome_arquivo = get_any(r, "nome_arquivo")
            rt_blob = get_any(r, "arquivo")
            tem_blob_rt = bool(rt_blob) and bool(rt_nome_arquivo)

            if tabela == "solicitacoes_retorno_trabalho" and tem_blob_rt:
                nome = str(rt_nome_arquivo).strip()
                # evita duplicar se já existe na pasta (ou na lista)
                if nome and not _doc_exists_in_list(docs, nome):
                    docs.insert(0, {"filename": nome, "stored_name": "__retorno_db__"})

            # ✅ NOVO: valor da resposta do consultor (se a coluna existir na tabela)
            resposta_consultor = "-"
            if col_resposta and (col_resposta in cols):
                val = r[col_resposta]
                if val is not None and str(val).strip():
                    resposta_consultor = str(val).strip()
                else:
                    resposta_consultor = "-"
            else:
                resposta_consultor = "-"

            item = {
                "protocolo": protocolo,
                "status": status,
                "tipo_exame": _infer_tipo_exame(tabela, r, cols),

                # ✅ NOVO (para exibir na tela do cliente)
                "resposta_consultor": resposta_consultor,

                # comuns
                "telefone": get_any(r, "telefone", "whatsapp", "celular"),
                "cpf": get_any(r, "cpf", "cpf_cliente"),
                "rg": get_any(r, "rg"),
                "empresa": get_any(r, "empresa"),
                "local_agendar": get_any(r, "local_agendar", "local", "endereco"),
                "funcionario": get_any(r, "funcionario", "colaborador"),
                "data_preferencia": get_any(r, "data_preferencia", "data", "data_agenda", "data_sugerida"),
                "profissional": get_any(r, "profissional", "medico", "consultor", "responsavel"),

                # admissional
                "cnpj": get_any(r, "cnpj"),
                "unidade": get_any(r, "unidade"),
                "centro_custo": get_any(r, "centro_custo"),
                "codigo_rh": get_any(r, "codigo_rh"),
                "nascimento": get_any(r, "nascimento"),
                "admissao": get_any(r, "admissao"),
                "funcao": get_any(r, "funcao"),
                "setor": get_any(r, "setor"),

                # avaliação médica
                "forma_justificativa": am_forma_just,
                "justificativa_texto": am_just_texto,
                "nome_arquivo": am_nome_arquivo,
                "tem_arquivo_db": tem_blob_am,

                # mudança de riscos
                "unidade_anterior": get_any(r, "unidade_anterior"),
                "setor_anterior": get_any(r, "setor_anterior"),
                "cargo_anterior": get_any(r, "cargo_anterior"),
                "unidade_atual": get_any(r, "unidade_atual"),
                "setor_atual": get_any(r, "setor_atual"),
                "cargo_atual": get_any(r, "cargo_atual"),

                # retorno ao trabalho
                "rt_nome_arquivo": rt_nome_arquivo,
                "tem_arquivo_retorno_db": tem_blob_rt,

                "documentos": docs,
                "_origem": tabela,
            }

            solicitacoes.append(item)

    db.close()

    tipos = sorted({(s.get("tipo_exame") or "").strip() for s in solicitacoes if s.get("tipo_exame")})
    protocolos = sorted({(s.get("protocolo") or "").strip() for s in solicitacoes if s.get("protocolo")})
    status_list = ["Em Aberto", "Finalizado", "Em Andamento", "Não Aprovado"]

    return render_template(
        "minhas_solicitacoes.html",
        solicitacoes=solicitacoes,
        tipos=tipos,
        protocolos=protocolos,
        status_list=status_list,
    )


@minhas_solicitacoes_bp.route("/documentos/<protocolo>/<stored_name>", methods=["GET"])
def baixar_documento(protocolo, stored_name):
    if not _is_logged():
        return redirect(url_for("auth.login"))
    if _tipo() != "cliente":
        return redirect(url_for("home_router.dashboard"))

    if not _safe_filename(protocolo) or not _safe_filename(stored_name):
        abort(400)

    pasta = _resolve_doc_dir(protocolo, stored_name)
    if not pasta:
        abort(404)

    return send_from_directory(pasta, stored_name, as_attachment=True)


@minhas_solicitacoes_bp.route("/documentos-avaliacao/<protocolo>", methods=["GET"])
def baixar_documento_avaliacao(protocolo):
    if not _is_logged():
        return redirect(url_for("auth.login"))
    if _tipo() != "cliente":
        return redirect(url_for("home_router.dashboard"))

    if not _safe_filename(protocolo):
        abort(400)

    cpf_cliente = (session.get("cpf") or "").strip()
    user_login = (session.get("user") or "").strip()

    db = _get_db()

    row = db.execute(
        """
        SELECT protocolo, cpf, user, nome_arquivo, arquivo
        FROM solicitacoes_avaliacao_medica
        WHERE protocolo = ?
        LIMIT 1
        """,
        (protocolo,),
    ).fetchone()

    if not row:
        db.close()
        abort(404)

    allowed = _is_owner(row, cpf_cliente, user_login)
    nome_arquivo = (row["nome_arquivo"] or "").strip()
    blob = row["arquivo"]

    db.close()

    if not allowed:
        abort(403)

    if not nome_arquivo or not blob:
        abort(404)

    mime, _ = mimetypes.guess_type(nome_arquivo)
    mime = mime or "application/octet-stream"

    return send_file(
        io.BytesIO(blob),
        mimetype=mime,
        as_attachment=True,
        download_name=nome_arquivo,
    )


@minhas_solicitacoes_bp.route("/documentos-retorno/<protocolo>", methods=["GET"])
def baixar_documento_retorno(protocolo):
    if not _is_logged():
        return redirect(url_for("auth.login"))
    if _tipo() != "cliente":
        return redirect(url_for("home_router.dashboard"))

    if not _safe_filename(protocolo):
        abort(400)

    cpf_cliente = (session.get("cpf") or "").strip()
    user_login = (session.get("user") or "").strip()

    db = _get_db()

    row = db.execute(
        """
        SELECT protocolo, cpf, user, nome_arquivo, arquivo
        FROM solicitacoes_retorno_trabalho
        WHERE protocolo = ?
        LIMIT 1
        """,
        (protocolo,),
    ).fetchone()

    if not row:
        db.close()
        abort(404)

    allowed = _is_owner(row, cpf_cliente, user_login)
    nome_arquivo = (row["nome_arquivo"] or "").strip()
    blob = row["arquivo"]

    db.close()

    if not allowed:
        abort(403)

    if not nome_arquivo or not blob:
        abort(404)

    mime, _ = mimetypes.guess_type(nome_arquivo)
    mime = mime or "application/octet-stream"

    return send_file(
        io.BytesIO(blob),
        mimetype=mime,
        as_attachment=True,
        download_name=nome_arquivo,
    )

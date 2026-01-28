# backend/routes/solicitacoes_consultor.py
import os
import io
import mimetypes
import sqlite3
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    current_app,
    request,
    jsonify,
    send_from_directory,
    send_file,
    abort,
)
from werkzeug.utils import secure_filename

solicitacoes_consultor_bp = Blueprint("solicitacoes_consultor", __name__)

# =========================================================
# Pasta por origem + salvar PDF final do consultor
# (✅ agora salva na PASTA REAL do protocolo, igual na criação)
# =========================================================
def _safe_join(base, *paths):
    """Evita path traversal. Garante que o caminho final fica dentro de base."""
    base = os.path.abspath(base)
    final = os.path.abspath(os.path.join(base, *paths))
    if not final.startswith(base + os.sep) and final != base:
        raise ValueError("unsafe_path")
    return final


def _base_dir_by_origem(origem: str) -> str:
    """
    Retorna a pasta base de documentos conforme a tabela/origem.

    ✅ Primeiro tenta pegar de current_app.config (para bater com suas pastas ABSOLUTAS do Windows).
    Se não existir, cai no fallback do projeto (database/Documentos_*).
    """
    origem = (origem or "").strip().lower()

    # ✅ se você configurar isso no app.config/.env, ele usa (recomendado)
    mapa_cfg = {
        "solicitacoes_admissional": "PASTA_ADMISSIONAL_BASE",
        "solicitacoes_periodico": "PASTA_PERIODICO_BASE",
        "solicitacoes_demissional": "PASTA_DEMISSIONAL_BASE",
        "solicitacoes_retorno_trabalho": "PASTA_RETORNO_BASE",
        "solicitacoes_avaliacao_medica": "PASTA_AVALIACAO_BASE",
        "solicitacoes_mudanca_riscos": "PASTA_MUDANCA_BASE",
    }
    cfg_key = mapa_cfg.get(origem)
    if cfg_key:
        cfg_val = current_app.config.get(cfg_key)
        if cfg_val:
            return os.path.abspath(cfg_val)

    # fallback relativo ao projeto
    mapa = {
        "solicitacoes_admissional": "database/Documentos_Admissional",
        "solicitacoes_periodico": "database/Documentos_Periodico",
        "solicitacoes_demissional": "database/Documentos_Demissional",
        "solicitacoes_retorno_trabalho": "database/Documentos_Retorno",
        "solicitacoes_avaliacao_medica": "database/Documentos_Avaliacao",
        "solicitacoes_mudanca_riscos": "database/Documentos_Mudanca",
    }

    base = mapa.get(origem)
    if base:
        return os.path.abspath(base)

    return os.path.abspath(current_app.config.get("UPLOADS_DIR", "uploads"))


def _find_existing_protocolo_dir(protocolo: str) -> str | None:
    """
    Procura uma pasta já existente do protocolo dentro de TODAS as bases conhecidas.
    ✅ Se achar, retorna o caminho dela (isso garante salvar na mesma pasta da criação).
    """
    if not protocolo or not _safe_filename(protocolo):
        return None

    for base in _doc_base_dirs():
        pasta = os.path.join(base, protocolo)
        if os.path.isdir(pasta):
            return pasta
    return None


def _save_consultor_pdf(protocolo: str, origem: str, file_storage):
    """
    Salva o PDF final do consultor.

    ✅ 1) Se já existir pasta do protocolo em alguma base, salva nela.
    ✅ 2) Se não existir, cria em base_dir_by_origem(origem)/<protocolo>/.

    Retorna (saved_dir, stored_name, original_name).
    """
    if not file_storage or not file_storage.filename:
        return None, None, None

    original_name = (file_storage.filename or "").strip()
    safe_name = secure_filename(original_name)
    if not safe_name:
        return None, None, None

    # só PDF
    if "." not in safe_name or safe_name.rsplit(".", 1)[-1].lower() != "pdf":
        return None, None, None

    # ✅ tenta salvar na pasta já existente do protocolo (pasta REAL)
    pasta_protocolo = _find_existing_protocolo_dir(protocolo)

    # ✅ se não existir, cria na base pela origem
    if not pasta_protocolo:
        base_dir = _base_dir_by_origem(origem)
        try:
            pasta_protocolo = _safe_join(base_dir, protocolo)
        except Exception:
            return None, None, None
        os.makedirs(pasta_protocolo, exist_ok=True)

    # evita sobrescrever: prefixo com timestamp
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stored_name = f"FINAL_{ts}_{safe_name}"

    full_path = os.path.join(pasta_protocolo, stored_name)
    file_storage.save(full_path)

    return pasta_protocolo, stored_name, original_name


# =========================
# Helpers (mesmo padrão)
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


def _status_slug(v: str) -> str:
    s = (v or "").strip().lower()
    s = (
        s.replace("á", "a").replace("à", "a").replace("â", "a").replace("ã", "a")
        .replace("é", "e").replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o").replace("ô", "o").replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )
    return s.replace(" ", "-")


def _to_ts(value):
    """
    Converte valores de data/tempo comuns do SQLite para timestamp (int).
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value)

    if isinstance(value, (datetime,)):
        return int(value.timestamp())

    s = str(value).strip()
    if not s:
        return None

    try:
        if len(s) == 10:
            dt = datetime.strptime(s, "%Y-%m-%d")
            return int(dt.timestamp())
        dt = datetime.fromisoformat(s)
        return int(dt.timestamp())
    except Exception:
        return None


# =========================
# Documentos (mesmo padrão do cliente)
# =========================
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


def _doc_base_dirs():
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


def _doc_exists_in_list(docs, name_or_stored: str) -> bool:
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


def _get_docs(db, protocolo):
    documentos = []
    if not protocolo:
        return documentos

    tables = _list_tables(db)

    # Opção A: tabela de docs
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

    # Opção B: pasta base/<protocolo>/
    encontrados = set()
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


# =========================
# API: atualizar status (DB)
# =========================
_ALLOWED_STATUS = {"Em Aberto", "Em Andamento", "Finalizado", "Não Aprovado"}


def _is_allowed_table(name: str) -> bool:
    name = (name or "").strip()
    return bool(name) and name.startswith("solicitacoes_")


@solicitacoes_consultor_bp.route("/api/solicitacoes/status", methods=["POST"])
def api_atualizar_status():
    if not _is_logged():
        return jsonify({"ok": False, "error": "not_logged"}), 401

    if _tipo() != "consultor":
        return jsonify({"ok": False, "error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}

    protocolo = (data.get("protocolo") or "").strip()
    origem = (data.get("origem") or "").strip()
    novo_status = (data.get("status") or "").strip()

    if not protocolo or not origem or not novo_status:
        return jsonify({"ok": False, "error": "missing_fields"}), 400

    if novo_status not in _ALLOWED_STATUS:
        return jsonify({"ok": False, "error": "invalid_status"}), 400

    if not _is_allowed_table(origem):
        return jsonify({"ok": False, "error": "invalid_table"}), 400

    db = _get_db()

    tables = _list_tables(db)
    if origem not in tables:
        db.close()
        return jsonify({"ok": False, "error": "table_not_found"}), 404

    cols = _table_columns(db, origem)
    col_protocolo = _first_existing(cols, ["protocolo", "protocol", "codigo", "id_protocolo"])
    col_status = _first_existing(cols, ["status_final", "status", "situacao"])

    if not col_protocolo or not col_status:
        db.close()
        return jsonify({"ok": False, "error": "missing_columns"}), 400

    sql = f'UPDATE "{origem}" SET "{col_status}" = ? WHERE "{col_protocolo}" = ?'
    cur = db.execute(sql, (novo_status, protocolo))
    db.commit()
    updated = cur.rowcount or 0
    db.close()

    if updated == 0:
        return jsonify({"ok": False, "error": "protocolo_not_found"}), 404

    return jsonify({"ok": True, "status": novo_status, "status_slug": _status_slug(novo_status)}), 200


# =========================
# Downloads (consultor também pode baixar)
# =========================
@solicitacoes_consultor_bp.route("/consultor/documentos/<protocolo>/<stored_name>", methods=["GET"])
def consultor_baixar_documento(protocolo, stored_name):
    if not _is_logged():
        return redirect(url_for("auth.login"))
    if _tipo() != "consultor":
        return redirect(url_for("home_router.dashboard"))

    if not _safe_filename(protocolo) or not _safe_filename(stored_name):
        abort(400)

    pasta = _resolve_doc_dir(protocolo, stored_name)
    if not pasta:
        abort(404)

    return send_from_directory(pasta, stored_name, as_attachment=True)


@solicitacoes_consultor_bp.route("/consultor/documentos-avaliacao/<protocolo>", methods=["GET"])
def consultor_baixar_documento_avaliacao(protocolo):
    if not _is_logged():
        return redirect(url_for("auth.login"))
    if _tipo() != "consultor":
        return redirect(url_for("home_router.dashboard"))

    if not _safe_filename(protocolo):
        abort(400)

    db = _get_db()
    row = db.execute(
        """
        SELECT protocolo, nome_arquivo, arquivo
        FROM solicitacoes_avaliacao_medica
        WHERE protocolo = ?
        LIMIT 1
        """,
        (protocolo,),
    ).fetchone()
    db.close()

    if not row:
        abort(404)

    nome_arquivo = (row["nome_arquivo"] or "").strip()
    blob = row["arquivo"]

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


@solicitacoes_consultor_bp.route("/consultor/documentos-retorno/<protocolo>", methods=["GET"])
def consultor_baixar_documento_retorno(protocolo):
    if not _is_logged():
        return redirect(url_for("auth.login"))
    if _tipo() != "consultor":
        return redirect(url_for("home_router.dashboard"))

    if not _safe_filename(protocolo):
        abort(400)

    db = _get_db()
    row = db.execute(
        """
        SELECT protocolo, nome_arquivo, arquivo
        FROM solicitacoes_retorno_trabalho
        WHERE protocolo = ?
        LIMIT 1
        """,
        (protocolo,),
    ).fetchone()
    db.close()

    if not row:
        abort(404)

    nome_arquivo = (row["nome_arquivo"] or "").strip()
    blob = row["arquivo"]

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


# =========================
# Route (apenas consultor)
# =========================
@solicitacoes_consultor_bp.route("/solicitacoes-consultor", methods=["GET"])
def solicitacoes_consultor():
    if not _is_logged():
        return redirect(url_for("auth.login"))

    if _tipo() != "consultor":
        return redirect(url_for("home_router.dashboard"))

    db = _get_db()

    all_tables = _list_tables(db)
    tabelas_solic = [t for t in all_tables if t.startswith("solicitacoes_")]

    solicitacoes = []

    for tabela in tabelas_solic:
        cols = _table_columns(db, tabela)

        col_protocolo = _first_existing(cols, ["protocolo", "protocol", "codigo", "id_protocolo"])
        col_status = _first_existing(cols, ["status_final", "status", "situacao"])
        col_data = _first_existing(cols, ["criado_em", "created_at", "data_criacao", "data", "timestamp"])

        if not col_protocolo:
            continue

        order_sql = f'ORDER BY "{col_data}" ASC' if col_data else "ORDER BY rowid ASC"
        rows = db.execute(f'SELECT rowid AS _rid, * FROM "{tabela}" {order_sql}').fetchall()

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

            sort_value = None
            if col_data and (col_data in r.keys()):
                sort_value = _to_ts(r[col_data])
            if sort_value is None:
                sort_value = int(r["_rid"])

            docs = _get_docs(db, protocolo)

            am_forma_just = get_any(r, "forma_justificativa")
            am_just_texto = get_any(r, "justificativa_texto")
            am_nome_arquivo = get_any(r, "nome_arquivo")
            am_blob = get_any(r, "arquivo")
            tem_blob_am = bool(am_blob) and bool(am_nome_arquivo)

            if tabela == "solicitacoes_avaliacao_medica" and tem_blob_am:
                nome = str(am_nome_arquivo).strip()
                if nome and not _doc_exists_in_list(docs, nome):
                    docs.insert(0, {"filename": nome, "stored_name": "__avaliacao_db__"})

            rt_nome_arquivo = get_any(r, "nome_arquivo")
            rt_blob = get_any(r, "arquivo")
            tem_blob_rt = bool(rt_blob) and bool(rt_nome_arquivo)

            if tabela == "solicitacoes_retorno_trabalho" and tem_blob_rt:
                nome = str(rt_nome_arquivo).strip()
                if nome and not _doc_exists_in_list(docs, nome):
                    docs.insert(0, {"filename": nome, "stored_name": "__retorno_db__"})

            # ✅ pega a última resposta do consultor (se a coluna existir na tabela)
            resposta_consultor = get_any(r, "resposta_consultor")

            item = {
                "_sort_value": int(sort_value),

                "protocolo": protocolo,
                "status": status,
                "status_slug": _status_slug(status),
                "tipo_exame": _infer_tipo_exame(tabela, r, cols),

                "telefone": get_any(r, "telefone", "whatsapp", "celular"),
                "cpf": get_any(r, "cpf", "cpf_cliente"),
                "rg": get_any(r, "rg"),
                "empresa": get_any(r, "empresa"),
                "local_agendar": get_any(r, "local_agendar", "local", "endereco"),
                "funcionario": get_any(r, "funcionario", "colaborador"),
                "data_preferencia": get_any(r, "data_preferencia", "data", "data_agenda", "data_sugerida"),
                "profissional": get_any(r, "profissional", "medico", "consultor", "responsavel"),

                "cnpj": get_any(r, "cnpj"),
                "unidade": get_any(r, "unidade"),
                "centro_custo": get_any(r, "centro_custo"),
                "codigo_rh": get_any(r, "codigo_rh"),
                "nascimento": get_any(r, "nascimento"),
                "admissao": get_any(r, "admissao"),
                "funcao": get_any(r, "funcao"),
                "setor": get_any(r, "setor"),

                "forma_justificativa": am_forma_just,
                "justificativa_texto": am_just_texto,
                "nome_arquivo": am_nome_arquivo,
                "tem_arquivo_db": tem_blob_am,

                "unidade_anterior": get_any(r, "unidade_anterior"),
                "setor_anterior": get_any(r, "setor_anterior"),
                "cargo_anterior": get_any(r, "cargo_anterior"),
                "unidade_atual": get_any(r, "unidade_atual"),
                "setor_atual": get_any(r, "setor_atual"),
                "cargo_atual": get_any(r, "cargo_atual"),

                "rt_nome_arquivo": rt_nome_arquivo,
                "tem_arquivo_retorno_db": tem_blob_rt,

                "documentos": docs,
                "_origem": tabela,

                # ✅ NOVO: expõe para o template (qualquer tipo de exame)
                "resposta_consultor": resposta_consultor,
            }

            solicitacoes.append(item)

    db.close()

    solicitacoes.sort(key=lambda x: x.get("_sort_value", 10**18))
    for s in solicitacoes:
        s.pop("_sort_value", None)

    tipos = sorted({(s.get("tipo_exame") or "").strip() for s in solicitacoes if s.get("tipo_exame")})
    protocolos = sorted({(s.get("protocolo") or "").strip() for s in solicitacoes if s.get("protocolo")})

    return render_template(
        "solicitacoes_consultor.html",
        solicitacoes=solicitacoes,
        tipos=tipos,
        protocolos=protocolos,
    )


# =========================
# API: salvar avaliação do consultor (texto + PDF final)
# =========================
@solicitacoes_consultor_bp.route("/api/solicitacoes/finalizar", methods=["POST"])
def api_salvar_avaliacao_consultor():
    if not _is_logged():
        return jsonify({"ok": False, "error": "not_logged"}), 401
    if _tipo() != "consultor":
        return jsonify({"ok": False, "error": "forbidden"}), 403

    protocolo = (request.form.get("protocolo") or "").strip()
    origem = (request.form.get("origem") or "").strip()
    resposta = (request.form.get("resposta") or "").strip()
    arquivo = request.files.get("arquivo")  # PDF final

    if not protocolo or not origem or not resposta:
        return jsonify({"ok": False, "error": "missing_fields"}), 400

    if not _is_allowed_table(origem):
        return jsonify({"ok": False, "error": "invalid_table"}), 400

    if not _safe_filename(protocolo):
        return jsonify({"ok": False, "error": "invalid_protocolo"}), 400

    db = _get_db()

    tables = _list_tables(db)
    if origem not in tables:
        db.close()
        return jsonify({"ok": False, "error": "table_not_found"}), 404

    cols = _table_columns(db, origem)

    col_protocolo = _first_existing(cols, ["protocolo", "protocol", "codigo", "id_protocolo"])
    col_status = _first_existing(cols, ["status_final", "status", "situacao"])
    col_resposta = "resposta_consultor"

    if not col_protocolo or not col_status:
        db.close()
        return jsonify({"ok": False, "error": "missing_columns"}), 400

    if col_resposta not in cols:
        db.close()
        return jsonify({"ok": False, "error": "column_not_found"}), 400

    row = db.execute(
        f'SELECT "{col_status}" FROM "{origem}" WHERE "{col_protocolo}" = ?',
        (protocolo,),
    ).fetchone()

    if (not row) or ((row[col_status] or "").strip() != "Finalizado"):
        db.close()
        return jsonify({"ok": False, "error": "status_not_finalizado"}), 400

    db.execute(
        f'UPDATE "{origem}" SET "{col_resposta}" = ? WHERE "{col_protocolo}" = ?',
        (resposta, protocolo),
    )
    db.commit()

    saved_dir = stored_name = original_name = None
    if arquivo and arquivo.filename:
        saved_dir, stored_name, original_name = _save_consultor_pdf(protocolo, origem, arquivo)
        if not stored_name:
            db.close()
            return jsonify({"ok": False, "error": "invalid_pdf"}), 400

        if "solicitacao_docs" in tables:
            try:
                db.execute(
                    """
                    INSERT INTO solicitacao_docs (protocolo, filename, stored_name)
                    VALUES (?, ?, ?)
                    """,
                    (protocolo, original_name, stored_name),
                )
                db.commit()
            except Exception:
                pass

    db.close()

    return jsonify({
        "ok": True,
        "stored_name": stored_name,
        "filename": original_name,
    })

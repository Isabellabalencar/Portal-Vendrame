import os
import random
import sqlite3
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, session, redirect, url_for, request, current_app
import shutil


sol_agendamento_bp = Blueprint("sol_agendamento", __name__)

def _db_path():
    return current_app.config.get("DATABASE", "database/Users.db")

def _pasta_admissional_base():
    # você pode colocar isso no .env como PASTA_ADMISSIONAL=...
    return r"C:\Users\Isabella Alencar\Documents\GRUPO EBG\VENDRAME - NEW FRONTEND\database\Documentos_Admissional"

def _safe_join(base, *paths):
    """Evita path traversal. Garante que o caminho final está dentro do base."""
    base_abs = os.path.abspath(base)
    final_abs = os.path.abspath(os.path.join(base, *paths))
    if not final_abs.startswith(base_abs + os.sep):
        raise ValueError("Caminho inválido.")
    return final_abs

def _colunas_tabela(cursor, tabela: str) -> set[str]:
    cursor.execute(f'PRAGMA table_info("{tabela}")')
    return {row[1] for row in cursor.fetchall()}  # row[1] = nome da coluna


@sol_agendamento_bp.route("/admissional/excluir/<protocolo>", methods=["POST"])
def excluir_admissional(protocolo):
    if "user" not in session:
        return redirect(url_for("auth.login"))

    # (Opcional) validar permissões por tipo de usuário:
    # if session.get("type") != "administrador": ...

    try:
        conn = sqlite3.connect(_db_path())
        cur = conn.cursor()

        # garante que existe antes de deletar (e evita apagar pasta errada)
        cur.execute("SELECT id FROM solicitacoes_admissional WHERE protocolo = ?", (protocolo,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return redirect(url_for("home.home"))  # ou uma tela com mensagem

        # 1) apaga no banco
        cur.execute("DELETE FROM solicitacoes_admissional WHERE protocolo = ?", (protocolo,))
        conn.commit()
        conn.close()

        # 2) apaga pasta do protocolo
        pasta = _safe_join(_pasta_admissional_base(), protocolo)
        if os.path.exists(pasta):
            shutil.rmtree(pasta)  # apaga tudo dentro

    except Exception as e:
        # Aqui você pode logar o erro e mostrar msg amigável
        return f"Erro ao excluir: {e}", 500

    return redirect(url_for("home.home"))

@sol_agendamento_bp.route("/solicitacao-agendamento", methods=["GET", "POST"])
def solicitacao_agendamento():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    erro = None
    sucesso = None
    protocolo_gerado = None




    if request.method == "POST":
        # Dropdown
        tipo_exame = (request.form.get("tipo_exame") or "").strip()
        telefone = (request.form.get("telefone") or "").strip()

        # (se por enquanto você só quer salvar Admissional)
        if tipo_exame != "Admissional":
            erro = "Por enquanto, esta tela salva apenas solicitações do tipo Admissional."
            return render_template("solicitacao_agendamento.html", erro=erro)

        # Campos do Admissional
        cnpj = (request.form.get("cnpj") or "").strip()
        unidade = (request.form.get("unidade") or "").strip()
        empresa = (request.form.get("empresa") or "").strip()
        centro_custo = (request.form.get("centro_custo") or "").strip()  # opcional
        codigo_rh = (request.form.get("codigo_rh") or "").strip()
        data_preferencia = (request.form.get("data_preferencia") or "").strip()  # yyyy-mm-dd
        local_agendar = (request.form.get("local_agendar") or "").strip()

        funcionario = (request.form.get("funcionario") or "").strip()
        rg = (request.form.get("rg") or "").strip()
        cpf = (request.form.get("cpf") or "").strip()
        nascimento = (request.form.get("nascimento") or "").strip()  # yyyy-mm-dd
        admissao = (request.form.get("admissao") or "").strip()      # yyyy-mm-dd
        funcao = (request.form.get("funcao") or "").strip()
        setor = (request.form.get("setor") or "").strip()

        obrigatorios = [
            tipo_exame, telefone,
            cnpj, unidade, empresa, codigo_rh,
            data_preferencia, local_agendar,
            funcionario, rg, cpf,
            nascimento, admissao,
            funcao, setor
        ]

        if not all(obrigatorios):
            erro = "❌ Preencha todos os campos obrigatórios antes de enviar."
            return render_template("solicitacao_agendamento.html", erro=erro)

        # ✅ gera protocolo antes para poder criar pasta
        protocolo_gerado = f"VENDRAME{random.randint(0, 9999999999):010d}SP"
        usuario_logado = session.get("user", "N/A")

        pasta_destino = os.path.join(_pasta_admissional_base(), protocolo_gerado)
        os.makedirs(pasta_destino, exist_ok=True)

        # ✅ upload opcional (PDF)
        arquivo = request.files.get("anexo_pdf")  # <input name="anexo_pdf" type="file" />
        nome_arquivo = None
        arquivo_binario = None

        if arquivo and (arquivo.filename or "").strip():
            if not arquivo.filename.lower().endswith(".pdf"):
                erro = "❌ O anexo precisa ser um PDF."
                return render_template("solicitacao_agendamento.html", erro=erro)

            nome_arquivo = secure_filename(arquivo.filename)
            arquivo_binario = arquivo.read()

            # ✅ cria pasta e salva arquivo localmente
            pasta_destino = os.path.join(_pasta_admissional_base(), protocolo_gerado)
            os.makedirs(pasta_destino, exist_ok=True)

            caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)
            with open(caminho_arquivo, "wb") as f:
                f.write(arquivo_binario)

        try:
            conn = sqlite3.connect(_db_path())
            cursor = conn.cursor()

            # ✅ detecta colunas existentes (pra não quebrar se sua tabela ainda não tiver upload)
            cols = _colunas_tabela(cursor, "solicitacoes_admissional")
            tem_upload = ("nome_arquivo" in cols) and ("arquivo" in cols)

            if tem_upload:
                cursor.execute("""
                    INSERT INTO solicitacoes_admissional (
                        protocolo, cnpj, unidade, empresa, centro_custo, codigo_rh,
                        data_preferencia, local_agendar, funcionario, rg, cpf,
                        nascimento, admissao, funcao, setor, telefone, user,
                        nome_arquivo, arquivo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    protocolo_gerado,
                    cnpj, unidade, empresa, centro_custo, codigo_rh,
                    data_preferencia, local_agendar,
                    funcionario, rg, cpf,
                    nascimento, admissao,
                    funcao, setor,
                    telefone, usuario_logado,
                    nome_arquivo, arquivo_binario
                ))
            else:
                # tabela sem colunas de upload
                cursor.execute("""
                    INSERT INTO solicitacoes_admissional (
                        protocolo, cnpj, unidade, empresa, centro_custo, codigo_rh,
                        data_preferencia, local_agendar, funcionario, rg, cpf,
                        nascimento, admissao, funcao, setor, telefone, user
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    protocolo_gerado,
                    cnpj, unidade, empresa, centro_custo, codigo_rh,
                    data_preferencia, local_agendar,
                    funcionario, rg, cpf,
                    nascimento, admissao,
                    funcao, setor,
                    telefone, usuario_logado
                ))

            conn.commit()
            conn.close()

            sucesso = "✅ Solicitação Admissional enviada com sucesso!"

        except Exception as e:
            erro = f"Erro ao salvar solicitação: {e}"

    return render_template(
        "solicitacao_agendamento.html",
        erro=erro,
        sucesso=sucesso,
        protocolo=protocolo_gerado
    )


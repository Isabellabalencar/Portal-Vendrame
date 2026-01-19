import os
import random
import sqlite3
import shutil
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, session, redirect, url_for, request, current_app
from flask import flash

sol_agendamento_bp = Blueprint("sol_agendamento", __name__)


def _db_path():
    return os.path.abspath(current_app.config.get("DATABASE", "database/Users.db"))


def _pasta_admissional_base():
    return r"C:\Users\Isabella Alencar\Documents\GRUPO EBG\VENDRAME - NEW FRONTEND\database\Documentos_Admissional"


def _pasta_periodico_base():
    return r"C:\Users\Isabella Alencar\Documents\GRUPO EBG\VENDRAME - NEW FRONTEND\database\Documentos_Periodico"

def _pasta_demissional_base():
    return r"C:\Users\Isabella Alencar\Documents\GRUPO EBG\VENDRAME - NEW FRONTEND\database\Documentos_Demissional"

def _pasta_retorno_trabalho_base():
    return r"C:\Users\Isabella Alencar\Documents\GRUPO EBG\VENDRAME - NEW FRONTEND\database\Documentos_Retorno"

def _pasta_mudanca_riscos_base():
    return r"C:\Users\Isabella Alencar\Documents\GRUPO EBG\VENDRAME - NEW FRONTEND\database\Documentos_Mudanca"

def _pasta_avaliacao_medica_base():
    return r"C:\Users\Isabella Alencar\Documents\GRUPO EBG\VENDRAME - NEW FRONTEND\database\Documentos_Avaliacao"


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

    try:
        conn = sqlite3.connect(_db_path())
        cur = conn.cursor()

        cur.execute("SELECT id FROM solicitacoes_admissional WHERE protocolo = ?", (protocolo,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return redirect(url_for("home.home"))

        # ✅ apaga a pasta primeiro; se der erro, NÃO perde o registro no banco
        pasta = _safe_join(_pasta_admissional_base(), protocolo)
        if os.path.exists(pasta):
            shutil.rmtree(pasta)

        # ✅ depois apaga do banco
        cur.execute("DELETE FROM solicitacoes_admissional WHERE protocolo = ?", (protocolo,))
        conn.commit()
        conn.close()

    except Exception as e:
        return f"Erro ao excluir: {e}", 500

    return redirect(url_for("home.home"))


@sol_agendamento_bp.route("/solicitacao-agendamento", methods=["GET", "POST"])
def solicitacao_agendamento():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    erro = None
    sucesso = None
    protocolo_gerado = None
    tipo_exame_atual = "Admissional"  # default no GET

    if request.method == "POST":
        tipo_exame_raw = (request.form.get("tipo_exame") or "").strip()
        telefone = (request.form.get("telefone") or "").strip()

        tipo_exame_atual = tipo_exame_raw or "Admissional"
        tipo_exame_norm = tipo_exame_raw.casefold()

        if not tipo_exame_raw or not telefone:
            flash("❌ Preencha os campos obrigatórios antes de enviar.", "erro")
            return render_template(
                "solicitacao_agendamento.html",
                erro=erro,
                sucesso=None,
                protocolo=None,
                tipo_exame=tipo_exame_atual,
            )

        protocolo_gerado = f"VENDRAME{random.randint(0, 9999999999):010d}SP"
        usuario_logado = session.get("user", "N/A")

        try:
            # ==========================================================
            # ✅ ADMISSIONAL
            # ==========================================================
            if tipo_exame_norm == "admissional":
                cnpj = (request.form.get("a_cnpj") or request.form.get("cnpj") or "").strip()
                unidade = (request.form.get("a_unidade") or request.form.get("unidade") or "").strip()
                empresa = (request.form.get("a_empresa") or request.form.get("empresa") or "").strip()
                centro_custo = (request.form.get("a_centro_custo") or request.form.get("centro_custo") or "").strip()
                codigo_rh = (request.form.get("a_codigo_rh") or request.form.get("codigo_rh") or "").strip()
                data_preferencia = (request.form.get("a_data_preferencia") or request.form.get("data_preferencia") or "").strip()
                local_agendar = (request.form.get("a_local_agendar") or request.form.get("local_agendar") or "").strip()

                funcionario = (request.form.get("a_funcionario") or request.form.get("funcionario") or "").strip()
                rg = (request.form.get("a_rg") or request.form.get("rg") or "").strip()
                cpf = (request.form.get("a_cpf") or request.form.get("cpf") or "").strip()
                nascimento = (request.form.get("a_nascimento") or request.form.get("nascimento") or "").strip()
                admissao = (request.form.get("a_admissao") or request.form.get("admissao") or "").strip()
                funcao = (request.form.get("a_funcao") or request.form.get("funcao") or "").strip()
                setor = (request.form.get("a_setor") or request.form.get("setor") or "").strip()

                obrigatorios = [
                    telefone,
                    cnpj, unidade, empresa, codigo_rh,
                    data_preferencia, local_agendar,
                    funcionario, rg, cpf,
                    nascimento, admissao,
                    funcao, setor
                ]

                if not all(obrigatorios):
                    flash("❌ Preencha todos os campos obrigatórios do Admissional.", "erro")
                    return render_template(
                        "solicitacao_agendamento.html",
                        erro=erro,
                        sucesso=None,
                        protocolo=None,
                        tipo_exame=tipo_exame_atual,
                    )

                # ✅ cria pasta do processo (Admissional)
                pasta_destino = _safe_join(_pasta_admissional_base(), protocolo_gerado)
                os.makedirs(pasta_destino, exist_ok=True)

                # ✅ upload opcional (PDF) - se existir no seu HTML
                arquivo = request.files.get("anexo_pdf")  # <input name="anexo_pdf" type="file" />
                nome_arquivo = None
                arquivo_binario = None

                if arquivo and (arquivo.filename or "").strip():
                    if not arquivo.filename.lower().endswith(".pdf"):
                        flash("❌ O anexo precisa ser um PDF.", "erro")
                        return render_template(
                            "solicitacao_agendamento.html",
                            erro=erro,
                            sucesso=None,
                            protocolo=None,
                            tipo_exame=tipo_exame_atual,
                        )

                    nome_arquivo = secure_filename(arquivo.filename)
                    arquivo_binario = arquivo.read()

                    caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)
                    with open(caminho_arquivo, "wb") as f:
                        f.write(arquivo_binario)

                conn = sqlite3.connect(_db_path())
                cursor = conn.cursor()

                # ✅ compatível com tabela COM ou SEM colunas de upload
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

                flash("✅ Solicitação Admissional enviada com sucesso!", "success")

            # ==========================================================
            # ✅ PERIÓDICO
            # ==========================================================
            elif tipo_exame_norm == "periódico":
                # ✅ pega primeiro os names NOVOS (p_*) e, se não existir, cai nos antigos
                funcionario = (request.form.get("p_funcionario") or request.form.get("funcionario") or "").strip()
                cpf = (request.form.get("p_cpf") or request.form.get("cpf") or "").strip()
                empresa = (request.form.get("p_empresa") or request.form.get("empresa") or "").strip()

                # ✅ IMPORTANTE: NÃO sobrescrever depois. Só fallback se p_* vier vazio.
                local_agendar = (
                    request.form.get("p_local")
                    or request.form.get("local_agendar")
                    or request.form.get("local")
                    or ""
                ).strip()

                data_preferencia = (
                    request.form.get("p_data")
                    or request.form.get("data_preferencia_exame")
                    or request.form.get("data_exame")
                    or request.form.get("data_preferencia")
                    or ""
                ).strip()

                obrigatorios = [telefone, funcionario, cpf, empresa, local_agendar, data_preferencia]

                if not all(obrigatorios):
                    flash( "❌ Preencha todos os campos obrigatórios do Periódico.", "erro")
                    return render_template(
                        "solicitacao_agendamento.html",
                        erro=erro,
                        sucesso=None,
                        protocolo=None,
                        tipo_exame=tipo_exame_atual,
                    )

                # ✅ cria pasta do processo (Periódico)
                pasta_destino = _safe_join(_pasta_periodico_base(), protocolo_gerado)
                os.makedirs(pasta_destino, exist_ok=True)

                conn = sqlite3.connect(_db_path())
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO solicitacoes_periodico (
                        protocolo, funcionario, cpf, empresa,
                        local_agendar, data_preferencia, telefone, user
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    protocolo_gerado,
                    funcionario, cpf, empresa,
                    local_agendar, data_preferencia,
                    telefone, usuario_logado
                ))

                conn.commit()
                conn.close()

                flash("✅ Solicitação Periódico enviada com sucesso!", "success")

            # ==========================================================
            # ✅ DEMISSIONAL
            # ==========================================================
            elif tipo_exame_norm == "demissional":
                funcionario = (request.form.get("d_funcionario") or "").strip()
                cpf = (request.form.get("d_cpf") or "").strip()
                empresa = (request.form.get("d_empresa") or "").strip()
                local_agendar = (request.form.get("d_local") or "").strip()
                data_preferencia = (request.form.get("d_data") or "").strip()

                obrigatorios = [telefone, funcionario, cpf, empresa, local_agendar, data_preferencia]

                if not all(obrigatorios):
                    flash( "❌ Preencha todos os campos obrigatórios do Demissional.", "erro")
                    return render_template(
                        "solicitacao_agendamento.html",
                        erro=erro,
                        sucesso=None,
                        protocolo=None,
                        tipo_exame=tipo_exame_atual,
                    )

                # ✅ cria pasta do processo (Demissional) — pasta correta
                pasta_destino = _safe_join(_pasta_demissional_base(), protocolo_gerado)
                os.makedirs(pasta_destino, exist_ok=True)

                conn = sqlite3.connect(_db_path())
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO solicitacoes_demissional (
                        protocolo, funcionario, cpf, empresa,
                        local_agendar, data_preferencia, telefone, user
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    protocolo_gerado,
                    funcionario, cpf, empresa,
                    local_agendar, data_preferencia,
                    telefone, usuario_logado
                ))

                conn.commit()
                conn.close()

                flash("✅ Solicitação Demissional enviada com sucesso!", "success")

            # ==========================================================
            # ✅ RETORNO AO TRABALHO
            # ==========================================================
            elif tipo_exame_norm == "retorno ao trabalho":
                funcionario = (request.form.get("r_funcionario") or "").strip()
                cpf = (request.form.get("r_cpf") or "").strip()
                empresa = (request.form.get("r_empresa") or "").strip()
                local_agendar = (request.form.get("r_local") or "").strip()
                data_preferencia = (request.form.get("r_data") or "").strip()

                # arquivo obrigatório (PDF)
                arquivo = request.files.get("r_pdf")
                if not arquivo or not (arquivo.filename or "").strip():
                    flash("❌ Anexe o documento em PDF.", "erro")
                    return render_template(
                        "solicitacao_agendamento.html",
                        erro=erro,
                        sucesso=None,
                        protocolo=None,
                        tipo_exame=tipo_exame_atual,
                    )

                if not arquivo.filename.lower().endswith(".pdf"):
                    flash("❌ O anexo precisa ser um PDF.", "erro")
                    return render_template(
                        "solicitacao_agendamento.html",
                        erro=erro,
                        sucesso=None,
                        protocolo=None,
                        tipo_exame=tipo_exame_atual,
                    )

                obrigatorios = [telefone, funcionario, cpf, empresa, local_agendar, data_preferencia]
                if not all(obrigatorios):
                    flash( "❌ Preencha todos os campos obrigatórios do Retorno ao Trabalho.", "erro")
                    return render_template(
                        "solicitacao_agendamento.html",
                        erro=erro,
                        sucesso=None,
                        protocolo=None,
                        tipo_exame=tipo_exame_atual,
                    )

                # ✅ cria pasta do processo (Retorno ao Trabalho) — certifique-se de ter essa função no arquivo:
                # def _pasta_retorno_trabalho_base(): return r"...\Documentos_RetornoTrabalho"
                pasta_destino = _safe_join(_pasta_retorno_trabalho_base(), protocolo_gerado)
                os.makedirs(pasta_destino, exist_ok=True)

                # salva arquivo no disco + no banco
                nome_arquivo = secure_filename(arquivo.filename)
                arquivo_binario = arquivo.read()

                caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)
                with open(caminho_arquivo, "wb") as f:
                    f.write(arquivo_binario)

                conn = sqlite3.connect(_db_path())
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO solicitacoes_retorno_trabalho (
                        protocolo, funcionario, cpf, empresa,
                        local_agendar, data_preferencia, telefone, user,
                        nome_arquivo, arquivo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    protocolo_gerado,
                    funcionario, cpf, empresa,
                    local_agendar, data_preferencia,
                    telefone, usuario_logado,
                    nome_arquivo, arquivo_binario
                ))

                conn.commit()
                conn.close()

                flash("✅ Solicitação de Retorno ao Trabalho enviada com sucesso!", "success")

            # ==========================================================
            # ✅ MUDANÇA DE RISCOS OCUPACIONAIS
            # ==========================================================
            elif tipo_exame_norm == "mudança de riscos ocupacionais":
                funcionario = (request.form.get("m_funcionario") or "").strip()
                cpf = (request.form.get("m_cpf") or "").strip()
                empresa = (request.form.get("m_empresa") or "").strip()
                local_agendar = (request.form.get("m_local") or "").strip()
                data_preferencia = (request.form.get("m_data") or "").strip()

                unidade_anterior = (request.form.get("m_unidade_anterior") or "").strip()
                setor_anterior = (request.form.get("m_setor_anterior") or "").strip()
                cargo_anterior = (request.form.get("m_cargo_anterior") or "").strip()

                unidade_atual = (request.form.get("m_unidade_atual") or "").strip()
                setor_atual = (request.form.get("m_setor_atual") or "").strip()
                cargo_atual = (request.form.get("m_cargo_atual") or "").strip()

                obrigatorios = [
                    telefone, funcionario, cpf, empresa, local_agendar, data_preferencia,
                    unidade_anterior, setor_anterior, cargo_anterior,
                    unidade_atual, setor_atual, cargo_atual
                ]

                if not all(obrigatorios):
                    flash( "❌ Preencha todos os campos obrigatórios da Mudança de riscos ocupacionais.", "erro")
                    return render_template(
                        "solicitacao_agendamento.html",
                        erro=erro,
                        sucesso=None,
                        protocolo=None,
                        tipo_exame=tipo_exame_atual,
                    )

                # ✅ cria pasta do processo (Mudança de riscos) — certifique-se de ter essa função:
                # def _pasta_mudanca_riscos_base(): return r"...\Documentos_MudancaRiscos"
                pasta_destino = _safe_join(_pasta_mudanca_riscos_base(), protocolo_gerado)
                os.makedirs(pasta_destino, exist_ok=True)

                conn = sqlite3.connect(_db_path())
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO solicitacoes_mudanca_riscos (
                        protocolo, funcionario, cpf, empresa,
                        local_agendar, data_preferencia, telefone, user,
                        unidade_anterior, setor_anterior, cargo_anterior,
                        unidade_atual, setor_atual, cargo_atual
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    protocolo_gerado,
                    funcionario, cpf, empresa,
                    local_agendar, data_preferencia,
                    telefone, usuario_logado,
                    unidade_anterior, setor_anterior, cargo_anterior,
                    unidade_atual, setor_atual, cargo_atual
                ))

                conn.commit()
                conn.close()

                flash("✅ Solicitação de Mudança de riscos ocupacionais enviada com sucesso!", "success")

            elif tipo_exame_norm in ("avaliação médica", "avaliacao medica"):
                funcionario = (request.form.get("am_funcionario") or "").strip()
                cpf = (request.form.get("am_cpf") or "").strip()
                empresa = (request.form.get("am_empresa") or "").strip()
                local_agendar = (request.form.get("am_local") or "").strip()
                data_preferencia = (request.form.get("am_data") or "").strip()

                forma = (request.form.get("am_forma") or "").strip().casefold()  # "texto" | "pdf"

                obrigatorios_base = [telefone, funcionario, cpf, empresa, local_agendar, data_preferencia]
                if not all(obrigatorios_base):
                    msg = "❌ Preencha todos os campos obrigatórios da Avaliação médica."
                    flash(msg, "erro")
                    return render_template(
                        "solicitacao_agendamento.html",
                        erro=msg, sucesso=None, protocolo=None, tipo_exame=tipo_exame_atual
                    )

                if forma not in ("texto", "pdf"):
                    msg = "❌ Selecione como deseja justificar (Texto explicativo ou Anexo em PDF)."
                    flash(msg, "erro")
                    return render_template(
                        "solicitacao_agendamento.html",
                        erro=msg, sucesso=None, protocolo=None, tipo_exame=tipo_exame_atual
                    )

                justificativa_texto = None
                nome_arquivo = None
                arquivo_binario = None

                if forma == "texto":
                    justificativa_texto = (request.form.get("am_justificativa") or "").strip()
                    if not justificativa_texto:
                        msg = "❌ Preencha a justificativa (texto)."
                        flash(msg, "erro")
                        return render_template(
                            "solicitacao_agendamento.html",
                            erro=msg, sucesso=None, protocolo=None, tipo_exame=tipo_exame_atual
                        )
                    justificativa_texto = justificativa_texto[:300]

                else:  # pdf
                    arquivo = request.files.get("am_pdf")

                    if not arquivo or not (arquivo.filename or "").strip():
                        msg = "❌ Para 'Anexo em PDF', você precisa anexar um arquivo PDF."
                        flash(msg, "erro")
                        return render_template(
                            "solicitacao_agendamento.html",
                            erro=msg, sucesso=None, protocolo=None, tipo_exame=tipo_exame_atual
                        )

                    if not arquivo.filename.lower().endswith(".pdf"):
                        msg = "❌ O anexo precisa ser um PDF."
                        flash(msg, "erro")
                        return render_template(
                            "solicitacao_agendamento.html",
                            erro=msg, sucesso=None, protocolo=None, tipo_exame=tipo_exame_atual
                        )

                    nome_arquivo = secure_filename(arquivo.filename)
                    arquivo_binario = arquivo.read()

                # só cria pasta depois de validar tudo
                pasta_destino = _safe_join(_pasta_avaliacao_medica_base(), protocolo_gerado)
                os.makedirs(pasta_destino, exist_ok=True)

                if forma == "pdf":
                    caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)
                    with open(caminho_arquivo, "wb") as f:
                        f.write(arquivo_binario)

                conn = sqlite3.connect(_db_path())
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO solicitacoes_avaliacao_medica (
                        protocolo, funcionario, cpf, empresa,
                        local_agendar, data_preferencia, telefone, user,
                        forma_justificativa, justificativa_texto,
                        nome_arquivo, arquivo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    protocolo_gerado,
                    funcionario, cpf, empresa,
                    local_agendar, data_preferencia,
                    telefone, usuario_logado,
                    forma,
                    justificativa_texto,
                    nome_arquivo,
                    arquivo_binario
                ))
                conn.commit()
                conn.close()

                flash("✅ Solicitação de Avaliação médica enviada com sucesso!", "success")
                return redirect(url_for("sol_agendamento.solicitacao_agendamento"))



            else:
                erro = f"⚠️ Ainda não implementamos o salvamento para: {tipo_exame_norm}"
                protocolo_gerado = None

        except Exception as e:
            erro = f"Erro ao salvar solicitação: {e}"

    return render_template(
        "solicitacao_agendamento.html",
        erro=erro,
        sucesso=sucesso,
        protocolo=protocolo_gerado,
        tipo_exame=tipo_exame_atual
    )

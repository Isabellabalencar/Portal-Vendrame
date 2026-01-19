import os
import sqlite3

def main():
    # Caminho do banco (mesmo padrão do seu projeto)
    base_dir = os.path.dirname(__file__)              # .../database
    db_path = os.path.join(base_dir, "Users.db")      # .../database/Users.db

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitacoes_avaliacao_medica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocolo TEXT,

            funcionario TEXT,
            cpf TEXT,
            empresa TEXT,
            local_agendar TEXT,
            data_preferencia TEXT,
            telefone TEXT,
            user TEXT,

            -- escolha do usuário: texto ou pdf
            forma_justificativa TEXT,     -- 'texto' ou 'pdf'

            -- quando for texto
            justificativa_texto TEXT,

            -- quando for pdf
            nome_arquivo TEXT,
            arquivo BLOB,

            status_final TEXT DEFAULT 'Em Aberto'
        )
    """)

    conn.commit()
    conn.close()

    print("✅ Tabela 'solicitacoes_avaliacao_medica' criada/verificada com sucesso!")

if __name__ == "__main__":
    main()

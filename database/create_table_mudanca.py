import os
import sqlite3

def main():
    base_dir = os.path.dirname(__file__)
    db_path = os.path.join(base_dir, "Users.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitacoes_mudanca_riscos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocolo TEXT,
            funcionario TEXT,
            cpf TEXT,
            empresa TEXT,
            local_agendar TEXT,
            data_preferencia TEXT,
            telefone TEXT,
            user TEXT,

            unidade_anterior TEXT,
            setor_anterior TEXT,
            cargo_anterior TEXT,

            unidade_atual TEXT,
            setor_atual TEXT,
            cargo_atual TEXT,

            status_final TEXT DEFAULT 'Em Aberto'
        )
    """)

    conn.commit()
    conn.close()

    print("✅ Tabela 'solicitacoes_mudanca_riscos' criada/verificada com sucesso!")

if __name__ == "__main__":
    main()

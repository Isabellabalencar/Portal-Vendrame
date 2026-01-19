import os
import sqlite3

def main():
    # Caminho do banco (mesmo padrão do seu projeto)
    base_dir = os.path.dirname(__file__)              # .../database
    db_path = os.path.join(base_dir, "Users.db")      # .../database/Users.db

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitacoes_periodico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocolo TEXT,
            funcionario TEXT,
            cpf TEXT,
            empresa TEXT,
            local_agendar TEXT,
            data_preferencia TEXT,
            telefone TEXT,
            user TEXT,
            status_final TEXT DEFAULT 'Em Aberto'
        )
    """)

    conn.commit()
    conn.close()

    print("✅ Tabela 'solicitacoes_periodico' criada/verificada com sucesso!")

if __name__ == "__main__":
    main()

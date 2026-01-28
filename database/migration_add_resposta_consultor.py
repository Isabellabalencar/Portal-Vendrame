import sqlite3

DB_PATH = "database/Users.db"

TABLES = [
    "solicitacoes_admissional",
    "solicitacoes_avaliacao_medica",
    "solicitacoes_demissional",
    "solicitacoes_mudanca_riscos",
    "solicitacoes_periodico",
    "solicitacoes_retorno_trabalho",
]

NEW_COL = "resposta_consultor"

def has_column(conn, table, col):
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    cols = [r[1] for r in rows]  # r[1] = name
    return col in cols

def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        for t in TABLES:
            if has_column(conn, t, NEW_COL):
                print(f"OK: {t}.{NEW_COL} já existe")
                continue

            print(f"ADD: {t}.{NEW_COL}")
            conn.execute(f'ALTER TABLE "{t}" ADD COLUMN "{NEW_COL}" TEXT')
        conn.commit()
        print("✅ Migração concluída.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

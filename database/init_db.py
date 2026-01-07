import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS "user" (
  user TEXT PRIMARY KEY,
  password TEXT,
  type TEXT CHECK(type IN ('cliente', 'consultor', 'administrador')),
  email TEXT,
  name TEXT
);

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
);

CREATE INDEX IF NOT EXISTS idx_solicitacoes_protocolo ON solicitacoes_periodico(protocolo);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_user ON solicitacoes_periodico(user);
"""

def create_or_reset_db(db_path: Path, reset: bool):
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if reset and db_path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = db_path.with_suffix(f".backup_{stamp}.db")
        shutil.copy2(db_path, backup)
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        # Melhor para apps web (menos lock)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")

        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()

def seed_default_users(db_path: Path):
    """
    Cria usuários de teste (idempotente):
    - admin/admin (administrador)
    - consultor/consultor (consultor)
    - cliente/cliente (cliente)
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")

        cur = conn.cursor()

        defaults = [
            ("admin", "admin", "administrador", "admin@vendrame.com", "Administrador"),
            ("consultor", "consultor", "consultor", "consultor@vendrame.com", "Consultor Teste"),
            ("cliente", "cliente", "cliente", "cliente@vendrame.com", "Cliente Teste"),
        ]

        for u, p, t, e, n in defaults:
            cur.execute('SELECT 1 FROM "user" WHERE user = ?', (u,))
            if cur.fetchone() is None:
                cur.execute(
                    'INSERT INTO "user" (user, password, type, email, name) VALUES (?, ?, ?, ?, ?)',
                    (u, p, t, e, n)
                )

        conn.commit()
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser()

    # ✅ caminho absoluto baseado no arquivo (independe de onde rodar o comando)
    project_root = Path(__file__).resolve().parent.parent
    default_db = project_root / "database" / "Users.db"

    parser.add_argument("--db", default=str(default_db), help="Caminho do SQLite")
    parser.add_argument("--reset", action="store_true", help="Recria do zero (faz backup antes)")
    parser.add_argument("--seed-defaults", action="store_true", help="Cria admin/consultor/cliente")
    args = parser.parse_args()

    db_path = Path(args.db)
    create_or_reset_db(db_path, reset=args.reset)

    if args.seed_defaults:
        seed_default_users(db_path)

    print(f"OK: banco pronto em {db_path.resolve()}")


if __name__ == "__main__":
    main()

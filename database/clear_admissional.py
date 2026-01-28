import os
import sqlite3
import argparse
import shutil

TABELA = "solicitacoes_admissional"

def tabela_existe(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name=?
    """, (TABELA,))
    return cur.fetchone() is not None

def listar_protocolos(conn):
    cur = conn.cursor()
    cur.execute(f"SELECT protocolo FROM {TABELA} WHERE protocolo IS NOT NULL AND protocolo != ''")
    return [row[0] for row in cur.fetchall()]

def safe_join(base, *paths):
    base_abs = os.path.abspath(base)
    final_abs = os.path.abspath(os.path.join(base, *paths))
    if not final_abs.startswith(base_abs + os.sep):
        raise ValueError("Caminho inválido (path traversal).")
    return final_abs

def main():
    parser = argparse.ArgumentParser(description="Limpa tabela solicitacoes_admissional e apaga pastas por protocolo.")
    parser.add_argument("--db", default="database/Users.db", help="Caminho do Users.db")
    parser.add_argument("--base-pastas", required=True, help="Base das pastas (ex: C:\\...\\Documentos_Admissional)")
    parser.add_argument("--dry", action="store_true", help="Simula (não apaga nada)")

    args = parser.parse_args()

    db_path = os.path.abspath(args.db)
    base_pastas = os.path.abspath(args.base_pastas)

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DB não encontrado: {db_path}")

    if not os.path.isdir(base_pastas):
        print(f"[AVISO] Base de pastas não existe (vou continuar mesmo assim): {base_pastas}")

    conn = sqlite3.connect(db_path)
    try:
        if not tabela_existe(conn):
            print(f"[OK] A tabela '{TABELA}' não existe. Nada a limpar.")
            return

        protocolos = listar_protocolos(conn)
        total = len(protocolos)

        if args.dry:
            print(f"[DRY] Encontrados {total} protocolos na tabela '{TABELA}'.")
            for p in protocolos[:10]:
                pasta = safe_join(base_pastas, p)
                print(f"[DRY] Apagaria: {pasta}")
            if total > 10:
                print(f"[DRY] ... e mais {total-10} pastas.")
            print(f"[DRY] Apagaria {total} registros do banco.")
            return

        # 1) Apaga linhas do banco
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {TABELA}")
        conn.commit()

        # 2) Apaga pastas dos protocolos
        apagadas = 0
        nao_encontradas = 0

        for p in protocolos:
            pasta = safe_join(base_pastas, p)
            if os.path.exists(pasta):
                shutil.rmtree(pasta)
                apagadas += 1
            else:
                nao_encontradas += 1

        # 3) Otimiza banco
        cur.execute("VACUUM")
        conn.commit()

        print(f"[OK] Banco limpo: {total} registros removidos de '{TABELA}'.")
        print(f"[OK] Pastas removidas: {apagadas}. Pastas não encontradas: {nao_encontradas}.")
        print("[OK] VACUUM executado.")

    finally:
        conn.close()

if __name__ == "__main__":
    main()

#executar
# python "C:\Users\Isabella Alencar\Documents\GRUPO EBG\VENDRAME - NEW FRONTEND\database\clear_admissional.py" --db "C:\Users\Isabella Alencar\Documents\GRUPO EBG\VENDRAME - NEW FRONTEND\database\Users.db" --base-pastas "C:\Users\Isabella Alencar\Documents\GRUPO EBG\VENDRAME - NEW FRONTEND\database\Documentos_Admissional"

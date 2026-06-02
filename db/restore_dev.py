"""
Restauration de la base dev à partir du backup prod.
Usage: python db/restore_dev.py
"""
import psycopg2
import sys
import os

DB_HOST = "192.168.1.161"
DB_PORT = 5432
DB_USER = "directus"
DB_PASSWORD = "directus"
DB_NAME = "directus"
BACKUP_FILE = os.path.join(os.path.dirname(__file__), "backup_prod_20260527_173647.sql")


def get_conn(database="postgres"):
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=database
    )
    conn.autocommit = True
    return conn


def drop_and_recreate():
    print(f"[1/3] Drop + recréation de la base '{DB_NAME}'...")
    conn = get_conn("postgres")
    cur = conn.cursor()

    # Terminer les connexions actives
    cur.execute(
        f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        f"WHERE datname = '{DB_NAME}' AND pid <> pg_backend_pid()"
    )
    terminated = cur.rowcount
    if terminated > 0:
        print(f"      {terminated} connexion(s) terminée(s)")

    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    print(f"      Base '{DB_NAME}' supprimée.")

    cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER} ENCODING 'UTF8'")
    print(f"      Base '{DB_NAME}' créée.")

    cur.close()
    conn.close()


def extract_sequences(sql: str) -> list[str]:
    """Extrait les noms de séquences référencées dans les DEFAULT nextval(...)."""
    import re
    return list(set(re.findall(r"nextval\('([^']+)'::regclass\)", sql)))


def create_sequences(sequences: list[str]):
    print(f"[2/4] Création des extensions + {len(sequences)} séquence(s)...")
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    try:
        with conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            for seq in sorted(sequences):
                cur.execute(f'CREATE SEQUENCE IF NOT EXISTS public."{seq}"')
        conn.commit()
        print(f"      Extension uuid-ossp + {len(sequences)} séquence(s) créée(s).")
    finally:
        conn.close()


def fix_jsonb_array_casts(sql: str) -> str:
    """
    Convertit les tableaux JSON simples (tableaux de strings) castés en ::jsonb
    vers ::text[] uniquement dans les lignes INSERT de audit_reason_code.
    Ces colonnes (entity_types, decision_types) sont text[] mais le backup
    les exporte avec le cast ::jsonb.
    """
    import re
    import json

    def json_array_to_pg_array(match):
        raw = match.group(1)
        try:
            values = json.loads(raw)
            if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
                return match.group(0)
            pg_values = ",".join(f'"{v}"' for v in values)
            return f"'{{{pg_values}}}'::text[]"
        except (json.JSONDecodeError, TypeError):
            return match.group(0)

    lines = sql.splitlines(keepends=True)
    result = []
    for line in lines:
        if line.startswith('INSERT INTO public."audit_reason_code"'):
            line = re.sub(r"'(\[.*?\])'::jsonb", json_array_to_pg_array, line)
        result.append(line)
    return "".join(result)


def restore():
    print(f"[3/4] Lecture du backup ({BACKUP_FILE})...")
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        sql = f.read()

    sql = fix_jsonb_array_casts(sql)

    sequences = extract_sequences(sql)
    create_sequences(sequences)

    print(f"[4/4] Import dans '{DB_NAME}'...")
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("      Import terminé avec succès.")
    except Exception as e:
        conn.rollback()
        print(f"ERREUR lors de l'import : {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    print("=== Restauration base DEV depuis backup PROD ===")
    drop_and_recreate()
    restore()
    print("=== Restauration terminée ===")

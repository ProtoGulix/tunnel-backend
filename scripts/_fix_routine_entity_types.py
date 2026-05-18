"""Ajoute 'request' aux entity_types de ROUTINE."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
import psycopg2

url = os.environ["DATABASE_URL"]
conn = psycopg2.connect(url)
cur = conn.cursor()

cur.execute("""
    UPDATE audit_reason_code
    SET entity_types = ARRAY['task', 'action', 'request']
    WHERE code = 'ROUTINE'
""")
conn.commit()
print(f"Lignes mises à jour : {cur.rowcount}")

cur.execute("SELECT entity_types FROM audit_reason_code WHERE code = 'ROUTINE'")
print(f"entity_types : {cur.fetchone()[0]}")

cur.close()
conn.close()

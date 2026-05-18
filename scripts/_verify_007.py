"""Vérifie que ROUTINE est bien présent en base après migration 007."""
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import psycopg2
from psycopg2.extras import RealDictCursor

url = os.environ["DATABASE_URL"]
conn = psycopg2.connect(url)
cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute("SELECT id, code, label, category, entity_types, is_active FROM audit_reason_code WHERE code = 'ROUTINE'")
row = cur.fetchone()

if row:
    print("OK — ROUTINE présent en base :")
    for k, v in dict(row).items():
        print(f"  {k}: {v}")
else:
    print("ERREUR — ROUTINE absent de audit_reason_code")

cur.close()
conn.close()

"""Supprime la révision fantôme 002_create_missing_tables de alembic_version_backend."""
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import psycopg2

url = os.environ["DATABASE_URL"]
conn = psycopg2.connect(url)
cur = conn.cursor()

cur.execute("SELECT version_num FROM alembic_version_backend")
before = [r[0] for r in cur.fetchall()]
print(f"Avant : {before}")

cur.execute("DELETE FROM alembic_version_backend WHERE version_num = '002_create_missing_tables'")
conn.commit()

cur.execute("SELECT version_num FROM alembic_version_backend")
after = [r[0] for r in cur.fetchall()]
print(f"Après : {after}")

cur.close()
conn.close()

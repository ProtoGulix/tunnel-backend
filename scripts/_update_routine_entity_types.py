import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute(
    "UPDATE audit_reason_code SET entity_types = %s WHERE code = %s",
    (["task", "action", "request", "intervention", "purchase_request"], "ROUTINE"),
)
conn.commit()
cur.execute("SELECT entity_types FROM audit_reason_code WHERE code = 'ROUTINE'")
print("entity_types :", cur.fetchone()[0])
cur.close()
conn.close()

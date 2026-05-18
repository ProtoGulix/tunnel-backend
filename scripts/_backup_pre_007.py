"""Backup ciblé des tables critiques avant migration 007."""
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import psycopg2
from psycopg2.extras import RealDictCursor

url = os.environ["DATABASE_URL"]
conn = psycopg2.connect(url)
cur = conn.cursor(cursor_factory=RealDictCursor)

lines = [
    "-- Backup pre-migration 007_audit_silent_routine",
    f"-- {datetime.now().isoformat()}",
    "",
]

# alembic_version_backend
cur.execute("SELECT * FROM alembic_version_backend")
rows = cur.fetchall()
lines.append("-- TABLE: alembic_version_backend")
for r in rows:
    v = r["version_num"]
    lines.append(f"INSERT INTO alembic_version_backend (version_num) VALUES ('{v}') ON CONFLICT DO NOTHING;")

lines.append("")

# audit_reason_code
cur.execute("SELECT * FROM audit_reason_code ORDER BY id")
rows = cur.fetchall()
lines.append(f"-- TABLE: audit_reason_code ({len(rows)} lignes)")
for r in rows:
    def q(v):
        if v is None:
            return "NULL"
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, list):
            escaped = ",".join(str(x).replace("'", "''") for x in v)
            return f"'{{{escaped}}}'"
        return "'" + str(v).replace("'", "''") + "'"

    lines.append(
        f"INSERT INTO audit_reason_code "
        f"(id, code, label, category, entity_types, decision_types, color, description, is_active) VALUES "
        f"({q(r['id'])}, {q(r['code'])}, {q(r['label'])}, {q(r['category'])}, "
        f"{q(r.get('entity_types'))}, {q(r.get('decision_types'))}, "
        f"{q(r.get('color'))}, {q(r.get('description'))}, {q(r['is_active'])}) "
        f"ON CONFLICT (code) DO NOTHING;"
    )

cur.close()
conn.close()

out = Path(__file__).parent.parent / "backups" / f"backup_pre_007_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"Backup créé : {out}")
print(f"Lignes audit_reason_code : {len(rows)}")

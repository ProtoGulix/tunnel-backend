"""
Validation du schéma SQL en base de production.
Vérifie : tables, colonnes, triggers, FK, index, migrations Alembic.
"""

import sys
import os
from collections import defaultdict
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor


def load_env(path=".env"):
    env = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env


env = load_env(os.path.join(os.path.dirname(__file__), "..", ".env"))
DATABASE_URL = env.get("DATABASE_URL") or os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    print("ERREUR : DATABASE_URL introuvable dans .env")
    sys.exit(1)

parsed = urlparse(DATABASE_URL)
conn_kwargs = dict(
    host=parsed.hostname,
    port=parsed.port or 5432,
    user=parsed.username,
    password=parsed.password,
    dbname=parsed.path.lstrip("/"),
    connect_timeout=10,
)

# ─── Schéma attendu ───────────────────────────────────────────────────────────
# Colonnes critiques réelles (vérifiées en production).
# Notes sur les divergences vs noms dans 01_core/ :
#   intervention : type→type_inter, statut→status_actual (pas de created_at/updated_at)
#   machine      : designation→name, statut→statut_id (FK)
#   location     : label→nom
#   stock_item   : reference→ref, designation→name (pas de created_at)
#   supplier_order : reference→order_number, statut→status
#   purchase_request : statut→status
#   request_status_log : purchase_request_id→request_id, statut→status_to, created_at→date
#   intervention_status_log : statut→status_to, created_at→date
#   preventive_occurrence : preventive_plan_id→plan_id
#   preventive_plan_gamme_step : preventive_plan_id→plan_id
#   machine_hours : pas d'id autonome (PK=machine_id), hours→hours_total
#   intervention_action_purchase_request : action_id→intervention_action_id
#   intervention_part : pas de stock_item_id (pièces libres, pas liées au catalogue)
#   equipment_class → equipement_class (orthographe française)
EXPECTED_TABLES = {
    # Core
    "intervention": [
        "id", "code", "machine_id", "type_inter", "status_actual",
        "tech_initials", "tech_id",
    ],
    "intervention_action": [
        "id", "intervention_id", "description", "created_at",
    ],
    "intervention_action_purchase_request": [
        "id", "intervention_action_id", "purchase_request_id",
    ],
    "intervention_part": [
        "id", "intervention_id", "quantity",
    ],
    "intervention_request": [
        "id", "machine_id", "statut", "created_at",
    ],
    "intervention_status_log": [
        "id", "intervention_id", "status_to", "date",
    ],
    "intervention_task": [
        "id", "intervention_id", "status", "created_at", "action_id",
    ],
    "machine": [
        "id", "code", "name", "statut_id",
    ],
    "machine_hours": [
        "machine_id", "hours_total",
    ],
    "location": [
        "id", "nom",
    ],
    "stock_item": [
        "id", "ref", "name",
    ],
    "stock_item_supplier": [
        "id", "stock_item_id", "supplier_id",
    ],
    "supplier": [
        "id", "name",
    ],
    "supplier_order": [
        "id", "order_number", "status", "created_at",
    ],
    "supplier_order_line": [
        "id", "supplier_order_id", "stock_item_id",
    ],
    "purchase_request": [
        "id", "status", "created_at",
    ],
    "request_status_log": [
        "id", "request_id", "status_to", "date",
    ],
    "preventive_occurrence": [
        "id", "plan_id", "created_at",
    ],
    # Ref
    "equipement_class": ["id", "code"],
    "intervention_status_ref": ["code", "label"],
    "manufacturer_item": ["id"],
    "preventive_plan": ["id", "label"],
    "preventive_plan_gamme_step": ["id", "plan_id"],
    "request_status_ref": ["code", "label"],
}

# Triggers critiques : nom exact ou sous-chaîne suffisant pour la correspondance
EXPECTED_TRIGGERS = {
    "intervention": ["trg_interv_code", "trg_log_status_change", "trg_check_intervention_closable"],
    "intervention_status_log": ["trg_sync_status_log_to_intervention"],
    "intervention_action": ["trg_compute_action_time"],
    "intervention_request": ["trg_request_code"],
    "stock_item": ["trg_generate_stock_item_ref"],
    "supplier_order": ["trg_generate_supplier_order_number"],
}

# FK critiques : (table, colonne, table_ref, colonne_ref)
CRITICAL_FKS = [
    ("intervention", "machine_id", "machine", "id"),
    ("intervention", "tech_id", "directus_users", "id"),
    ("intervention_action", "intervention_id", "intervention", "id"),
    ("intervention_task", "intervention_id", "intervention", "id"),
    ("intervention_task", "action_id", "intervention_action", "id"),
    ("intervention_status_log", "intervention_id", "intervention", "id"),
    ("supplier_order_line", "supplier_order_id", "supplier_order", "id"),
    ("purchase_request", "stock_item_id", "stock_item", "id"),
    ("preventive_occurrence", "plan_id", "preventive_plan", "id"),
    ("preventive_occurrence", "intervention_id", "intervention", "id"),
]

# ─── Connexion ────────────────────────────────────────────────────────────────

print(f"\n{'='*70}")
print(f"  VALIDATION SCHÉMA — {parsed.hostname}:{parsed.port}/{parsed.path.lstrip('/')}")
print(f"{'='*70}\n")

try:
    conn = psycopg2.connect(**conn_kwargs)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)
    print("✅ Connexion établie\n")
except Exception as e:
    print(f"❌ Connexion impossible : {e}")
    sys.exit(1)

issues = []
warnings = []

# ─── 1. Migrations Alembic ────────────────────────────────────────────────────
print("─── 1. MIGRATIONS ALEMBIC ────────────────────────────────────────────")
try:
    cur.execute("SELECT version_num FROM alembic_version_backend ORDER BY version_num")
    applied = [r["version_num"] for r in cur.fetchall()]
    n = len(applied)
    status = "✅" if n == 1 else "⚠️ " if n > 1 else "❌"
    print(f"  {status} {n} head(s) en base (attendu : 1 seul après merge)")
    for v in applied:
        print(f"      {v}")
    if n > 1:
        warnings.append(f"Alembic : {n} heads actifs — relancer 'alembic upgrade head'")
except Exception as e:
    issues.append(f"Table alembic_version_backend introuvable : {e}")
    print(f"  ❌ {issues[-1]}")

# ─── 2. Tables présentes ──────────────────────────────────────────────────────
print("\n─── 2. TABLES PRÉSENTES ──────────────────────────────────────────────")
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
existing_tables = {r["table_name"] for r in cur.fetchall()}
print(f"  {len(existing_tables)} tables trouvées en base\n")

for tbl in sorted(EXPECTED_TABLES.keys()):
    if tbl in existing_tables:
        print(f"  ✅ {tbl}")
    else:
        print(f"  ❌ MANQUANTE : {tbl}")
        issues.append(f"Table manquante : {tbl}")

extra = existing_tables - set(EXPECTED_TABLES.keys())
if extra:
    print(f"\n  ℹ️  Tables supplémentaires (non vérifiées) :")
    for t in sorted(extra):
        print(f"      {t}")

# ─── 3. Colonnes critiques ────────────────────────────────────────────────────
print("\n─── 3. COLONNES CRITIQUES ────────────────────────────────────────────")
cur.execute("""
    SELECT table_name, column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position
""")
columns_by_table = defaultdict(dict)
for r in cur.fetchall():
    columns_by_table[r["table_name"]][r["column_name"]] = {
        "type": r["data_type"],
        "nullable": r["is_nullable"],
        "default": r["column_default"],
    }

for tbl, expected_cols in sorted(EXPECTED_TABLES.items()):
    if tbl not in existing_tables:
        continue
    actual_cols = columns_by_table.get(tbl, {})
    missing = [c for c in expected_cols if c not in actual_cols]
    if missing:
        for col in missing:
            print(f"  ❌ {tbl}.{col} MANQUANTE")
            issues.append(f"Colonne manquante : {tbl}.{col}")
    else:
        print(f"  ✅ {tbl}")

# ─── 4. Détail colonnes des tables clés ───────────────────────────────────────
def print_columns(title, tbl):
    print(f"\n─── 4. DÉTAIL — {title} {'─'*(50 - len(title))}")
    if tbl not in columns_by_table:
        print(f"  ⚠️  Table absente")
        return
    for col, meta in columns_by_table[tbl].items():
        nullable = "NULL    " if meta["nullable"] == "YES" else "NOT NULL"
        default = f"  DEFAULT {meta['default']}" if meta["default"] else ""
        print(f"    {col:<35} {meta['type']:<30} {nullable}{default}")

print_columns("intervention", "intervention")
print_columns("intervention_task", "intervention_task")
print_columns("intervention_action", "intervention_action")

# ─── 5. Triggers ──────────────────────────────────────────────────────────────
print("\n─── 5. TRIGGERS ─────────────────────────────────────────────────────")
cur.execute("""
    SELECT trigger_name, event_object_table
    FROM information_schema.triggers
    WHERE trigger_schema = 'public'
    ORDER BY event_object_table, trigger_name
""")
triggers_by_table = defaultdict(list)
all_triggers = cur.fetchall()
for r in all_triggers:
    triggers_by_table[r["event_object_table"]].append(r["trigger_name"])

print(f"  {len(all_triggers)} triggers trouvés\n")
for tbl, expected_trgs in EXPECTED_TRIGGERS.items():
    actual = triggers_by_table.get(tbl, [])
    for trg in expected_trgs:
        found = any(trg in t for t in actual)
        if found:
            print(f"  ✅ {tbl} → {trg}")
        else:
            print(f"  ❌ {tbl} → {trg} MANQUANT")
            issues.append(f"Trigger manquant : {tbl}.{trg}")

print("\n  Triggers actifs par table :")
for tbl in sorted(triggers_by_table.keys()):
    for trg in sorted(set(triggers_by_table[tbl])):
        print(f"    {tbl:<40} {trg}")

# ─── 6. Clés étrangères ───────────────────────────────────────────────────────
print("\n─── 6. CLÉS ÉTRANGÈRES (FK) ─────────────────────────────────────────")
cur.execute("""
    SELECT
        tc.table_name AS from_table,
        kcu.column_name AS from_col,
        ccu.table_name AS to_table,
        ccu.column_name AS to_col,
        rc.delete_rule
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
    JOIN information_schema.referential_constraints rc
        ON tc.constraint_name = rc.constraint_name AND tc.table_schema = rc.constraint_schema
    JOIN information_schema.constraint_column_usage ccu
        ON rc.unique_constraint_name = ccu.constraint_name AND rc.unique_constraint_schema = ccu.constraint_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = 'public'
    ORDER BY tc.table_name, kcu.column_name
""")
fks = cur.fetchall()
print(f"  {len(fks)} FK trouvées\n")

fk_set = {(r["from_table"], r["from_col"], r["to_table"], r["to_col"]) for r in fks}
for from_tbl, from_col, to_tbl, to_col in CRITICAL_FKS:
    if (from_tbl, from_col, to_tbl, to_col) in fk_set:
        print(f"  ✅ {from_tbl}.{from_col} → {to_tbl}.{to_col}")
    else:
        print(f"  ❌ {from_tbl}.{from_col} → {to_tbl}.{to_col} MANQUANTE")
        issues.append(f"FK manquante : {from_tbl}.{from_col} → {to_tbl}.{to_col}")

# ─── 7. Index ─────────────────────────────────────────────────────────────────
print("\n─── 7. INDEX ────────────────────────────────────────────────────────")
cur.execute("""
    SELECT tablename, indexname
    FROM pg_indexes
    WHERE schemaname = 'public'
    ORDER BY tablename, indexname
""")
indexes = cur.fetchall()
print(f"  {len(indexes)} index trouvés\n")

key_tables = {
    "intervention", "intervention_action", "intervention_task",
    "machine", "supplier_order", "stock_item",
}
for idx in indexes:
    if idx["tablename"] in key_tables:
        print(f"  {idx['tablename']:<40} {idx['indexname']}")

# ─── 8. Extensions PostgreSQL ─────────────────────────────────────────────────
print("\n─── 8. EXTENSIONS POSTGRESQL ────────────────────────────────────────")
cur.execute("SELECT extname, extversion FROM pg_extension ORDER BY extname")
exts = cur.fetchall()
for ext in exts:
    print(f"  ✅ {ext['extname']}  v{ext['extversion']}")

if not any(r["extname"] == "uuid-ossp" for r in exts):
    issues.append("Extension uuid-ossp manquante")
    print("  ❌ uuid-ossp MANQUANTE")

# ─── 9. Volumétrie ────────────────────────────────────────────────────────────
print("\n─── 9. VOLUMÉTRIE ────────────────────────────────────────────────────")
count_tables = [
    "intervention", "intervention_action", "intervention_task",
    "machine", "supplier_order", "purchase_request",
    "stock_item", "preventive_occurrence", "preventive_plan",
    "intervention_status_log", "intervention_request",
]
for tbl in count_tables:
    if tbl in existing_tables:
        try:
            cur.execute(f"SELECT COUNT(*) AS n FROM {tbl}")
            n = cur.fetchone()["n"]
            print(f"  {tbl:<40} {n:>8} lignes")
        except Exception as e:
            print(f"  ⚠️  {tbl} : erreur COUNT — {e}")

# ─── 10. Tables obsolètes ─────────────────────────────────────────────────────
print("\n─── 10. TABLES OBSOLÈTES ────────────────────────────────────────────")
old_tables = ["gamme_step_validation"]
for tbl in old_tables:
    if tbl in existing_tables:
        print(f"  ⚠️  Table obsolète encore présente : {tbl}")
        warnings.append(f"Table obsolète présente : {tbl}")
    else:
        print(f"  ✅ {tbl} absente (renommée en intervention_task)")

# ─── Bilan ────────────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print("  BILAN FINAL")
print(f"{'='*70}")
if not issues and not warnings:
    print("  ✅ Aucun problème détecté — schéma cohérent\n")
else:
    if issues:
        print(f"\n  🔴 ERREURS ({len(issues)}) :")
        for i in issues:
            print(f"    • {i}")
    if warnings:
        print(f"\n  🟡 AVERTISSEMENTS ({len(warnings)}) :")
        for w in warnings:
            print(f"    • {w}")
    print()

cur.close()
conn.close()

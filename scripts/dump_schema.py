"""
Extrait le schéma complet du schéma public en SQL pur via les catalogues PostgreSQL.
Produit un fichier schema_current.sql utilisable comme baseline Alembic.

Usage : python scripts/dump_schema.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from textwrap import dedent

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DSN = os.environ["DATABASE_URL"]
OUT = Path(__file__).resolve().parent.parent / "schema_current.sql"


def connect():
    dsn = DSN.replace("postgresql://", "").replace("postgres://", "")
    # postgresql://user:pass@host:port/dbname
    from urllib.parse import urlparse
    u = urlparse("postgresql://" + DSN.split("://", 1)[-1])
    return psycopg2.connect(
        host=u.hostname, port=u.port or 5432,
        user=u.username, password=u.password, dbname=u.path.lstrip("/"),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def q(conn, sql, params=None):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def section(title: str) -> str:
    bar = "-" * 78
    return f"\n\n-- {bar}\n-- {title}\n-- {bar}\n"


# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------

def dump_extensions(conn) -> str:
    rows = q(conn, """
        SELECT extname FROM pg_extension
        WHERE extname NOT IN ('plpgsql')
        ORDER BY extname
    """)
    if not rows:
        return ""
    out = section("EXTENSIONS")
    for r in rows:
        out += f"CREATE EXTENSION IF NOT EXISTS \"{r['extname']}\";\n"
    return out


# ---------------------------------------------------------------------------
# Types ENUM
# ---------------------------------------------------------------------------

def dump_enums(conn) -> str:
    rows = q(conn, """
        SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder) AS labels
        FROM pg_type t
        JOIN pg_enum e ON e.enumtypid = t.oid
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = 'public'
        GROUP BY t.typname
        ORDER BY t.typname
    """)
    if not rows:
        return ""
    out = section("ENUM TYPES")
    for r in rows:
        labels = ", ".join(f"'{l}'" for l in r["labels"])
        out += f"CREATE TYPE {r['typname']} AS ENUM ({labels});\n"
    return out


# ---------------------------------------------------------------------------
# Séquences standalone (hors SERIAL/IDENTITY)
# ---------------------------------------------------------------------------

def dump_sequences(conn) -> str:
    rows = q(conn, """
        SELECT sequence_name, start_value, minimum_value, maximum_value,
               increment, cycle_option
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
          AND sequence_name NOT LIKE '%_seq'   -- SERIAL auto-gérées
        ORDER BY sequence_name
    """)
    if not rows:
        return ""
    out = section("SEQUENCES")
    for r in rows:
        cycle = "CYCLE" if r["cycle_option"] == "YES" else "NO CYCLE"
        out += (
            f"CREATE SEQUENCE IF NOT EXISTS {r['sequence_name']}\n"
            f"    START {r['start_value']} INCREMENT {r['increment']}\n"
            f"    MINVALUE {r['minimum_value']} MAXVALUE {r['maximum_value']} {cycle};\n"
        )
    return out


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def _col_default(default: str | None, col_type: str) -> str:
    if default is None:
        return ""
    # Nettoyer le cast redondant
    return f" DEFAULT {default}"


def dump_tables(conn) -> str:
    tables = q(conn, """
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)
    if not tables:
        return ""

    out = section("TABLES")

    for t in tables:
        tname = t["tablename"]
        cols = q(conn, """
            SELECT
                c.column_name,
                c.udt_name,
                c.data_type,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                c.is_nullable,
                c.column_default,
                c.identity_generation
            FROM information_schema.columns c
            WHERE c.table_schema = 'public' AND c.table_name = %s
            ORDER BY c.ordinal_position
        """, (tname,))

        pk_cols = q(conn, """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON kcu.constraint_name = tc.constraint_name
             AND kcu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = %s
            ORDER BY kcu.ordinal_position
        """, (tname,))
        pk_names = [r["column_name"] for r in pk_cols]

        lines = []
        for c in cols:
            dtype = _pg_type(c)
            nullable = "" if c["is_nullable"] == "YES" else " NOT NULL"
            default = _col_default(c["column_default"], dtype)
            lines.append(f"    {c['column_name']} {dtype}{default}{nullable}")

        if pk_names:
            lines.append(f"    PRIMARY KEY ({', '.join(pk_names)})")

        col_block = ",\n".join(lines)
        out += f"\nCREATE TABLE IF NOT EXISTS {tname} (\n{col_block}\n);\n"

    return out


def _pg_type(c) -> str:
    dt = c["data_type"]
    udt = c["udt_name"]

    if dt == "USER-DEFINED":
        return udt
    if dt == "ARRAY":
        base = udt.lstrip("_")
        return f"{base}[]"
    if dt in ("character varying", "varchar"):
        if c["character_maximum_length"]:
            return f"VARCHAR({c['character_maximum_length']})"
        return "TEXT"
    if dt == "character":
        if c["character_maximum_length"]:
            return f"CHAR({c['character_maximum_length']})"
        return "CHAR"
    if dt == "numeric":
        if c["numeric_precision"] and c["numeric_scale"] is not None:
            return f"NUMERIC({c['numeric_precision']},{c['numeric_scale']})"
        return "NUMERIC"
    if dt == "timestamp without time zone":
        return "TIMESTAMP"
    if dt == "timestamp with time zone":
        return "TIMESTAMPTZ"
    if dt == "time without time zone":
        return "TIME"
    if dt == "time with time zone":
        return "TIMETZ"
    if dt == "double precision":
        return "FLOAT8"
    if dt == "integer":
        return "INTEGER"
    if dt == "bigint":
        return "BIGINT"
    if dt == "smallint":
        return "SMALLINT"
    if dt == "boolean":
        return "BOOLEAN"
    if dt == "uuid":
        return "UUID"
    if dt == "text":
        return "TEXT"
    if dt == "jsonb":
        return "JSONB"
    if dt == "json":
        return "JSON"
    if dt == "bytea":
        return "BYTEA"
    if dt == "date":
        return "DATE"
    if dt == "interval":
        return "INTERVAL"
    return udt


# ---------------------------------------------------------------------------
# Index (hors PK)
# ---------------------------------------------------------------------------

def dump_indexes(conn) -> str:
    rows = q(conn, """
        SELECT indexname, tablename, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND indexname NOT IN (
              SELECT constraint_name FROM information_schema.table_constraints
              WHERE table_schema = 'public'
                AND constraint_type IN ('PRIMARY KEY', 'UNIQUE')
          )
        ORDER BY tablename, indexname
    """)
    if not rows:
        return ""
    out = section("INDEXES")
    for r in rows:
        out += f"{r['indexdef']};\n"
    return out


# ---------------------------------------------------------------------------
# Contraintes (UNIQUE, CHECK, FK)
# ---------------------------------------------------------------------------

def dump_constraints(conn) -> str:
    # UNIQUE et CHECK
    rows = q(conn, """
        SELECT tc.constraint_name, tc.constraint_type, tc.table_name,
               cc.check_clause,
               array_agg(kcu.column_name ORDER BY kcu.ordinal_position) AS columns
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
          ON kcu.constraint_name = tc.constraint_name
         AND kcu.table_schema = tc.table_schema
        LEFT JOIN information_schema.check_constraints cc
          ON cc.constraint_name = tc.constraint_name
         AND cc.constraint_schema = tc.table_schema
        WHERE tc.table_schema = 'public'
          AND tc.constraint_type IN ('UNIQUE', 'CHECK')
          AND tc.constraint_name NOT LIKE '%_not_null'
        GROUP BY tc.constraint_name, tc.constraint_type, tc.table_name, cc.check_clause
        ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name
    """)

    out = section("UNIQUE & CHECK CONSTRAINTS")
    for r in rows:
        tname = r["table_name"]
        cname = r["constraint_name"]
        if r["constraint_type"] == "UNIQUE":
            cols = ", ".join(r["columns"])
            out += f"ALTER TABLE {tname} ADD CONSTRAINT {cname} UNIQUE ({cols});\n"
        elif r["constraint_type"] == "CHECK":
            out += f"ALTER TABLE {tname} ADD CONSTRAINT {cname} CHECK ({r['check_clause']});\n"

    # FOREIGN KEYS
    fks = q(conn, """
        SELECT
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column,
            rc.update_rule,
            rc.delete_rule
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON kcu.constraint_name = tc.constraint_name
         AND kcu.table_schema = tc.table_schema
        JOIN information_schema.referential_constraints rc
          ON rc.constraint_name = tc.constraint_name
         AND rc.constraint_schema = tc.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = rc.unique_constraint_name
         AND ccu.table_schema = tc.table_schema
        WHERE tc.table_schema = 'public'
          AND tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_name, tc.constraint_name
    """)

    out += section("FOREIGN KEY CONSTRAINTS")
    for r in fks:
        on_delete = f" ON DELETE {r['delete_rule']}" if r["delete_rule"] != "NO ACTION" else ""
        on_update = f" ON UPDATE {r['update_rule']}" if r["update_rule"] != "NO ACTION" else ""
        out += (
            f"ALTER TABLE {r['table_name']} ADD CONSTRAINT {r['constraint_name']}\n"
            f"    FOREIGN KEY ({r['column_name']}) REFERENCES {r['foreign_table']}({r['foreign_column']})"
            f"{on_update}{on_delete};\n"
        )

    return out


# ---------------------------------------------------------------------------
# Fonctions & Procédures
# ---------------------------------------------------------------------------

def dump_functions(conn) -> str:
    rows = q(conn, """
        SELECT
            p.proname AS name,
            pg_get_functiondef(p.oid) AS definition,
            p.prokind
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'
          AND p.proname NOT LIKE 'pg_%'
        ORDER BY p.proname
    """)
    if not rows:
        return ""
    out = section("FUNCTIONS & PROCEDURES")
    for r in rows:
        out += f"{r['definition'].strip()};\n\n"
    return out


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------

def dump_triggers(conn) -> str:
    rows = q(conn, """
        SELECT
            t.tgname AS trigger_name,
            c.relname AS table_name,
            pg_get_triggerdef(t.oid) AS definition
        FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND NOT t.tgisinternal
        ORDER BY c.relname, t.tgname
    """)
    if not rows:
        return ""
    out = section("TRIGGERS")
    for r in rows:
        out += f"{r['definition']};\n"
    return out


# ---------------------------------------------------------------------------
# Vues
# ---------------------------------------------------------------------------

def dump_views(conn) -> str:
    rows = q(conn, """
        SELECT table_name, view_definition
        FROM information_schema.views
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    if not rows:
        return ""
    out = section("VIEWS")
    for r in rows:
        out += f"CREATE OR REPLACE VIEW {r['table_name']} AS\n{r['view_definition'].strip()};\n\n"
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Connexion a {DSN.split('@')[-1]} ...")
    conn = connect()
    try:
        parts = [
            "-- schema_current.sql — généré automatiquement par scripts/dump_schema.py\n"
            "-- Source de vérité unique pour le schéma public.\n"
            "-- NE PAS MODIFIER MANUELLEMENT — régénérer via le script.\n",
            dump_extensions(conn),
            dump_enums(conn),
            dump_sequences(conn),
            dump_tables(conn),
            dump_indexes(conn),
            dump_constraints(conn),
            dump_functions(conn),
            dump_triggers(conn),
            dump_views(conn),
        ]
        sql = "".join(p for p in parts if p)
        OUT.write_text(sql, encoding="utf-8")
        print(f"Schema exporte -> {OUT}")
        print(f"Taille : {len(sql):,} caracteres")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

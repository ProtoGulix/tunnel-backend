"""Rediriger les FK des tables métier de directus_users vers tunnel_user

Depuis v3.1.0, l'auth utilise tunnel_user. Les contraintes FK des tables métier
pointaient encore sur directus_users, causant une violation FK à la création
d'une intervention (tech_id présent dans tunnel_user mais pas dans directus_users).

Inclut un backfill des UUIDs orphelins : 4 utilisateurs existent dans les deux
tables avec des UUIDs différents → on remplace l'ancien UUID Directus par le
nouvel UUID tunnel_user (correspondance par email). 1 utilisateur sans email
(Stéphane DAMONS) n'a pas de correspondance → tech_id mis à NULL.

Les tables directus_* conservent leurs FK sur directus_users (non modifiées).

Revision ID: 001_fk_tunnel_user
Revises: 000_baseline_clean
Create Date: 2026-05-04
"""
from __future__ import annotations

from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_fk_tunnel_user"
down_revision: Union[str, None] = "000_baseline_clean"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None

_FK = [
    ("intervention",            "tech_id",        "intervention_tech_id_fkey",                      "SET NULL"),
    ("intervention",            "updated_by",      "intervention_updated_by_foreign",                "SET NULL"),
    ("intervention_action",     "tech",            "intervention_action_tech_foreign",               "NO ACTION"),
    ("intervention_status_log", "technician_id",   "intervention_status_log_technician_id_foreign",  "SET NULL"),
    ("intervention_task",       "assigned_to",     "intervention_task_assigned_to_fkey",             "SET NULL"),
    ("intervention_task",       "created_by",      "intervention_task_created_by_fkey",              "SET NULL"),
]

# Colonnes à backfiller : (table, colonne)
_BACKFILL_COLS = [
    ("intervention",            "tech_id"),
    ("intervention",            "updated_by"),
    ("intervention_action",     "tech"),
    ("intervention_status_log", "technician_id"),
    ("intervention_task",       "assigned_to"),
    ("intervention_task",       "created_by"),
]


def _backfill_uuids(conn: sa.engine.Connection) -> None:
    """Remplace les UUIDs directus_users par les UUIDs tunnel_user correspondants.

    Correspondance par email. Les lignes sans correspondance (utilisateur sans
    email dans directus_users) sont mises à NULL.
    """
    # Construire le mapping directus_uuid → tunnel_uuid via email
    result = conn.execute(sa.text("""
        SELECT CAST(du.id AS text) AS old_id, CAST(tu.id AS text) AS new_id
        FROM directus_users du
        JOIN tunnel_user tu ON tu.email = du.email
        WHERE du.email IS NOT NULL
    """))
    mapping = {row.old_id: row.new_id for row in result}

    # Trouver tous les UUIDs orphelins (présents dans les tables métier
    # mais absents de tunnel_user)
    orphan_query = sa.text("""
        SELECT DISTINCT col_val
        FROM (
            SELECT CAST(tech_id AS text)       AS col_val FROM intervention           WHERE tech_id IS NOT NULL
            UNION
            SELECT CAST(updated_by AS text)               FROM intervention           WHERE updated_by IS NOT NULL
            UNION
            SELECT CAST(tech AS text)                     FROM intervention_action    WHERE tech IS NOT NULL
            UNION
            SELECT CAST(technician_id AS text)            FROM intervention_status_log WHERE technician_id IS NOT NULL
            UNION
            SELECT CAST(assigned_to AS text)              FROM intervention_task      WHERE assigned_to IS NOT NULL
            UNION
            SELECT CAST(created_by AS text)               FROM intervention_task      WHERE created_by IS NOT NULL
        ) vals
        WHERE NOT EXISTS (SELECT 1 FROM tunnel_user tu WHERE CAST(tu.id AS text) = vals.col_val)
    """)
    orphans = [row.col_val for row in conn.execute(orphan_query)]

    for old_id in orphans:
        new_id = mapping.get(old_id)
        for table, col in _BACKFILL_COLS:
            if new_id:
                conn.execute(sa.text(
                    f"UPDATE {table} SET {col} = CAST(:new_id AS uuid) WHERE CAST({col} AS text) = :old_id"
                ), {"new_id": new_id, "old_id": old_id})
            else:
                # Aucune correspondance email → NULL (contrainte SET NULL)
                conn.execute(sa.text(
                    f"UPDATE {table} SET {col} = NULL WHERE CAST({col} AS text) = :old_id"
                ), {"old_id": old_id})


def upgrade() -> None:
    # 0. Créer tunnel_user si elle n'existe pas encore (prod pre-v3.1.0)
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS tunnel_user (
            id UUID DEFAULT gen_random_uuid() NOT NULL,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            initial VARCHAR(5) NOT NULL,
            role_id UUID NOT NULL,
            auth_provider VARCHAR(20) DEFAULT 'local' NOT NULL,
            external_id VARCHAR(255),
            is_active BOOLEAN DEFAULT true NOT NULL,
            provisioning VARCHAR(20) DEFAULT 'manual' NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            PRIMARY KEY (id)
        )
    """))

    # 1. Supprimer les FK avant le backfill (sinon l'UPDATE viole la contrainte existante)
    for table, column, constraint, on_delete in _FK:
        op.drop_constraint(constraint, table, type_="foreignkey")

    # 2. Backfiller les UUIDs orphelins
    conn = op.get_bind()
    _backfill_uuids(conn)

    # 3. Recréer les FK vers tunnel_user
    for table, column, constraint, on_delete in _FK:
        op.create_foreign_key(
            constraint, table,
            "tunnel_user", [column], ["id"],
            ondelete=on_delete if on_delete != "NO ACTION" else None,
        )


def downgrade() -> None:
    for table, column, constraint, on_delete in _FK:
        op.drop_constraint(constraint, table, type_="foreignkey")
        op.create_foreign_key(
            constraint, table,
            "directus_users", [column], ["id"],
            ondelete=on_delete if on_delete != "NO ACTION" else None,
        )

"""Table de jonction M2M intervention_action ↔ intervention_task

Supprime les deux FK 1:1 cassées (intervention_action.task_id et
intervention_task.action_id) et les remplace par une table de jonction
permettant N actions → N tâches.

Revision ID: 003_m2m_action_task
Revises: 002_audit_log
Create Date: 2026-05-12
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "003_m2m_action_task"
down_revision: Union[str, None] = "002_audit_log"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # ── 1. Créer la table de jonction ─────────────────────────────
    op.execute("""
        CREATE TABLE intervention_action_task (
            action_id UUID NOT NULL,
            task_id   UUID NOT NULL,
            PRIMARY KEY (action_id, task_id),
            FOREIGN KEY (action_id)
                REFERENCES intervention_action(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id)
                REFERENCES intervention_task(id) ON DELETE CASCADE
        )
    """)

    op.execute("""
        CREATE INDEX idx_intervention_action_task_task_id
            ON intervention_action_task(task_id)
    """)

    # ── 2. Backfill depuis intervention_task.action_id ─────────────
    # Source de vérité : la colonne active que le code Python alimentait
    op.execute("""
        INSERT INTO intervention_action_task (action_id, task_id)
        SELECT it.action_id, it.id
        FROM intervention_task it
        WHERE it.action_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    # Backfill complémentaire depuis intervention_action.task_id (legacy)
    # au cas où des données existent uniquement via l'ancien modèle
    op.execute("""
        INSERT INTO intervention_action_task (action_id, task_id)
        SELECT ia.id, ia.task_id
        FROM intervention_action ia
        WHERE ia.task_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    # ── 3. Supprimer les contraintes FK avant de dropper les colonnes
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE intervention_task
                DROP CONSTRAINT IF EXISTS intervention_task_action_id_fkey CASCADE;
        EXCEPTION WHEN undefined_object THEN NULL;
        END $$
    """)

    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE intervention_action
                DROP CONSTRAINT IF EXISTS intervention_action_task_id_fkey CASCADE;
        EXCEPTION WHEN undefined_object THEN NULL;
        END $$
    """)

    # ── 4. Supprimer les index portant sur ces colonnes ────────────
    op.execute("DROP INDEX IF EXISTS idx_intervention_task_action_id")
    op.execute("DROP INDEX IF EXISTS idx_intervention_action_task_id")

    # ── 5. Supprimer les colonnes FK ───────────────────────────────
    op.execute("ALTER TABLE intervention_task   DROP COLUMN IF EXISTS action_id")
    op.execute("ALTER TABLE intervention_action DROP COLUMN IF EXISTS task_id")


def downgrade() -> None:
    # ── 1. Restaurer les colonnes ──────────────────────────────────
    op.execute("ALTER TABLE intervention_action ADD COLUMN task_id UUID")
    op.execute("ALTER TABLE intervention_task   ADD COLUMN action_id UUID")

    # ── 2. Restaurer les FK ────────────────────────────────────────
    op.execute("""
        ALTER TABLE intervention_action
            ADD CONSTRAINT intervention_action_task_id_fkey
            FOREIGN KEY (task_id)
            REFERENCES intervention_task(id) ON DELETE SET NULL
    """)

    op.execute("""
        ALTER TABLE intervention_task
            ADD CONSTRAINT intervention_task_action_id_fkey
            FOREIGN KEY (action_id)
            REFERENCES intervention_action(id) ON DELETE SET NULL
    """)

    # ── 3. Restaurer les index ─────────────────────────────────────
    op.execute("""
        CREATE INDEX idx_intervention_action_task_id
            ON intervention_action(task_id)
    """)
    op.execute("""
        CREATE INDEX idx_intervention_task_action_id
            ON intervention_task(action_id)
    """)

    # ── 4. Backfill inverse — chaque tâche récupère sa dernière action
    op.execute("""
        UPDATE intervention_task it
        SET action_id = (
            SELECT iat.action_id
            FROM intervention_action_task iat
            INNER JOIN intervention_action ia ON ia.id = iat.action_id
            WHERE iat.task_id = it.id
            ORDER BY ia.created_at DESC
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1 FROM intervention_action_task iat WHERE iat.task_id = it.id
        )
    """)

    # ── 5. Supprimer la table de jonction ──────────────────────────
    op.execute("DROP TABLE IF EXISTS intervention_action_task")

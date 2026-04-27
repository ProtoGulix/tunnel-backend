"""Revert task_id on intervention_action — use action_id on intervention_task

Revision ID: j5e6f7a8b9c0
Revises: i4d5e6f7g8h9
Create Date: 2026-04-26

Correction du modèle de relation action ↔ tâche :
- Supprime task_id sur intervention_action (ajouté par erreur dans i4d5e6f7g8h9)
- La relation reste portée par intervention_task.action_id (modèle original)
- Ajoute trigger fn_task_status_on_action_link : todo→in_progress auto au SET action_id
"""
from alembic import op
import sqlalchemy as sa

revision = "j5e6f7a8b9c0"
down_revision = "i4d5e6f7g8h9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Supprimer task_id sur intervention_action ──────────────
    op.execute("DROP INDEX IF EXISTS idx_intervention_action_task_id")
    op.execute(
        "ALTER TABLE public.intervention_action DROP COLUMN IF EXISTS task_id"
    )

    # ── 2. S'assurer que action_id existe sur intervention_task ───
    # (il existait avant la migration i4d5e6f7g8h9 — vérification défensive)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name   = 'intervention_task'
                  AND column_name  = 'action_id'
            ) THEN
                ALTER TABLE public.intervention_task
                    ADD COLUMN action_id UUID
                    REFERENCES public.intervention_action (id) ON DELETE SET NULL;
                CREATE INDEX idx_intervention_task_action_id
                    ON public.intervention_task (action_id);
            END IF;
        END $$;
        """
    )

    # ── 3. Trigger todo → in_progress au SET action_id ────────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.fn_task_status_on_action_link()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.action_id IS NOT NULL
               AND (OLD.action_id IS NULL OR OLD.action_id != NEW.action_id)
               AND NEW.status = 'todo'
            THEN
                NEW.status     := 'in_progress';
                NEW.updated_at := NOW();
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_task_status_on_action_link ON public.intervention_task"
    )
    op.execute(
        """
        CREATE TRIGGER trg_task_status_on_action_link
            BEFORE UPDATE ON public.intervention_task
            FOR EACH ROW EXECUTE FUNCTION public.fn_task_status_on_action_link();
        """
    )


def downgrade() -> None:
    # Supprimer le trigger
    op.execute(
        "DROP TRIGGER IF EXISTS trg_task_status_on_action_link ON public.intervention_task"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS public.fn_task_status_on_action_link()"
    )

    # Remettre task_id sur intervention_action (nullable — données perdues, acceptable en DEV)
    op.execute(
        """
        ALTER TABLE public.intervention_action
            ADD COLUMN IF NOT EXISTS task_id UUID
            REFERENCES public.intervention_task (id) ON DELETE SET NULL
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_intervention_action_task_id "
        "ON public.intervention_action (task_id)"
    )

"""task_id on intervention_action — une tâche peut avoir plusieurs actions

Revision ID: k6f7a8b9c0d1
Revises: j5e6f7a8b9c0
Create Date: 2026-04-26

Corrige le modèle de relation action ↔ tâche pour revenir au plan initial :
- Une tâche peut être liée à plusieurs actions (one-to-many)
- task_id est porté par intervention_action (FK nullable vers intervention_task)
- action_id sur intervention_task est supprimé (modèle j5e6 était incorrect)
- Le trigger trg_task_status_on_action_link est supprimé (plus nécessaire)
- La transition todo→in_progress est gérée en Python dans InterventionActionRepository.add()
"""
from alembic import op

revision = "k6f7a8b9c0d1"
down_revision = "j5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Supprimer le trigger et la fonction du modèle j5e6 ─────
    op.execute(
        "DROP TRIGGER IF EXISTS trg_task_status_on_action_link ON public.intervention_task"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS public.fn_task_status_on_action_link()"
    )

    # ── 2. Supprimer action_id de intervention_task ───────────────
    op.execute("DROP INDEX IF EXISTS idx_intervention_task_action_id")
    op.execute(
        "ALTER TABLE public.intervention_task DROP COLUMN IF EXISTS action_id"
    )

    # ── 3. Ajouter task_id sur intervention_action ────────────────
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


def downgrade() -> None:
    # Supprimer task_id de intervention_action
    op.execute("DROP INDEX IF EXISTS idx_intervention_action_task_id")
    op.execute(
        "ALTER TABLE public.intervention_action DROP COLUMN IF EXISTS task_id"
    )

    # Remettre action_id sur intervention_task
    op.execute(
        """
        ALTER TABLE public.intervention_task
            ADD COLUMN IF NOT EXISTS action_id UUID
            REFERENCES public.intervention_action (id) ON DELETE SET NULL
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_intervention_task_action_id "
        "ON public.intervention_task (action_id)"
    )

    # Remettre le trigger
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
        """
        CREATE TRIGGER trg_task_status_on_action_link
            BEFORE UPDATE ON public.intervention_task
            FOR EACH ROW EXECUTE FUNCTION public.fn_task_status_on_action_link();
        """
    )

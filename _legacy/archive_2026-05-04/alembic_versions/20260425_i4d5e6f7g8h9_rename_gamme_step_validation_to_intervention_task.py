"""rename gamme_step_validation to intervention_task

Revision ID: i4d5e6f7g8h9
Revises: h3c4d5e6f7a8
Create Date: 2026-04-25

Conversion in-place de gamme_step_validation en intervention_task :
- Renommage table + colonnes
- Migration des statuts (pending→todo, validated→done)
- Ajout colonnes : label, origin, optional, sort_order, assigned_to, due_date, created_by, created_at
- Ajout colonne task_id sur intervention_action
- Renommage contraintes et index
"""
from alembic import op
import sqlalchemy as sa
import logging

revision = "i4d5e6f7g8h9"
down_revision = "h3c4d5e6f7a8"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.migration")


def upgrade() -> None:
    # ── 1. Renommer la table ──────────────────────────────────────
    op.execute(
        "ALTER TABLE public.gamme_step_validation RENAME TO intervention_task")

    # ── 2. Renommer les colonnes ──────────────────────────────────
    op.execute(
        "ALTER TABLE public.intervention_task RENAME COLUMN step_id TO gamme_step_id")
    op.execute(
        "ALTER TABLE public.intervention_task RENAME COLUMN validated_at TO updated_at")
    op.execute(
        "ALTER TABLE public.intervention_task RENAME COLUMN validated_by TO closed_by")

    # ── 3. Modifier les colonnes existantes ───────────────────────
    # gamme_step_id : nullable (tâches non-préventives)
    op.execute(
        "ALTER TABLE public.intervention_task ALTER COLUMN gamme_step_id DROP NOT NULL")

    # intervention_id : nullable (avant acceptation DI)
    op.execute(
        "ALTER TABLE public.intervention_task ALTER COLUMN intervention_id DROP NOT NULL")

    # Migrer les statuts
    op.execute(
        "UPDATE public.intervention_task SET status = 'todo'  WHERE status = 'pending'")
    op.execute(
        "UPDATE public.intervention_task SET status = 'done'  WHERE status = 'validated'")

    # Remplacer la contrainte CHECK sur status
    op.execute(
        "ALTER TABLE public.intervention_task DROP CONSTRAINT IF EXISTS gamme_step_validation_skip_reason_check")
    op.execute(
        "ALTER TABLE public.intervention_task DROP CONSTRAINT IF EXISTS gamme_step_validation_status_check")
    op.execute(
        "ALTER TABLE public.intervention_task "
        "ADD CONSTRAINT intervention_task_status_check "
        "CHECK (status IN ('todo', 'in_progress', 'done', 'skipped'))"
    )
    op.execute(
        "ALTER TABLE public.intervention_task "
        "ADD CONSTRAINT intervention_task_skip_reason_check "
        "CHECK ((status != 'skipped') OR (skip_reason IS NOT NULL))"
    )

    # ── 4. Ajouter les nouvelles colonnes ─────────────────────────
    op.execute("ALTER TABLE public.intervention_task ADD COLUMN label TEXT")

    # Peupler label depuis le step de gamme pour les données existantes
    op.execute(
        """
        UPDATE public.intervention_task it
        SET label = pgs.label
        FROM public.preventive_plan_gamme_step pgs
        WHERE it.gamme_step_id = pgs.id
        """
    )

    op.execute(
        "ALTER TABLE public.intervention_task "
        "ADD COLUMN origin VARCHAR(10) NOT NULL DEFAULT 'plan' "
        "CHECK (origin IN ('plan', 'resp', 'tech'))"
    )

    op.execute(
        "ALTER TABLE public.intervention_task ADD COLUMN optional BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute(
        """
        UPDATE public.intervention_task it
        SET optional = pgs.optional
        FROM public.preventive_plan_gamme_step pgs
        WHERE it.gamme_step_id = pgs.id
        """
    )

    # FK vers directus_users — pas de contrainte référentielle (Directus gère cette table)
    op.execute(
        "ALTER TABLE public.intervention_task "
        "ADD COLUMN assigned_to UUID REFERENCES public.directus_users (id) ON DELETE SET NULL"
    )

    op.execute("ALTER TABLE public.intervention_task ADD COLUMN due_date DATE")

    op.execute(
        "ALTER TABLE public.intervention_task ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
    op.execute(
        """
        UPDATE public.intervention_task it
        SET sort_order = pgs.sort_order
        FROM public.preventive_plan_gamme_step pgs
        WHERE it.gamme_step_id = pgs.id
        """
    )

    op.execute(
        "ALTER TABLE public.intervention_task "
        "ADD COLUMN created_by UUID REFERENCES public.directus_users (id) ON DELETE SET NULL"
    )

    op.execute(
        "ALTER TABLE public.intervention_task "
        "ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
    )

    op.execute(
        "ALTER TABLE public.intervention_task ALTER COLUMN updated_at SET DEFAULT NOW()"
    )

    # ── 5. Ajouter task_id sur intervention_action ────────────────
    op.execute(
        "ALTER TABLE public.intervention_action "
        "ADD COLUMN task_id UUID REFERENCES public.intervention_task (id) ON DELETE SET NULL"
    )

    # Migrer : la relation était inversée (intervention_task.action_id → intervention_action.id)
    # Désactiver le trigger le temps de la migration de données pour éviter la validation
    op.execute("ALTER TABLE public.intervention_action DISABLE TRIGGER ALL")
    op.execute(
        """
        UPDATE public.intervention_action ia
        SET task_id = it.id
        FROM public.intervention_task it
        WHERE it.action_id = ia.id
        """
    )
    op.execute("ALTER TABLE public.intervention_action ENABLE TRIGGER ALL")

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_intervention_action_task_id "
        "ON public.intervention_action (task_id)"
    )

    # ── 6. Renommer contraintes et index ──────────────────────────
    op.execute(
        "ALTER TABLE public.intervention_task "
        "RENAME CONSTRAINT gamme_step_validation_step_occurrence_key "
        "TO intervention_task_gamme_step_unique"
    )

    op.execute(
        "ALTER INDEX IF EXISTS idx_gamme_step_validation_intervention_id "
        "RENAME TO idx_intervention_task_intervention_id"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_gamme_step_validation_action_id "
        "RENAME TO idx_intervention_task_action_id"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_gamme_step_validation_status "
        "RENAME TO idx_intervention_task_status"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_intervention_task_assigned_to "
        "ON public.intervention_task (assigned_to)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_intervention_task_occurrence_id "
        "ON public.intervention_task (occurrence_id)"
    )

    # ── 7. Vérification finale ────────────────────────────────────
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM public.intervention_task WHERE label IS NULL")
    )
    null_count = result.scalar()
    if null_count > 0:
        logger.warning(
            "ATTENTION : %s ligne(s) dans intervention_task ont label IS NULL — "
            "à corriger manuellement avant de rendre la colonne NOT NULL.",
            null_count,
        )


def downgrade() -> None:
    # Supprimer les nouveaux index et colonnes
    op.execute("DROP INDEX IF EXISTS idx_intervention_task_occurrence_id")
    op.execute("DROP INDEX IF EXISTS idx_intervention_task_assigned_to")
    op.execute("DROP INDEX IF EXISTS idx_intervention_action_task_id")
    op.execute(
        "ALTER TABLE public.intervention_action DROP COLUMN IF EXISTS task_id")

    # Supprimer les nouvelles colonnes
    for col in ("created_at", "created_by", "sort_order", "due_date", "assigned_to", "optional", "origin", "label"):
        op.execute(
            f"ALTER TABLE public.intervention_task DROP COLUMN IF EXISTS {col}")

    # Remettre les statuts
    op.execute(
        "UPDATE public.intervention_task SET status = 'pending'   WHERE status = 'todo'")
    op.execute(
        "UPDATE public.intervention_task SET status = 'validated' WHERE status = 'done'")

    # Remettre les contraintes
    op.execute(
        "ALTER TABLE public.intervention_task DROP CONSTRAINT IF EXISTS intervention_task_skip_reason_check")
    op.execute(
        "ALTER TABLE public.intervention_task DROP CONSTRAINT IF EXISTS intervention_task_status_check")
    op.execute(
        "ALTER TABLE public.intervention_task "
        "ADD CONSTRAINT gamme_step_validation_skip_reason_check "
        "CHECK ((status != 'skipped') OR (skip_reason IS NOT NULL))"
    )

    # Remettre NOT NULL
    op.execute(
        "ALTER TABLE public.intervention_task ALTER COLUMN gamme_step_id SET NOT NULL")

    # Remettre les noms de colonnes
    op.execute(
        "ALTER TABLE public.intervention_task RENAME COLUMN closed_by TO validated_by")
    op.execute(
        "ALTER TABLE public.intervention_task RENAME COLUMN updated_at TO validated_at")
    op.execute(
        "ALTER TABLE public.intervention_task RENAME COLUMN gamme_step_id TO step_id")

    # Renommer la contrainte unique
    op.execute(
        "ALTER TABLE public.intervention_task "
        "RENAME CONSTRAINT intervention_task_gamme_step_unique "
        "TO gamme_step_validation_step_interv_key"
    )

    # Renommer les index
    op.execute(
        "ALTER INDEX IF EXISTS idx_intervention_task_intervention_id "
        "RENAME TO idx_gamme_step_validation_intervention_id"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_intervention_task_action_id "
        "RENAME TO idx_gamme_step_validation_action_id"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_intervention_task_status "
        "RENAME TO idx_gamme_step_validation_status"
    )

    # Renommer la table
    op.execute(
        "ALTER TABLE public.intervention_task RENAME TO gamme_step_validation")

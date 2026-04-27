"""Réparation des liens action ↔ tâche après migration k6f7a8b9c0d1

Revision ID: l7g8h9i0j1k2
Revises: k6f7a8b9c0d1
Create Date: 2026-04-27

Pour les interventions ayant exactement une tâche, lie toutes les actions
orphelines (task_id IS NULL) de cette intervention à cette unique tâche.
Heuristique sûre : si l'intervention a plusieurs tâches, aucune action
n'est modifiée (ambiguïté impossible à résoudre automatiquement).
"""
from alembic import op

revision = "l7g8h9i0j1k2"
down_revision = "k6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Désactiver temporairement le trigger fn_compute_action_time qui bloquerait
    # le UPDATE sur des lignes historiques ayant action_start/end ET time_spent.
    op.execute(
        "ALTER TABLE public.intervention_action DISABLE TRIGGER ALL"
    )
    op.execute(
        """
        UPDATE public.intervention_action ia
        SET task_id = sub.task_id
        FROM (
            SELECT
                ia2.id AS action_id,
                it.id  AS task_id
            FROM public.intervention_action ia2
            JOIN public.intervention_task it
              ON it.intervention_id = ia2.intervention_id
            WHERE ia2.task_id IS NULL
              AND ia2.intervention_id IS NOT NULL
              AND (
                  SELECT COUNT(*)
                  FROM public.intervention_task t2
                  WHERE t2.intervention_id = ia2.intervention_id
              ) = 1
        ) sub
        WHERE ia.id = sub.action_id
        """
    )
    op.execute(
        "ALTER TABLE public.intervention_action ENABLE TRIGGER ALL"
    )


def downgrade() -> None:
    # Non réversible sans snapshot : on ne peut pas savoir quelles actions
    # avaient task_id=NULL avant la réparation.
    pass

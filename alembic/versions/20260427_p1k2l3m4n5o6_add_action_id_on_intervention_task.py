"""add_action_id_on_intervention_task

Le modèle task_id sur intervention_action (one action → one task) ne supporte
pas le cas où une seule action couvre plusieurs tâches. On ajoute action_id
sur intervention_task (many tasks → one action) pour permettre ce lien.
task_id sur intervention_action est conservé mais n'est plus utilisé en écriture.

Revision ID: p1k2l3m4n5o6
Revises: o0j1k2l3m4n5
Create Date: 2026-04-27 00:00:00.000000
"""
from __future__ import annotations

from typing import Union

from alembic import op


revision: str = "p1k2l3m4n5o6"
down_revision: Union[str, None] = "o0j1k2l3m4n5"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE public.intervention_task
            ADD COLUMN IF NOT EXISTS action_id UUID
            REFERENCES public.intervention_action (id) ON DELETE SET NULL
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_intervention_task_action_id
            ON public.intervention_task (action_id)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_intervention_task_action_id")
    op.execute(
        "ALTER TABLE public.intervention_task DROP COLUMN IF EXISTS action_id"
    )

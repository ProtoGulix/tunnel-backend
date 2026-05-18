"""Ajouter les raisons d'audit système pour les mutations de tâches

Revision ID: 004_audit_task_reasons
Revises: 003_m2m_action_task
Create Date: 2026-05-13
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "004_audit_task_reasons"
down_revision: Union[str, None] = "003_m2m_action_task"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO audit_reason_code
            (code, label, category, entity_types, color, description)
        VALUES
            ('TASK_CREATED',    'Tâche créée',               'system', ARRAY['task'], '#10b981', 'Création automatique ou manuelle d''une tâche'),
            ('TASK_UPDATED',    'Tâche modifiée',             'system', ARRAY['task'], '#6366f1', 'Modification d''un champ de la tâche (label, date, affectation…)'),
            ('TASK_STATUS',     'Changement de statut tâche', 'system', ARRAY['task'], '#f59e0b', 'Transition de statut : todo → in_progress → done / skipped'),
            ('TASK_DELETED',    'Tâche supprimée',            'system', ARRAY['task'], '#ef4444', 'Suppression d''une tâche manuelle')
        ON CONFLICT (code) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM audit_reason_code
        WHERE code IN ('TASK_CREATED', 'TASK_UPDATED', 'TASK_STATUS', 'TASK_DELETED')
    """)

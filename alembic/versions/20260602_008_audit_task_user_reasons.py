"""Ajouter les raisons utilisateur pour les mutations explicites de tâches

due_date et assigned_to nécessitent une raison visible dans le dialog d'audit.

Revision ID: 008_audit_task_user_reasons
Revises: 007_audit_silent_routine
Create Date: 2026-06-02
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "008_audit_task_user_reasons"
down_revision: Union[str, None] = "007_audit_silent_routine"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # Resync sequence in case it drifted (e.g. manual inserts bypassed it)
    op.execute("SELECT setval('audit_reason_code_id_seq', (SELECT MAX(id) FROM audit_reason_code))")

    for code, label, category, entity_types, color, description in [
        ('PLANNING_CHANGE',  'Changement de planning',  'user', 'ARRAY[\'task\']', '#3b82f6', 'La date ou le technicien a ete modifie suite a une reorganisation du planning'),
        ('TECH_UNAVAILABLE', 'Technicien indisponible', 'user', 'ARRAY[\'task\']', '#f97316', 'Le technicien assigne nest plus disponible (absence, surcharge)'),
        ('PRIORITY_CHANGE',  'Changement de priorite',  'user', 'ARRAY[\'task\']', '#8b5cf6', 'La tache est reprogrammee ou reassignee suite a une nouvelle priorite'),
    ]:
        op.execute(f"""
            INSERT INTO audit_reason_code (code, label, category, entity_types, color, description)
            SELECT '{code}', '{label}', '{category}', {entity_types}, '{color}', '{description}'
            WHERE NOT EXISTS (SELECT 1 FROM audit_reason_code WHERE code = '{code}')
        """)
    # OTHER existe peut-être déjà — on s'assure juste qu'il couvre aussi 'task'
    op.execute("""
        UPDATE audit_reason_code
        SET entity_types = array_append(entity_types, 'task')
        WHERE code = 'OTHER'
          AND (entity_types IS NULL OR NOT 'task' = ANY(entity_types))
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM audit_reason_code
        WHERE code IN ('PLANNING_CHANGE', 'TECH_UNAVAILABLE', 'PRIORITY_CHANGE')
        AND 'task' = ANY(entity_types)
    """)

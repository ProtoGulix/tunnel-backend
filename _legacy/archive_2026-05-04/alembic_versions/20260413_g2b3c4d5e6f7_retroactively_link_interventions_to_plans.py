"""retroactively_link_interventions_to_plans

Fixes interventions générées automatiquement par occurrence préventive
qui n'ont pas reçu le plan_id lors de leur création.

Liaise les interventions à leur plan via preventive_occurrence.

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-04-13 15:00:00.000000
"""
from __future__ import annotations

from typing import Union

from alembic import op


revision: str = "g2b3c4d5e6f7"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # Link interventions to their preventive plan via preventive_occurrence
    op.execute("""
        UPDATE public.intervention i
        SET plan_id = po.plan_id
        FROM public.preventive_occurrence po
        WHERE i.id = po.intervention_id
          AND i.plan_id IS NULL
          AND po.plan_id IS NOT NULL
    """)


def downgrade() -> None:
    # Downgrade: revert plan_id to NULL for interventions linked via occurrence
    # (risky operation, skip for safety)
    pass

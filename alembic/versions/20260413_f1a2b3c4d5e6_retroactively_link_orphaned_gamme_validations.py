"""retroactively_link_orphaned_gamme_validations

Corrects orphaned gamme_step_validation records by linking them to their
parent intervention through preventive_occurrence.

The issue: when a preventive DI was manually accepted, the code updated
gamme_step_validation.intervention_id, but forgot to update
preventive_occurrence.intervention_id. This migration fixes both.

Revision ID: f1a2b3c4d5e6
Revises: e91c4a7b2f16
Create Date: 2026-04-13 14:00:00.000000
"""
from __future__ import annotations

from typing import Union

from alembic import op


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e91c4a7b2f16"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # 1) Link preventive_occurrence to interventions via di_id
    op.execute("""
        UPDATE public.preventive_occurrence po
        SET intervention_id = (
            SELECT intervention_id
            FROM public.intervention_request ir
            WHERE ir.id = po.di_id
        )
        WHERE po.di_id IS NOT NULL
          AND po.intervention_id IS NULL
          AND (SELECT intervention_id FROM public.intervention_request ir WHERE ir.id = po.di_id) IS NOT NULL
    """)

    # 2) Link gamme_step_validation to interventions via occurrence
    op.execute("""
        UPDATE public.gamme_step_validation gsv
        SET intervention_id = po.intervention_id
        FROM public.preventive_occurrence po
        WHERE gsv.occurrence_id = po.id
          AND gsv.intervention_id IS NULL
          AND po.intervention_id IS NOT NULL
    """)


def downgrade() -> None:
    # Downgrade: revert orphaned gamme_step_validation back to NULL if they were
    # previously orphaned. Since we don't track history, we can only revert
    # by checking if intervention_id matches the parent occurrence's intervention_id
    # and if there's no direct intervention_id, set to NULL (risky operation).
    #
    # For safety, we don't downgrade - this is a data correction, not a schema change.
    pass

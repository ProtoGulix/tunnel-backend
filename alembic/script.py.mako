"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from __future__ import annotations

from typing import Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# ---------------------------------------------------------------------------
# Identifiants Alembic
# ---------------------------------------------------------------------------
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, tuple[str, ...], None] = ${repr(branch_labels)}
depends_on: Union[str, tuple[str, ...], None] = ${repr(depends_on)}


# ---------------------------------------------------------------------------
# UPGRADE — appliquer la migration
# ---------------------------------------------------------------------------
def upgrade() -> None:
    # Écrire du SQL brut avec op.execute() :
    #
    #   op.execute("""
    #       ALTER TABLE public.machine
    #           ADD COLUMN IF NOT EXISTS nouveau_champ TEXT;
    #   """)
    #
    # Pour des instructions complexes (DO $$...$$, CREATE FUNCTION, etc.)
    # les insérer telles quelles dans la chaîne.
    pass


# ---------------------------------------------------------------------------
# DOWNGRADE — annuler la migration
# ---------------------------------------------------------------------------
def downgrade() -> None:
    # op.execute("""
    #     ALTER TABLE public.machine
    #         DROP COLUMN IF EXISTS nouveau_champ;
    # """)
    pass

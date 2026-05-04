"""add_is_system_and_suggested_type_inter_to_intervention_request

Ajoute sur intervention_request :
  - is_system             BOOLEAN NOT NULL DEFAULT FALSE
  - suggested_type_inter  VARCHAR(255) + CHECK sur les types valides
  - index filtré idx_intervention_request_is_system

Valeurs du CHECK issues de api/constants.INTERVENTION_TYPE_IDS :
  CUR, PRE, REA, BAT, PRO, COF, PIL, MES

Revision ID: d2a7b3c0e15f
Revises: c4f8a2e1d09b
Create Date: 2026-04-13 00:00:00.000000
"""
from __future__ import annotations
from typing import Union
from alembic import op

revision: str = "d2a7b3c0e15f"
down_revision: Union[str, None] = "c4f8a2e1d09b"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Nouvelles colonnes
    # -------------------------------------------------------------------------
    op.execute("""
        ALTER TABLE public.intervention_request
            ADD COLUMN IF NOT EXISTS is_system BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS suggested_type_inter VARCHAR(255)
    """)

    # -------------------------------------------------------------------------
    # 2. Contrainte CHECK sur suggested_type_inter
    # -------------------------------------------------------------------------
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'chk_suggested_type_inter'
                  AND conrelid = 'public.intervention_request'::regclass
            ) THEN
                ALTER TABLE public.intervention_request
                    ADD CONSTRAINT chk_suggested_type_inter
                    CHECK (
                        suggested_type_inter IS NULL
                        OR suggested_type_inter IN ('CUR', 'PRE', 'REA', 'BAT', 'PRO', 'COF', 'PIL', 'MES')
                    );
            END IF;
        END
        $$
    """)

    # -------------------------------------------------------------------------
    # 3. Index filtré sur is_system = TRUE
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_intervention_request_is_system
            ON public.intervention_request (is_system)
            WHERE is_system = TRUE
    """)

    # -------------------------------------------------------------------------
    # 4. Commentaires
    # -------------------------------------------------------------------------
    op.execute("""
        COMMENT ON COLUMN public.intervention_request.is_system IS
            'TRUE si la DI a été créée automatiquement par le système (scheduler préventif ou autre source non humaine). Governe les règles de transition : une DI système ne peut pas être rejetée sans rôle RESP.'
    """)
    op.execute("""
        COMMENT ON COLUMN public.intervention_request.suggested_type_inter IS
            'Type d''intervention suggéré à la création. Utilisé comme valeur par défaut lors de la transition acceptee si le payload ne fournit pas de type_inter. Valeur forcée et non écrasable si is_system = TRUE et rôle insuffisant.'
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_intervention_request_is_system")
    op.execute("""
        ALTER TABLE public.intervention_request
            DROP CONSTRAINT IF EXISTS chk_suggested_type_inter
    """)
    op.execute("""
        ALTER TABLE public.intervention_request
            DROP COLUMN IF EXISTS suggested_type_inter,
            DROP COLUMN IF EXISTS is_system
    """)

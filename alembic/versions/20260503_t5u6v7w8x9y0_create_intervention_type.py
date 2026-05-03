"""create_intervention_type — référentiel des types d'intervention

Revision ID: t5u6v7w8x9y0
Revises: s4t5u6v7w8x9
Create Date: 2026-05-03

Crée la table intervention_type et la peuple avec les 8 types
définis dans api/constants.py INTERVENTION_TYPES.
"""
from alembic import op

revision = 't5u6v7w8x9y0'
down_revision = 's4t5u6v7w8x9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.intervention_type (
            id        SERIAL      PRIMARY KEY,
            code      VARCHAR(10) NOT NULL UNIQUE,
            label     TEXT        NOT NULL,
            color     VARCHAR(30),
            is_active BOOLEAN     NOT NULL DEFAULT true
        )
    """)

    op.execute("""
        COMMENT ON TABLE public.intervention_type
            IS 'Référentiel des types d''intervention maintenance'
    """)

    op.execute("""
        INSERT INTO public.intervention_type (code, label, color) VALUES
            ('CUR', 'Curatif',              'red'),
            ('PRE', 'Préventif',            'green'),
            ('REA', 'Réapprovisionnement',  'blue'),
            ('BAT', 'Batiment',             'gray'),
            ('PRO', 'Projet',               'blue'),
            ('COF', 'Remise en conformité', 'amber'),
            ('PIL', 'Pilotage',             'blue'),
            ('MES', 'Mise en service',      'amber')
        ON CONFLICT (code) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.intervention_type")

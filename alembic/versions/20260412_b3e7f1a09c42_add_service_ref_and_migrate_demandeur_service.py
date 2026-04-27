"""add_service_ref_and_migrate_demandeur_service

Cree la table referentielle `service`, renomme `demandeur_service` en
`demandeur_service_legacy` sur `intervention_request`, ajoute la FK
`service_id` et tente un mapping automatique des donnees existantes.

Revision ID: b3e7f1a09c42
Revises: a1b2c3d4e5f0
Create Date: 2026-04-12 00:00:00.000000
"""
from __future__ import annotations
from typing import Union
from alembic import op

revision: str = "b3e7f1a09c42"
down_revision: Union[str, None] = "a1b2c3d4e5f0"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE service (
            id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code      VARCHAR(50)  UNIQUE NOT NULL,
            label     TEXT         NOT NULL,
            is_active BOOLEAN      NOT NULL DEFAULT TRUE
        )
    """)
    op.execute("""
        INSERT INTO service (code, label) VALUES
            ('PROD',  'Production'),
            ('MAINT', 'Maintenance'),
            ('LOGIS', 'Logistique'),
            ('QHSE',  'QHSE'),
            ('ADMIN', 'Administration'),
            ('INFRA', 'Infrastructure / Bâtiment'),
            ('IT',    'Informatique')
    """)
    op.execute("""
        ALTER TABLE intervention_request
            RENAME COLUMN demandeur_service TO demandeur_service_legacy
    """)
    op.execute("""
        ALTER TABLE intervention_request
            ADD COLUMN service_id UUID REFERENCES service(id) ON DELETE SET NULL
    """)
    op.execute("""
        UPDATE intervention_request ir
        SET service_id = s.id
        FROM service s
        WHERE LOWER(TRIM(ir.demandeur_service_legacy)) = LOWER(s.label)
           OR UPPER(TRIM(ir.demandeur_service_legacy)) = s.code
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE intervention_request DROP COLUMN service_id")
    op.execute("""
        ALTER TABLE intervention_request
            RENAME COLUMN demandeur_service_legacy TO demandeur_service
    """)
    op.execute("DROP TABLE service")

"""Ajoute le suivi de la dernière version du changelog vue par l'utilisateur

Nécessaire pour la fonctionnalité "Nouveautés" : à la connexion, le frontend
demande au backend quelles entrées du CHANGELOG.md afficher depuis la
dernière visite de l'utilisateur. On ne stocke qu'un numéro de version
(jamais le contenu du changelog, qui reste la source unique de vérité).

Revision ID: 015_user_last_seen_changelog
Revises: 014_supplier_order_total_trigger
Create Date: 2026-07-15
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "015_user_last_seen_changelog"
down_revision: Union[str, None] = "014_supplier_order_total_trigger"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE tunnel_user
        ADD COLUMN IF NOT EXISTS last_seen_changelog_version VARCHAR(20)
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE tunnel_user
        DROP COLUMN IF EXISTS last_seen_changelog_version
    """)

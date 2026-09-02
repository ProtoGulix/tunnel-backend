"""Active l'extension unaccent pour des recherches insensibles aux accents

Les endpoints de recherche (parts, suppliers, equipements, interventions,
users, ...) utilisent ILIKE, qui est déjà insensible à la casse mais pas
aux accents : chercher "secable" ne trouvait pas "sécable". L'extension
unaccent() ajoute une fonction SQL permettant de normaliser les accents
des deux côtés de la comparaison (api/utils/search.py).

Revision ID: 022_enable_unaccent_extension
Revises: 021_purchase_request_user_refs
Create Date: 2026-09-02
"""
from __future__ import annotations

from typing import Union

from alembic import op

revision: str = "022_enable_unaccent_extension"
down_revision: Union[str, None] = "021_purchase_request_user_refs"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent")

"""Baseline propre — schéma complet extrait de la prod (2026-05-04)

Source de vérité unique : schema_current.sql à la racine du dépôt.
Tous les anciens fichiers SQL (01_core/, 02_ref/, etc.) et les migrations
manuelles (migrations/) sont archivés dans _legacy/ et ne sont plus exécutés.

Pour une NOUVELLE installation  : alembic upgrade head
Pour une BASE DÉJÀ EN PRODUCTION : alembic stamp 000_baseline_clean

Revision ID: 000_baseline_clean
Revises: (première révision de la nouvelle chaîne)
Create Date: 2026-05-04
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from alembic import op

revision: str = "000_baseline_clean"
down_revision: Union[str, None] = None
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None

_SCHEMA_FILE = Path(__file__).resolve().parent.parent.parent / "schema_current.sql"


def upgrade() -> None:
    if not _SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"schema_current.sql introuvable : {_SCHEMA_FILE}\n"
            "Régénérer avec : python scripts/dump_schema.py"
        )
    sql = _SCHEMA_FILE.read_text(encoding="utf-8").strip()
    if sql:
        op.execute(sql)


def downgrade() -> None:
    op.execute("DROP SCHEMA public CASCADE")
    op.execute("CREATE SCHEMA public")
    op.execute("GRANT ALL ON SCHEMA public TO public")

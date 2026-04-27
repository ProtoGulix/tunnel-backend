"""
convert_to_alembic.py — Convertit les migrations historiques en révisions Alembic
==================================================================================
Génère un fichier de révision Alembic pour chaque dossier migrations/v*_to_v*/
en s'appuyant sur les up.sql et down.sql existants.

La chaîne générée part de la révision baseline (a1b2c3d4e5f0) et parcourt
tous les dossiers dans l'ordre chronologique.

Usage :
    python scripts/convert_to_alembic.py [--dry-run] [--output-dir PATH]

Options :
    --dry-run        Affiche les fichiers qui seraient créés sans les écrire.
    --output-dir     Répertoire de sortie (défaut : alembic/versions/).
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime
from pathlib import Path
from textwrap import indent

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = REPO_ROOT / "migrations"
VERSIONS_DIR = REPO_ROOT / "alembic" / "versions"
BASELINE_REVISION = "a1b2c3d4e5f0"

# Ordre canonique des dossiers de migration (chronologique)
MIGRATION_ORDER = [
    "v1.0.0_to_v1.1.0",
    "v1.1.0_to_v1.2.0",
    "v1.2.0_to_v1.2.1",
    "v1.2.1_to_v1.3.0",
    "v1.3.0_to_v1.4.0",
    "v1.4.0_to_v1.4.1",
    "v1.4.1_to_v1.5.0",
    "v1.5.0_to_v1.6.0",
    "v1.6.0_to_v1.7.0",
    "v1.7.0_to_v1.8.0",
    "v1.8.0_to_v1.9.0",
    "v1.9.0_to_v1.9.1",
    "v1.9.1_to_v1.10.0",
    "v1.10.0_to_v1.11.0",
    "v1.11.0_to_v1.11.1",
    "v1.11.1_to_v1.12.0",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _revision_id(folder_name: str) -> str:
    """Génère un ID de révision Alembic déterministe (12 hex) à partir du nom du dossier."""
    return hashlib.sha256(folder_name.encode()).hexdigest()[:12]


def _slug(folder_name: str) -> str:
    """Transforme 'v1.2.1_to_v1.3.0' en 'upgrade_v1_2_1_to_v1_3_0'."""
    clean = re.sub(r"[^a-z0-9]+", "_", folder_name.lower()).strip("_")
    return f"upgrade_{clean}"


def _quote_sql(sql: str) -> str:
    """Échappe un bloc SQL pour l'intégrer dans une triple-quote Python."""
    # Éviter des fermetures accidentelles de triple-quote
    return sql.replace('"""', '\"\"\"')


def _render_revision(
    revision: str,
    down_revision: str | None,
    folder_name: str,
    up_sql: str,
    down_sql: str,
    create_date: str,
) -> str:
    """Génère le contenu complet du fichier de révision Alembic."""
    slug = _slug(folder_name)
    down_rev_repr = repr(down_revision)

    # Indentation du SQL embarqué
    up_sql_indented = indent(up_sql.strip(), "    ")
    down_sql_indented = indent(down_sql.strip(), "    ")

    return f'''\
"""Migration historique : {folder_name}

Converti automatiquement depuis migrations/{folder_name}/up.sql et down.sql.

Revision ID: {revision}
Revises: {down_revision}
Create Date: {create_date}
"""
from __future__ import annotations

from typing import Union

from alembic import op

# ---------------------------------------------------------------------------
# Identifiants Alembic
# ---------------------------------------------------------------------------
revision: str = "{revision}"
down_revision: Union[str, None] = {down_rev_repr}
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


# ---------------------------------------------------------------------------
# UPGRADE — {folder_name}
# ---------------------------------------------------------------------------
def upgrade() -> None:
    op.execute("""
{up_sql_indented}
    """)


# ---------------------------------------------------------------------------
# DOWNGRADE — rollback {folder_name}
# ---------------------------------------------------------------------------
def downgrade() -> None:
    op.execute("""
{down_sql_indented}
    """)
'''


def _get_create_date(folder_name: str) -> str:
    """Retourne une date de création fictive basée sur le nom de version."""
    return f"2026-01-01 00:00:00.000000 (converti le {datetime.now():%Y-%m-%d})"


# ---------------------------------------------------------------------------
# Logique principale
# ---------------------------------------------------------------------------
def convert_migrations(output_dir: Path, dry_run: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Détecter les dossiers disponibles
    available = {d.name for d in MIGRATIONS_DIR.iterdir() if d.is_dir()}
    missing = [f for f in MIGRATION_ORDER if f not in available]
    if missing:
        print(
            f"⚠️  Dossiers introuvables dans migrations/ : {missing}", file=sys.stderr)

    prev_revision: str | None = BASELINE_REVISION

    for i, folder_name in enumerate(MIGRATION_ORDER):
        folder = MIGRATIONS_DIR / folder_name
        if not folder.exists():
            print(f"  [SKIP] {folder_name} — dossier introuvable")
            continue

        up_file = folder / "up.sql"
        down_file = folder / "down.sql"

        if not up_file.exists():
            print(f"  [SKIP] {folder_name} — up.sql introuvable")
            continue
        if not down_file.exists():
            print(
                f"  [WARN] {folder_name} — down.sql introuvable, downgrade() sera vide")

        up_sql = up_file.read_text(encoding="utf-8")
        down_sql = down_file.read_text(
            encoding="utf-8") if down_file.exists() else "-- Pas de rollback disponible\n"

        rev_id = _revision_id(folder_name)
        slug = _slug(folder_name)
        date_str = _get_create_date(folder_name)

        content = _render_revision(
            revision=rev_id,
            down_revision=prev_revision,
            folder_name=folder_name,
            up_sql=up_sql,
            down_sql=down_sql,
            create_date=date_str,
        )

        # Nommage : 20260412_<rev>_<slug>.py
        filename = f"20260412_{rev_id}_{slug}.py"
        out_file = output_dir / filename

        if dry_run:
            print(
                f"  [DRY-RUN] Serait créé : {out_file.relative_to(REPO_ROOT)}")
        else:
            if out_file.exists():
                print(f"  [SKIP] {filename} — existe déjà")
            else:
                out_file.write_text(content, encoding="utf-8")
                print(f"  [OK]   {filename}")

        prev_revision = rev_id

    if not dry_run:
        print(f"\n✅  Révision head : {prev_revision}")
        print("   Mettez à jour alembic.ini ou utilisez : alembic stamp head")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convertit les migrations historiques en révisions Alembic."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche les fichiers qui seraient créés sans les écrire.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=VERSIONS_DIR,
        help=f"Répertoire de sortie (défaut : {VERSIONS_DIR})",
    )
    args = parser.parse_args()

    print(f"Conversion des migrations historiques → Alembic")
    print(f"Output : {args.output_dir}")
    print(f"Dry run : {args.dry_run}")
    print()

    convert_migrations(output_dir=args.output_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

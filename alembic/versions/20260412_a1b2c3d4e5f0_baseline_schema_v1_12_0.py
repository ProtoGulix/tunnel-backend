"""Baseline schema — v1.12.0

Révision de référence représentant le schéma complet à la version 1.12.0.

Pour une NOUVELLE installation  : alembic upgrade head
  → exécute upgrade() qui charge tous les fichiers SQL du dépôt.

Pour une BASE DÉJÀ EN PRODUCTION : alembic stamp head
  → marque la base comme étant à jour sans rien exécuter.

Revision ID: a1b2c3d4e5f0
Revises: (première révision, pas de parent)
Create Date: 2026-04-12 00:00:00.000000
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from alembic import op

# ---------------------------------------------------------------------------
# Identifiants Alembic
# ---------------------------------------------------------------------------
revision: str = "a1b2c3d4e5f0"
down_revision: Union[str, None] = None
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None

# Racine du dépôt (deux niveaux au-dessus : alembic/versions/ → alembic/ → racine)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_sql(rel_path: str) -> str:
    """Lit un fichier SQL relatif à la racine du dépôt."""
    return (_REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _sql_files_ordered() -> list[str]:
    """
    Retourne la liste ordonnée des fichiers SQL à exécuter pour un fresh install.
    L'ordre suit db_import.sql : extensions → core → ref → meta → preventive → triggers.
    """
    # -- 00 Extensions -------------------------------------------------------
    files = ["00_extensions.sql"]

    # -- 01 Core (ordre de db_import.sql) ------------------------------------
    core_ordered = [
        "intervention_action.sql",
        "intervention_action_purchase_request.sql",
        "intervention_request.sql",
        "request_status_log.sql",
        "intervention_part.sql",
        "intervention_status_log.sql",
        "intervention.sql",
        "location.sql",
        "machine.sql",
        "manufacturer_item.sql",
        "purchase_request.sql",
        "stock_item_standard_spec.sql",
        "stock_item_supplier.sql",
        "stock_item.sql",
        "subtask.sql",
        "supplier_order_line_purchase_request.sql",
        "supplier_order_line.sql",
        "supplier_order.sql",
        "supplier.sql",
    ]
    # Ajouter les fichiers de 01_core/ non encore listés (ex : ajouts futurs)
    core_dir = _REPO_ROOT / "01_core"
    listed = set(core_ordered)
    extras = sorted(f.name for f in core_dir.glob(
        "*.sql") if f.name not in listed)
    for name in core_ordered + extras:
        files.append(f"01_core/{name}")

    # -- 02 Ref (ordre de db_import.sql) -------------------------------------
    ref_ordered = [
        "action_category.sql",
        "action_subcategory.sql",
        "complexity_factor.sql",
        "equipement_statuts.sql",
        "equipment_class.sql",
        "intervention_status_ref.sql",
        "part_template_field_enum.sql",
        "part_template_field.sql",
        "part_template.sql",
        "purchase_status.sql",
        "request_status_ref.sql",
        "stock_family.sql",
        "stock_sub_family_template.sql",
        "stock_sub_family.sql",
    ]
    ref_dir = _REPO_ROOT / "02_ref"
    listed = set(ref_ordered)
    extras = sorted(f.name for f in ref_dir.glob(
        "*.sql") if f.name not in listed)
    for name in ref_ordered + extras:
        files.append(f"02_ref/{name}")

    # -- 03 Meta -------------------------------------------------------------
    meta_ordered = [
        "action_category_meta.sql",
        "action_classification_probe.sql",
        "anomaly_threshold.sql",
        "seed_meta_configuration.sql",
    ]
    meta_dir = _REPO_ROOT / "03_meta"
    listed = set(meta_ordered)
    extras = sorted(f.name for f in meta_dir.glob(
        "*.sql") if f.name not in listed)
    for name in meta_ordered + extras:
        files.append(f"03_meta/{name}")

    # -- 04 Preventive -------------------------------------------------------
    preventive_ordered = [
        "detect_preventive_function.sql",
        "preventive_rule.sql",
        "preventive_suggestion.sql",
    ]
    preventive_dir = _REPO_ROOT / "04_preventive"
    listed = set(preventive_ordered)
    extras = sorted(
        f.name for f in preventive_dir.glob("*.sql") if f.name not in listed
    )
    for name in preventive_ordered + extras:
        files.append(f"04_preventive/{name}")

    # -- 05 Triggers (99_foreign_keys.sql doit être dernier) -----------------
    triggers_dir = _REPO_ROOT / "05_triggers"
    trigger_files = sorted(
        f.name
        for f in triggers_dir.glob("*.sql")
        if not f.name.startswith("test_")         # ignorer les fichiers test_*
        and f.name != "99_foreign_keys.sql"
    )
    for name in trigger_files:
        files.append(f"05_triggers/{name}")
    files.append("05_triggers/99_foreign_keys.sql")  # toujours en dernier

    return files


# ---------------------------------------------------------------------------
# UPGRADE — crée le schéma complet (fresh install)
# ---------------------------------------------------------------------------
def upgrade() -> None:
    for rel_path in _sql_files_ordered():
        sql_file = _REPO_ROOT / rel_path
        if not sql_file.exists():
            raise FileNotFoundError(
                f"Fichier SQL introuvable pendant le baseline : {rel_path}"
            )
        sql = sql_file.read_text(encoding="utf-8").strip()
        if sql:
            op.execute(sql)


# ---------------------------------------------------------------------------
# DOWNGRADE — supprime tout le schéma public (opération destructive !)
# ---------------------------------------------------------------------------
def downgrade() -> None:
    # ⚠️  DESTRUCTIF — supprime toutes les tables, fonctions, triggers, etc.
    op.execute("DROP SCHEMA public CASCADE")
    op.execute("CREATE SCHEMA public")
    op.execute("GRANT ALL ON SCHEMA public TO public")

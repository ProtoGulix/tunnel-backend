"""
Consolidation de la base de données — Option A "Clean slate"

Ce script :
1. Archive les anciens dossiers SQL et migrations dans _legacy/
2. Supprime les anciennes versions Alembic de la chaîne
3. Met a jour alembic.ini pour pointer sur la nouvelle chaîne
4. Regenere schema_current.sql depuis la base active

Usage : python scripts/consolidate_db.py [--dry-run]
"""
from __future__ import annotations

import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGACY = ROOT / "_legacy"
DRY_RUN = "--dry-run" in sys.argv

DIRS_TO_ARCHIVE = [
    "01_core",
    "02_ref",
    "03_meta",
    "04_preventive",
    "05_triggers",
    "migrations",
]

FILES_TO_ARCHIVE = [
    "db_import.sql",
    "00_extensions.sql",
]

OLD_ALEMBIC_VERSIONS = [
    "20260412_a1b2c3d4e5f0_baseline_schema_v1_12_0.py",
    "20260412_b3e7f1a09c42_add_service_ref_and_migrate_demandeur_service.py",
    "20260413_c4f8a2e1d09b_add_preventive_v2_schema.py",
    "20260413_d2a7b3c0e15f_add_is_system_and_suggested_type_inter.py",
    "20260413_e91c4a7b2f16_add_preventive_v2_addendum_02.py",
    "20260413_f1a2b3c4d5e6_retroactively_link_orphaned_gamme_validations.py",
    "20260413_g2b3c4d5e6f7_retroactively_link_interventions_to_plans.py",
    "20260414_h3c4d5e6f7a8_trg_sync_status_log_to_intervention.py",
    "20260415_i4d5e6f7a8b9_drop_redundant_trg_sync_status_from_log.py",
    "20260425_i4d5e6f7g8h9_rename_gamme_step_validation_to_intervention_task.py",
    "20260426_j5e6f7a8b9c0_revert_task_id_on_action_use_action_id_on_task.py",
    "20260426_k6f7a8b9c0d1_task_id_on_action_one_task_many_actions.py",
    "20260427_l7g8h9i0j1k2_repair_action_task_links.py",
    "20260427_m8h9i0j1k2l3_fix_trg_compute_action_time_column_filter.py",
    "20260427_n9i0j1k2l3m4_fix_trg_sync_status_log_use_id_not_code.py",
    "20260427_o0j1k2l3m4n5_fix_trg_check_closable_use_intervention_task.py",
    "20260427_p1k2l3m4n5o6_add_action_id_on_intervention_task.py",
    "20260428_q2r3s4t5u6v7_add_tech_id_to_intervention.py",
    "20260430_r3s4t5u6v7w8_merge_branch_i4d5_et_q2r3.py",
    "20260503_s4t5u6v7w8x9_auth_sovereign_v3.py",
    "20260503_t5u6v7w8x9y0_create_intervention_type.py",
    "20260503_u6v7w8x9y0z1_api_keys.py",
]


def log(msg: str):
    prefix = "[DRY-RUN] " if DRY_RUN else ""
    print(f"{prefix}{msg}")


def archive_dir(src: Path, dst: Path):
    if not src.exists():
        print(f"  SKIP (inexistant) : {src.name}")
        return
    log(f"  Archive : {src} -> {dst}")
    if not DRY_RUN:
        shutil.copytree(src, dst, dirs_exist_ok=True)
        shutil.rmtree(src)


def archive_file(src: Path, dst_dir: Path):
    if not src.exists():
        print(f"  SKIP (inexistant) : {src.name}")
        return
    log(f"  Archive : {src.name} -> _legacy/")
    if not DRY_RUN:
        shutil.copy2(src, dst_dir / src.name)
        src.unlink()


def archive_alembic_version(fname: str, dst_dir: Path):
    src = ROOT / "alembic" / "versions" / fname
    if not src.exists():
        print(f"  SKIP (inexistant) : {fname}")
        return
    log(f"  Archive alembic : {fname}")
    if not DRY_RUN:
        shutil.copy2(src, dst_dir / fname)
        src.unlink()


def main():
    today = date.today().isoformat()
    legacy_run = LEGACY / f"archive_{today}"

    print("=" * 60)
    print("CONSOLIDATION DB — Option A Clean Slate")
    print(f"Archive destination : {legacy_run}")
    if DRY_RUN:
        print("MODE DRY-RUN : aucune modification effectuee")
    print("=" * 60)

    # 1. Creer le dossier d'archive
    if not DRY_RUN:
        legacy_run.mkdir(parents=True, exist_ok=True)
        (legacy_run / "alembic_versions").mkdir(exist_ok=True)
        (legacy_run / "sql_dirs").mkdir(exist_ok=True)

    # 2. Archiver les dossiers SQL
    print("\n[1/3] Archivage des anciens dossiers SQL...")
    for d in DIRS_TO_ARCHIVE:
        archive_dir(ROOT / d, legacy_run / "sql_dirs" / d)
    for f in FILES_TO_ARCHIVE:
        archive_file(ROOT / f, legacy_run / "sql_dirs")

    # 3. Archiver les anciennes versions Alembic
    print("\n[2/3] Archivage des anciennes versions Alembic...")
    for fname in OLD_ALEMBIC_VERSIONS:
        archive_alembic_version(fname, legacy_run / "alembic_versions")

    # 4. Regenerer schema_current.sql
    print("\n[3/3] Regeneration de schema_current.sql depuis la base active...")
    if not DRY_RUN:
        import subprocess
        result = subprocess.run(
            ["python", "scripts/dump_schema.py"],
            cwd=ROOT, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ERREUR dump_schema.py :\n{result.stderr}")
            sys.exit(1)
        print(f"  {result.stdout.strip()}")
    else:
        log("  python scripts/dump_schema.py")

    print("\nConsolidation terminee.")
    print("\nProchaines etapes :")
    print("  - Sur une NOUVELLE installation : alembic upgrade head")
    print("  - Sur une BASE EXISTANTE        : alembic stamp 000_baseline_clean")

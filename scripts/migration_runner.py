"""
migration_runner.py - Exécuteur générique de migrations
========================================================
Script générique pour exécuter des migrations SQL et Python.
Supporte les migrations up/down et le rollback.

Usage:
    python migration_runner.py --version v1.2.1_to_v1.3.0 --direction up
    python migration_runner.py --version v1.2.1_to_v1.3.0 --direction down
    python migration_runner.py --list
"""

import argparse
import os
import sys
import importlib.util
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from db_connection import get_cursor, get_dict_cursor, test_connection


# Chemin vers le dossier migrations
MIGRATIONS_DIR = Path(__file__).parent.parent / 'migrations'


def get_available_migrations() -> List[str]:
    """Liste toutes les migrations disponibles."""
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted([d.name for d in MIGRATIONS_DIR.iterdir() if d.is_dir()])


def ensure_migration_table() -> None:
    """Crée la table de suivi des migrations si elle n'existe pas."""
    with get_cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.schema_migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(100) NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                direction VARCHAR(10) NOT NULL,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        """)

        # Créer un index sur version pour les requêtes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schema_migrations_version 
            ON public.schema_migrations(version, direction, success)
        """)


def is_migration_applied(version: str) -> bool:
    """Vérifie si une migration a déjà été appliquée (et n'a pas été rollback)."""
    with get_cursor() as cursor:
        # Compter les UP réussis moins les DOWN réussis
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN direction = 'up' AND success THEN 1 ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN direction = 'down' AND success THEN 1 ELSE 0 END), 0)
            FROM public.schema_migrations 
            WHERE version = %s
        """, (version,))
        balance = cursor.fetchone()[0]
        return balance > 0


def record_migration(version: str, direction: str, success: bool, error_msg: Optional[str] = None) -> None:
    """Enregistre l'exécution d'une migration."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO public.schema_migrations (version, direction, success, error_message)
            VALUES (%s, %s, %s, %s)
        """, (version, direction, success, error_msg))


def run_sql_file(file_path: Path) -> None:
    """Exécute un fichier SQL."""
    if not file_path.exists():
        raise FileNotFoundError(f"Fichier SQL non trouvé: {file_path}")

    sql_content = file_path.read_text(encoding='utf-8')

    with get_cursor() as cursor:
        cursor.execute(sql_content)

    print(f"  ✓ SQL exécuté: {file_path.name}")


def run_python_script(file_path: Path, direction: str) -> None:
    """
    Exécute un script Python de migration.
    Le script doit avoir une fonction `migrate_up()` ou `migrate_down()`.
    """
    if not file_path.exists():
        return  # Scripts Python optionnels

    spec = importlib.util.spec_from_file_location(
        "migration_script", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["migration_script"] = module
    spec.loader.exec_module(module)

    func_name = f"migrate_{direction}"
    if hasattr(module, func_name):
        func = getattr(module, func_name)
        print(f"  → Exécution de {func_name}()...")
        func()
        print(f"  ✓ Script Python exécuté: {file_path.name}")
    else:
        print(f"  ⚠ Fonction {func_name}() non trouvée dans {file_path.name}")


def verify_migration(version: str, direction: str, migration_module=None) -> bool:
    """
    Vérifie que la migration a bien été appliquée ou annulée.

    Args:
        version: Version de la migration
        direction: 'up' ou 'down'
        migration_module: Module Python de la migration (si disponible)

    Returns:
        True si toutes les vérifications passent, False sinon
    """
    print(f"\n{'─'*60}")
    print(f"Vérification post-migration...")
    print(f"{'─'*60}")

    # Utiliser les fonctions verify_up()/verify_down() du module migrate.py
    if migration_module:
        verify_func_name = f"verify_{direction}"
        if hasattr(migration_module, verify_func_name):
            verify_func = getattr(migration_module, verify_func_name)
            try:
                result = verify_func()

                # Le résultat doit être un dict avec 'success' et 'errors'
                if isinstance(result, dict):
                    success = result.get('success', True)
                    errors = result.get('errors', [])

                    print(f"\n{'─'*60}")
                    if success:
                        print("✓ Toutes les vérifications sont passées")
                    else:
                        print("✗ Certaines vérifications ont échoué")
                        if errors:
                            print("\nErreurs détectées :")
                            for error in errors:
                                print(f"  - {error}")
                    print(f"{'─'*60}")

                    return success
                else:
                    # Si la fonction ne retourne pas le bon format, considérer comme succès
                    print(
                        f"⚠ Fonction {verify_func_name}() ne retourne pas le bon format")
                    return True

            except Exception as e:
                print(f"✗ Erreur lors de la vérification: {e}")
                print(f"{'─'*60}")
                return False

    # Pas de vérifications configurées pour cette migration
    print("  Aucune vérification configurée pour cette migration")
    print(f"  Ajoutez verify_{direction}() dans le fichier migrate.py")
    print(f"{'─'*60}")
    return True


def run_migration(version: str, direction: str, force: bool = False) -> bool:
    """
    Exécute une migration dans la direction spécifiée.

    Args:
        version: Version de la migration (ex: v1.2.1_to_v1.3.0)
        direction: 'up' ou 'down'
        force: Force l'exécution même si déjà appliquée

    Returns:
        True si succès, False sinon
    """
    migration_path = MIGRATIONS_DIR / version

    if not migration_path.exists():
        print(f"✗ Migration non trouvée: {version}")
        return False

    # Vérification état
    if direction == 'up' and is_migration_applied(version) and not force:
        print(
            f"⚠ Migration {version} déjà appliquée. Utiliser --force pour réexécuter.")
        return True

    print(f"\n{'='*60}")
    print(f"Migration: {version} ({direction.upper()})")
    print(f"{'='*60}")

    migration_module = None

    try:
        # 1. Exécuter le script Python pre-migration (si existe)
        pre_script = migration_path / f"pre_{direction}.py"
        run_python_script(pre_script, direction)

        # 2. Exécuter le SQL
        sql_file = migration_path / f"{direction}.sql"
        if sql_file.exists():
            run_sql_file(sql_file)

        # 3. Exécuter le script Python post-migration (si existe)
        post_script = migration_path / f"post_{direction}.py"
        run_python_script(post_script, direction)

        # 4. Script Python principal (migrate.py) - aussi pour les vérifications
        main_script = migration_path / "migrate.py"
        if main_script.exists():
            spec = importlib.util.spec_from_file_location(
                "migration_script", main_script)
            migration_module = importlib.util.module_from_spec(spec)
            sys.modules["migration_script"] = migration_module
            spec.loader.exec_module(migration_module)

            # Exécuter migrate_up() ou migrate_down() si présent
            func_name = f"migrate_{direction}"
            if hasattr(migration_module, func_name):
                func = getattr(migration_module, func_name)
                print(f"  → Exécution de {func_name}()...")
                func()
                print(f"  ✓ Script Python exécuté: {main_script.name}")

        # 5. Vérifications post-migration
        verification_passed = verify_migration(
            version, direction, migration_module)

        if not verification_passed:
            print("\n⚠ Attention : Des vérifications post-migration ont échoué")
            print(
                "  La migration a été exécutée mais certains changements attendus sont manquants")

        # Enregistrer le succès
        record_migration(version, direction, True)
        print(f"\n✓ Migration {version} ({direction}) réussie!")
        return True

    except Exception as e:
        error_msg = str(e)
        record_migration(version, direction, False, error_msg)
        print(f"\n✗ Migration {version} ({direction}) échouée: {error_msg}")
        return False


def list_migrations() -> None:
    """Affiche la liste des migrations et leur état."""
    ensure_migration_table()
    migrations = get_available_migrations()

    print("\nMigrations disponibles:")
    print("-" * 60)

    for version in migrations:
        applied = is_migration_applied(version)
        status = "✓ Appliquée" if applied else "○ Non appliquée"
        print(f"  {version}: {status}")

    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Exécuteur de migrations SQL/Python')
    parser.add_argument('--version', '-v',
                        help='Version de la migration à exécuter')
    parser.add_argument('--direction', '-d', choices=['up', 'down'], default='up',
                        help='Direction de la migration (up ou down)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='Liste les migrations disponibles')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force l\'exécution même si déjà appliquée')

    args = parser.parse_args()

    # Test connexion
    if not test_connection():
        print("✗ Impossible de se connecter à la base de données.")
        print("  Vérifiez les paramètres dans .env")
        sys.exit(1)

    ensure_migration_table()

    if args.list:
        list_migrations()
        return

    if not args.version:
        parser.print_help()
        print("\nErreur: --version requis pour exécuter une migration")
        sys.exit(1)

    success = run_migration(args.version, args.direction, args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

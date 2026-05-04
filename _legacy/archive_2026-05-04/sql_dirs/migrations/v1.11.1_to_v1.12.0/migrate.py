"""
migrate.py - Migration v1.11.1 to v1.12.0
==========================================
Référentiel equipement_statuts + colonne statut_id sur equipements.

Cette migration n'a pas de code Python (tout est dans up.sql/down.sql),
mais fournit les fonctions de vérification post-migration.
"""

from db_connection import get_cursor
import sys
from pathlib import Path

# Ajouter le dossier scripts au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))


def table_exists(table_name: str) -> bool:
    """Vérifie si une table existe."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            )
        """, (table_name,))
        return cursor.fetchone()[0]


def column_exists(table_name: str, column_name: str) -> bool:
    """Vérifie si une colonne existe dans une table."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                AND column_name = %s
            )
        """, (table_name, column_name))
        return cursor.fetchone()[0]


def row_count(table_name: str) -> int:
    """Retourne le nombre de lignes dans une table."""
    with get_cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM public.{table_name}")
        return cursor.fetchone()[0]


def verify_up() -> dict:
    """
    Vérifie que la migration UP a été correctement appliquée.

    Returns:
        dict avec 'success' (bool) et 'errors' (list)
    """
    errors = []

    # Vérifier la table créée
    print("\n✓ Vérification des tables créées :")
    tables = ['equipement_statuts']
    for table in tables:
        exists = table_exists(table)
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")
        if not exists:
            errors.append(f"Table {table} non créée")

    # Vérifier les 6 statuts initiaux
    if table_exists('equipement_statuts'):
        print("\n✓ Vérification des données initiales :")
        count = row_count('equipement_statuts')
        status = "✓" if count >= 6 else "✗"
        print(f"  {status} equipement_statuts : {count} ligne(s) (attendu ≥ 6)")
        if count < 6:
            errors.append(f"equipement_statuts : {count} ligne(s) insérée(s), attendu 6")

        # Vérifier les codes attendus
        expected_codes = ['EN_PROJET', 'EN_CONSTRUCTION', 'EN_SERVICE', 'ARRET', 'REBUT', 'INCONNU']
        with get_cursor() as cursor:
            cursor.execute("SELECT code FROM public.equipement_statuts")
            found_codes = {row[0] for row in cursor.fetchall()}
        for code in expected_codes:
            present = code in found_codes
            status = "✓" if present else "✗"
            print(f"  {status} code '{code}'")
            if not present:
                errors.append(f"Statut '{code}' manquant dans equipement_statuts")

    # Vérifier la colonne ajoutée
    print("\n✓ Vérification des colonnes ajoutées :")
    columns = [('machine', 'statut_id')]
    for table, column in columns:
        exists = column_exists(table, column)
        status = "✓" if exists else "✗"
        print(f"  {status} {table}.{column}")
        if not exists:
            errors.append(f"Colonne {table}.{column} non ajoutée")

    return {
        'success': len(errors) == 0,
        'errors': errors
    }


def verify_down() -> dict:
    """
    Vérifie que le rollback (DOWN) a été correctement effectué.

    Returns:
        dict avec 'success' (bool) et 'errors' (list)
    """
    errors = []

    # Vérifier la table supprimée
    print("\n✓ Vérification des tables supprimées :")
    tables = ['equipement_statuts']
    for table in tables:
        exists = table_exists(table)
        status = "✓" if not exists else "✗"
        print(f"  {status} {table} {'(supprimée)' if not exists else '(existe encore)'}")
        if exists:
            errors.append(f"Table {table} non supprimée")

    # Vérifier la colonne supprimée
    print("\n✓ Vérification des colonnes supprimées :")
    columns = [('machine', 'statut_id')]
    for table, column in columns:
        exists = column_exists(table, column)
        status = "✓" if not exists else "✗"
        print(f"  {status} {table}.{column} {'(supprimée)' if not exists else '(existe encore)'}")
        if exists:
            errors.append(f"Colonne {table}.{column} non supprimée")

    return {
        'success': len(errors) == 0,
        'errors': errors
    }


def migrate_up() -> None:
    """Migration UP (pas de code Python pour cette migration, tout est dans up.sql)."""
    print("  Rien à faire en Python pour cette migration.")


def migrate_down() -> None:
    """Migration DOWN (pas de code Python pour cette migration, tout est dans down.sql)."""
    print("  Rien à faire en Python pour cette migration.")


if __name__ == "__main__":
    print("=== Test des vérifications ===")

    print("\n--- Test verify_up() ---")
    result_up = verify_up()
    print(f"\nRésultat: {'✓ Succès' if result_up['success'] else '✗ Échec'}")
    if result_up['errors']:
        print("Erreurs:")
        for error in result_up['errors']:
            print(f"  - {error}")

    print("\n--- Test verify_down() ---")
    result_down = verify_down()
    print(f"\nRésultat: {'✓ Succès' if result_down['success'] else '✗ Échec'}")
    if result_down['errors']:
        print("Erreurs:")
        for error in result_down['errors']:
            print(f"  - {error}")

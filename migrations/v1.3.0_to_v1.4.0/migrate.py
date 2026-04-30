"""
migrate.py - Migration v1.3.0 to v1.4.0
========================================
Système de caractérisation des pièces par templates versionnés.

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


def verify_up() -> dict:
    """
    Vérifie que la migration UP a été correctement appliquée.

    Returns:
        dict avec 'success' (bool) et 'errors' (list)
    """
    errors = []

    # Vérifier les tables créées
    tables_to_create = [
        'part_template',
        'part_template_field',
        'part_template_field_enum',
        'stock_item_characteristic'
    ]

    print("\n✓ Vérification des tables créées :")
    for table in tables_to_create:
        exists = table_exists(table)
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")
        if not exists:
            errors.append(f"Table {table} non créée")

    # Vérifier les colonnes ajoutées
    columns_to_add = [
        ('stock_sub_family', 'template_id'),
        ('stock_item', 'template_id'),
        ('stock_item', 'template_version')
    ]

    print("\n✓ Vérification des colonnes ajoutées :")
    for table, column in columns_to_add:
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

    # Vérifier les tables supprimées
    tables_to_delete = [
        'part_template',
        'part_template_field',
        'part_template_field_enum',
        'stock_item_characteristic'
    ]

    print("\n✓ Vérification des tables supprimées :")
    for table in tables_to_delete:
        exists = table_exists(table)
        status = "✓" if not exists else "✗"
        print(
            f"  {status} {table} {'(supprimée)' if not exists else '(existe encore)'}")
        if exists:
            errors.append(f"Table {table} non supprimée")

    # Vérifier les colonnes supprimées
    columns_to_delete = [
        ('stock_sub_family', 'template_id'),
        ('stock_item', 'template_id'),
        ('stock_item', 'template_version')
    ]

    print("\n✓ Vérification des colonnes supprimées :")
    for table, column in columns_to_delete:
        exists = column_exists(table, column)
        status = "✓" if not exists else "✗"
        print(
            f"  {status} {table}.{column} {'(supprimée)' if not exists else '(existe encore)'}")
        if exists:
            errors.append(f"Colonne {table}.{column} non supprimée")

    return {
        'success': len(errors) == 0,
        'errors': errors
    }


def migrate_up() -> None:
    """
    Migration UP (optionnel - le SQL fait tout).
    Cette fonction peut être utilisée pour des opérations Python supplémentaires.
    """
    pass


def migrate_down() -> None:
    """
    Migration DOWN (optionnel - le SQL fait tout).
    Cette fonction peut être utilisée pour des opérations Python supplémentaires.
    """
    pass


if __name__ == "__main__":
    # Mode standalone: tester les vérifications
    print("=== Test des vérifications ===")
    print("\nTest verify_up():")
    result = verify_up()
    print(f"\nRésultat: {'✓ Succès' if result['success'] else '✗ Échec'}")
    if result['errors']:
        print("Erreurs:")
        for error in result['errors']:
            print(f"  - {error}")

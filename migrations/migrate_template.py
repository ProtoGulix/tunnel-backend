"""
migrate.py - Template pour migration
=====================================
Ce template montre comment implémenter les vérifications post-migration.

Instructions:
1. Copier ce fichier dans votre dossier de migration
2. Implémenter verify_up() et verify_down()
3. Optionnellement, implémenter migrate_up() et migrate_down() pour du code Python

Les fonctions verify_*() doivent retourner un dict:
{
    'success': bool,  # True si toutes les vérifications passent
    'errors': []      # Liste des messages d'erreur
}
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


def constraint_exists(table_name: str, constraint_name: str) -> bool:
    """Vérifie si une contrainte existe."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.table_constraints
                WHERE table_schema = 'public'
                AND table_name = %s
                AND constraint_name = %s
            )
        """, (table_name, constraint_name))
        return cursor.fetchone()[0]


def index_exists(index_name: str) -> bool:
    """Vérifie si un index existe."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE schemaname = 'public'
                AND indexname = %s
            )
        """, (index_name,))
        return cursor.fetchone()[0]


def verify_up() -> dict:
    """
    Vérifie que la migration UP a été correctement appliquée.

    Returns:
        dict avec 'success' (bool) et 'errors' (list)
    """
    errors = []

    # Exemple : vérifier qu'une table a été créée
    print("\n✓ Vérification des tables créées :")
    tables = ['ma_nouvelle_table']
    for table in tables:
        exists = table_exists(table)
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")
        if not exists:
            errors.append(f"Table {table} non créée")

    # Exemple : vérifier qu'une colonne a été ajoutée
    print("\n✓ Vérification des colonnes ajoutées :")
    columns = [('ma_table', 'ma_colonne')]
    for table, column in columns:
        exists = column_exists(table, column)
        status = "✓" if exists else "✗"
        print(f"  {status} {table}.{column}")
        if not exists:
            errors.append(f"Colonne {table}.{column} non ajoutée")

    # Exemple : vérifier qu'un index a été créé
    print("\n✓ Vérification des index créés :")
    indexes = ['idx_ma_table_colonne']
    for index in indexes:
        exists = index_exists(index)
        status = "✓" if exists else "✗"
        print(f"  {status} {index}")
        if not exists:
            errors.append(f"Index {index} non créé")

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

    # Exemple : vérifier qu'une table a été supprimée
    print("\n✓ Vérification des tables supprimées :")
    tables = ['ma_nouvelle_table']
    for table in tables:
        exists = table_exists(table)
        status = "✓" if not exists else "✗"
        print(
            f"  {status} {table} {'(supprimée)' if not exists else '(existe encore)'}")
        if exists:
            errors.append(f"Table {table} non supprimée")

    # Exemple : vérifier qu'une colonne a été supprimée
    print("\n✓ Vérification des colonnes supprimées :")
    columns = [('ma_table', 'ma_colonne')]
    for table, column in columns:
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
    Migration UP (optionnel).
    Utilisez cette fonction pour des opérations Python qui ne peuvent 
    pas être faites en SQL (parsing de données, conversions complexes, etc.)
    """
    print("  Exécution de migrate_up()")

    # Exemple: migration de données
    # with get_cursor() as cursor:
    #     cursor.execute("SELECT id, old_field FROM ma_table")
    #     rows = cursor.fetchall()
    #     for row_id, old_value in rows:
    #         new_value = transform(old_value)
    #         cursor.execute(
    #             "UPDATE ma_table SET new_field = %s WHERE id = %s",
    #             (new_value, row_id)
    #         )


def migrate_down() -> None:
    """
    Migration DOWN (optionnel).
    Utilisez cette fonction pour des opérations Python de rollback.
    """
    print("  Exécution de migrate_down()")


if __name__ == "__main__":
    # Mode standalone: tester les vérifications
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

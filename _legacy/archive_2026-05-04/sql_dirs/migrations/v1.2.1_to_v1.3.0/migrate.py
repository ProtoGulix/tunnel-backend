"""
migrate.py - Migration complexity_anotation vers complexity_factor
===================================================================
Extrait les données JSON de complexity_anotation et les convertit en FK.

Formats actuels de complexity_anotation:
- {"key": "PCE", "collection": "complexity_factor"} -> complexity_factor = 'PCE'
- {"AUT": true} -> complexity_factor = 'AUT'

Cette migration:
1. Extrait les clés uniques des annotations existantes
2. Insère les complexity_factor manquants
3. Met à jour la colonne complexity_factor avec la valeur extraite du JSON
"""

from db_connection import get_cursor, get_dict_cursor
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

# Ajouter le dossier scripts au path AVANT les imports locaux
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))


def extract_complexity_keys_from_annotation(annotation: Any) -> Set[str]:
    """
    Extrait les clés de complexity_factor depuis une annotation JSON.

    Gère les formats:
    - {"key": "PCE", "collection": "complexity_factor"} -> {"PCE"}
    - {"AUT": true} -> {"AUT"}
    - {"PCE": true, "AUT": true} -> {"PCE", "AUT"}
    """
    keys = set()

    if annotation is None:
        return keys

    # Si c'est une string, parser en JSON
    if isinstance(annotation, str):
        try:
            annotation = json.loads(annotation)
        except json.JSONDecodeError:
            return keys

    if not isinstance(annotation, dict):
        return keys

    # Format {"key": "XXX", "collection": "complexity_factor"}
    if 'key' in annotation and annotation.get('collection') == 'complexity_factor':
        keys.add(annotation['key'])

    # Format {"XXX": true, "YYY": true, ...}
    for key, value in annotation.items():
        if key not in ('key', 'collection') and value is True:
            keys.add(key)

    return keys


def get_all_existing_complexity_annotations() -> List[Dict[str, Any]]:
    """Récupère toutes les annotations de complexité existantes."""
    with get_dict_cursor() as cursor:
        cursor.execute("""
            SELECT id, complexity_anotation
            FROM public.intervention_action
            WHERE complexity_anotation IS NOT NULL
        """)
        return cursor.fetchall()


def get_unique_complexity_keys() -> Set[str]:
    """Extrait toutes les clés uniques de complexity_factor utilisées."""
    annotations = get_all_existing_complexity_annotations()
    all_keys = set()

    for row in annotations:
        keys = extract_complexity_keys_from_annotation(
            row['complexity_anotation'])
        all_keys.update(keys)

    return all_keys


def get_existing_complexity_factors() -> Set[str]:
    """Récupère les codes de complexity_factor existants."""
    with get_cursor() as cursor:
        cursor.execute("SELECT code FROM public.complexity_factor")
        return {row[0] for row in cursor.fetchall()}


def insert_missing_complexity_factors(keys: Set[str]) -> None:
    """Insère les complexity_factor manquants."""
    existing = get_existing_complexity_factors()
    missing = keys - existing

    if not missing:
        print("  Tous les complexity_factor existent déjà.")
        return

    print(
        f"  Insertion de {len(missing)} nouveaux complexity_factor: {', '.join(sorted(missing))}")

    with get_cursor() as cursor:
        for code in missing:
            cursor.execute("""
                INSERT INTO public.complexity_factor (code, label, category)
                VALUES (%s, %s, 'imported')
                ON CONFLICT (code) DO NOTHING
            """, (code, code))


def extract_single_complexity_key(annotation: Any) -> Optional[str]:
    """
    Extrait UNE SEULE clé de complexity_factor depuis une annotation JSON.
    Si plusieurs clés, prend la première par ordre alphabétique.
    """
    keys = extract_complexity_keys_from_annotation(annotation)
    if not keys:
        return None
    return sorted(keys)[0]


def migrate_annotations_to_fk() -> int:
    """
    Migre les annotations JSON vers la colonne complexity_factor.
    Retourne le nombre d'enregistrements migrés.
    """
    annotations = get_all_existing_complexity_annotations()
    migrated_count = 0

    with get_cursor() as cursor:
        for row in annotations:
            action_id = row['id']
            key = extract_single_complexity_key(row['complexity_anotation'])

            if key:
                cursor.execute("""
                    UPDATE public.intervention_action 
                    SET complexity_factor = %s
                    WHERE id = %s
                """, (key, action_id))
                migrated_count += 1

    return migrated_count


def migrate_up() -> None:
    """
    Migration UP: Extrait complexity_anotation et remplit complexity_factor.
    """
    print("\n--- Extraction des clés de complexité ---")

    # 1. Extraire toutes les clés uniques
    unique_keys = get_unique_complexity_keys()
    print(f"  Clés uniques trouvées: {sorted(unique_keys)}")

    if not unique_keys:
        print("  Aucune annotation de complexité à migrer.")
        return

    # 2. Insérer les complexity_factor manquants
    print("\n--- Insertion des complexity_factor manquants ---")
    insert_missing_complexity_factors(unique_keys)

    # 3. Migrer les données JSON vers complexity_factor
    print("\n--- Migration vers complexity_factor ---")
    count = migrate_annotations_to_fk()
    print(f"  {count} enregistrements mis à jour avec complexity_factor")

    print("\n✓ Migration UP terminée avec succès!")


def migrate_down() -> None:
    """
    Migration DOWN: Remet complexity_factor à NULL.
    Note: Les complexity_factor insérés ne sont pas supprimés par sécurité.
    Note: complexity_anotation est conservé avec ses données d'origine.
    """
    print("\n--- Rollback de complexity_factor ---")

    with get_cursor() as cursor:
        cursor.execute(
            "UPDATE public.intervention_action SET complexity_factor = NULL")
        print(f"  Colonne complexity_factor remise à NULL")

    print("\n✓ Migration DOWN terminée!")
    print("  Note: Les complexity_factor ajoutés n'ont pas été supprimés (données de référence).")
    print("  Note: complexity_anotation est toujours présent avec les données d'origine.")


def print_statistics() -> None:
    """Affiche des statistiques sur les données à migrer."""
    annotations = get_all_existing_complexity_annotations()
    unique_keys = get_unique_complexity_keys()

    print("\n=== Statistiques de migration ===")
    print(f"  Intervention_actions avec annotations: {len(annotations)}")
    print(f"  Clés de complexité uniques: {len(unique_keys)}")
    print(f"  Clés: {sorted(unique_keys)}")

    # Analyser les formats
    formats = {'key_collection': 0, 'bool_keys': 0, 'other': 0}
    for row in annotations:
        ann = row['complexity_anotation']
        if isinstance(ann, str):
            try:
                ann = json.loads(ann)
            except:
                continue

        if isinstance(ann, dict):
            if 'key' in ann and 'collection' in ann:
                formats['key_collection'] += 1
            elif any(v is True for v in ann.values()):
                formats['bool_keys'] += 1
            else:
                formats['other'] += 1

    print(f"\n  Formats d'annotations:")
    print(f"    - Format {{key, collection}}: {formats['key_collection']}")
    print(f"    - Format {{KEY: true}}: {formats['bool_keys']}")
    print(f"    - Autres: {formats['other']}")


if __name__ == "__main__":
    # Mode standalone: afficher les statistiques
    print_statistics()

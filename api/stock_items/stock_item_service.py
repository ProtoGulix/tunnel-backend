import logging
from typing import Dict, Any
from uuid import uuid4

from api.settings import settings
from api.errors.exceptions import DatabaseError, ValidationError
from api.stock_items.template_service import TemplateService
from api.stock_items.template_schemas import CharacteristicValue, StockItemWithCharacteristics
from api.stock_sub_families.repo import StockSubFamilyRepository

logger = logging.getLogger(__name__)


class StockItemService:
    """Service de gestion des stock_items avec support templates"""

    def __init__(self):
        self.template_service = TemplateService()
        self.sub_family_repo = StockSubFamilyRepository()

    def _get_connection(self):
        """Ouvre une connexion à la base de données"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def create_stock_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un stock_item (legacy ou template-based)

        Logique :
        1. Vérifier si la sous-famille a un template
        2. Si OUI :
           - Forcer l'utilisation du template
           - Valider les caractéristiques
           - Générer dimension automatiquement
           - Interdire saisie manuelle de dimension
        3. Si NON :
           - Créer en mode legacy (comme avant v1.4)
           - Accepter dimension manuelle
        """
        family_code = data.get('family_code')
        sub_family_code = data.get('sub_family_code')

        if not family_code or not sub_family_code:
            raise ValidationError(
                "family_code et sub_family_code sont obligatoires")

        # Charger le template de la sous-famille (si existant)
        template = self.sub_family_repo.load_template_for_sub_family(
            family_code, sub_family_code)

        if template is None:
            # Mode LEGACY : pas de template
            logger.info("Création item legacy pour %s/%s",
                        family_code, sub_family_code)
            return self._create_legacy_item(data)
        else:
            # Mode TEMPLATE : validation + génération
            logger.info("Création item template-based pour %s/%s avec template %s",
                        family_code, sub_family_code, template.code)
            return self._create_template_item(data, template)

    def _create_legacy_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un item legacy (sans template)
        Comportement identique à avant v1.4
        """
        if 'dimension' not in data or not data['dimension']:
            raise ValidationError(
                "dimension est obligatoire pour les pièces legacy")

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            item_id = str(uuid4())

            cur.execute(
                """
                INSERT INTO stock_item
                (id, name, family_code, sub_family_code, spec, dimension,
                 quantity, unit, location, standars_spec, manufacturer_item_id,
                 template_id, template_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL)
                RETURNING *
                """,
                (
                    item_id,
                    data['name'],
                    data['family_code'],
                    data['sub_family_code'],
                    data.get('spec'),
                    data['dimension'],
                    data.get('quantity', 0),
                    data.get('unit'),
                    data.get('location'),
                    data.get('standars_spec'),
                    data.get('manufacturer_item_id')
                )
            )
            row = cur.fetchone()
            cols = [desc[0] for desc in cur.description]
            result = dict(zip(cols, row))
            conn.commit()

            logger.info("Item legacy créé: %s", result['id'])
            return result

        except Exception as e:
            conn.rollback()
            logger.error("Erreur création item legacy: %s", str(e))
            raise DatabaseError(f"Erreur lors de la création: {str(e)}") from e
        finally:
            conn.close()

    def _create_template_item(self, data: Dict[str, Any], template) -> Dict[str, Any]:
        """
        Crée un item basé sur un template

        Règles :
        - Les caractéristiques sont obligatoires
        - dimension est INTERDIT en saisie (généré auto)
        - Validation complète via TemplateService
        """
        # Interdire saisie manuelle de dimension
        if 'dimension' in data and data['dimension']:
            raise ValidationError(
                "dimension ne peut pas être saisi manuellement pour les pièces avec template. "
                "Elle est générée automatiquement à partir des caractéristiques."
            )

        # Vérifier que les caractéristiques sont fournies
        characteristics = data.get('characteristics', [])
        if not characteristics:
            raise ValidationError(
                "Les caractéristiques sont obligatoires pour les pièces avec template")

        # Validation des caractéristiques
        validated_chars = self.template_service.validate_characteristics(
            template, characteristics)

        # Génération de la dimension
        dimension = self.template_service.generate_dimension(
            template, validated_chars)

        # Transaction complète
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            item_id = str(uuid4())

            # Insertion du stock_item
            cur.execute(
                """
                INSERT INTO stock_item
                (id, name, family_code, sub_family_code, spec, dimension,
                 quantity, unit, location, standars_spec, manufacturer_item_id,
                 template_id, template_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    item_id,
                    data['name'],
                    data['family_code'],
                    data['sub_family_code'],
                    data.get('spec'),
                    dimension,  # Généré automatiquement
                    data.get('quantity', 0),
                    data.get('unit'),
                    data.get('location'),
                    data.get('standars_spec'),
                    data.get('manufacturer_item_id'),
                    str(template.id),
                    template.version
                )
            )

            item_row = cur.fetchone()
            item_cols = [desc[0] for desc in cur.description]
            result = dict(zip(item_cols, item_row))

            # Insertion des caractéristiques
            for char in validated_chars:
                char_id = str(uuid4())
                cur.execute(
                    """
                    INSERT INTO stock_item_characteristic
                    (id, stock_item_id, field_id, value_text, value_number, value_enum)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        char_id,
                        item_id,
                        str(char.field_id),
                        char.value_text,
                        char.value_number,
                        char.value_enum
                    )
                )

            conn.commit()
            logger.info("Item template créé: %s avec template %s v%s",
                        result['id'], template.code, template.version)

            return result

        except ValidationError:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            logger.error("Erreur création item template: %s", str(e))
            raise DatabaseError(f"Erreur lors de la création: {str(e)}") from e
        finally:
            conn.close()

    def update_stock_item(self, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un stock_item

        Règles d'immutabilité :
        - template_id NON modifiable
        - template_version NON modifiable
        - characteristics NON modifiables pour items template

        Pour items legacy : mise à jour normale
        Pour items template : mise à jour limitée (quantity, location, etc.)
        """
        # Récupérer l'item existant
        item = self._get_item_by_id(item_id)

        is_template_item = item.get('template_id') is not None

        if is_template_item:
            # Interdire modification des champs liés au template
            forbidden_fields = ['template_id', 'template_version', 'dimension',
                                'family_code', 'sub_family_code', 'characteristics']

            for field in forbidden_fields:
                if field in data:
                    raise ValidationError(
                        f"Le champ {field} ne peut pas être modifié pour un item avec template")

        # Mise à jour normale des champs autorisés
        return self._update_item_fields(item_id, data)

    def _get_item_by_id(self, item_id: str) -> Dict[str, Any]:
        """Récupère un item par ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM stock_item WHERE id = %s", (item_id,))
            row = cur.fetchone()

            if not row:
                raise ValidationError(f"Item {item_id} non trouvé")

            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        finally:
            conn.close()

    def _update_item_fields(self, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour les champs autorisés d'un item"""
        updatable_fields = ['name', 'spec', 'quantity', 'unit', 'location',
                            'standars_spec', 'manufacturer_item_id']

        set_clauses = []
        params = []

        for field in updatable_fields:
            if field in data:
                set_clauses.append(f"{field} = %s")
                params.append(data[field])

        if not set_clauses:
            return self._get_item_by_id(item_id)

        params.append(item_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            query = f"""
                UPDATE stock_item
                SET {', '.join(set_clauses)}
                WHERE id = %s
                RETURNING *
            """
            cur.execute(query, params)
            conn.commit()

            row = cur.fetchone()
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour: {str(e)}") from e
        finally:
            conn.close()

    def get_item_with_characteristics(self, item_id: str) -> StockItemWithCharacteristics:
        """
        Récupère un item avec ses caractéristiques si c'est un item template
        """
        item = self._get_item_by_id(item_id)

        # Si legacy, pas de caractéristiques
        if item.get('template_id') is None:
            return StockItemWithCharacteristics(**item, characteristics=[])

        # Charger les caractéristiques
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT sc.field_id, f.field_key, sc.value_text, sc.value_number, sc.value_enum
                FROM stock_item_characteristic sc
                JOIN part_template_field f ON f.id = sc.field_id
                WHERE sc.stock_item_id = %s
                ORDER BY f.sort_order, f.field_key
                """,
                (item_id,)
            )

            char_rows = cur.fetchall()

            characteristics = [
                CharacteristicValue(
                    field_id=row[0],
                    key=row[1],
                    value_text=row[2],
                    value_number=row[3],
                    value_enum=row[4]
                )
                for row in char_rows
            ]

            return StockItemWithCharacteristics(**item, characteristics=characteristics)

        finally:
            conn.close()


def is_legacy_item(item: Dict[str, Any]) -> bool:
    """
    Utilitaire pour déterminer si un item est legacy

    Args:
        item: Dictionnaire représentant un stock_item

    Returns:
        True si l'item est legacy (pas de template), False sinon
    """
    return item.get('template_id') is None

import logging
import re
from typing import Dict, Any, List, Optional
from uuid import UUID

from api.errors.exceptions import DatabaseError, NotFoundError, ValidationError
from api.stock_items.template_schemas import (
    PartTemplate,
    TemplateField,
    TemplateFieldEnum,
    CharacteristicValue
)
from api.part_templates.repo import PartTemplateRepository

logger = logging.getLogger(__name__)


class TemplateService:
    """Service de gestion des templates de pièces - BUSINESS LOGIC ONLY"""

    def load_template(self, template_id: UUID, version: Optional[int] = None) -> PartTemplate:
        """
        Charge un template avec ses champs et enum values
        Si version est None, charge la version la plus récente

        Délègue au Repository (SOURCE DE VÉRITÉ) puis convertit en Pydantic
        """
        try:
            repo = PartTemplateRepository()
            template_data = repo.get_by_id_with_fields(template_id, version)

            # Convertir les champs du dict en objets Pydantic
            fields = []
            for field_data in template_data.get('fields', []):
                field_dict = dict(field_data)

                # Convertir enum_values si présent
                if field_dict.get('enum_values'):
                    field_dict['enum_values'] = [
                        TemplateFieldEnum(**enum)
                        for enum in field_dict['enum_values']
                    ]
                else:
                    field_dict['enum_values'] = None

                fields.append(TemplateField(**field_dict))

            # Créer le template avec les champs convertis
            template_dict = {
                'id': template_data['id'],
                'code': template_data['code'],
                'version': template_data['version'],
                'pattern': template_data['pattern'],
                'fields': fields
            }

            return PartTemplate(**template_dict)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Erreur lors du chargement du template: %s", str(e))
            raise DatabaseError(
                f"Erreur lors du chargement du template: {str(e)}") from e

    def validate_characteristics(
        self,
        template: PartTemplate,
        characteristics: List[Dict[str, Any]]
    ) -> List[CharacteristicValue]:
        """
        Valide les caractéristiques fournies contre le template

        Règles :
        - Exactement un champ rempli selon field_type
        - Enum obligatoire si type enum
        - Tous les required présents
        - Aucun champ hors template

        Returns:
            Liste de CharacteristicValue validés
        """
        # Map des fields par key
        template_fields = {field.key: field for field in template.fields}

        # Map des caractéristiques fournies par key
        provided_chars = {char['key']: char for char in characteristics}

        # Vérification des champs obligatoires
        for field in template.fields:
            if field.required and field.key not in provided_chars:
                raise ValidationError(
                    f"Champ obligatoire manquant: {field.key}")

        # Validation de chaque caractéristique
        validated_chars = []
        for char_data in characteristics:
            key = char_data.get('key')

            if not key:
                raise ValidationError("key manquant dans une caractéristique")

            if key not in template_fields:
                raise ValidationError(f"Champ hors template: {key}")

            field = template_fields[key]

            # Vérifier qu'exactement un champ est rempli
            text_val = char_data.get('text_value')
            number_val = char_data.get('number_value')
            enum_val = char_data.get('enum_value')

            filled_count = sum([
                text_val is not None,
                number_val is not None,
                enum_val is not None
            ])

            if filled_count == 0:
                raise ValidationError(
                    f"Aucune valeur fournie pour le champ: {key}")

            if filled_count > 1:
                raise ValidationError(
                    f"Plusieurs valeurs fournies pour le champ: {key}")

            # Validation selon le type
            if field.field_type == 'text':
                if text_val is None:
                    raise ValidationError(
                        f"Champ {key} doit être de type text")
                validated_chars.append(CharacteristicValue(
                    key=key,
                    text_value=text_val,
                    number_value=None,
                    enum_value=None
                ))

            elif field.field_type == 'number':
                if number_val is None:
                    raise ValidationError(
                        f"Champ {key} doit être de type number")
                validated_chars.append(CharacteristicValue(
                    key=key,
                    text_value=None,
                    number_value=number_val,
                    enum_value=None
                ))

            elif field.field_type == 'enum':
                if enum_val is None:
                    raise ValidationError(
                        f"Champ {key} doit être de type enum")

                # Vérifier que la valeur est dans les enum_values
                if field.enum_values:
                    valid_values = [e.value for e in field.enum_values]
                    if enum_val not in valid_values:
                        raise ValidationError(
                            f"Valeur {enum_val} invalide pour {key}. Valeurs autorisées: {', '.join(valid_values)}"
                        )

                validated_chars.append(CharacteristicValue(
                    key=key,
                    text_value=None,
                    number_value=None,
                    enum_value=enum_val
                ))

        return validated_chars

    def generate_dimension(self, template: PartTemplate, characteristics: List[CharacteristicValue]) -> str:
        """
        Génère la dimension automatiquement selon le pattern du template

        Example:
            pattern = "{DIAM}x{LONG}-{MAT}"
            characteristics = [
                {"key": "DIAM", "number_value": 10},
                {"key": "LONG", "number_value": 50},
                {"key": "MAT", "enum_value": "INOX"}
            ]
            -> "10x50-INOX"
        """
        dimension = template.pattern

        # Map des caractéristiques par key
        char_map = {char.key: char for char in characteristics}

        # Trouver tous les placeholders {KEY} dans le pattern
        placeholders = re.findall(r'\{([^}]+)\}', template.pattern)

        for placeholder in placeholders:
            if placeholder not in char_map:
                raise ValidationError(
                    f"Caractéristique manquante pour le pattern: {placeholder}")

            char = char_map[placeholder]

            # Récupérer la valeur selon le type
            if char.text_value is not None:
                value = char.text_value
            elif char.number_value is not None:
                # Formater le nombre sans décimales inutiles
                value = str(int(char.number_value)) if char.number_value == int(
                    char.number_value) else str(char.number_value)
            elif char.enum_value is not None:
                value = char.enum_value
            else:
                raise ValidationError(
                    f"Aucune valeur pour la caractéristique: {placeholder}")

            dimension = dimension.replace(f"{{{placeholder}}}", value)

        logger.debug("Dimension générée: %s", dimension)
        return dimension

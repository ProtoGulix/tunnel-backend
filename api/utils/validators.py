"""Validateurs communs réutilisables pour l'ensemble de l'API"""
from typing import Any
from datetime import datetime


def validate_date(date_value: Any, field_name: str = "date") -> datetime:
    """
    Valide qu'une date est valide et la convertit en datetime

    Args:
        date_value: La valeur à valider (datetime, str, ou autre)
        field_name: Le nom du champ pour les messages d'erreur

    Returns:
        datetime: La date validée et convertie

    Raises:
        ValueError: Si la date est invalide
    """
    if date_value is None:
        raise ValueError(f"{field_name} est obligatoire")

    # Si c'est déjà un datetime, vérifier qu'il est valide
    if isinstance(date_value, datetime):
        # Vérifier la plage d'années
        if date_value.year < 1900 or date_value.year > 2100:
            raise ValueError(
                f"L'année {date_value.year} est hors de la plage valide (1900-2100)"
            )
        return date_value

    # Si c'est une string, essayer de la parser
    if isinstance(date_value, str):
        try:
            # Parser strictement la date ISO 8601
            # Supporte: "YYYY-MM-DD", "YYYY-MM-DDTHH:MM:SS", "YYYY-MM-DDTHH:MM:SS.microsZ"
            date_str = date_value.replace('Z', '+00:00').strip()

            # Si c'est juste une date (YYYY-MM-DD), convertir en datetime à minuit
            if len(date_str) == 10 and date_str.count('-') == 2:
                # Format date seule: YYYY-MM-DD
                parsed = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                # Format datetime complet
                parsed = datetime.fromisoformat(date_str)

            # Vérifier que la date est valide (pas dans le futur lointain, etc.)
            if parsed.year < 1900 or parsed.year > 2100:
                raise ValueError(
                    f"L'année {parsed.year} est hors de la plage valide (1900-2100)"
                )

            return parsed
        except ValueError as e:
            raise ValueError(f"{field_name} invalide: {str(e)}") from e

    raise ValueError(f"Format de {field_name} invalide: {type(date_value).__name__}")

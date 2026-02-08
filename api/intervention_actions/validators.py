from typing import Dict, Any
from datetime import datetime
from api.utils.sanitizer import strip_html
from api.utils.validators import validate_date
from api.complexity_factors.repo import ComplexityFactorRepository
from api.errors.exceptions import NotFoundError


class InterventionActionValidator:
    """Validation des règles métier pour les actions d'intervention"""

    @staticmethod
    def validate_time_spent(time_spent: float) -> None:
        """Valide que time_spent est un quart d'heure (0.25, 0.5, 0.75, 1.0, etc.) >= 0.25"""
        if time_spent is None:
            raise ValueError("time_spent est obligatoire")

        if time_spent < 0.25:
            raise ValueError(
                "time_spent doit être au minimum 0.25 heure (15 minutes)")

        # Vérifie que c'est un multiple de 0.25
        if round(time_spent % 0.25, 2) != 0:
            raise ValueError(
                "time_spent doit être un quart d'heure (0.25, 0.5, 0.75, 1.0, etc.)")

    @staticmethod
    def validate_complexity_score(score: int) -> None:
        """Valide que complexity_score est entre 1 et 10"""
        if score is None:
            raise ValueError("complexity_score est obligatoire")

        if not isinstance(score, int) or score < 1 or score > 10:
            raise ValueError(
                "complexity_score doit être un entier entre 1 et 10")

    @staticmethod
    def validate_required_fields(action_data: Dict[str, Any]) -> None:
        """Valide que tous les champs obligatoires sont présents"""
        required_fields = [
            'intervention_id',
            'description',
            'time_spent',
            'action_subcategory',
            'tech',
            'complexity_score'
        ]

        missing = [
            field for field in required_fields if not action_data.get(field)]
        if missing:
            raise ValueError(
                f"Champs obligatoires manquants: {', '.join(missing)}")

    @staticmethod
    def validate_complexity_factor(factor: str | None) -> str | None:
        """Valide que complexity_factor est un code existant en base (si fourni)"""
        if factor is None or factor == "":
            return None

        if not isinstance(factor, str):
            raise ValueError("complexity_factor doit être un code (string)")

        code = factor.strip()
        if not code:
            return None

        repo = ComplexityFactorRepository()
        try:
            repo.get_by_code(code)
        except NotFoundError as exc:
            raise ValueError(
                f"complexity_factor contient un facteur inconnu: {code}") from exc

        return code

    @staticmethod
    def validate_complexity_with_factor(complexity_score: int, complexity_factor: str | None) -> None:
        """
        Valide que si complexity_score > 5, un facteur de complexité valide est renseigné
        """
        if complexity_score > 5 and (not complexity_factor or not complexity_factor.strip()):
            raise ValueError(
                "Un facteur de complexité (complexity_factor) est obligatoire pour un score de complexité supérieur à 5"
            )

    @staticmethod
    def sanitize_description(description: str) -> str:
        """Nettoie la description en supprimant le HTML"""
        if not description:
            raise ValueError("description est obligatoire")

        sanitized = strip_html(description).strip()
        if not sanitized:
            raise ValueError(
                "description ne peut pas être vide après nettoyage")

        return sanitized

    @classmethod
    def validate_and_prepare(cls, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide toutes les règles métier et prépare les données
        Retourne les données validées et nettoyées
        """
        # Vérifie les champs obligatoires
        cls.validate_required_fields(action_data)

        # Valide et sanitise la description
        action_data['description'] = cls.sanitize_description(
            action_data['description'])

        # Valide time_spent
        cls.validate_time_spent(action_data['time_spent'])

        # Valide complexity_score
        cls.validate_complexity_score(action_data['complexity_score'])

        # Valide complexity_factor (si fourni)
        action_data['complexity_factor'] = cls.validate_complexity_factor(
            action_data.get('complexity_factor'))

        # Valide que si score > 5, un facteur de complexité est obligatoire
        cls.validate_complexity_with_factor(
            action_data['complexity_score'],
            action_data.get('complexity_factor')
        )

        # Valide et normalise created_at (utilise now() si None)
        created_at = action_data.get('created_at')
        if created_at is None:
            action_data['created_at'] = datetime.now()
        else:
            action_data['created_at'] = validate_date(created_at, 'created_at')

        return action_data

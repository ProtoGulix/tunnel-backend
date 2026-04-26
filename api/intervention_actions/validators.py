from typing import Dict, Any
from datetime import datetime
from api.utils.sanitizer import strip_html
from api.utils.validators import validate_date
from api.complexity_factors.repo import ComplexityFactorRepository
from api.errors.exceptions import NotFoundError, ValidationError


class InterventionActionValidator:
    """Validation des règles métier pour les actions d'intervention"""

    @staticmethod
    def validate_time_spent(time_spent: float) -> None:
        """Valide que time_spent est un quart d'heure (0.25, 0.5, 0.75, 1.0, etc.) >= 0.25"""
        if time_spent < 0.25:
            raise ValidationError(
                "time_spent doit être au minimum 0.25 heure (15 minutes)")

        if round(time_spent % 0.25, 2) != 0:
            raise ValidationError(
                "time_spent doit être un multiple de 0.25h (ex: 0.25, 0.5, 0.75, 1.0...)")

    @staticmethod
    def validate_complexity_score(score: int) -> None:
        """Valide que complexity_score est entre 1 et 10"""
        if not isinstance(score, int) or score < 1 or score > 10:
            raise ValidationError(
                "complexity_score doit être un entier entre 1 et 10")

    @staticmethod
    def validate_required_fields(action_data: Dict[str, Any]) -> None:
        """
        Valide que tous les champs obligatoires sont présents.
        complexity_factor est ajouté aux champs manquants si complexity_score > 5.
        """
        required_fields = [
            'intervention_id',
            'task_id',
            'action_subcategory',
            'tech',
            'complexity_score',
        ]

        missing = [
            field for field in required_fields
            if action_data.get(field) is None
        ]

        # complexity_factor obligatoire si complexity_score > 5
        score = action_data.get('complexity_score')
        if isinstance(score, int) and score > 5:
            factor = action_data.get('complexity_factor')
            if not factor or not str(factor).strip():
                missing.append(
                    'complexity_factor (obligatoire si complexity_score > 5)')

        if missing:
            raise ValidationError(
                f"Champs obligatoires manquants : {', '.join(missing)}")

    @staticmethod
    def validate_complexity_factor(factor: str | None) -> str | None:
        """Valide que complexity_factor est un code existant en base (si fourni)"""
        if factor is None or factor == "":
            return None

        code = str(factor).strip()
        if not code:
            return None

        repo = ComplexityFactorRepository()
        try:
            repo.get_by_code(code)
        except NotFoundError:
            raise ValidationError(
                f"complexity_factor '{code}' est inconnu. Vérifiez les facteurs disponibles.")

        return code

    @staticmethod
    def sanitize_description(description: str) -> str:
        """Nettoie la description en supprimant le HTML"""
        sanitized = strip_html(description).strip()
        if not sanitized:
            raise ValidationError(
                "description ne peut pas être vide")

        return sanitized

    @classmethod
    def validate_and_prepare(cls, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide toutes les règles métier et prépare les données.
        Lève ValidationError (HTTP 400) en cas d'erreur.
        Retourne les données validées et nettoyées.
        """
        # Vérifie les champs obligatoires (incluant complexity_factor si score > 5)
        cls.validate_required_fields(action_data)

        # Valide et sanitise la description (note optionnelle)
        if action_data.get('description'):
            action_data['description'] = cls.sanitize_description(
                action_data['description'])

        # Valide time_spent si fourni (sinon le trigger calcule depuis action_start/action_end)
        if action_data.get('time_spent') is not None:
            cls.validate_time_spent(action_data['time_spent'])

        # Valide complexity_score
        cls.validate_complexity_score(action_data['complexity_score'])

        # Valide complexity_factor (existence en base si fourni)
        action_data['complexity_factor'] = cls.validate_complexity_factor(
            action_data.get('complexity_factor'))

        # Valide et normalise created_at (utilise now() si None)
        created_at = action_data.get('created_at')
        if created_at is None:
            action_data['created_at'] = datetime.now()
        else:
            action_data['created_at'] = validate_date(created_at, 'created_at')

        return action_data

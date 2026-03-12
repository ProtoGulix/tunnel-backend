from typing import Any, Dict, List, Optional

from api.errors.exceptions import ValidationError

# Transitions autorisées : statut_from → [statuts_to possibles]
ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "nouvelle":   ["en_attente", "acceptee", "rejetee"],
    "en_attente": ["acceptee", "rejetee"],
    "acceptee":   ["cloturee"],
    "rejetee":    [],
    "cloturee":   [],
}


class InterventionRequestValidator:
    """Validation des règles métier pour les demandes d'intervention."""

    @staticmethod
    def validate_transition(
        current_statut: str,
        status_to: str,
        notes: Optional[str],
        intervention_data: Optional[Dict[str, Any]],
    ) -> None:
        """
        Valide qu'une transition de statut est autorisée et que les données
        associées sont cohérentes avec le statut cible.
        """
        allowed = ALLOWED_TRANSITIONS.get(current_statut, [])
        if status_to not in allowed:
            raise ValidationError(
                f"Transition '{current_statut}' → '{status_to}' non autorisée. "
                f"Transitions possibles : {allowed or 'aucune'}"
            )

        # Motif obligatoire pour rejet
        if status_to == "rejetee" and not (notes or "").strip():
            raise ValidationError(
                "Un motif (notes) est obligatoire pour rejeter une demande"
            )

        # Champs obligatoires pour acceptation (création intervention)
        if status_to == "acceptee":
            if not intervention_data or not intervention_data.get("type_inter"):
                raise ValidationError(
                    "type_inter est obligatoire pour accepter une demande"
                )
            if not intervention_data.get("tech_initials"):
                raise ValidationError(
                    "tech_initials est obligatoire pour accepter une demande"
                )

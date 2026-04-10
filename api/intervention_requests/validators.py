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
    """
    Validation des règles métier pour les demandes d'intervention.

    Règles de liaison :
    - Une demande liée à une intervention est verrouillée : elle ne peut plus être liée à une autre.
    - Une intervention liée à une demande est verrouillée : elle ne peut plus être liée à une autre demande.
    Ces vérifications sont effectuées dans InterventionRepository._link_request() et
    InterventionRequestRepository.transition_status() au moment de l'acceptation.
    """

    @staticmethod
    def validate_transition(
        current_statut: str,
        status_to: str,
        notes: Optional[str],
        intervention_data: Optional[Dict[str, Any]],
        current_intervention_id: Optional[Any] = None,
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

        # Liaison verrouillée : une demande déjà liée ne peut pas être re-acceptée
        if status_to == "acceptee" and current_intervention_id is not None:
            raise ValidationError(
                f"Cette demande est déjà liée à l'intervention '{current_intervention_id}'. "
                f"Une demande ne peut être liée qu'à une seule intervention."
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

    @staticmethod
    def validate_create(data: Dict[str, Any]) -> None:
        """Valide les règles métier avant création d'une demande d'intervention."""
        demandeur_nom = (data.get("demandeur_nom") or "").strip()
        description = (data.get("description") or "").strip()

        if not demandeur_nom:
            raise ValidationError("demandeur_nom est obligatoire")
        if not description:
            raise ValidationError("description est obligatoire")
        if not data.get("machine_id"):
            raise ValidationError("machine_id est obligatoire")

        from api.equipement_statuts.repo import check_equipement_statut_allows_interventions
        check_equipement_statut_allows_interventions(str(data["machine_id"]))

from typing import Any, Dict, Optional

from api.db import get_connection, release_connection
from api.errors.exceptions import ConflictError, ValidationError
from api.constants import INTERVENTION_TYPE_IDS


class InterventionValidator:
    """Validation des règles métier pour les interventions"""

    @staticmethod
    def validate_unique_code(
        machine_id: str,
        type_inter: str,
        tech_initials: str,
        exclude_id: Optional[str] = None,
    ) -> None:
        """
        RÈGLE MÉTIER : Le code intervention ({machine.code}-{type_inter}-{YYYYMMDD}-{tech_initials})
        doit être unique. Lève ConflictError 409 si une intervention avec le même code existe déjà.
        """
        from api.db import get_connection, release_connection

        conn = get_connection()
        try:
            cur = conn.cursor()
            # Reconstitue le code tel que le trigger le génère
            cur.execute(
                """
                SELECT i.id, i.code
                FROM intervention i
                JOIN machine m ON m.id = i.machine_id
                WHERE m.id = %s
                  AND i.type_inter = %s
                  AND i.tech_initials = %s
                  AND DATE(i.reported_date) = CURRENT_DATE
                  AND (%s IS NULL OR i.id != %s)
                LIMIT 1
                """,
                (machine_id, type_inter, tech_initials, exclude_id, exclude_id),
            )
            row = cur.fetchone()
            if row:
                raise ConflictError(
                    f"Une intervention avec le code '{row[1]}' existe déjà "
                    f"pour cette machine, ce type et ces initiales aujourd'hui. "
                    f"Choisissez des initiales différentes ou modifiez le type."
                )
        finally:
            release_connection(conn)

    @staticmethod
    def validate_type_inter(type_inter: str) -> None:
        """Valide que le type d'intervention est connu."""
        if type_inter not in INTERVENTION_TYPE_IDS:
            raise ConflictError(
                f"Type d'intervention '{type_inter}' inconnu. "
                f"Valeurs autorisées : {', '.join(INTERVENTION_TYPE_IDS)}"
            )

    @staticmethod
    def validate_deletable(intervention_id: str) -> None:
        """
        RÈGLE MÉTIER : Une intervention ne peut être supprimée que si elle
        n'a ni action ni demande d'achat liée.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    COUNT(DISTINCT ia.id) AS action_count,
                    COUNT(DISTINCT iapr.purchase_request_id) AS purchase_count
                FROM intervention i
                LEFT JOIN intervention_action ia ON ia.intervention_id = i.id
                LEFT JOIN intervention_action_purchase_request iapr ON iapr.intervention_action_id = ia.id
                WHERE i.id = %s
                """,
                (intervention_id,),
            )
            row = cur.fetchone()
            action_count = row[0] or 0
            purchase_count = row[1] or 0

            if action_count > 0:
                raise ValidationError(
                    f"Impossible de supprimer cette intervention : "
                    f"elle possède {action_count} action(s) liée(s). "
                    f"Supprimez d'abord les actions."
                )
            if purchase_count > 0:
                raise ValidationError(
                    f"Impossible de supprimer cette intervention : "
                    f"elle possède {purchase_count} demande(s) d'achat liée(s). "
                    f"Supprimez d'abord les demandes d'achat."
                )
        finally:
            release_connection(conn)

    @classmethod
    def validate_create(cls, data: Dict[str, Any]) -> None:
        """Valide les règles métier avant création d'une intervention."""
        if data.get("type_inter"):
            cls.validate_type_inter(data["type_inter"])
        if data.get("machine_id"):
            from api.equipement_statuts.repo import check_equipement_statut_allows_interventions
            check_equipement_statut_allows_interventions(str(data["machine_id"]))
        if data.get("machine_id") and data.get("type_inter") and data.get("tech_initials"):
            cls.validate_unique_code(
                machine_id=str(data["machine_id"]),
                type_inter=data["type_inter"],
                tech_initials=data["tech_initials"],
            )

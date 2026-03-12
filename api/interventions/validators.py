from typing import Any, Dict, Optional

from api.db import get_connection, release_connection
from api.errors.exceptions import ConflictError
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

    @classmethod
    def validate_create(cls, data: Dict[str, Any]) -> None:
        """Valide les règles métier avant création d'une intervention."""
        if data.get("type_inter"):
            cls.validate_type_inter(data["type_inter"])
        if data.get("machine_id") and data.get("type_inter") and data.get("tech_initials"):
            cls.validate_unique_code(
                machine_id=str(data["machine_id"]),
                type_inter=data["type_inter"],
                tech_initials=data["tech_initials"],
            )

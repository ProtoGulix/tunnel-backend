from typing import Dict, Any
from api.utils.sanitizer import strip_html
from api.intervention_status.repo import InterventionStatusRepository
from api.errors.exceptions import NotFoundError


class InterventionStatusLogValidator:
    """Validation des règles métier pour les logs de changement de statut"""

    @staticmethod
    def validate_required_fields(log_data: Dict[str, Any]) -> None:
        """Valide que tous les champs obligatoires sont présents"""
        required_fields = ['intervention_id', 'status_to', 'technician_id', 'date']

        missing = [field for field in required_fields if not log_data.get(field)]
        if missing:
            raise ValueError(f"Champs obligatoires manquants: {', '.join(missing)}")

    @staticmethod
    def validate_intervention_exists(intervention_id: str) -> Dict[str, Any]:
        """Vérifie que l'intervention existe et retourne ses données"""
        # Import lazy pour éviter la dépendance circulaire
        from api.interventions.repo import InterventionRepository

        repo = InterventionRepository()
        try:
            return repo.get_by_id(intervention_id, include_actions=False)
        except NotFoundError as exc:
            raise ValueError(f"Intervention {intervention_id} non trouvée") from exc

    @staticmethod
    def validate_status_exists(status_id: str) -> None:
        """Vérifie qu'un statut existe dans intervention_status_ref"""
        if status_id is None:
            return  # status_from peut être null

        repo = InterventionStatusRepository()
        all_statuses = repo.get_all()
        status_ids = [s['id'] for s in all_statuses]

        if status_id not in status_ids:
            raise ValueError(f"Statut {status_id} non trouvé dans intervention_status_ref")

    @staticmethod
    def validate_status_from_matches_current(
        intervention: Dict[str, Any],
        status_from: str | None
    ) -> None:
        """
        RÈGLE CRITIQUE: Vérifie que status_from correspond au statut actuel de l'intervention
        """
        current_status = intervention.get('status_actual')

        # Si status_from est None, on autorise (premier changement de statut)
        if status_from is None:
            return

        # Sinon, status_from doit correspondre au statut actuel
        if current_status != status_from:
            raise ValueError(
                f"Le status_from '{status_from}' ne correspond pas au statut actuel "
                f"de l'intervention '{current_status}'"
            )

    @staticmethod
    def validate_technician_exists(technician_id: str) -> None:
        """Vérifie que le technicien existe dans directus_users"""
        from api.settings import settings

        conn = settings.get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM directus_users WHERE id = %s", (technician_id,))
            row = cur.fetchone()

            if not row:
                raise ValueError(f"Technicien {technician_id} non trouvé")
        finally:
            conn.close()

    @staticmethod
    def sanitize_notes(notes: str | None) -> str | None:
        """Nettoie les notes en supprimant le HTML et les espaces"""
        if notes is None or not notes:
            return None

        sanitized = strip_html(notes).strip()
        return sanitized if sanitized else None

    @classmethod
    def validate_and_prepare(cls, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide toutes les règles métier et prépare les données
        Retourne les données validées et nettoyées
        """
        # Vérifie les champs obligatoires
        cls.validate_required_fields(log_data)

        # Valide que l'intervention existe et récupère ses données
        intervention = cls.validate_intervention_exists(str(log_data['intervention_id']))

        # Valide que les statuts existent
        cls.validate_status_exists(log_data.get('status_from'))
        cls.validate_status_exists(log_data['status_to'])

        # RÈGLE CRITIQUE: Vérifie que status_from correspond au statut actuel
        cls.validate_status_from_matches_current(
            intervention,
            log_data.get('status_from')
        )

        # Valide que le technicien existe
        cls.validate_technician_exists(str(log_data['technician_id']))

        # Sanitize les notes
        log_data['notes'] = cls.sanitize_notes(log_data.get('notes'))

        return log_data

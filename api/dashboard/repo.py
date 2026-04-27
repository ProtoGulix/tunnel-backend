"""Repository pour les données de dashboard/menu."""
from typing import Dict, Any
from api.db import get_connection, release_connection
from api.errors.exceptions import raise_db_error


class DashboardRepository:
    """Requêtes pour agrégations de dashboard (compteurs pour badges menu)"""

    def _get_connection(self):
        return get_connection()

    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des comptages pour les badges du menu.

        Endpoint léger (pas d'authentification requise, public).
        Retourne comptages par section principale du menu.
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Interventions ouvertes
            cur.execute(
                """SELECT COUNT(*) FROM intervention 
                   WHERE status_actual = (SELECT id FROM intervention_status_ref WHERE code = 'ouvert' LIMIT 1)"""
            )
            interventions_open = cur.fetchone()[0] or 0

            # Tâches non terminées
            cur.execute(
                """SELECT COUNT(*) FROM intervention_task 
                   WHERE status IN ('todo', 'in_progress')"""
            )
            tasks_pending = cur.fetchone()[0] or 0

            # Équipements (total)
            cur.execute("SELECT COUNT(*) FROM machine")
            equipements_total = cur.fetchone()[0] or 0

            # Plans préventifs actifs
            cur.execute(
                """SELECT COUNT(*) FROM preventive_plan WHERE active = TRUE"""
            )
            preventive_plans_active = cur.fetchone()[0] or 0

            # Stock items (total)
            cur.execute("SELECT COUNT(*) FROM stock_item")
            stock_items_total = cur.fetchone()[0] or 0

            # Demandes d'achat ouvertes
            cur.execute(
                """SELECT COUNT(*) FROM intervention_request 
                   WHERE statut IN ('nouvelle', 'en_attente', 'acceptee')"""
            )
            purchase_requests_open = cur.fetchone()[0] or 0

            # Fournisseurs
            cur.execute("SELECT COUNT(*) FROM supplier")
            suppliers_total = cur.fetchone()[0] or 0

            # Occurrence préventives en attente (générées mais pas acceptées)
            cur.execute(
                """SELECT COUNT(*) FROM preventive_occurrence 
                   WHERE status = 'pending' AND di_id IS NOT NULL"""
            )
            preventive_pending = cur.fetchone()[0] or 0

            return {
                "interventions": {
                    "open": interventions_open,
                    "label": "Interventions"
                },
                "tasks": {
                    "pending": tasks_pending,
                    "label": "Tâches"
                },
                "equipements": {
                    "total": equipements_total,
                    "label": "Équipements"
                },
                "preventive": {
                    "plans_active": preventive_plans_active,
                    "pending": preventive_pending,
                    "label": "Préventif"
                },
                "stock": {
                    "items": stock_items_total,
                    "label": "Stock"
                },
                "purchase_requests": {
                    "open": purchase_requests_open,
                    "label": "Demandes d'achat"
                },
                "suppliers": {
                    "total": suppliers_total,
                    "label": "Fournisseurs"
                }
            }
        except Exception as e:
            raise_db_error(e, "agrégation dashboard")
        finally:
            release_connection(conn)

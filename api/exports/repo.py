from typing import Dict, Any
from api.errors.exceptions import NotFoundError, DatabaseError
from api.settings import settings


class ExportRepository:
    """Repository spécialisé pour données d'export"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def get_intervention_code(self, intervention_id: str) -> str:
        """Récupère uniquement le code intervention (lightweight pour QR)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT code FROM intervention WHERE id = %s", (intervention_id,))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Intervention {intervention_id} non trouvée")
            return row[0] or intervention_id  # Fallback sur ID si pas de code
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur DB: {str(e)}")
        finally:
            conn.close()

    def get_intervention_export_data(self, intervention_id: str) -> Dict[str, Any]:
        """
        Récupère données complètes pour export PDF

        Returns structure compatible avec template:
        {
            "code": "INT-2026-001",
            "title": "...",
            "equipements": {...},
            "actions": [{...}],
            "status_logs": [{...}],
            ...
        }
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Query principale avec tous les JOINs
            query = """
                SELECT
                    i.id, i.code, i.title, i.priority, i.status_actual,
                    i.reported_date, i.reported_by, i.type_inter,
                    m.id as machine_id, m.code as machine_code,
                    m.name as machine_name, m.no_machine,
                    m.affectation, m.fabricant, m.numero_serie,
                    m.date_mise_service
                FROM intervention i
                LEFT JOIN machine m ON i.machine_id = m.id
                WHERE i.id = %s
            """
            cur.execute(query, (intervention_id,))
            row = cur.fetchone()

            if not row:
                raise NotFoundError(f"Intervention {intervention_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            intervention = dict(zip(cols, row))

            # Fetch actions (separate query for clarity)
            cur.execute("""
                SELECT
                    ia.id, ia.description, ia.time_spent, ia.created_at,
                    ia.complexity_score,
                    u.first_name, u.last_name,
                    asub.name as subcategory_name, asub.code as subcategory_code,
                    ac.name as category_name, ac.code as category_code
                FROM intervention_action ia
                LEFT JOIN directus_users u ON ia.tech = u.id
                LEFT JOIN action_subcategory asub ON ia.action_subcategory = asub.id
                LEFT JOIN action_category ac ON asub.category_id = ac.id
                WHERE ia.intervention_id = %s
                ORDER BY ia.created_at
            """, (intervention_id,))

            actions = []
            for action_row in cur.fetchall():
                action_dict = dict(zip([d[0] for d in cur.description], action_row))

                # Structure tech object (compatible avec template)
                first_name = action_dict.get('first_name')
                last_name = action_dict.get('last_name')
                initials = ""
                if first_name and last_name:
                    initials = f"{first_name[0]}{last_name[0]}"

                action_dict['tech'] = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'initial': initials
                }

                # Structure subcategory nested object (compatible avec template)
                action_dict['action_subcategory'] = {
                    'name': action_dict.get('subcategory_name'),
                    'code': action_dict.get('subcategory_code'),
                    'category': {
                        'name': action_dict.get('category_name'),
                        'code': action_dict.get('category_code')
                    }
                }
                actions.append(action_dict)

            # Fetch status logs
            cur.execute("""
                SELECT
                    sl.date, sl.status_from, sl.status_to,
                    u.first_name, u.last_name
                FROM intervention_status_log sl
                LEFT JOIN directus_users u ON sl.technician_id = u.id
                WHERE sl.intervention_id = %s
                ORDER BY sl.date ASC
            """, (intervention_id,))

            status_logs = []
            for log_row in cur.fetchall():
                log_dict = dict(zip([d[0] for d in cur.description], log_row))

                # Structure technician object (compatible avec template)
                first_name = log_dict.get('first_name')
                last_name = log_dict.get('last_name')
                initials = ""
                if first_name and last_name:
                    initials = f"{first_name[0]}{last_name[0]}"

                log_dict['technician_id'] = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'initial': initials
                }
                status_logs.append(log_dict)

            # Fetch purchase requests linked to this intervention
            cur.execute("""
                SELECT
                    pr.id, pr.item_label, pr.quantity_requested, pr.quantity_approved,
                    pr.urgent, pr.unit, pr.created_at, pr.requester_name,
                    si.ref as stock_item_ref, si.name as stock_item_name
                FROM purchase_request pr
                LEFT JOIN stock_item si ON pr.stock_item_id = si.id
                WHERE pr.intervention_id = %s
                ORDER BY pr.created_at DESC
            """, (intervention_id,))

            purchase_requests = []
            for pr_row in cur.fetchall():
                pr_dict = dict(zip([d[0] for d in cur.description], pr_row))
                purchase_requests.append(pr_dict)

            # Structure finale compatible template
            return {
                "code": intervention.get("code"),
                "title": intervention.get("title"),
                "priority": intervention.get("priority"),
                "status_actual": intervention.get("status_actual"),
                "reported_date": intervention.get("reported_date"),
                "reported_by": intervention.get("reported_by"),
                "type_inter": intervention.get("type_inter"),
                "observations": None,  # Champ non disponible dans le schéma
                "equipements": {
                    "code": intervention.get("machine_code"),
                    "name": intervention.get("machine_name"),
                    "no_machine": intervention.get("no_machine"),
                    "affectation": intervention.get("affectation"),
                    "fabricant": intervention.get("fabricant"),
                    "numero_serie": intervention.get("numero_serie"),
                    "date_mise_service": intervention.get("date_mise_service"),
                },
                "actions": actions,
                "status_logs": status_logs,
                "purchase_requests": purchase_requests,
                "stats": {
                    "action_count": len(actions),
                    "total_time": sum(a.get('time_spent', 0) or 0 for a in actions),
                    "purchase_requests_count": len(purchase_requests),
                }
            }

        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur lors de la récupération des données: {str(e)}")
        finally:
            conn.close()

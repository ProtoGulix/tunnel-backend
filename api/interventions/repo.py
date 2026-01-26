from typing import Dict, Any, List, Optional
from datetime import datetime

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.constants import PRIORITY_TYPES


class InterventionRepository:
    """Requêtes pour le domaine interventions"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}")

    def _map_equipement(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Mappe machine_id et ses colonnes associées en objet equipements + stats"""
        if row_dict.get('machine_id') is not None:
            row_dict['equipements'] = {
                'id': row_dict['machine_id'],
                'code': row_dict['m_code'],
                'name': row_dict['m_name'],
                'no_machine': row_dict['m_no_machine'],
                'affectation': row_dict['m_affectation'],
                'marque': row_dict['m_marque'],
                'model': row_dict['m_model'],
                'no_serie': row_dict['m_no_serie'],
                'equipement_mere': row_dict['m_equipement_mere'],
                'is_mere': row_dict['m_is_mere'],
                'type_equipement': row_dict['m_type_equipement'],
                'fabricant': row_dict['m_fabricant'],
                'numero_serie': row_dict['m_numero_serie'],
                'date_mise_service': row_dict['m_date_mise_service'],
                'notes': row_dict['m_notes']
            }
        else:
            row_dict['equipements'] = None

        # Crée l'objet stats
        row_dict['stats'] = {
            'action_count': row_dict.get('action_count', 0),
            'total_time': row_dict.get('total_time', 0),
            'avg_complexity': row_dict.get('avg_complexity')
        }

        # Nettoie les colonnes intermédiaires
        for key in list(row_dict.keys()):
            if key.startswith('m_') or key in ['action_count', 'total_time', 'avg_complexity']:
                row_dict.pop(key, None)

        return row_dict

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        equipement_id: str | None = None,
        statuses: List[str] | None = None,
        priorities: List[str] | None = None,
        sort: str | None = None,
        include_stats: bool = True,
    ) -> List[Dict[str, Any]]:
        """Récupère interventions avec filtres/sort et stats calculées en SQL (sans actions)"""
        # Garde-fou: limit max 1000
        limit = min(limit, 1000)

        # Valider priorités via PRIORITY_TYPES (source de vérité unique)
        priorities_norm = None
        if priorities:
            allowed_ids = {p['id'] for p in PRIORITY_TYPES}
            priorities_norm = [p for p in priorities if p in allowed_ids]

        # Construire SQL
        where_clauses = []
        params: List[Any] = []
        joins = []

        if equipement_id:
            where_clauses.append("i.machine_id = %s")
            params.append(equipement_id)

        if statuses and len(statuses) > 0:
            placeholders = ",".join(["%s"] * len(statuses))
            where_clauses.append(f"LOWER(i.status_actual) IN ({placeholders})")
            params.extend([s.lower() for s in statuses])

        if priorities_norm and len(priorities_norm) > 0:
            placeholders = ",".join(["%s"] * len(priorities_norm))
            where_clauses.append(f"i.priority IN ({placeholders})")
            params.extend(priorities_norm)

        where_sql = ("WHERE " + " AND ".join(where_clauses)
                     ) if where_clauses else ""

        # Tri
        order_sql_parts = []
        if sort:
            for item in [s.strip() for s in sort.split(',') if s.strip()]:
                desc = item.startswith('-')
                key = item[1:] if desc else item
                if key == 'reported_date':
                    order_sql_parts.append(
                        f"i.reported_date {'DESC' if desc else 'ASC'}")
                elif key == 'priority':
                    # Tri de sévérité: urgent > important > normale > faible
                    case_expr = (
                        "CASE i.priority "
                        "WHEN 'urgent' THEN 0 "
                        "WHEN 'important' THEN 1 "
                        "WHEN 'normale' THEN 2 "
                        "WHEN 'faible' THEN 3 "
                        "ELSE 4 END"
                    )
                    order_sql_parts.append(
                        f"{case_expr} {'ASC' if desc else 'DESC'}")
        if not order_sql_parts:
            order_sql_parts.append("i.reported_date DESC")
        order_sql = " ORDER BY " + ", ".join(order_sql_parts)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            query = f"""
                SELECT 
                    i.*,
                    m.code as m_code, m.name as m_name, m.no_machine as m_no_machine,
                    m.affectation as m_affectation, m.marque as m_marque, m.model as m_model,
                    m.no_serie as m_no_serie, m.equipement_mere as m_equipement_mere,
                    m.is_mere as m_is_mere, m.type_equipement as m_type_equipement,
                    m.fabricant as m_fabricant, m.numero_serie as m_numero_serie,
                    m.date_mise_service as m_date_mise_service, m.notes as m_notes,
                    COALESCE(SUM(ia.time_spent), 0) as total_time,
                    COUNT(ia.id) as action_count,
                    ROUND(AVG(ia.complexity_score)::numeric, 2)::float as avg_complexity
                FROM intervention i
                LEFT JOIN machine m ON i.machine_id = m.id
                LEFT JOIN intervention_action ia ON i.id = ia.intervention_id
                {" ".join(joins)}
                {where_sql}
                GROUP BY i.id, m.id
                {order_sql}
                LIMIT %s OFFSET %s
            """
            cur.execute(query, (*params, limit, offset))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            result = []
            for row in rows:
                row_dict = dict(zip(cols, row))
                row_dict['actions'] = []  # Vide
                mapped = self._map_equipement(row_dict)
                if not include_stats:
                    # Retirer l'objet stats si non demandé
                    mapped.pop('stats', None)
                result.append(mapped)

            return result
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_by_id(self, intervention_id: str) -> Dict[str, Any]:
        """Récupère une intervention par ID avec équipement et stats calculées en SQL"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 
                    i.*,
                    m.code as m_code, m.name as m_name, m.no_machine as m_no_machine,
                    m.affectation as m_affectation, m.marque as m_marque, m.model as m_model,
                    m.no_serie as m_no_serie, m.equipement_mere as m_equipement_mere,
                    m.is_mere as m_is_mere, m.type_equipement as m_type_equipement,
                    m.fabricant as m_fabricant, m.numero_serie as m_numero_serie,
                    m.date_mise_service as m_date_mise_service, m.notes as m_notes,
                    COALESCE(SUM(ia.time_spent), 0) as total_time,
                    COUNT(ia.id) as action_count,
                    ROUND(AVG(ia.complexity_score)::numeric, 2)::float as avg_complexity
                FROM intervention i
                LEFT JOIN machine m ON i.machine_id = m.id
                LEFT JOIN intervention_action ia ON i.id = ia.intervention_id
                WHERE i.id = %s
                GROUP BY i.id, m.id
                """,
                (intervention_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(
                    f"Intervention {intervention_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            return self._map_equipement(dict(zip(cols, row)))
        except NotFoundError:
            raise
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg:
                raise DatabaseError(
                    "Table 'intervention' inexistante - vérifier la structure de la base")
            elif "connection" in error_msg.lower():
                raise DatabaseError(
                    "Impossible de se connecter à la base de données")
            else:
                raise DatabaseError(f"Erreur base de données: {error_msg}")
        finally:
            conn.close()

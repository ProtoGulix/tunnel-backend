from typing import Dict, Any, List
from uuid import uuid4

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.constants import PRIORITY_TYPES

from api.intervention_actions.repo import InterventionActionRepository
from api.intervention_status_log.repo import InterventionStatusLogRepository


class InterventionRepository:
    """Requêtes pour le domaine interventions"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        equipement_id: str | None = None,
        statuses: List[str] | None = None,
        priorities: List[str] | None = None,
        sort: str | None = None,
        include_stats: bool = True,
        printed: bool | None = None,
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

        if printed is not None:
            where_clauses.append("i.printed_fiche = %s")
            params.append(printed)

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

                # Construire l'objet equipement depuis les colonnes m_*
                if row_dict.get('machine_id') is not None:
                    row_dict['equipements'] = {
                        'id': row_dict.pop('machine_id'),
                        'code': row_dict.pop('m_code', None),
                        'name': row_dict.pop('m_name', None),
                        'no_machine': row_dict.pop('m_no_machine', None),
                        'affectation': row_dict.pop('m_affectation', None),
                        'marque': row_dict.pop('m_marque', None),
                        'model': row_dict.pop('m_model', None),
                        'no_serie': row_dict.pop('m_no_serie', None),
                        'equipement_mere': row_dict.pop('m_equipement_mere', None),
                        'is_mere': row_dict.pop('m_is_mere', None),
                        'type_equipement': row_dict.pop('m_type_equipement', None),
                        'fabricant': row_dict.pop('m_fabricant', None),
                        'numero_serie': row_dict.pop('m_numero_serie', None),
                        'date_mise_service': row_dict.pop('m_date_mise_service', None),
                        'notes': row_dict.pop('m_notes', None),
                        'health': {
                            'level': 'unknown',
                            'reason': 'not_provided',
                            'rules_triggered': None
                        },
                        'parent_id': row_dict.get('m_equipement_mere'),
                        'children_ids': []
                    }
                else:
                    row_dict['equipements'] = None
                    # Nettoyer les colonnes m_* si machine_id est None
                    for key in list(row_dict.keys()):
                        if key.startswith('m_'):
                            row_dict.pop(key)

                # Créer l'objet stats si demandé
                if include_stats:
                    row_dict['stats'] = {
                        'action_count': row_dict.pop('action_count', 0),
                        'total_time': row_dict.pop('total_time', 0),
                        'avg_complexity': row_dict.pop('avg_complexity', None)
                    }
                else:
                    # Nettoyer les colonnes stats si non demandées
                    row_dict.pop('action_count', None)
                    row_dict.pop('total_time', None)
                    row_dict.pop('avg_complexity', None)

                row_dict['actions'] = []  # Vide pour get_all
                row_dict['status_logs'] = []  # Vide pour get_all
                result.append(row_dict)

            return result
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(self, intervention_id: str, include_actions: bool = True) -> Dict[str, Any]:
        """Récupère une intervention par ID avec équipement et stats calculées depuis les actions"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM intervention WHERE id = %s",
                (intervention_id,)
            )
            row = cur.fetchone()

            if not row:
                raise NotFoundError(
                    f"Intervention {intervention_id} non trouvée")

            cols = [desc[0] for desc in cur.description]
            intervention = dict(zip(cols, row))

            # Récupérer l'équipement via EquipementRepository pour garantir la cohérence
            if intervention.get('machine_id'):
                from api.equipements.repo import EquipementRepository
                equipement_repo = EquipementRepository()
                try:
                    intervention['equipements'] = equipement_repo.get_by_id(
                        intervention['machine_id'])
                except NotFoundError:
                    intervention['equipements'] = None
            else:
                intervention['equipements'] = None

            # Récupérer les actions via InterventionActionRepository
            if include_actions:

                action_repo = InterventionActionRepository()
                actions = action_repo.get_by_intervention(intervention_id)
                intervention['actions'] = actions

                # Calculer les stats depuis les actions récupérées
                intervention['stats'] = {
                    'action_count': len(actions),
                    'total_time': sum(a.get('time_spent', 0) or 0 for a in actions),
                    'avg_complexity': (
                        round(sum(a.get('complexity_score', 0) or 0 for a in actions if a.get('complexity_score')) /
                              len([a for a in actions if a.get('complexity_score')]), 2)
                        if any(a.get('complexity_score') for a in actions) else None
                    )
                }
            else:
                intervention['actions'] = []
                intervention['stats'] = {
                    'action_count': 0,
                    'total_time': 0,
                    'avg_complexity': None
                }

            # Récupérer les status logs via InterventionStatusLogRepository
            status_log_repo = InterventionStatusLogRepository()
            intervention['status_logs'] = status_log_repo.get_by_intervention(
                intervention_id)

            return intervention
        except NotFoundError:
            raise
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg:
                raise DatabaseError(
                    "Table 'intervention' inexistante - vérifier la structure de la base") from e
            if "connection" in error_msg.lower():
                raise DatabaseError(
                    "Impossible de se connecter à la base de données") from e
            raise DatabaseError(f"Erreur base de données: {error_msg}") from e
        finally:
            conn.close()

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle intervention"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            intervention_id = str(uuid4())

            cur.execute(
                """
                INSERT INTO intervention
                (id, title, machine_id, type_inter, priority,
                 reported_by, tech_initials, status_actual,
                 printed_fiche, reported_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    intervention_id,
                    data.get('title'),
                    data.get('machine_id'),
                    data.get('type_inter'),
                    data.get('priority'),
                    data.get('reported_by'),
                    data.get('tech_initials'),
                    data.get('status_actual', 'ouvert'),
                    data.get('printed_fiche', False),
                    data.get('reported_date')
                )
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la création de l'intervention: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(intervention_id)

    def update(self, intervention_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une intervention existante"""
        self.get_by_id(intervention_id, include_actions=False)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            updatable_fields = [
                'title', 'machine_id', 'type_inter', 'priority',
                'reported_by', 'tech_initials', 'status_actual',
                'printed_fiche', 'reported_date'
            ]

            set_clauses = []
            params = []

            for field in updatable_fields:
                if field in data:
                    set_clauses.append(f"{field} = %s")
                    params.append(data[field])

            if not set_clauses:
                return self.get_by_id(intervention_id)

            params.append(intervention_id)

            query = f"""
                UPDATE intervention
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """

            cur.execute(query, params)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise à jour: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(intervention_id)

    def delete(self, intervention_id: str) -> bool:
        """Supprime une intervention"""
        self.get_by_id(intervention_id, include_actions=False)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM intervention WHERE id = %s",
                (intervention_id,)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression: {str(e)}") from e
        finally:
            conn.close()

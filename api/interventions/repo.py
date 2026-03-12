from fastapi import HTTPException
from typing import Dict, Any, List
from uuid import uuid4

from api.settings import settings
from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, raise_db_error, NotFoundError
from api.constants import PRIORITY_TYPES, CLOSED_STATUS_CODE

from api.intervention_actions.repo import InterventionActionRepository
from api.intervention_status_log.repo import InterventionStatusLogRepository


class InterventionRepository:
    """Requêtes pour le domaine interventions"""

    def _get_connection(self):
        return get_connection()

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
                    ir.id AS request_id,
                    m.code as m_code, m.name as m_name,
                    m.equipement_mere as m_parent_id,
                    ec.id as ec_id, ec.code as ec_code, ec.label as ec_label,
                    mh.m_open_count, mh.m_urgent_count,
                    COALESCE(SUM(ia.time_spent), 0) as total_time,
                    COUNT(DISTINCT ia.id) as action_count,
                    ROUND(AVG(ia.complexity_score)::numeric, 2)::float as avg_complexity,
                    COUNT(DISTINCT iapr.purchase_request_id) as purchase_count
                FROM intervention i
                LEFT JOIN intervention_request ir ON ir.intervention_id = i.id
                LEFT JOIN machine m ON i.machine_id = m.id
                LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
                LEFT JOIN LATERAL (
                    SELECT
                        COUNT(CASE WHEN i2.status_actual != (SELECT id FROM intervention_status_ref WHERE code = %s LIMIT 1) THEN i2.id END) as m_open_count,
                        COUNT(CASE WHEN i2.status_actual != (SELECT id FROM intervention_status_ref WHERE code = %s LIMIT 1) AND i2.priority = 'urgent' THEN i2.id END) as m_urgent_count
                    FROM intervention i2
                    WHERE i2.machine_id = m.id
                ) mh ON TRUE
                LEFT JOIN intervention_action ia ON i.id = ia.intervention_id
                LEFT JOIN intervention_action_purchase_request iapr ON ia.id = iapr.intervention_action_id
                {" ".join(joins)}
                {where_sql}
                GROUP BY i.id, ir.id, m.id, ec.id, mh.m_open_count, mh.m_urgent_count
                {order_sql}
                LIMIT %s OFFSET %s
            """
            cur.execute(query, (CLOSED_STATUS_CODE,
                        CLOSED_STATUS_CODE, *params, limit, offset))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

            result = []
            for row in rows:
                row_dict = dict(zip(cols, row))

                # Construire l'objet equipement depuis les colonnes préfixées
                if row_dict.get('machine_id') is not None:
                    open_count = row_dict.pop('m_open_count', 0) or 0
                    urgent_count = row_dict.pop('m_urgent_count', 0) or 0
                    if urgent_count > 0:
                        health = {
                            'level': 'critical', 'reason': f'{urgent_count} intervention(s) urgente(s)', 'rules_triggered': None}
                    elif open_count > 0:
                        health = {
                            'level': 'maintenance', 'reason': f'{open_count} intervention(s) ouverte(s)', 'rules_triggered': None}
                    else:
                        health = {
                            'level': 'ok', 'reason': 'Aucune intervention ouverte', 'rules_triggered': None}

                    ec_id = row_dict.pop('ec_id', None)
                    ec_code = row_dict.pop('ec_code', None)
                    ec_label = row_dict.pop('ec_label', None)

                    row_dict['equipements'] = {
                        'id': row_dict.pop('machine_id'),
                        'code': row_dict.pop('m_code', None),
                        'name': row_dict.pop('m_name', None),
                        'health': health,
                        'parent_id': row_dict.pop('m_parent_id', None),
                        'equipement_class': {'id': ec_id, 'code': ec_code, 'label': ec_label} if ec_id else None
                    }
                else:
                    row_dict['equipements'] = None
                    for key in list(row_dict.keys()):
                        if key.startswith('m_') or key.startswith('ec_') or key in ('m_open_count', 'm_urgent_count'):
                            row_dict.pop(key)

                # Créer l'objet stats si demandé
                if include_stats:
                    row_dict['stats'] = {
                        'action_count': row_dict.pop('action_count', 0),
                        'total_time': row_dict.pop('total_time', 0),
                        'avg_complexity': row_dict.pop('avg_complexity', None),
                        'purchase_count': row_dict.pop('purchase_count', 0)
                    }
                else:
                    # Nettoyer les colonnes stats si non demandées
                    row_dict.pop('action_count', None)
                    row_dict.pop('total_time', None)
                    row_dict.pop('avg_complexity', None)
                    row_dict.pop('purchase_count', None)

                row_dict['actions'] = []  # Vide pour get_all
                row_dict['status_logs'] = []  # Vide pour get_all
                result.append(row_dict)

            return result
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def get_by_id(self, intervention_id: str, include_actions: bool = True) -> Dict[str, Any]:
        """Récupère une intervention par ID avec équipement et stats calculées depuis les actions"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT i.*, ir.id AS request_id
                FROM intervention i
                LEFT JOIN intervention_request ir ON ir.intervention_id = i.id
                WHERE i.id = %s
                """,
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
                # purchase_count: compter les purchase_requests liées via les actions
                purchase_count = sum(
                    len(a.get('purchase_requests', [])) for a in actions)
                intervention['stats'] = {
                    'action_count': len(actions),
                    'total_time': sum(a.get('time_spent', 0) or 0 for a in actions),
                    'avg_complexity': (
                        round(sum(a.get('complexity_score', 0) or 0 for a in actions if a.get('complexity_score')) /
                              len([a for a in actions if a.get('complexity_score')]), 2)
                        if any(a.get('complexity_score') for a in actions) else None
                    ),
                    'purchase_count': purchase_count
                }
            else:
                intervention['actions'] = []
                intervention['stats'] = {
                    'action_count': 0,
                    'total_time': 0,
                    'avg_complexity': None,
                    'purchase_count': 0
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
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle intervention"""
        from api.interventions.validators import InterventionValidator
        InterventionValidator.validate_create(data)

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
            release_connection(conn)

        return self.get_by_id(intervention_id)

    def update(self, intervention_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une intervention existante"""
        existing = self.get_by_id(intervention_id, include_actions=False)

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
            release_connection(conn)

        result = self.get_by_id(intervention_id)

        # Si le statut vient de changer vers 'ferme', clôturer la demande liée
        if 'status_actual' in data:
            new_status = result.get('status_actual')
            old_status = existing.get('status_actual')
            if new_status != old_status:
                # Résoudre le code du nouveau statut
                self._notify_if_closed(intervention_id, new_status)

        return result

    def _notify_if_closed(self, intervention_id: str, status_actual_id: Any) -> None:
        """Notifie le repo des demandes si l'intervention vient d'être fermée."""
        if not status_actual_id:
            return
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT code FROM intervention_status_ref WHERE id = %s LIMIT 1",
                (str(status_actual_id),),
            )
            row = cur.fetchone()
            if row and row[0] == CLOSED_STATUS_CODE:
                from api.intervention_requests.repo import InterventionRequestRepository
                InterventionRequestRepository().on_intervention_closed(intervention_id)
        except Exception:
            pass  # Ne pas bloquer la mise à jour de l'intervention
        finally:
            release_connection(conn)

    def delete(self, intervention_id: str) -> bool:
        """Supprime une intervention (interdit si actions ou demandes d'achat liées)"""
        from api.interventions.validators import InterventionValidator
        self.get_by_id(intervention_id, include_actions=False)
        InterventionValidator.validate_deletable(intervention_id)

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
            release_connection(conn)

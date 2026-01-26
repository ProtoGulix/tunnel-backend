from typing import Dict, Any, List
from datetime import datetime, timedelta

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.constants import INTERVENTION_TYPE_IDS, get_active_status_ids, PRIORITY_TYPES, CLOSED_STATUS_CODE


class EquipementRepository:
    """Requêtes pour le domaine equipement avec statistiques interventions"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}")

    def _get_closed_status_id(self, conn) -> str:
        """Récupère l'ID du statut 'ferme' depuis la DB"""
        cur = conn.cursor()
        cur.execute(
            f"SELECT id FROM intervention_status_ref WHERE code = %s LIMIT 1",
            (CLOSED_STATUS_CODE,)
        )
        row = cur.fetchone()
        return row[0] if row else CLOSED_STATUS_CODE

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère tous les équipements - liste légère avec health"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ferme_id = self._get_closed_status_id(conn)

            query = f"""
                SELECT
                    m.id,
                    m.code,
                    m.name,
                    m.equipement_mere,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' THEN i.id END) as open_interventions_count,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                GROUP BY m.id
                ORDER BY urgent_count DESC, open_interventions_count DESC, m.name ASC
            """

            cur.execute(query)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            equipements = [dict(zip(cols, row)) for row in rows]

            # Enrichir avec health
            for equipement in equipements:
                open_count = equipement.pop('open_interventions_count', 0) or 0
                urgent_count = equipement.pop('urgent_count', 0) or 0

                health = self._calculate_health(open_count, urgent_count)
                equipement['health'] = {
                    'level': health['level'],
                    'reason': health['reason']
                }
                equipement['parent_id'] = equipement.pop(
                    'equipement_mere', None)

            return equipements

        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_all_with_stats(self) -> List[Dict[str, Any]]:
        """Récupère tous les équipements avec statistiques interventions"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ferme_id = self._get_closed_status_id(conn)

            status_columns = []
            for status_id, _ in all_status:
                status_columns.append(
                    f"COUNT(CASE WHEN i.status_actual = '{status_id}' THEN i.id END) as status_{status_id}"
                )

            # Générer dynamiquement les colonnes par priorité via IDs
            priority_columns = []
            for p in PRIORITY_TYPES:
                pid = p.get('id')
                priority_columns.append(
                    f"COUNT(CASE WHEN i.priority = '{pid}' THEN i.id END) as priority_{pid}"
                )

            query = f"""
                SELECT
                    m.id,
                    m.code,
                    m.name,
                    m.equipement_mere,
                    m.is_mere,
                    parent.id as parent_id,
                    parent.code as parent_code,
                    parent.name as parent_name,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' THEN i.id END) as open_interventions_count,
                    {', '.join(status_columns)},
                    {', '.join(priority_columns)},
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN machine parent ON m.equipement_mere = parent.id
                LEFT JOIN intervention i ON i.machine_id = m.id
                GROUP BY m.id, parent.id
                ORDER BY open_interventions_count DESC, m.name ASC
            """

            cur.execute(query)

            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            equipements = [dict(zip(cols, row)) for row in rows]

            # Enrichir avec statut calculé
            for equipement in equipements:
                open_count = equipement.get('open_interventions_count', 0) or 0
                urgent_count = equipement.get('urgent_count', 0) or 0

                equipement['status'] = self._calculate_status(
                    open_count,
                    urgent_count
                )
                equipement['status_color'] = self._get_status_color(
                    equipement['status'])

                # Formater parent
                if equipement.get('parent_id'):
                    equipement['parent'] = {
                        'id': equipement['parent_id'],
                        'code': equipement['parent_code'],
                        'name': equipement['parent_name']
                    }
                else:
                    equipement['parent'] = None

                # Formater stats par statut (clé = ID, comptage basé sur ID)
                by_status = {}
                for status_id, status_code in all_status:
                    by_status[str(status_id)] = equipement.pop(
                        f'status_{status_id}', 0) or 0

                # Formater stats par priorité (clé = ID de priorité)
                by_priority = {}
                for p in PRIORITY_TYPES:
                    pid = p.get('id')
                    by_priority[pid] = equipement.pop(
                        f'priority_{pid}', 0) or 0

                equipement['stats'] = {
                    'by_status': by_status,
                    'by_priority': by_priority,
                    'open_interventions_count': open_count
                }

                # Nettoyage champs internes
                equipement.pop('parent_id', None)
                equipement.pop('parent_code', None)
                equipement.pop('parent_name', None)
                equipement.pop('urgent_count', None)
                equipement.pop('open_interventions_count', None)

            return equipements

        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_by_id(self, equipement_id: str) -> Dict[str, Any]:
        """Récupère un équipement par ID avec health et children_ids"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ferme_id = self._get_closed_status_id(conn)

            query = f"""
                SELECT 
                    m.id,
                    m.code,
                    m.name,
                    m.equipement_mere,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' THEN i.id END) as open_interventions_count,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                WHERE m.id = %s
                GROUP BY m.id
            """

            cur.execute(query, (equipement_id,))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Équipement {equipement_id} non trouvé")

            cols = [desc[0] for desc in cur.description]
            equipement = dict(zip(cols, row))

            # Health calculation
            open_count = equipement.pop('open_interventions_count', 0) or 0
            urgent_count = equipement.pop('urgent_count', 0) or 0
            health = self._calculate_health(open_count, urgent_count)

            equipement['health'] = health
            equipement['parent_id'] = equipement.pop('equipement_mere', None)

            # Get children_ids
            cur.execute(
                "SELECT id FROM machine WHERE equipement_mere = %s", (equipement_id,))
            children = cur.fetchall()
            equipement['children_ids'] = [str(child[0]) for child in children]

            return equipement
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_by_id_with_details(self, equipement_id: str, period_days: int = 30) -> Dict[str, Any]:
        """Récupère un équipement avec interventions et actions en une seule requête"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ferme_status_id = self._get_closed_status_id(conn)

            # Une seule requête pour tout
            cur.execute(
                """
                SELECT 
                    m.id, m.code, m.name, m.equipement_mere, m.is_mere,
                    parent.id as parent_id, parent.code as parent_code, parent.name as parent_name,
                    i.id as intervention_id,
                    i.code as intervention_code,
                    i.title as intervention_title,
                    i.status_actual as intervention_status,
                    i.priority as intervention_priority,
                    i.reported_date,
                    i.type_inter,
                    ia.id as action_id,
                    ia.time_spent,
                    ia.created_at,
                    ia.complexity_score,
                    COALESCE(SUM(ia.time_spent) OVER (PARTITION BY i.id), 0) as intervention_total_time,
                    COUNT(ia.id) OVER (PARTITION BY i.id) as intervention_action_count,
                    ROUND(AVG(ia.complexity_score) OVER (PARTITION BY i.id)::numeric, 2)::float as intervention_avg_complexity
                FROM machine m
                LEFT JOIN machine parent ON m.equipement_mere = parent.id
                LEFT JOIN intervention i ON i.machine_id = m.id
                LEFT JOIN intervention_action ia ON i.id = ia.intervention_id
                WHERE m.id = %s
                ORDER BY 
                    i.id,
                    CASE WHEN i.priority = 'urgent' THEN 0 ELSE 1 END,
                    CASE WHEN i.status_actual = (SELECT id FROM intervention_status_ref WHERE code = 'ferme' LIMIT 1) THEN 2 
                         ELSE 0 END,
                    i.reported_date DESC,
                    ia.created_at DESC
                """,
                (equipement_id,)
            )

            rows = cur.fetchall()

            if not rows:
                raise NotFoundError(f"Équipement {equipement_id} non trouvé")

            cols = [desc[0] for desc in cur.description]
            all_rows = [dict(zip(cols, row)) for row in rows]

            # Récupérer info équipement (même pour chaque ligne)
            first_row = all_rows[0]
            equipement = {
                'id': first_row['id'],
                'code': first_row['code'],
                'name': first_row['name'],
                'equipement_mere': first_row['equipement_mere'],
                'is_mere': first_row['is_mere'],
            }

            # Parent si existe
            if first_row.get('parent_id'):
                equipement['parent'] = {
                    'id': first_row['parent_id'],
                    'code': first_row['parent_code'],
                    'name': first_row['parent_name']
                }
            else:
                equipement['parent'] = None

            # Regrouper interventions et actions
            interventions_map = {}
            actions = []
            total_time_spent = 0

            for row in all_rows:
                # Ajouter action si existe
                if row.get('action_id'):
                    actions.append({
                        'id': row['action_id'],
                        'intervention_id': row['intervention_id'],
                        'time_spent': row['time_spent'],
                        'created_at': row['created_at']
                    })
                    total_time_spent += float(row['time_spent'] or 0)

                # Ajouter intervention avec stats (une fois)
                if row.get('intervention_id') and row['intervention_id'] not in interventions_map:
                    interventions_map[row['intervention_id']] = {
                        'id': row['intervention_id'],
                        'code': row['intervention_code'],
                        'title': row['intervention_title'],
                        'status': row['intervention_status'],
                        'priority': row['intervention_priority'],
                        'reported_date': row['reported_date'],
                        'type_inter': row['type_inter'],
                        'closed_date': row['reported_date'],
                        'total_time': row['intervention_total_time'],
                        'action_count': int(row['intervention_action_count']),
                        'avg_complexity': row['intervention_avg_complexity']
                    }

            interventions = list(interventions_map.values())

            # Statut equipement
            urgent_count = sum(
                1 for i in interventions
                if i.get('priority') == 'urgent' and i.get('status') != ferme_status_id
            )
            open_count = sum(
                1 for i in interventions
                if i.get('status') != ferme_status_id
            )

            equipement['status'] = self._calculate_status(
                open_count, urgent_count)
            equipement['status_color'] = self._get_status_color(
                equipement['status'])
            equipement['interventions'] = interventions
            equipement['actions'] = actions
            equipement['time_spent_period_hours'] = round(total_time_spent, 2)
            equipement['period_days'] = period_days

            return equipement

        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_by_equipement_mere(self, equipement_mere_id: str) -> List[Dict[str, Any]]:
        """Récupère les sous-équipements d'un équipement parent avec health"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ferme_id = self._get_closed_status_id(conn)

            query = f"""
                SELECT 
                    m.id,
                    m.code,
                    m.name,
                    m.equipement_mere,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' THEN i.id END) as open_interventions_count,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                WHERE m.equipement_mere = %s
                GROUP BY m.id
                ORDER BY urgent_count DESC, open_interventions_count DESC, m.name ASC
            """

            cur.execute(query, (equipement_mere_id,))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            equipements = [dict(zip(cols, row)) for row in rows]

            # Enrichir avec health
            for equipement in equipements:
                open_count = equipement.pop('open_interventions_count', 0) or 0
                urgent_count = equipement.pop('urgent_count', 0) or 0

                health = self._calculate_health(open_count, urgent_count)
                equipement['health'] = {
                    'level': health['level'],
                    'reason': health['reason']
                }
                equipement['parent_id'] = equipement.pop(
                    'equipement_mere', None)

            return equipements
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_stats_by_id(self, equipement_id: str, start_date=None, end_date=None) -> Dict[str, Any]:
        """Récupère les statistiques détaillées d'un équipement, avec filtre période optionnel"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ferme_id = self._get_closed_status_id(conn)

            # Vérifier que l'équipement existe
            cur.execute("SELECT id FROM machine WHERE id = %s",
                        (equipement_id,))
            if not cur.fetchone():
                raise NotFoundError(f"Équipement {equipement_id} non trouvé")

            # Récupérer tous les statuts
            cur.execute("SELECT id, code FROM intervention_status_ref")
            all_status = [(row[0], row[1]) for row in cur.fetchall()]

            # Générer colonnes par statut
            status_columns = []
            for status_id, _ in all_status:
                status_columns.append(
                    f"COUNT(CASE WHEN i.status_actual = '{status_id}' THEN i.id END) as status_{status_id}"
                )

            # Générer colonnes par priorité
            priority_columns = []
            for p in PRIORITY_TYPES:
                pid = p.get('id')
                priority_columns.append(
                    f"COUNT(CASE WHEN i.priority = '{pid}' THEN i.id END) as priority_{pid}"
                )

            where_clauses = ["i.machine_id = %s"]
            params = [equipement_id]

            # Période: start_date optionnel, end_date optionnel (defaut = NOW())
            if start_date:
                where_clauses.append("i.reported_date >= %s")
                params.append(start_date)
            if end_date:
                where_clauses.append("i.reported_date <= %s")
                params.append(end_date)

            where_sql = "WHERE " + " AND ".join(where_clauses)

            query = f"""
                SELECT 
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' THEN i.id END) as open_count,
                    COUNT(CASE WHEN i.status_actual = '{ferme_id}' THEN i.id END) as closed_count,
                    {', '.join(status_columns)},
                    {', '.join(priority_columns)}
                FROM intervention i
                {where_sql}
            """

            cur.execute(query, tuple(params))
            row = cur.fetchone()
            cols = [desc[0] for desc in cur.description]
            data = dict(zip(cols, row))

            # Formater stats
            by_status = {}
            for status_id, status_code in all_status:
                by_status[str(status_id)] = data.pop(
                    f'status_{status_id}', 0) or 0

            by_priority = {}
            for p in PRIORITY_TYPES:
                pid = p.get('id')
                by_priority[pid] = data.pop(f'priority_{pid}', 0) or 0

            return {
                'interventions': {
                    'open': data['open_count'] or 0,
                    'closed': data['closed_count'] or 0,
                    'by_status': by_status,
                    'by_priority': by_priority
                }
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_health_by_id(self, equipement_id: str) -> Dict[str, Any]:
        """Récupère uniquement le health d'un équipement (ultra-léger)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ferme_id = self._get_closed_status_id(conn)

            query = f"""
                SELECT 
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' THEN i.id END) as open_count,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                WHERE m.id = %s
                GROUP BY m.id
            """

            cur.execute(query, (equipement_id,))
            row = cur.fetchone()

            if row is None:
                # Vérifier si l'équipement existe
                cur.execute("SELECT id FROM machine WHERE id = %s",
                            (equipement_id,))
                if not cur.fetchone():
                    raise NotFoundError(
                        f"Équipement {equipement_id} non trouvé")
                # Équipement existe mais pas d'interventions
                open_count, urgent_count = 0, 0
            else:
                open_count = row[0] or 0
                urgent_count = row[1] or 0

            health = self._calculate_health(open_count, urgent_count)
            return {
                'level': health['level'],
                'reason': health['reason']
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def _calculate_health(self, open_count: int, urgent_count: int) -> Dict[str, Any]:
        """Calcule le health d'un équipement selon interventions"""
        rules_triggered = []
        level = 'ok'
        reason = 'Aucune intervention ouverte'

        if urgent_count >= 1:
            level = 'critical'
            reason = f"{urgent_count} intervention{'s' if urgent_count > 1 else ''} urgente{'s' if urgent_count > 1 else ''} ouverte{'s' if urgent_count > 1 else ''}"
            rules_triggered.append('URGENT_OPEN >= 1')
        elif open_count > 5:
            level = 'warning'
            reason = f"{open_count} interventions ouvertes"
            rules_triggered.append('OPEN_TOTAL > 5')
        elif open_count > 0:
            level = 'maintenance'
            reason = f"{open_count} intervention{'s' if open_count > 1 else ''} ouverte{'s' if open_count > 1 else ''}"
            rules_triggered.append('OPEN_TOTAL > 0')

        return {
            'level': level,
            'reason': reason,
            'rules_triggered': rules_triggered
        }

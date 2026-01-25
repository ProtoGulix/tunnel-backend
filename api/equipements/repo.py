from typing import Dict, Any, List
from datetime import datetime, timedelta

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.constants import INTERVENTION_TYPE_IDS


class EquipementRepository:
    """Requêtes pour le domaine equipement avec statistiques interventions"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}")

    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère tous les équipements avec statistiques interventions"""
        return self.get_all_with_stats()

    def get_all_with_stats(self) -> List[Dict[str, Any]]:
        """Récupère tous les équipements avec statistiques interventions"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Générer dynamiquement les colonnes pour tous les types
            type_columns = []
            for t_id in INTERVENTION_TYPE_IDS:
                t_lower = t_id.lower()
                type_columns.extend([
                    f"COUNT(CASE WHEN i.status_actual IN ('open', 'in_progress') AND i.type_inter = '{t_id}' THEN i.id END) as {t_lower}_total",
                    f"COUNT(CASE WHEN i.status_actual = 'open' AND i.type_inter = '{t_id}' THEN i.id END) as {t_lower}_open",
                    f"COUNT(CASE WHEN i.status_actual = 'in_progress' AND i.type_inter = '{t_id}' THEN i.id END) as {t_lower}_in_progress"
                ])

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
                    COUNT(CASE WHEN i.status_actual IN ('open', 'in_progress') THEN i.id END) as open_interventions_count,
                    {', '.join(type_columns)},
                    COUNT(CASE WHEN i.status_actual IN ('open', 'in_progress') AND i.priority = 'urgent' THEN i.id END) as urgent_count
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
                equipement['status'] = self._calculate_status(
                    equipement['open_interventions_count'],
                    equipement['urgent_count']
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

                # Formater stats interventions par type
                interventions_stats = {}
                for t_id in INTERVENTION_TYPE_IDS:
                    t_lower = t_id.lower()
                    interventions_stats[t_id] = {
                        'total': equipement.pop(f'{t_lower}_total', 0) or 0,
                        'open': equipement.pop(f'{t_lower}_open', 0) or 0,
                        'in_progress': equipement.pop(f'{t_lower}_in_progress', 0) or 0
                    }

                equipement['stats'] = {'interventions': interventions_stats}

                # Nettoyage champs internes
                equipement.pop('parent_id', None)
                equipement.pop('parent_code', None)
                equipement.pop('parent_name', None)
                equipement.pop('urgent_count', None)

            return equipements

        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def get_by_id(self, equipement_id: str) -> Dict[str, Any]:
        """Récupère un équipement par ID avec statistiques interventions"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Générer dynamiquement les colonnes pour tous les types
            type_columns = []
            for t_id in INTERVENTION_TYPE_IDS:
                t_lower = t_id.lower()
                type_columns.extend([
                    f"COUNT(CASE WHEN i.status_actual IN ('open', 'in_progress') AND i.type_inter = '{t_id}' THEN i.id END) as {t_lower}_total",
                    f"COUNT(CASE WHEN i.status_actual = 'open' AND i.type_inter = '{t_id}' THEN i.id END) as {t_lower}_open",
                    f"COUNT(CASE WHEN i.status_actual = 'in_progress' AND i.type_inter = '{t_id}' THEN i.id END) as {t_lower}_in_progress"
                ])

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
                    COUNT(CASE WHEN i.status_actual IN ('open', 'in_progress') THEN i.id END) as open_interventions_count,
                    {', '.join(type_columns)},
                    COUNT(CASE WHEN i.status_actual IN ('open', 'in_progress') AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN machine parent ON m.equipement_mere = parent.id
                LEFT JOIN intervention i ON i.machine_id = m.id
                WHERE m.id = %s
                GROUP BY m.id, parent.id
            """

            cur.execute(query, (equipement_id,))

            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Équipement {equipement_id} non trouvé")

            cols = [desc[0] for desc in cur.description]
            equipement = dict(zip(cols, row))

            # Enrichir avec statut calculé
            equipement['status'] = self._calculate_status(
                equipement['open_interventions_count'],
                equipement['urgent_count']
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

            # Formater stats interventions par type
            interventions_stats = {}
            for t_id in INTERVENTION_TYPE_IDS:
                t_lower = t_id.lower()
                interventions_stats[t_id] = {
                    'total': equipement.pop(f'{t_lower}_total', 0) or 0,
                    'open': equipement.pop(f'{t_lower}_open', 0) or 0,
                    'in_progress': equipement.pop(f'{t_lower}_in_progress', 0) or 0
                }

            equipement['stats'] = {'interventions': interventions_stats}

            # Nettoyage champs internes
            equipement.pop('parent_id', None)
            equipement.pop('parent_code', None)
            equipement.pop('parent_name', None)
            equipement.pop('urgent_count', None)

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
                    CASE WHEN i.status_actual = 'open' THEN 0 
                         WHEN i.status_actual = 'in_progress' THEN 1 
                         ELSE 2 END,
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
                1 for i in interventions if i.get('priority') == 'urgent')
            open_count = sum(
                1 for i in interventions
                if i.get('status') in ('open', 'in_progress')
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
        """Récupère les sous-équipements d'un équipement parent avec statistiques interventions"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Générer dynamiquement les colonnes pour tous les types
            type_columns = []
            for t_id in INTERVENTION_TYPE_IDS:
                t_lower = t_id.lower()
                type_columns.extend([
                    f"COUNT(CASE WHEN i.status_actual IN ('open', 'in_progress') AND i.type_inter = '{t_id}' THEN i.id END) as {t_lower}_total",
                    f"COUNT(CASE WHEN i.status_actual = 'open' AND i.type_inter = '{t_id}' THEN i.id END) as {t_lower}_open",
                    f"COUNT(CASE WHEN i.status_actual = 'in_progress' AND i.type_inter = '{t_id}' THEN i.id END) as {t_lower}_in_progress"
                ])

            query = f"""
                SELECT 
                    m.id,
                    m.code,
                    m.name,
                    m.equipement_mere,
                    m.is_mere,
                    NULL as parent_id,
                    NULL as parent_code,
                    NULL as parent_name,
                    COUNT(CASE WHEN i.status_actual IN ('open', 'in_progress') THEN i.id END) as open_interventions_count,
                    {', '.join(type_columns)},
                    COUNT(CASE WHEN i.status_actual IN ('open', 'in_progress') AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                WHERE m.equipement_mere = %s
                GROUP BY m.id
                ORDER BY open_interventions_count DESC, m.name ASC
            """

            cur.execute(query, (equipement_mere_id,))

            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            equipements = [dict(zip(cols, row)) for row in rows]

            # Enrichir avec statut calculé
            for equipement in equipements:
                equipement['status'] = self._calculate_status(
                    equipement['open_interventions_count'],
                    equipement['urgent_count']
                )
                equipement['status_color'] = self._get_status_color(
                    equipement['status'])
                equipement['parent'] = None

                # Formater stats interventions par type
                interventions_stats = {}
                for t_id in INTERVENTION_TYPE_IDS:
                    t_lower = t_id.lower()
                    interventions_stats[t_id] = {
                        'total': equipement.pop(f'{t_lower}_total', 0) or 0,
                        'open': equipement.pop(f'{t_lower}_open', 0) or 0,
                        'in_progress': equipement.pop(f'{t_lower}_in_progress', 0) or 0
                    }

                equipement['stats'] = {'interventions': interventions_stats}

                # Nettoyage champs internes
                equipement.pop('parent_id', None)
                equipement.pop('parent_code', None)
                equipement.pop('parent_name', None)
                equipement.pop('urgent_count', None)

            return equipements
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}")
        finally:
            conn.close()

    def _calculate_status(self, open_count: int, urgent_count: int) -> str:
        """Calcule le statut d'un équipement selon interventions"""
        if urgent_count > 0:
            return 'critical'
        if open_count >= 3:
            return 'warning'
        if open_count > 0:
            return 'maintenance'
        return 'ok'

    def _get_status_color(self, status: str) -> str:
        """Retourne la couleur associée au statut"""
        colors = {
            'ok': 'green',
            'maintenance': 'blue',
            'warning': 'orange',
            'critical': 'red'
        }
        return colors.get(status, 'gray')

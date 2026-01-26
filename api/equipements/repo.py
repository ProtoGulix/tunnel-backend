"""Requêtes pour le domaine équipements"""
from typing import Dict, Any, List

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.constants import PRIORITY_TYPES, CLOSED_STATUS_CODE


class EquipementRepository:
    """Requêtes pour le domaine equipement avec statistiques interventions"""

    def _get_connection(self):
        """Ouvre une connexion à la base de données via settings"""
        try:
            return settings.get_db_connection()
        except Exception as e:
            raise DatabaseError(
                f"Erreur de connexion base de données: {str(e)}") from e

    def _get_closed_status_id(self, conn) -> str:
        """Récupère l'ID du statut 'ferme' depuis la DB"""
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM intervention_status_ref WHERE code = %s LIMIT 1",
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
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
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
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
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
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
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
            for status_id, _ in all_status:
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
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
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
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
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

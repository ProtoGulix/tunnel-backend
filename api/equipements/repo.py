"""Requêtes pour le domaine équipements"""
from typing import Dict, Any, List
from uuid import uuid4

from api.settings import settings
from api.errors.exceptions import DatabaseError, NotFoundError
from api.constants import PRIORITY_TYPES, CLOSED_STATUS_CODE, INTERVENTION_TYPES_MAP


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
                    ec.id as equipement_class_id,
                    ec.code as equipement_class_code,
                    ec.label as equipement_class_label,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' THEN i.id END) as open_interventions_count,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
                GROUP BY m.id, ec.id, ec.code, ec.label
                ORDER BY urgent_count DESC, open_interventions_count DESC, m.name ASC
            """

            cur.execute(query)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            equipements = [dict(zip(cols, row)) for row in rows]

            # Enrichir avec health et restructurer equipement_class
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

                # Restructurer equipement_class
                ec_id = equipement.pop('equipement_class_id', None)
                ec_code = equipement.pop('equipement_class_code', None)
                ec_label = equipement.pop('equipement_class_label', None)

                if ec_id:
                    equipement['equipement_class'] = {
                        'id': ec_id,
                        'code': ec_code,
                        'label': ec_label
                    }
                else:
                    equipement['equipement_class'] = None

            return equipements

        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_by_id(
        self,
        equipement_id: str,
        interventions_page: int = 1,
        interventions_limit: int = 20
    ) -> Dict[str, Any]:
        """Récupère un équipement par ID avec tous les champs, children_count et interventions paginées"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ferme_id = self._get_closed_status_id(conn)

            query = f"""
                SELECT
                    m.id,
                    m.code,
                    m.name,
                    m.no_machine,
                    m.affectation,
                    m.is_mere,
                    m.fabricant,
                    m.numero_serie,
                    m.date_mise_service,
                    m.notes,
                    m.equipement_mere,
                    ec.id as equipement_class_id,
                    ec.code as equipement_class_code,
                    ec.label as equipement_class_label,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' THEN i.id END) as open_interventions_count,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
                WHERE m.id = %s
                GROUP BY m.id, ec.id, ec.code, ec.label
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

            # Normaliser les champs string (peuvent être stockés comme int en DB)
            for field in ('no_machine', 'affectation', 'fabricant', 'numero_serie', 'notes'):
                if equipement.get(field) is not None:
                    equipement[field] = str(equipement[field])

            # Restructurer equipement_class
            ec_id = equipement.pop('equipement_class_id', None)
            ec_code = equipement.pop('equipement_class_code', None)
            ec_label = equipement.pop('equipement_class_label', None)

            if ec_id:
                equipement['equipement_class'] = {
                    'id': ec_id,
                    'code': ec_code,
                    'label': ec_label
                }
            else:
                equipement['equipement_class'] = None

            # children_count
            cur.execute(
                "SELECT COUNT(*) FROM machine WHERE equipement_mere = %s",
                (equipement_id,)
            )
            equipement['children_count'] = cur.fetchone()[0] or 0

            # Interventions paginées (liées directement à cet équipement)
            offset = (interventions_page - 1) * interventions_limit

            cur.execute(
                "SELECT COUNT(*) FROM intervention WHERE machine_id = %s",
                (equipement_id,)
            )
            interventions_total = cur.fetchone()[0] or 0

            from math import ceil
            total_pages = ceil(
                interventions_total / interventions_limit) if interventions_limit > 0 else 1

            cur.execute(
                """
                SELECT id, code, title, type_inter, status_actual, priority, reported_date
                FROM intervention
                WHERE machine_id = %s
                ORDER BY reported_date DESC
                LIMIT %s OFFSET %s
                """,
                (equipement_id, interventions_limit, offset)
            )
            int_rows = cur.fetchall()
            int_cols = [desc[0] for desc in cur.description]
            interventions_items = [dict(zip(int_cols, r)) for r in int_rows]

            # Enrichir type_inter avec code et label
            for item in interventions_items:
                type_inter_code = item.get('type_inter')
                if type_inter_code and type_inter_code in INTERVENTION_TYPES_MAP:
                    type_info = INTERVENTION_TYPES_MAP[type_inter_code]
                    item['type_inter'] = {
                        'code': type_inter_code,
                        'label': type_info.get('title')
                    }
                elif type_inter_code:
                    # Si le code n'est pas dans le mapping, retourner juste le code
                    item['type_inter'] = {
                        'code': type_inter_code,
                        'label': None
                    }
                else:
                    item['type_inter'] = None

            equipement['interventions'] = {
                'total': interventions_total,
                'page': interventions_page,
                'page_size': interventions_limit,
                'total_pages': total_pages,
                'items': interventions_items
            }

            return equipement
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def get_children(
        self,
        equipement_id: str,
        page: int = 1,
        limit: int = 20,
        search: str | None = None
    ) -> Dict[str, Any]:
        """Récupère les enfants paginés d'un équipement avec health"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            ferme_id = self._get_closed_status_id(conn)

            # Vérifier que l'équipement existe
            cur.execute("SELECT id FROM machine WHERE id = %s",
                        (equipement_id,))
            if not cur.fetchone():
                raise NotFoundError(f"Équipement {equipement_id} non trouvé")

            search_clause = ""
            params_count: list = [equipement_id]
            params_items: list = [equipement_id]

            if search:
                search_clause = " AND (m.code ILIKE %s OR m.name ILIKE %s)"
                like = f"%{search}%"
                params_count += [like, like]
                params_items += [like, like]

            # Total
            cur.execute(
                f"SELECT COUNT(*) FROM machine m WHERE m.equipement_mere = %s{search_clause}",
                params_count
            )
            total = cur.fetchone()[0] or 0

            from math import ceil
            total_pages = ceil(total / limit) if limit > 0 else 1
            offset = (page - 1) * limit

            query = f"""
                SELECT
                    m.id,
                    m.code,
                    m.name,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' THEN i.id END) as open_interventions_count,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                WHERE m.equipement_mere = %s{search_clause}
                GROUP BY m.id
                ORDER BY m.name ASC
                LIMIT %s OFFSET %s
            """
            params_items += [limit, offset]
            cur.execute(query, params_items)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            items = []
            for row in rows:
                child = dict(zip(cols, row))
                open_c = child.pop('open_interventions_count', 0) or 0
                urgent_c = child.pop('urgent_count', 0) or 0
                child['health'] = self._calculate_health(open_c, urgent_c)
                items.append(child)

            return {
                'total': total,
                'page': page,
                'page_size': limit,
                'total_pages': total_pages,
                'items': items
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Erreur base de données: {str(e)}") from e
        finally:
            conn.close()

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouvel équipement"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            equipement_id = str(uuid4())

            cur.execute(
                """
                INSERT INTO machine (id, code, name, equipement_mere, equipement_class_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    equipement_id,
                    data.get('code'),
                    data['name'],
                    data.get('parent_id'),
                    data.get('equipement_class_id')
                )
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la creation de l'equipement: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(equipement_id)

    def update(self, equipement_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un équipement existant"""
        self.get_by_id(equipement_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()

            field_map = {
                'code': 'code',
                'name': 'name',
                'parent_id': 'equipement_mere',
                'equipement_class_id': 'equipement_class_id'
            }

            set_clauses = []
            params = []

            for field, column in field_map.items():
                if field in data:
                    set_clauses.append(f"{column} = %s")
                    params.append(data[field])

            if not set_clauses:
                return self.get_by_id(equipement_id)

            params.append(equipement_id)
            query = f"""
                UPDATE machine
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """

            cur.execute(query, params)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise a jour de l'equipement: {str(e)}") from e
        finally:
            conn.close()

        return self.get_by_id(equipement_id)

    def delete(self, equipement_id: str) -> bool:
        """Supprime un équipement"""
        self.get_by_id(equipement_id)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM machine WHERE id = %s", (equipement_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la suppression de l'equipement: {str(e)}") from e
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
                    ec.id as equipement_class_id,
                    ec.code as equipement_class_code,
                    ec.label as equipement_class_label,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' THEN i.id END) as open_interventions_count,
                    COUNT(CASE WHEN i.status_actual != '{ferme_id}' AND i.priority = 'urgent' THEN i.id END) as urgent_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
                WHERE m.equipement_mere = %s
                GROUP BY m.id, ec.id, ec.code, ec.label
                ORDER BY urgent_count DESC, open_interventions_count DESC, m.name ASC
            """

            cur.execute(query, (equipement_mere_id,))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            equipements = [dict(zip(cols, row)) for row in rows]

            # Enrichir avec health et restructurer equipement_class
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

                # Restructurer equipement_class
                ec_id = equipement.pop('equipement_class_id', None)
                ec_code = equipement.pop('equipement_class_code', None)
                ec_label = equipement.pop('equipement_class_label', None)

                if ec_id:
                    equipement['equipement_class'] = {
                        'id': ec_id,
                        'code': ec_code,
                        'label': ec_label
                    }
                else:
                    equipement['equipement_class'] = None

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

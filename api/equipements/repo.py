from fastapi import HTTPException
"""Requêtes pour le domaine équipements"""
import logging
from typing import Dict, Any, List
from uuid import uuid4

from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, raise_db_error, NotFoundError
from api.constants import PRIORITY_TYPES, CLOSED_STATUS_CODE, INTERVENTION_TYPES_MAP

logger = logging.getLogger(__name__)


class EquipementRepository:
    """Requêtes pour le domaine equipement avec statistiques interventions"""

    def _get_connection(self):
        return get_connection()

    def _closed_status_subquery(self) -> str:
        """Retourne un placeholder pour le code du statut fermé (comparaison directe sur status_actual)"""
        return "%s"

    def _build_filter_clause(
        self,
        search: str | None = None,
        exclude_class: list[str] | None = None,
        select_class: list[str] | None = None,
        select_mere: str | None = None,
    ) -> tuple[str, list]:
        """Construit la clause WHERE et les params associés pour les filtres de liste."""
        conditions = []
        params: list = []
        if search:
            like = f"%{search}%"
            conditions.append(
                "(m.code ILIKE %s OR m.name ILIKE %s OR m.affectation ILIKE %s)")
            params.extend([like, like, like])
        if select_mere:
            conditions.append("m.equipement_mere = %s")
            params.append(select_mere)
        if select_class:
            placeholders = ",".join(["%s"] * len(select_class))
            conditions.append(f"ec.code IN ({placeholders})")
            params.extend(select_class)
        if exclude_class:
            placeholders = ",".join(["%s"] * len(exclude_class))
            conditions.append(
                f"(ec.code IS NULL OR ec.code NOT IN ({placeholders}))")
            params.extend(exclude_class)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        return where_clause, params

    def get_all(
        self,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
        exclude_class: list[str] | None = None,
        select_class: list[str] | None = None,
        select_mere: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Récupère les équipements paginés - liste légère avec health"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            csq = self._closed_status_subquery()
            where_clause, filter_params = self._build_filter_clause(
                search=search, exclude_class=exclude_class, select_class=select_class, select_mere=select_mere)

            query = f"""
                SELECT
                    m.id,
                    m.code,
                    m.name,
                    pm.id   AS parent_id,
                    pm.code AS parent_code,
                    pm.name AS parent_name,
                    ec.id as equipement_class_id,
                    ec.code as equipement_class_code,
                    ec.label as equipement_class_label,
                    es.id as statut_id,
                    es.code as statut_code,
                    es.libelle as statut_label,
                    es.interventions as statut_interventions,
                    es.couleur as statut_couleur,
                    COUNT(CASE WHEN i.status_actual != {csq} THEN i.id END) as open_interventions_count,
                    COUNT(CASE WHEN i.status_actual != {csq} AND i.priority = 'urgent' THEN i.id END) as urgent_count,
                    (SELECT COUNT(*) FROM intervention_request WHERE machine_id = m.id AND statut = 'nouvelle') as new_requests_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
                LEFT JOIN equipement_statuts es ON es.id = m.statut_id
                LEFT JOIN machine pm ON pm.id = m.equipement_mere
                {where_clause}
                GROUP BY m.id, pm.id, pm.code, pm.name, ec.id, ec.code, ec.label, es.id, es.code, es.libelle, es.interventions, es.couleur
                ORDER BY urgent_count DESC, open_interventions_count DESC, m.name ASC
                LIMIT %s OFFSET %s
            """

            cur.execute(query, (CLOSED_STATUS_CODE,
                        CLOSED_STATUS_CODE, *filter_params, limit, skip))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            equipements = [dict(zip(cols, row)) for row in rows]

            # Enrichir avec health et restructurer equipement_class
            for equipement in equipements:
                open_count = equipement.pop('open_interventions_count', 0) or 0
                urgent_count = equipement.pop('urgent_count', 0) or 0
                new_requests_count = equipement.pop('new_requests_count', 0) or 0

                equipement['health'] = self._calculate_health(open_count, urgent_count, new_requests_count)
                equipement['parent_id'] = equipement.pop(
                    'equipement_mere', None)

                ec_id = equipement.pop('equipement_class_id', None)
                ec_code = equipement.pop('equipement_class_code', None)
                ec_label = equipement.pop('equipement_class_label', None)

                equipement['equipement_class'] = (
                    {'id': ec_id, 'code': ec_code,
                        'label': ec_label} if ec_id else None
                )

                statut_id = equipement.pop('statut_id', None)
                statut_code = equipement.pop('statut_code', None)
                statut_label = equipement.pop('statut_label', None)
                statut_interventions = equipement.pop('statut_interventions', None)
                statut_couleur = equipement.pop('statut_couleur', None)
                equipement['statut'] = (
                    {'id': statut_id, 'code': statut_code, 'label': statut_label,
                     'interventions': statut_interventions, 'couleur': statut_couleur}
                    if statut_id else None
                )

            return equipements

        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def count_all(
        self,
        search: str | None = None,
        exclude_class: list[str] | None = None,
        select_class: list[str] | None = None,
        select_mere: str | None = None,
    ) -> int:
        """Compte le nombre total d'équipements avec les mêmes filtres que get_all."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where_clause, filter_params = self._build_filter_clause(
                search=search, exclude_class=exclude_class, select_class=select_class, select_mere=select_mere)
            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM machine m
                LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
                {where_clause}
                """,
                filter_params,
            )
            return cur.fetchone()[0] or 0
        except Exception as e:
            raise_db_error(e, "comptage équipements")
        finally:
            release_connection(conn)

    def get_facets(self, search: str | None = None) -> List[Dict[str, Any]]:
        """Retourne le nombre d'équipements par classe."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where_clause, filter_params = self._build_filter_clause(
                search=search)
            cur.execute(
                f"""
                SELECT ec.code, ec.label, COUNT(m.id) as count
                FROM machine m
                LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
                {where_clause}
                GROUP BY ec.code, ec.label
                ORDER BY count DESC
                """,
                filter_params,
            )
            rows = cur.fetchall()
            return [{"code": r[0], "label": r[1], "count": r[2]} for r in rows]
        except Exception as e:
            raise_db_error(e, "facettes équipements")
        finally:
            release_connection(conn)

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
            csq = self._closed_status_subquery()

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
                    pm.id   AS parent_id,
                    pm.code AS parent_code,
                    pm.name AS parent_name,
                    ec.id as equipement_class_id,
                    ec.code as equipement_class_code,
                    ec.label as equipement_class_label,
                    es.id as statut_id,
                    es.code as statut_code,
                    es.libelle as statut_label,
                    es.interventions as statut_interventions,
                    es.couleur as statut_couleur,
                    COUNT(CASE WHEN i.status_actual != {csq} THEN i.id END) as open_interventions_count,
                    COUNT(CASE WHEN i.status_actual != {csq} AND i.priority = 'urgent' THEN i.id END) as urgent_count,
                    (SELECT COUNT(*) FROM intervention_request WHERE machine_id = m.id AND statut = 'nouvelle') as new_requests_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
                LEFT JOIN equipement_statuts es ON es.id = m.statut_id
                LEFT JOIN machine pm ON pm.id = m.equipement_mere
                WHERE m.id = %s
                GROUP BY m.id, pm.id, pm.code, pm.name, ec.id, ec.code, ec.label, es.id, es.code, es.libelle, es.interventions, es.couleur
            """

            cur.execute(query, (CLOSED_STATUS_CODE,
                        CLOSED_STATUS_CODE, equipement_id))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Équipement {equipement_id} non trouvé")

            cols = [desc[0] for desc in cur.description]
            equipement = dict(zip(cols, row))

            # Health calculation
            open_count = equipement.pop('open_interventions_count', 0) or 0
            urgent_count = equipement.pop('urgent_count', 0) or 0
            new_requests_count = equipement.pop('new_requests_count', 0) or 0
            health = self._calculate_health(open_count, urgent_count, new_requests_count)

            equipement['health'] = health

            parent_id = equipement.pop('parent_id', None)
            parent_code = equipement.pop('parent_code', None)
            parent_name = equipement.pop('parent_name', None)
            equipement['parent'] = (
                {'id': parent_id, 'code': parent_code, 'name': parent_name}
                if parent_id else None
            )

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

            statut_id = equipement.pop('statut_id', None)
            statut_code = equipement.pop('statut_code', None)
            statut_label = equipement.pop('statut_label', None)
            statut_interventions = equipement.pop('statut_interventions', None)
            statut_couleur = equipement.pop('statut_couleur', None)
            equipement['statut'] = (
                {'id': statut_id, 'code': statut_code, 'label': statut_label,
                 'interventions': statut_interventions, 'couleur': statut_couleur}
                if statut_id else None
            )

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

            # Enrichir avec les blocs contextuels (plans, occurrences, demandes)
            # Extraire equipement_class_id depuis l'objet déjà construit
            equipement_class = equipement.get('equipement_class')
            equipement_class_id = equipement_class.get('id') if equipement_class else None
            if equipement_class_id:
                equipement_class_id = str(equipement_class_id)

            plans = self._fetch_preventive_plans(cur, equipement_class_id, equipement_id)
            equipement['preventive_plans'] = plans if plans else None

            occurrences_summary = self._fetch_preventive_occurrences_summary(cur, equipement_id)
            equipement['preventive_occurrences_summary'] = occurrences_summary

            open_requests = self._fetch_open_requests(cur, equipement_id)
            equipement['open_requests'] = open_requests if open_requests else None

            return equipement
        except NotFoundError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def _assign_children(self, cur, parent_id: str, children_ids: list) -> None:
        """Assigne une liste d'équipements comme enfants de parent_id"""
        if not children_ids:
            return
        placeholders = ','.join(['%s'] * len(children_ids))
        cur.execute(
            f"UPDATE machine SET equipement_mere = %s WHERE id IN ({placeholders})",
            (parent_id, *[str(cid) for cid in children_ids])
        )

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouvel équipement"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            equipement_id = str(uuid4())

            cur.execute(
                """
                INSERT INTO machine (
                    id, code, name, no_machine, affectation, is_mere,
                    fabricant, numero_serie, date_mise_service, notes,
                    equipement_mere, equipement_class_id, statut_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    equipement_id,
                    data.get('code'),
                    data['name'],
                    data.get('no_machine'),
                    data.get('affectation'),
                    data.get('is_mere'),
                    data.get('fabricant'),
                    data.get('numero_serie'),
                    data.get('date_mise_service'),
                    data.get('notes'),
                    str(data['parent_id']) if data.get('parent_id') else None,
                    str(data['equipement_class_id']) if data.get('equipement_class_id') else None,
                    data.get('statut_id'),
                )
            )
            if data.get('children_ids'):
                self._assign_children(cur, equipement_id, data['children_ids'])
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la creation de l'equipement: {str(e)}") from e
        finally:
            release_connection(conn)

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
                'no_machine': 'no_machine',
                'affectation': 'affectation',
                'is_mere': 'is_mere',
                'fabricant': 'fabricant',
                'numero_serie': 'numero_serie',
                'date_mise_service': 'date_mise_service',
                'notes': 'notes',
                'parent_id': 'equipement_mere',
                'equipement_class_id': 'equipement_class_id',
                'statut_id': 'statut_id',
            }

            set_clauses = []
            params = []

            for field, column in field_map.items():
                if field in data:
                    set_clauses.append(f"{column} = %s")
                    params.append(data[field])

            if set_clauses:
                params.append(equipement_id)
                cur.execute(
                    f"UPDATE machine SET {', '.join(set_clauses)} WHERE id = %s",
                    params
                )

            if data.get('children_ids') is not None:
                self._assign_children(cur, equipement_id, data['children_ids'])

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(
                f"Erreur lors de la mise a jour de l'equipement: {str(e)}") from e
        finally:
            release_connection(conn)

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
            release_connection(conn)

    def get_by_equipement_mere(self, equipement_mere_id: str) -> List[Dict[str, Any]]:
        """Récupère les sous-équipements d'un équipement parent avec health"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            csq = self._closed_status_subquery()

            query = f"""
                SELECT
                    m.id,
                    m.code,
                    m.name,
                    m.equipement_mere,
                    ec.id as equipement_class_id,
                    ec.code as equipement_class_code,
                    ec.label as equipement_class_label,
                    COUNT(CASE WHEN i.status_actual != {csq} THEN i.id END) as open_interventions_count,
                    COUNT(CASE WHEN i.status_actual != {csq} AND i.priority = 'urgent' THEN i.id END) as urgent_count,
                    (SELECT COUNT(*) FROM intervention_request WHERE machine_id = m.id AND statut = 'nouvelle') as new_requests_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
                WHERE m.equipement_mere = %s
                GROUP BY m.id, ec.id, ec.code, ec.label
                ORDER BY urgent_count DESC, open_interventions_count DESC, m.name ASC
            """

            cur.execute(query, (CLOSED_STATUS_CODE,
                        CLOSED_STATUS_CODE, equipement_mere_id))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            equipements = [dict(zip(cols, row)) for row in rows]

            # Enrichir avec health et restructurer equipement_class
            for equipement in equipements:
                open_count = equipement.pop('open_interventions_count', 0) or 0
                urgent_count = equipement.pop('urgent_count', 0) or 0
                new_requests_count = equipement.pop('new_requests_count', 0) or 0

                equipement['health'] = self._calculate_health(open_count, urgent_count, new_requests_count)
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
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def get_stats_by_id(self, equipement_id: str, start_date=None, end_date=None) -> Dict[str, Any]:
        """Récupère les statistiques détaillées d'un équipement, avec filtre période optionnel"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            csq = self._closed_status_subquery()

            # Vérifier que l'équipement existe
            cur.execute("SELECT id FROM machine WHERE id = %s",
                        (equipement_id,))
            if not cur.fetchone():
                raise NotFoundError(f"Équipement {equipement_id} non trouvé")

            # Récupérer tous les statuts
            cur.execute("SELECT id, code FROM intervention_status_ref")
            all_status = [(row[0], row[1]) for row in cur.fetchall()]

            # Générer colonnes par statut (comparaison sur le code, pas l'UUID)
            status_columns = []
            for _, status_code in all_status:
                safe_code = status_code.replace("'", "''")
                status_columns.append(
                    f"COUNT(CASE WHEN i.status_actual = '{safe_code}' THEN i.id END) as status_{safe_code}"
                )

            # Générer colonnes par priorité (pid est une constante applicative)
            priority_columns = []
            for p in PRIORITY_TYPES:
                pid = p.get('id')
                priority_columns.append(
                    f"COUNT(CASE WHEN i.priority = '{pid}' THEN i.id END) as priority_{pid}"
                )

            where_clauses = ["i.machine_id = %s"]
            params: list = [CLOSED_STATUS_CODE,
                            CLOSED_STATUS_CODE, equipement_id]

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
                    COUNT(CASE WHEN i.status_actual != {csq} THEN i.id END) as open_count,
                    COUNT(CASE WHEN i.status_actual = {csq} THEN i.id END) as closed_count,
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
            for _, status_code in all_status:
                by_status[status_code] = data.pop(
                    f'status_{status_code}', 0) or 0

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
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def get_health_by_id(self, equipement_id: str) -> Dict[str, Any]:
        """Récupère uniquement le health d'un équipement (ultra-léger)"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            csq = self._closed_status_subquery()

            query = f"""
                SELECT
                    COUNT(CASE WHEN i.status_actual != {csq} THEN i.id END) as open_count,
                    COUNT(CASE WHEN i.status_actual != {csq} AND i.priority = 'urgent' THEN i.id END) as urgent_count,
                    (SELECT COUNT(*) FROM intervention_request WHERE machine_id = m.id AND statut = 'nouvelle') as new_requests_count
                FROM machine m
                LEFT JOIN intervention i ON i.machine_id = m.id
                WHERE m.id = %s
                GROUP BY m.id
            """

            cur.execute(query, (CLOSED_STATUS_CODE,
                        CLOSED_STATUS_CODE, equipement_id))
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
                new_requests_count = row[2] or 0

            return self._calculate_health(open_count, urgent_count, new_requests_count)
        except NotFoundError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            raise_db_error(e, "opération")
        finally:
            release_connection(conn)

    def _fetch_preventive_plans(self, cur, equipement_class_id: str | None, machine_id: str) -> List[Dict[str, Any]]:
        """Récupère les plans de maintenance préventive applicables"""
        if not equipement_class_id:
            return []

        try:
            query = """
                SELECT
                    pp.id, pp.code, pp.label,
                    pp.trigger_type, pp.periodicity_days, pp.hours_threshold,
                    pp.active,
                    MIN(po.scheduled_date) AS next_occurrence
                FROM preventive_plan pp
                LEFT JOIN preventive_occurrence po ON po.plan_id = pp.id
                    AND po.machine_id = %s
                    AND po.status IN ('pending', 'generated')
                WHERE pp.equipement_class_id = %s AND pp.active = true
                GROUP BY pp.id, pp.code, pp.label, pp.trigger_type, pp.periodicity_days, pp.hours_threshold, pp.active
                ORDER BY pp.code ASC
            """
            cur.execute(query, (machine_id, equipement_class_id))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            logger.error(f"Erreur récupération plans préventifs pour équipement: {e}")
            return []

    def _fetch_preventive_occurrences_summary(self, cur, equipement_id: str) -> Dict[str, Any]:
        """Récupère le résumé des occurrences préventives"""
        try:
            query = """
                SELECT
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) AS pending_count,
                    COUNT(CASE WHEN status = 'generated' THEN 1 END) AS generated_count,
                    COUNT(CASE WHEN status = 'skipped' THEN 1 END) AS skipped_count,
                    MIN(CASE WHEN status = 'pending' THEN scheduled_date END) AS next_scheduled,
                    (
                        SELECT skip_reason FROM preventive_occurrence
                        WHERE machine_id = %s AND status = 'skipped'
                        ORDER BY created_at DESC LIMIT 1
                    ) AS last_skipped_reason
                FROM preventive_occurrence
                WHERE machine_id = %s
            """
            cur.execute(query, (equipement_id, equipement_id))
            row = cur.fetchone()
            if not row:
                return {
                    'pending_count': 0,
                    'generated_count': 0,
                    'skipped_count': 0,
                    'next_scheduled': None,
                    'last_skipped_reason': None
                }
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except Exception as e:
            logger.error(f"Erreur récupération résumé occurrences: {e}")
            return {
                'pending_count': 0,
                'generated_count': 0,
                'skipped_count': 0,
                'next_scheduled': None,
                'last_skipped_reason': None
            }

    def _fetch_open_requests(self, cur, equipement_id: str) -> List[Dict[str, Any]]:
        """Récupère les demandes d'intervention ouvertes"""
        try:
            query = """
                SELECT
                    ir.id, ir.code, ir.description, ir.statut,
                    rs.label AS statut_label, rs.color AS statut_color,
                    ir.is_system, ir.created_at
                FROM intervention_request ir
                LEFT JOIN request_status_ref rs ON rs.code = ir.statut
                WHERE ir.machine_id = %s
                  AND ir.statut NOT IN ('rejetee', 'cloturee')
                ORDER BY ir.created_at DESC
            """
            cur.execute(query, (equipement_id,))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            logger.error(f"Erreur récupération demandes ouvertes: {e}")
            return []

    def _calculate_health(self, open_count: int, urgent_count: int, new_requests_count: int = 0) -> Dict[str, Any]:
        """Calcule le health d'un équipement selon interventions et demandes"""
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

        if new_requests_count > 0:
            rules_triggered.append('NEW_REQUESTS > 0')
            if level == 'ok':
                level = 'maintenance'
                reason = f"{new_requests_count} demande{'s' if new_requests_count > 1 else ''} en attente de traitement"

        return {
            'level': level,
            'reason': reason,
            'open_interventions_count': open_count,
            'urgent_count': urgent_count,
            'new_requests_count': new_requests_count,
            'rules_triggered': rules_triggered
        }

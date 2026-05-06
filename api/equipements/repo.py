"""Requêtes pour le domaine équipements"""
from fastapi import HTTPException
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

            equipement_ids = [str(e.get('id'))
                              for e in equipements if e.get('id')]
            health_inputs_map = self._fetch_health_inputs(cur, equipement_ids)

            # Enrichir avec health et restructurer equipement_class
            for equipement in equipements:
                open_count = equipement.pop('open_interventions_count', 0) or 0
                urgent_count = equipement.pop('urgent_count', 0) or 0
                new_requests_count = equipement.pop(
                    'new_requests_count', 0) or 0
                metrics = health_inputs_map.get(str(equipement.get('id')), {})
                metrics.setdefault('open_interventions_count', int(open_count))
                metrics.setdefault('urgent_count', int(urgent_count))
                metrics.setdefault('new_requests_count',
                                   int(new_requests_count))

                equipement['health'] = self._calculate_health(metrics)
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
                statut_interventions = equipement.pop(
                    'statut_interventions', None)
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
            health_inputs_map = self._fetch_health_inputs(cur, [equipement_id])
            metrics = health_inputs_map.get(str(equipement_id), {})
            metrics.setdefault('open_interventions_count', int(open_count))
            metrics.setdefault('urgent_count', int(urgent_count))
            metrics.setdefault('new_requests_count', int(new_requests_count))
            health = self._calculate_health(metrics)

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
            equipement_class_id = equipement_class.get(
                'id') if equipement_class else None
            if equipement_class_id:
                equipement_class_id = str(equipement_class_id)

            plans = self._fetch_preventive_plans(
                cur, equipement_class_id, equipement_id)
            equipement['preventive_plans'] = plans or None

            occurrences_summary = self._fetch_preventive_occurrences_summary(
                cur, equipement_id)
            equipement['preventive_occurrences_summary'] = occurrences_summary

            open_requests = self._fetch_open_requests(cur, equipement_id)
            equipement['open_requests'] = open_requests or None

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
                    str(data['equipement_class_id']) if data.get(
                        'equipement_class_id') else None,
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

            equipement_ids = [str(e.get('id'))
                              for e in equipements if e.get('id')]
            health_inputs_map = self._fetch_health_inputs(cur, equipement_ids)

            # Enrichir avec health et restructurer equipement_class
            for equipement in equipements:
                open_count = equipement.pop('open_interventions_count', 0) or 0
                urgent_count = equipement.pop('urgent_count', 0) or 0
                new_requests_count = equipement.pop(
                    'new_requests_count', 0) or 0
                metrics = health_inputs_map.get(str(equipement.get('id')), {})
                metrics.setdefault('open_interventions_count', int(open_count))
                metrics.setdefault('urgent_count', int(urgent_count))
                metrics.setdefault('new_requests_count',
                                   int(new_requests_count))

                equipement['health'] = self._calculate_health(metrics)
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
            cur.execute("SELECT id FROM machine WHERE id = %s",
                        (equipement_id,))
            if not cur.fetchone():
                raise NotFoundError(f"Équipement {equipement_id} non trouvé")

            health_inputs_map = self._fetch_health_inputs(cur, [equipement_id])
            metrics = health_inputs_map.get(str(equipement_id), {
                'open_interventions_count': 0,
                'urgent_count': 0,
                'open_requests_count': 0,
                'new_requests_count': 0,
                'request_status_counts': {},
                'open_tasks_count': 0,
                'overdue_tasks_count': 0,
                'unassigned_tasks_count': 0,
                'open_purchase_requests_count': 0,
                'purchase_request_status_counts': {},
                'has_affectation': False,
            })

            return self._calculate_health(metrics)
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
            logger.error(
                "Erreur récupération plans préventifs pour équipement: %s", e)
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
            logger.error("Erreur récupération résumé occurrences: %s", e)
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
            logger.error("Erreur récupération demandes ouvertes: %s", e)
            return []

    def _normalize_status_counts(self, raw_counts: Any) -> Dict[str, int]:
        """Normalise un objet de compteurs de statuts en dict[str, int]."""
        if not raw_counts:
            return {}
        if not isinstance(raw_counts, dict):
            return {}
        normalized: Dict[str, int] = {}
        for key, value in raw_counts.items():
            normalized[str(key)] = int(value or 0)
        return normalized

    def _fetch_health_inputs(self, cur, equipement_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Récupère toutes les métriques nécessaires au calcul de santé pour une liste d'équipements."""
        if not equipement_ids:
            return {}

        query = """
            WITH target AS (
                SELECT UNNEST(%s::uuid[]) AS machine_id
            ),
            interventions_agg AS (
                SELECT
                    i.machine_id,
                    COUNT(*) FILTER (WHERE i.status_actual != %s) AS open_interventions_count,
                    COUNT(*) FILTER (WHERE i.status_actual != %s AND i.priority = 'urgent') AS urgent_count
                FROM intervention i
                JOIN target t ON t.machine_id = i.machine_id
                GROUP BY i.machine_id
            ),
            requests_agg AS (
                SELECT
                    ir.machine_id,
                    COUNT(*) FILTER (WHERE ir.statut NOT IN ('rejetee', 'cloturee')) AS open_requests_count,
                    COUNT(*) FILTER (WHERE ir.statut = 'nouvelle') AS new_requests_count
                FROM intervention_request ir
                JOIN target t ON t.machine_id = ir.machine_id
                GROUP BY ir.machine_id
            ),
            request_status_agg AS (
                SELECT
                    x.machine_id,
                    COALESCE(jsonb_object_agg(x.statut, x.cnt), '{}'::jsonb) AS request_status_counts
                FROM (
                    SELECT
                        ir.machine_id,
                        ir.statut,
                        COUNT(*)::int AS cnt
                    FROM intervention_request ir
                    JOIN target t ON t.machine_id = ir.machine_id
                    WHERE ir.statut NOT IN ('rejetee', 'cloturee')
                    GROUP BY ir.machine_id, ir.statut
                ) x
                GROUP BY x.machine_id
            ),
            tasks_agg AS (
                SELECT
                    i.machine_id,
                    COUNT(*) FILTER (WHERE it.status NOT IN ('done', 'skipped')) AS open_tasks_count,
                    COUNT(*) FILTER (
                        WHERE it.status NOT IN ('done', 'skipped')
                          AND it.due_date IS NOT NULL
                          AND it.due_date < CURRENT_DATE
                    ) AS overdue_tasks_count,
                    COUNT(*) FILTER (
                        WHERE it.status NOT IN ('done', 'skipped')
                          AND it.assigned_to IS NULL
                    ) AS unassigned_tasks_count
                FROM intervention_task it
                JOIN intervention i ON i.id = it.intervention_id
                JOIN target t ON t.machine_id = i.machine_id
                GROUP BY i.machine_id
            ),
            purchase_request_machine AS (
                SELECT DISTINCT
                    pr.id AS purchase_request_id,
                    i.machine_id,
                    pr.status
                FROM purchase_request pr
                JOIN intervention i ON i.id = pr.intervention_id
                JOIN target t ON t.machine_id = i.machine_id
                UNION
                SELECT DISTINCT
                    pr.id AS purchase_request_id,
                    i.machine_id,
                    pr.status
                FROM purchase_request pr
                JOIN intervention_action_purchase_request iapr ON iapr.purchase_request_id = pr.id
                JOIN intervention_action ia ON ia.id = iapr.intervention_action_id
                JOIN intervention i ON i.id = ia.intervention_id
                JOIN target t ON t.machine_id = i.machine_id
            ),
            purchase_agg AS (
                SELECT
                    prm.machine_id,
                    COUNT(*) FILTER (
                        WHERE LOWER(COALESCE(prm.status, '')) NOT IN ('closed', 'cloturee', 'cancelled', 'annulee')
                    ) AS open_purchase_requests_count
                FROM purchase_request_machine prm
                GROUP BY prm.machine_id
            ),
            purchase_status_agg AS (
                SELECT
                    y.machine_id,
                    COALESCE(jsonb_object_agg(y.status, y.cnt), '{}'::jsonb) AS purchase_request_status_counts
                FROM (
                    SELECT
                        prm.machine_id,
                        UPPER(COALESCE(prm.status, 'UNKNOWN')) AS status,
                        COUNT(*)::int AS cnt
                    FROM purchase_request_machine prm
                    WHERE LOWER(COALESCE(prm.status, '')) NOT IN ('closed', 'cloturee', 'cancelled', 'annulee')
                    GROUP BY prm.machine_id, UPPER(COALESCE(prm.status, 'UNKNOWN'))
                ) y
                GROUP BY y.machine_id
            )
            SELECT
                t.machine_id,
                COALESCE(i.open_interventions_count, 0) AS open_interventions_count,
                COALESCE(i.urgent_count, 0) AS urgent_count,
                COALESCE(r.open_requests_count, 0) AS open_requests_count,
                COALESCE(r.new_requests_count, 0) AS new_requests_count,
                COALESCE(rs.request_status_counts, '{}'::jsonb) AS request_status_counts,
                COALESCE(ts.open_tasks_count, 0) AS open_tasks_count,
                COALESCE(ts.overdue_tasks_count, 0) AS overdue_tasks_count,
                COALESCE(ts.unassigned_tasks_count, 0) AS unassigned_tasks_count,
                COALESCE(p.open_purchase_requests_count, 0) AS open_purchase_requests_count,
                COALESCE(ps.purchase_request_status_counts, '{}'::jsonb) AS purchase_request_status_counts,
                CASE
                    WHEN NULLIF(BTRIM(COALESCE(m.affectation::text, '')), '') IS NULL THEN FALSE
                    ELSE TRUE
                END AS has_affectation
            FROM target t
            JOIN machine m ON m.id = t.machine_id
            LEFT JOIN interventions_agg i ON i.machine_id = t.machine_id
            LEFT JOIN requests_agg r ON r.machine_id = t.machine_id
            LEFT JOIN request_status_agg rs ON rs.machine_id = t.machine_id
            LEFT JOIN tasks_agg ts ON ts.machine_id = t.machine_id
            LEFT JOIN purchase_agg p ON p.machine_id = t.machine_id
            LEFT JOIN purchase_status_agg ps ON ps.machine_id = t.machine_id
        """

        cur.execute(
            query, (equipement_ids, CLOSED_STATUS_CODE, CLOSED_STATUS_CODE))
        rows = cur.fetchall()

        health_inputs: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            machine_id = str(row[0])
            health_inputs[machine_id] = {
                'open_interventions_count': int(row[1] or 0),
                'urgent_count': int(row[2] or 0),
                'open_requests_count': int(row[3] or 0),
                'new_requests_count': int(row[4] or 0),
                'request_status_counts': self._normalize_status_counts(row[5]),
                'open_tasks_count': int(row[6] or 0),
                'overdue_tasks_count': int(row[7] or 0),
                'unassigned_tasks_count': int(row[8] or 0),
                'open_purchase_requests_count': int(row[9] or 0),
                'purchase_request_status_counts': self._normalize_status_counts(row[10]),
                'has_affectation': bool(row[11]),
            }

        return health_inputs

    def get_health_map(self, cur, equipement_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Retourne le health calculé pour une liste d'équipements (clé = machine_id)."""
        inputs_map = self._fetch_health_inputs(cur, equipement_ids)
        return {
            machine_id: self._calculate_health(metrics)
            for machine_id, metrics in inputs_map.items()
        }

    def _calculate_health(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule le health d'un équipement selon interventions, demandes, DA et tâches."""
        open_count = int(metrics.get('open_interventions_count', 0) or 0)
        urgent_count = int(metrics.get('urgent_count', 0) or 0)
        open_requests_count = int(metrics.get('open_requests_count', 0) or 0)
        new_requests_count = int(metrics.get('new_requests_count', 0) or 0)
        open_tasks_count = int(metrics.get('open_tasks_count', 0) or 0)
        overdue_tasks_count = int(metrics.get('overdue_tasks_count', 0) or 0)
        unassigned_tasks_count = int(
            metrics.get('unassigned_tasks_count', 0) or 0)
        open_purchase_requests_count = int(
            metrics.get('open_purchase_requests_count', 0) or 0)
        has_affectation = bool(metrics.get('has_affectation', False))
        request_status_counts = self._normalize_status_counts(
            metrics.get('request_status_counts'))
        purchase_request_status_counts = self._normalize_status_counts(
            metrics.get('purchase_request_status_counts'))

        rules_triggered = []
        level = 'ok'
        reason = 'Aucune intervention ouverte'

        if urgent_count >= 1:
            level = 'critical'
            reason = f"{urgent_count} intervention{'s' if urgent_count > 1 else ''} urgente{'s' if urgent_count > 1 else ''} ouverte{'s' if urgent_count > 1 else ''}"
            rules_triggered.append('URGENT_OPEN >= 1')
        elif overdue_tasks_count >= 3:
            level = 'critical'
            reason = f"{overdue_tasks_count} tâches en retard"
            rules_triggered.append('OVERDUE_TASKS >= 3')
        elif overdue_tasks_count > 0:
            level = 'warning'
            reason = f"{overdue_tasks_count} tâche{'s' if overdue_tasks_count > 1 else ''} en retard"
            rules_triggered.append('OVERDUE_TASKS > 0')
        elif open_count > 5:
            level = 'warning'
            reason = f"{open_count} interventions ouvertes"
            rules_triggered.append('OPEN_TOTAL > 5')
        elif open_count > 0:
            level = 'maintenance'
            reason = f"{open_count} intervention{'s' if open_count > 1 else ''} ouverte{'s' if open_count > 1 else ''}"
            rules_triggered.append('OPEN_TOTAL > 0')

        if open_tasks_count > 0:
            rules_triggered.append('OPEN_TASKS > 0')
            if level == 'ok':
                level = 'maintenance'
                reason = f"{open_tasks_count} tâche{'s' if open_tasks_count > 1 else ''} non clôturée{'s' if open_tasks_count > 1 else ''}"

        if unassigned_tasks_count > 0:
            rules_triggered.append('UNASSIGNED_TASKS > 0')
            if level == 'ok':
                level = 'maintenance'
                reason = f"{unassigned_tasks_count} tâche{'s' if unassigned_tasks_count > 1 else ''} non affectée{'s' if unassigned_tasks_count > 1 else ''}"

        if new_requests_count > 0:
            rules_triggered.append('NEW_REQUESTS > 0')
            if level == 'ok':
                level = 'maintenance'
                reason = f"{new_requests_count} demande{'s' if new_requests_count > 1 else ''} en attente de traitement"

        if open_requests_count > 0:
            rules_triggered.append('OPEN_REQUESTS > 0')
            if level == 'ok':
                level = 'maintenance'
                reason = f"{open_requests_count} demande{'s' if open_requests_count > 1 else ''} d'intervention ouverte{'s' if open_requests_count > 1 else ''}"

        if open_purchase_requests_count > 0:
            rules_triggered.append('OPEN_PURCHASE_REQUESTS > 0')
            if level == 'ok':
                level = 'maintenance'
                reason = f"{open_purchase_requests_count} demande{'s' if open_purchase_requests_count > 1 else ''} d'achat ouverte{'s' if open_purchase_requests_count > 1 else ''}"

        has_open_work = (
            open_count > 0
            or open_requests_count > 0
            or open_tasks_count > 0
            or open_purchase_requests_count > 0
        )
        if has_open_work and not has_affectation:
            rules_triggered.append('OPEN_WORK_WITHOUT_AFFECTATION')
            if level in ('ok', 'maintenance'):
                level = 'warning'
                reason = "Travaux en cours sans affectation d'équipement"

        return {
            'level': level,
            'reason': reason,
            'open_interventions_count': open_count,
            'urgent_count': urgent_count,
            'open_requests_count': open_requests_count,
            'new_requests_count': new_requests_count,
            'request_status_counts': request_status_counts,
            'open_tasks_count': open_tasks_count,
            'overdue_tasks_count': overdue_tasks_count,
            'unassigned_tasks_count': unassigned_tasks_count,
            'open_purchase_requests_count': open_purchase_requests_count,
            'purchase_request_status_counts': purchase_request_status_counts,
            'has_affectation': has_affectation,
            'rules_triggered': rules_triggered
        }

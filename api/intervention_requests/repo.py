import json
import logging
from typing import Any, Dict, List, Optional

from api.db import get_connection, release_connection
from api.errors.exceptions import ConflictError, DatabaseError, NotFoundError, ValidationError, raise_db_error
from api.constants import CLOSED_STATUS_CODE, IN_PROGRESS_STATUS_CODE
from api.intervention_requests.validators import InterventionRequestValidator

# Sous-requête réutilisable pour l'ID du statut fermé
_CLOSED_SQ = "(SELECT id FROM intervention_status_ref WHERE code = %s LIMIT 1)"

# Colonnes équipement + health calculés en SQL (aucune query N+1)
_EQUIPEMENT_COLS = f"""
    m.id        AS eq_id,
    m.code      AS eq_code,
    m.name      AS eq_name,
    pm.id       AS eq_parent_id,
    pm.code     AS eq_parent_code,
    pm.name     AS eq_parent_name,
    ec.id       AS ec_id,
    ec.code     AS ec_code,
    ec.label    AS ec_label,
    COUNT(CASE WHEN i_h.status_actual != {_CLOSED_SQ} THEN i_h.id END) AS eq_open_count,
    COUNT(CASE WHEN i_h.status_actual != {_CLOSED_SQ} AND i_h.priority = 'urgent' THEN i_h.id END) AS eq_urgent_count
"""

# Colonnes service
_SERVICE_COLS = """
    s.id        AS service_id,
    s.code      AS service_code,
    s.label     AS service_label,
    s.is_active AS service_is_active
"""

# Colonnes intervention liée (premier niveau, sans tâches — celles-ci sont portées par di_tasks)
_INTERVENTION_COLS = """
    iv.id              AS iv_id,
    iv.code            AS iv_code,
    iv.title           AS iv_title,
    iv.type_inter      AS iv_type_inter,
    iv.priority        AS iv_priority,
    iv.status_actual   AS iv_status_actual,
    ivs.label          AS iv_status_label,
    ivs.color          AS iv_status_color,
    iv.tech_initials   AS iv_tech_initials,
    iv.tech_id         AS iv_tech_id,
    iv.reported_by     AS iv_reported_by,
    iv.reported_date   AS iv_reported_date,
    iv.plan_id         AS iv_plan_id,
    iv.printed_fiche   AS iv_printed_fiche,
    COALESCE(iv_stats.action_count, 0)   AS iv_action_count,
    COALESCE(iv_stats.total_time, 0)     AS iv_total_time,
    iv_stats.avg_complexity              AS iv_avg_complexity,
    COALESCE(iv_stats.purchase_count, 0) AS iv_purchase_count
"""

# Agrégat JSON des tâches liées à la DI — via intervention OU via occurrence préventive
_DI_TASKS_COLS = """
    di_tasks.tasks_json::text AS di_tasks
"""

_EQUIPEMENT_JOINS = """
    LEFT JOIN machine m ON ir.machine_id = m.id
    LEFT JOIN machine pm ON pm.id = m.equipement_mere
    LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
    LEFT JOIN intervention i_h ON i_h.machine_id = m.id
    LEFT JOIN service s ON ir.service_id = s.id
    LEFT JOIN intervention iv ON iv.id = ir.intervention_id
    LEFT JOIN intervention_status_ref ivs ON ivs.code = iv.status_actual
    LEFT JOIN LATERAL (
        SELECT
            COUNT(*)                                                          AS action_count,
            COALESCE(SUM(a.time_spent), 0)                                   AS total_time,
            AVG(NULLIF(a.complexity_score, 0))                               AS avg_complexity,
            COUNT(DISTINCT iapr.purchase_request_id)
                FILTER (WHERE iapr.purchase_request_id IS NOT NULL)          AS purchase_count
        FROM intervention_action a
        LEFT JOIN intervention_action_purchase_request iapr
               ON iapr.intervention_action_id = a.id
        WHERE a.intervention_id = iv.id
    ) iv_stats ON TRUE
    LEFT JOIN LATERAL (
        SELECT COALESCE(
            json_agg(
                json_build_object(
                    'id',            it.id,
                    'intervention_id', it.intervention_id,
                    'label',         it.label,
                    'origin',        it.origin,
                    'status',        it.status,
                    'optional',      it.optional,
                    'due_date',      it.due_date,
                    'sort_order',    it.sort_order,
                    'skip_reason',   it.skip_reason,
                    'gamme_step_id', it.gamme_step_id,
                    'occurrence_id', it.occurrence_id,
                    'closed_by',     it.closed_by,
                    'created_by',    it.created_by,
                    'created_at',    it.created_at,
                    'updated_at',    it.updated_at,
                    'action_count',  COALESCE(tagg.action_count, 0),
                    'time_spent',    COALESCE(tagg.time_spent, 0.0),
                    'assigned_to',   CASE WHEN u.id IS NOT NULL THEN json_build_object(
                        'id',         u.id,
                        'first_name', u.first_name,
                        'last_name',  u.last_name,
                        'email',      u.email,
                        'initial',    u.initial
                    ) END
                )
                ORDER BY it.sort_order, it.created_at
            ),
            '[]'::json
        ) AS tasks_json
        FROM intervention_task it
        LEFT JOIN tunnel_user u ON u.id = it.assigned_to
        LEFT JOIN LATERAL (
            SELECT
                COUNT(DISTINCT iat.action_id) AS action_count,
                COALESCE(SUM(ia.time_spent), 0) AS time_spent
            FROM intervention_action_task iat
            INNER JOIN intervention_action ia ON ia.id = iat.action_id
            WHERE iat.task_id = it.id
        ) tagg ON TRUE
        WHERE
            it.intervention_id = iv.id
            OR it.occurrence_id IN (
                SELECT po.id FROM preventive_occurrence po WHERE po.di_id = ir.id
            )
    ) di_tasks ON TRUE
"""

logger = logging.getLogger(__name__)


def _audit_request(
    cur,
    request_id: str,
    decision_type: str,
    old_value: Optional[Dict],
    new_value: Optional[Dict],
    reason_code: str,
    reason_text: Optional[str] = None,
    changed_by: Optional[str] = None,
    is_system: bool = False,
) -> None:
    """Insère un log d'audit pour une DI via fn_audit_log_decision().
    Les erreurs sont loggées sans jamais interrompre la mutation métier.
    """
    try:
        cur.execute(
            """
            SELECT public.fn_audit_log_decision(
                %s, %s::uuid, %s, %s::jsonb, %s::jsonb, %s, %s, %s::uuid, %s
            )
            """,
            (
                "request",
                request_id,
                decision_type,
                json.dumps(old_value) if old_value is not None else None,
                json.dumps(new_value) if new_value is not None else None,
                reason_code,
                reason_text,
                changed_by,
                is_system,
            ),
        )
    except Exception as exc:
        logger.error("_audit_request(%s, %s) : %s", request_id, decision_type, exc)


class InterventionRequestRepository:

    def _get_connection(self):
        return get_connection()

    @staticmethod
    def _build_equipement(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Construit l'objet equipement (EquipementListItem) depuis les colonnes préfixées eq_/ec_."""
        if not row.get("eq_id"):
            return None
        open_count = row.pop("eq_open_count", 0) or 0
        urgent_count = row.pop("eq_urgent_count", 0) or 0
        if urgent_count > 0:
            health = {"level": "critical",
                      "reason": f"{urgent_count} intervention(s) urgente(s)", "rules_triggered": None}
        elif open_count > 5:
            health = {"level": "warning",
                      "reason": f"{open_count} interventions ouvertes",        "rules_triggered": None}
        elif open_count > 0:
            health = {"level": "maintenance",
                      "reason": f"{open_count} intervention(s) ouverte(s)",    "rules_triggered": None}
        else:
            health = {"level": "ok",           "reason": "Aucune intervention ouverte",
                      "rules_triggered": None}

        ec_id = row.pop("ec_id",    None)
        ec_code = row.pop("ec_code",  None)
        ec_label = row.pop("ec_label", None)

        p_id = row.pop("eq_parent_id",   None)
        p_code = row.pop("eq_parent_code", None)
        p_name = row.pop("eq_parent_name", None)

        return {
            "id":        row.pop("eq_id"),
            "code":      row.pop("eq_code",      None),
            "name":      row.pop("eq_name"),
            "health":    health,
            "parent":    {"id": p_id, "code": p_code, "name": p_name} if p_id else None,
            "equipement_class": {"id": ec_id, "code": ec_code, "label": ec_label} if ec_id else None,
        }

    @staticmethod
    def _build_intervention(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Construit l'objet intervention (InterventionRef) depuis les colonnes préfixées iv_."""
        if not row.get("iv_id"):
            for key in list(row.keys()):
                if key.startswith("iv_"):
                    row.pop(key, None)
            return None
        stats = {
            "action_count":   row.pop("iv_action_count", 0) or 0,
            "total_time":     float(row.pop("iv_total_time", 0) or 0),
            "avg_complexity": row.pop("iv_avg_complexity", None),
            "purchase_count": row.pop("iv_purchase_count", 0) or 0,
        }
        return {
            "id":            row.pop("iv_id"),
            "code":          row.pop("iv_code",          None),
            "title":         row.pop("iv_title",         None),
            "type_inter":    row.pop("iv_type_inter",    None),
            "priority":      row.pop("iv_priority",      None),
            "status_actual": row.pop("iv_status_actual", None),
            "status_label":  row.pop("iv_status_label",  None),
            "status_color":  row.pop("iv_status_color",  None),
            "tech_initials": row.pop("iv_tech_initials", None),
            "tech_id":       row.pop("iv_tech_id",       None),
            "reported_by":   row.pop("iv_reported_by",   None),
            "reported_date": row.pop("iv_reported_date", None),
            "next_due_date": None,
            "overdue":       False,
            "plan_id":       row.pop("iv_plan_id",       None),
            "printed_fiche": row.pop("iv_printed_fiche", None),
            "created_at":    None,
            "updated_at":    None,
            "stats":         stats,
        }

    @staticmethod
    def _build_tasks(row: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Désérialise la colonne di_tasks (json agrégé) en liste de tâches."""
        raw = row.pop("di_tasks", None)
        if isinstance(raw, str):
            return json.loads(raw)
        if isinstance(raw, list):
            return raw
        return []

    @staticmethod
    def _build_service(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Construit l'objet service (ServiceOut) depuis les colonnes préfixées service_."""
        if not row.get("service_id"):
            return None
        return {
            "id":        row.pop("service_id"),
            "code":      row.pop("service_code"),
            "label":     row.pop("service_label"),
            "is_active": row.pop("service_is_active"),
        }

    # ──────────────────────────────────────────────────────────────
    # Référentiel statuts
    # ──────────────────────────────────────────────────────────────

    def get_statuses(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT code, label, color, sort_order FROM request_status_ref ORDER BY sort_order"
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            raise DatabaseError(
                "Erreur récupération statuts: %s" % str(e)) from e
        finally:
            release_connection(conn)

    # ──────────────────────────────────────────────────────────────
    # Liste
    # ──────────────────────────────────────────────────────────────

    def get_list(
        self,
        limit: int = 50,
        offset: int = 0,
        statut: Optional[str] = None,
        exclude_statuses: Optional[List[str]] = None,
        machine_id: Optional[str] = None,
        search: Optional[str] = None,
        is_system: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        limit = min(limit, 500)
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where = []
            params: List[Any] = []

            if statut:
                where.append("ir.statut = %s")
                params.append(statut)
            if exclude_statuses:
                placeholders = ",".join(["%s"] * len(exclude_statuses))
                where.append(f"ir.statut NOT IN ({placeholders})")
                params.extend(exclude_statuses)
            if machine_id:
                where.append("ir.machine_id = %s")
                params.append(machine_id)
            if search:
                where.append(
                    "(ir.code ILIKE %s OR ir.demandeur_nom ILIKE %s OR ir.description ILIKE %s)"
                )
                params += [f"%{search}%", f"%{search}%", f"%{search}%"]
            if is_system is not None:
                where.append("ir.is_system = %s")
                params.append(is_system)

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""

            cur.execute(
                f"""
                SELECT
                    ir.id, ir.code,
                    ir.demandeur_nom, ir.demandeur_service_legacy, ir.description,
                    ir.statut,
                    rs.label AS statut_label, rs.color AS statut_color,
                    ir.intervention_id,
                    ir.is_system, ir.suggested_type_inter,
                    ir.created_at, ir.updated_at,
                    {_EQUIPEMENT_COLS},
                    {_SERVICE_COLS},
                    {_INTERVENTION_COLS},
                    {_DI_TASKS_COLS}
                FROM intervention_request ir
                LEFT JOIN request_status_ref rs ON ir.statut = rs.code
                {_EQUIPEMENT_JOINS}
                {where_sql}
                GROUP BY ir.id, rs.label, rs.color, m.id, pm.id, pm.code, pm.name, ec.id, s.id,
                         iv.id, ivs.label, ivs.color,
                         iv_stats.action_count, iv_stats.total_time, iv_stats.avg_complexity, iv_stats.purchase_count,
                         di_tasks.tasks_json::text
                ORDER BY ir.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (CLOSED_STATUS_CODE, CLOSED_STATUS_CODE, *params, limit, offset),
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            result = []
            for row in rows:
                r = dict(zip(cols, row))
                r["equipement"] = self._build_equipement(r)
                r["service"] = self._build_service(r)
                r["intervention"] = self._build_intervention(r)
                r["tasks"] = self._build_tasks(r)
                result.append(r)
            return result
        except Exception as e:
            raise DatabaseError("Erreur liste demandes: %s" % str(e)) from e
        finally:
            release_connection(conn)

    def count_list(
        self,
        statut: Optional[str] = None,
        exclude_statuses: Optional[List[str]] = None,
        machine_id: Optional[str] = None,
        search: Optional[str] = None,
        is_system: Optional[bool] = None,
    ) -> int:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where = []
            params: List[Any] = []

            if statut:
                where.append("statut = %s")
                params.append(statut)
            if exclude_statuses:
                placeholders = ",".join(["%s"] * len(exclude_statuses))
                where.append(f"statut NOT IN ({placeholders})")
                params.extend(exclude_statuses)
            if machine_id:
                where.append("machine_id = %s")
                params.append(machine_id)
            if search:
                where.append(
                    "(code ILIKE %s OR demandeur_nom ILIKE %s OR description ILIKE %s)"
                )
                params += [f"%{search}%", f"%{search}%", f"%{search}%"]
            if is_system is not None:
                where.append("is_system = %s")
                params.append(is_system)

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""
            cur.execute(
                f"SELECT COUNT(*) FROM intervention_request {where_sql}", params)
            return cur.fetchone()[0]
        except Exception as e:
            raise DatabaseError("Erreur comptage demandes: %s" % str(e)) from e
        finally:
            release_connection(conn)

    def get_facets(
        self,
        machine_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Comptage par statut (filtres machine_id/search appliqués, statut exclu)."""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where = []
            params: List[Any] = []

            if machine_id:
                where.append("ir.machine_id = %s")
                params.append(machine_id)
            if search:
                where.append(
                    "(ir.code ILIKE %s OR ir.demandeur_nom ILIKE %s OR ir.description ILIKE %s)"
                )
                params += [f"%{search}%", f"%{search}%", f"%{search}%"]

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""

            cur.execute(
                f"""
                SELECT rs.code, rs.label, rs.color, rs.sort_order, COUNT(ir.id) AS count
                FROM request_status_ref rs
                LEFT JOIN intervention_request ir ON ir.statut = rs.code
                    {('AND ' + ' AND '.join(where)) if where else ''}
                GROUP BY rs.code, rs.label, rs.color, rs.sort_order
                ORDER BY rs.sort_order
                """,
                params,
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            raise DatabaseError("Erreur facets demandes: %s" % str(e)) from e
        finally:
            release_connection(conn)

    # ──────────────────────────────────────────────────────────────
    # Détail
    # ──────────────────────────────────────────────────────────────

    def get_by_id(self, request_id: str) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT
                    ir.id, ir.code,
                    ir.demandeur_nom, ir.demandeur_service_legacy, ir.description,
                    ir.statut,
                    rs.label AS statut_label, rs.color AS statut_color,
                    ir.intervention_id,
                    ir.is_system, ir.suggested_type_inter,
                    ir.created_at, ir.updated_at,
                    {_EQUIPEMENT_COLS},
                    {_SERVICE_COLS},
                    {_INTERVENTION_COLS},
                    {_DI_TASKS_COLS}
                FROM intervention_request ir
                LEFT JOIN request_status_ref rs ON ir.statut = rs.code
                {_EQUIPEMENT_JOINS}
                WHERE ir.id = %s
                GROUP BY ir.id, rs.label, rs.color, m.id, pm.id, pm.code, pm.name, ec.id, s.id,
                         iv.id, ivs.label, ivs.color,
                         iv_stats.action_count, iv_stats.total_time, iv_stats.avg_complexity, iv_stats.purchase_count,
                         di_tasks.tasks_json::text
                """,
                (CLOSED_STATUS_CODE, CLOSED_STATUS_CODE, request_id),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Demande {request_id} non trouvée")
            cols = [d[0] for d in cur.description]
            result = dict(zip(cols, row))
            result["equipement"] = self._build_equipement(result)
            result["service"] = self._build_service(result)
            result["intervention"] = self._build_intervention(result)
            result["tasks"] = self._build_tasks(result)

            # Log des transitions
            cur.execute(
                """
                SELECT
                    l.id, l.status_from, l.status_to,
                    sf.label AS status_from_label,
                    st.label AS status_to_label, st.color AS status_to_color,
                    l.changed_by, l.notes, l.date
                FROM request_status_log l
                LEFT JOIN request_status_ref sf ON l.status_from = sf.code
                LEFT JOIN request_status_ref st ON l.status_to = st.code
                WHERE l.request_id = %s
                ORDER BY l.date ASC
                """,
                (request_id,),
            )
            log_rows = cur.fetchall()
            log_cols = [d[0] for d in cur.description]
            result["status_log"] = [dict(zip(log_cols, r)) for r in log_rows]

            return result
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(
                "Erreur récupération demande: %s" % str(e)) from e
        finally:
            release_connection(conn)

    # ──────────────────────────────────────────────────────────────
    # Création
    # ──────────────────────────────────────────────────────────────

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        InterventionRequestValidator.validate_create(data)
        demandeur_nom = (data.get("demandeur_nom") or "").strip()
        description = (data.get("description") or "").strip()
        service_id = data.get("service_id")
        is_system = bool(data.get("is_system", False))
        suggested_type_inter = data.get("suggested_type_inter") or None

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO intervention_request
                    (machine_id, demandeur_nom, service_id, description,
                     is_system, suggested_type_inter, code, statut)
                VALUES (%s, %s, %s, %s, %s, %s, 'PLACEHOLDER', 'nouvelle')
                RETURNING id
                """,
                (
                    str(data["machine_id"]),
                    demandeur_nom,
                    str(service_id) if service_id else None,
                    description,
                    is_system,
                    suggested_type_inter,
                ),
            )
            new_id = cur.fetchone()[0]

            _audit_request(
                cur=cur,
                request_id=str(new_id),
                decision_type="created",
                old_value=None,
                new_value={
                    "machine_id": str(data["machine_id"]),
                    "demandeur_nom": demandeur_nom,
                    "description": description,
                    "is_system": is_system,
                },
                reason_code=data.get("reason_code", "OTHER"),
                reason_text=data.get("reason_text"),
                is_system=is_system,
            )

            conn.commit()
            logger.info("Demande d'intervention créée: %s", new_id)
        except ValidationError:
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError("Erreur création demande: %s" % str(e)) from e
        finally:
            release_connection(conn)

        return self.get_by_id(str(new_id))

    # ──────────────────────────────────────────────────────────────
    # Transition de statut
    # ──────────────────────────────────────────────────────────────

    def transition_status(
        self,
        request_id: str,
        status_to: str,
        notes: Optional[str],
        changed_by: Optional[str],
        intervention_data: Optional[Dict[str, Any]] = None,
        reason_code: str = "OTHER",
        reason_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        existing = self.get_by_id(request_id)
        current_statut = existing["statut"]

        intervention_id = existing.get("intervention_id")

        InterventionRequestValidator.validate_transition(
            current_statut=current_statut,
            status_to=status_to,
            notes=notes,
            intervention_data=intervention_data,
            current_intervention_id=intervention_id,
        )

        # Valider que status_to existe dans le référentiel
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            preventive_occurrence_id = None  # Résolu plus bas uniquement si status_to == "acceptee"
            cur.execute(
                "SELECT code FROM request_status_ref WHERE code = %s", (
                    status_to,)
            )
            if not cur.fetchone():
                raise ValidationError(f"Statut '{status_to}' inconnu")

            # ── Acceptation : résolution du type_inter et création intervention ───
            if status_to == "acceptee":
                # Résolution du type_inter effectif par priorité
                payload_type = (intervention_data or {}).get("type_inter")
                di_is_system = existing.get("is_system", False)
                di_suggested = existing.get("suggested_type_inter")

                if di_is_system and di_suggested:
                    # DI système : suggested_type_inter est autoritaire
                    if payload_type and payload_type != di_suggested:
                        raise ValidationError(
                            f"Cette demande système impose le type '{di_suggested}'. "
                            f"Le type '{payload_type}' ne peut pas être substitué."
                        )
                    effective_type_inter = di_suggested
                elif di_suggested and not payload_type:
                    # DI humaine avec suggestion : utilisée par défaut si rien dans le payload
                    effective_type_inter = di_suggested
                elif payload_type:
                    # Cas standard : le payload fournit le type
                    effective_type_inter = payload_type
                else:
                    raise ValidationError(
                        "Le type d'intervention est requis pour accepter cette demande."
                    )

                # Injecter le type résolu dans intervention_data
                if intervention_data is None:
                    intervention_data = {}
                intervention_data["type_inter"] = effective_type_inter

                # Récupérer l'occurrence_id ICI, avant d'appeler _create_intervention_for_request.
                # Après cet appel le curseur partagé a été utilisé plusieurs fois (SELECT plan_id,
                # INSERT intervention…) et un nouveau fetchone() retournerait None ou un résidu.
                cur.execute(
                    "SELECT id FROM preventive_occurrence WHERE di_id = %s LIMIT 1",
                    (request_id,),
                )
                occ_row = cur.fetchone()
                preventive_occurrence_id = str(occ_row[0]) if occ_row else None

                intervention_id = self._create_intervention_for_request(
                    cur=cur,
                    request=existing,
                    intervention_data=intervention_data,
                )
                logger.info(
                    "Demande %s acceptée : intervention %s créée (type: %s)",
                    request_id, intervention_id, effective_type_inter,
                )

            # ── Clôture : fermer l'intervention liée + compléter l'occurrence ──
            elif status_to == "cloturee":
                if intervention_id:
                    self._close_linked_intervention(
                        cur=cur, intervention_id=str(intervention_id))
                    logger.info(
                        "Demande %s clôturée : intervention %s fermée",
                        request_id, intervention_id,
                    )
                # Passer l'occurrence préventive liée à 'completed'.
                # Double critère : di_id (cas standard) OU intervention_id (cas où
                # l'occurrence a son di_id NULL suite à un repair ou un bug de liaison).
                cur.execute(
                    """
                    UPDATE preventive_occurrence
                    SET status = 'completed'
                    WHERE status NOT IN ('completed', 'skipped')
                      AND (
                          di_id = %s
                          OR intervention_id = %s
                      )
                    """,
                    (request_id, str(intervention_id) if intervention_id else None),
                )
                if cur.rowcount:
                    logger.info(
                        "Occurrence préventive liée à la demande %s passée à 'completed'",
                        request_id,
                    )

            # ── Rejet : remettre l'occurrence préventive liée en pending ──
            elif status_to == "rejetee":
                cur.execute(
                    """
                    UPDATE preventive_occurrence
                    SET status = 'pending', di_id = NULL
                    WHERE di_id = %s
                    """,
                    (request_id,),
                )
                if cur.rowcount:
                    logger.info(
                        "Demande %s rejetée : occurrence préventive remise en pending",
                        request_id,
                    )

            # Appliquer la transition (flag pour éviter double-trigger)
            cur.execute("SET LOCAL app.skip_request_status_log = 'true'")
            cur.execute(
                """
                INSERT INTO request_status_log (request_id, status_from, status_to, changed_by, notes)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (request_id, current_statut, status_to, changed_by, notes),
            )

            # Mettre à jour intervention_id si besoin
            if status_to == "acceptee" and intervention_id:
                cur.execute(
                    "UPDATE intervention_request SET intervention_id = %s WHERE id = %s",
                    (str(intervention_id), request_id),
                )
                # Rattacher l'occurrence et les intervention_task à l'intervention créée.
                # preventive_occurrence_id a été résolu AVANT _create_intervention_for_request
                # pour éviter toute pollution du curseur partagé.
                if preventive_occurrence_id:
                    cur.execute(
                        """
                        UPDATE preventive_occurrence
                        SET intervention_id = %s, status = 'in_progress'
                        WHERE id = %s
                        """,
                        (str(intervention_id), preventive_occurrence_id),
                    )
                    cur.execute(
                        """
                        UPDATE intervention_task
                        SET intervention_id = %s
                        WHERE occurrence_id = %s
                        AND intervention_id IS NULL
                        """,
                        (str(intervention_id), preventive_occurrence_id),
                    )
                    logger.info(
                        "Rattachement tâches : %s tâche(s) liées à l'intervention %s",
                        cur.rowcount, intervention_id,
                    )

            _audit_request(
                cur=cur,
                request_id=request_id,
                decision_type="status_transitioned",
                old_value={"statut": current_statut},
                new_value={"statut": status_to, "notes": notes},
                reason_code=reason_code,
                reason_text=reason_text,
                changed_by=changed_by,
            )

            conn.commit()
            logger.info(
                "Demande %s : transition %s → %s", request_id, current_statut, status_to
            )
        except (ValidationError, ConflictError, DatabaseError):
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError("Erreur transition statut: %s" % str(e)) from e
        finally:
            release_connection(conn)

        return self.get_by_id(request_id)

    # ──────────────────────────────────────────────────────────────
    # Helpers internes
    # ──────────────────────────────────────────────────────────────

    def _create_intervention_for_request(
        self,
        cur: Any,
        request: Dict[str, Any],
        intervention_data: Dict[str, Any],
    ) -> str:
        """Crée une intervention liée à une demande et retourne son ID."""
        from uuid import uuid4
        from api.interventions.validators import InterventionValidator

        # Résoudre tech_initials depuis tech_id si fourni
        tech_id = intervention_data.get("tech_id")
        if tech_id and not intervention_data.get("tech_initials"):
            cur.execute(
                "SELECT initial FROM tunnel_user WHERE id = %s",
                (str(tech_id),),
            )
            row = cur.fetchone()
            if not row:
                raise ValidationError(f"Utilisateur {tech_id} introuvable")
            intervention_data["tech_initials"] = row[0]

        # Valider l'unicité du code avant l'INSERT (remonte ConflictError 409)
        InterventionValidator.validate_create({
            "machine_id": str(request["machine_id"]),
            "type_inter": intervention_data["type_inter"],
            "tech_initials": intervention_data["tech_initials"],
        })

        intervention_id = str(uuid4())

        # Résoudre l'ID du statut "pris en charge"
        cur.execute(
            "SELECT id FROM intervention_status_ref WHERE code = %s LIMIT 1",
            (IN_PROGRESS_STATUS_CODE,),
        )
        row = cur.fetchone()
        if not row:
            # Fallback : prendre le premier statut non fermé
            cur.execute(
                """
                SELECT id FROM intervention_status_ref
                WHERE code NOT IN (%s, 'closed', 'cancelled', 'archived')
                ORDER BY id ASC
                LIMIT 1
                """,
                (CLOSED_STATUS_CODE,),
            )
            row = cur.fetchone()
        if not row:
            raise DatabaseError(
                "Impossible de résoudre le statut 'pris en charge' dans intervention_status_ref"
            )
        status_pris_en_charge_id = row[0]

        reported_date = intervention_data.get("reported_date") or None

        # Récupérer plan_id depuis l'occurrence liée (DI système préventive)
        cur.execute(
            "SELECT plan_id FROM preventive_occurrence WHERE di_id = %s LIMIT 1",
            (str(request["id"]),),
        )
        occ_row = cur.fetchone()
        plan_id = str(occ_row[0]) if occ_row and occ_row[0] else None

        cur.execute(
            """
            INSERT INTO intervention
                (id, title, machine_id, type_inter, priority,
                 reported_by, tech_initials, tech_id, status_actual,
                 printed_fiche, reported_date, plan_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                intervention_id,
                # titre = description de la demande
                request.get("description"),
                str(request["machine_id"]),
                intervention_data["type_inter"],
                intervention_data.get("priority", "normale"),
                request.get("demandeur_nom"),         # reported_by = demandeur
                intervention_data["tech_initials"],
                str(intervention_data["tech_id"]) if intervention_data.get("tech_id") else None,
                status_pris_en_charge_id,
                False,
                reported_date,
                plan_id,
            ),
        )
        return intervention_id

    def _close_linked_intervention(self, cur: Any, intervention_id: str) -> None:
        """Passe une intervention au statut fermé (code = CLOSED_STATUS_CODE).
        Utilise le code texte directement pour que status_actual = 'ferme'
        et que _notify_if_closed() le détecte correctement.
        """
        cur.execute(
            "UPDATE intervention SET status_actual = %s WHERE id = %s",
            (CLOSED_STATUS_CODE, intervention_id),
        )

    # ──────────────────────────────────────────────────────────────
    # Appelé par InterventionRepository quand une intervention est fermée
    # ──────────────────────────────────────────────────────────────

    def on_intervention_closed(self, intervention_id: str) -> None:
        """
        Cascade de fermeture déclenchée quand une intervention est fermée (via PATCH direct).
        - Passe la demande liée à 'cloturee' (si encore 'acceptee')
        - Passe l'occurrence préventive liée à 'completed' (si elle existe)
        Appelé depuis InterventionRepository._notify_if_closed().
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # 1. Clôturer la demande liée.
            # Tentative 1 : chercher via intervention_request.intervention_id (lien direct).
            cur.execute(
                """
                SELECT id, statut FROM intervention_request
                WHERE intervention_id = %s AND statut = 'acceptee'
                LIMIT 1
                """,
                (intervention_id,),
            )
            row = cur.fetchone()

            # Tentative 2 (fallback) : DI dont intervention_id est NULL (ex. auto-accept)
            # mais liée via preventive_occurrence.di_id → occurrence.intervention_id.
            if not row:
                cur.execute(
                    """
                    SELECT ir.id, ir.statut
                    FROM intervention_request ir
                    JOIN preventive_occurrence po ON po.di_id = ir.id
                    WHERE po.intervention_id = %s AND ir.statut = 'acceptee'
                    LIMIT 1
                    """,
                    (intervention_id,),
                )
                row = cur.fetchone()
                if row:
                    # Corriger le lien manquant pour les prochaines fermetures
                    cur.execute(
                        "UPDATE intervention_request SET intervention_id = %s WHERE id = %s",
                        (intervention_id, str(row[0])),
                    )

            if row:
                request_id, current_statut = row[0], row[1]

                cur.execute("SET LOCAL app.skip_request_status_log = 'true'")
                cur.execute(
                    "UPDATE intervention_request SET statut = 'cloturee' WHERE id = %s",
                    (str(request_id),),
                )
                cur.execute(
                    """
                    INSERT INTO request_status_log (request_id, status_from, status_to, changed_by, notes)
                    VALUES (%s, %s, %s, NULL, %s)
                    """,
                    (str(request_id), current_statut, "cloturee",
                     "Clôture automatique suite à la fermeture de l'intervention"),
                )
                logger.info(
                    "Demande %s automatiquement clôturée (intervention %s fermée)",
                    request_id, intervention_id,
                )

            # 2. Passer l'occurrence préventive liée à 'completed'.
            # Double critère : intervention_id (cas standard) OU di_id (cas où
            # occurrence.intervention_id est NULL suite à un bug de rattachement).
            # On récupère le di_id sans filtrer sur le statut de la DI, car le trigger
            # trg_sync_status_log_to_intervention peut avoir déjà clôturé la DI avant
            # que cette fonction ne soit appelée — row serait None dans ce cas.
            closed_request_id = str(row[0]) if row else None
            if not closed_request_id:
                cur.execute(
                    "SELECT id FROM intervention_request WHERE intervention_id = %s LIMIT 1",
                    (intervention_id,),
                )
                di_row = cur.fetchone()
                closed_request_id = str(di_row[0]) if di_row else None

            cur.execute(
                """
                UPDATE preventive_occurrence
                SET status = 'completed'
                WHERE status NOT IN ('completed', 'skipped')
                  AND (
                      intervention_id = %s
                      OR (di_id = %s AND %s IS NOT NULL)
                  )
                """,
                (intervention_id, closed_request_id, closed_request_id),
            )
            if cur.rowcount:
                logger.info(
                    "Occurrence préventive liée à l'intervention %s passée à 'completed'",
                    intervention_id,
                )

            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(
                "Erreur clôture automatique pour intervention %s: %s",
                intervention_id, str(e),
            )
        finally:
            release_connection(conn)

    # ──────────────────────────────────────────────────────────────
    # Réparation manuelle des DIs orphelines
    # ──────────────────────────────────────────────────────────────

    def repair_orphaned_requests(self) -> Dict[str, Any]:
        """
        Passe à 'cloturee' toutes les DIs en statut 'acceptee' dont l'intervention
        liée est déjà fermée (status_actual = CLOSED_STATUS_CODE).

        Réplique la cascade de on_intervention_closed pour les DIs orphelines :
        cas où la fermeture automatique n'a pas été déclenchée (données historiques,
        fermeture directe en DB, etc.).

        Idempotente : peut être appelée plusieurs fois sans effet secondaire.
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()

            # Trouve toutes les DIs acceptées dont l'intervention est fermée.
            # UNION : chemin direct (intervention_id sur la DI) ET chemin via occurrence
            # (DIs auto-acceptées dont intervention_id est NULL mais liées via occurrence).
            cur.execute(
                """
                SELECT ir.id, ir.code, m.code AS machine_code
                FROM intervention_request ir
                JOIN intervention i ON i.id = ir.intervention_id
                LEFT JOIN machine m ON m.id = ir.machine_id
                WHERE ir.statut = 'acceptee'
                  AND i.status_actual = %s

                UNION

                SELECT ir.id, ir.code, m.code AS machine_code
                FROM intervention_request ir
                JOIN preventive_occurrence po ON po.di_id = ir.id
                JOIN intervention i ON i.id = po.intervention_id
                LEFT JOIN machine m ON m.id = ir.machine_id
                WHERE ir.statut = 'acceptee'
                  AND ir.intervention_id IS NULL
                  AND i.status_actual = %s

                ORDER BY id
                """,
                (CLOSED_STATUS_CODE, CLOSED_STATUS_CODE),
            )
            rows = cur.fetchall()

            repaired = []

            # Empêche le trigger de créer un doublon dans request_status_log
            cur.execute("SET LOCAL app.skip_request_status_log = 'true'")

            for request_id, di_code, machine_code in rows:
                # Corriger intervention_id manquant (DIs auto-acceptées via occurrence)
                cur.execute(
                    """
                    UPDATE intervention_request ir
                    SET intervention_id = po.intervention_id
                    FROM preventive_occurrence po
                    WHERE po.di_id = ir.id
                      AND ir.id = %s
                      AND ir.intervention_id IS NULL
                    """,
                    (str(request_id),),
                )
                cur.execute(
                    "UPDATE intervention_request SET statut = 'cloturee' WHERE id = %s",
                    (str(request_id),),
                )
                cur.execute(
                    """
                    INSERT INTO request_status_log
                        (request_id, status_from, status_to, changed_by, notes)
                    VALUES (%s, %s, %s, NULL, %s)
                    """,
                    (
                        str(request_id),
                        "acceptee",
                        "cloturee",
                        "Clôture manuelle via endpoint /repair",
                    ),
                )
                _audit_request(
                    cur=cur,
                    request_id=str(request_id),
                    decision_type="status_transitioned",
                    old_value={"statut": "acceptee"},
                    new_value={"statut": "cloturee", "notes": "Clôture manuelle via endpoint /repair"},
                    reason_code="SYSTEM",
                    is_system=True,
                )
                repaired.append({
                    "id": str(request_id),
                    "code": di_code,
                    "machine_code": machine_code,
                })

            conn.commit()
            logger.info(
                "repair_orphaned_requests : %d DI(s) pass\u00e9es \u00e0 cloturee", len(repaired)
            )
            return {
                "repaired_count": len(repaired),
                "details": repaired,
            }
        except Exception as e:
            conn.rollback()
            raise_db_error(e, "r\u00e9paration DIs orphelines")
        finally:
            release_connection(conn)

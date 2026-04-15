import logging
from typing import Any, Dict, List, Optional

from api.db import get_connection, release_connection
from api.errors.exceptions import ConflictError, DatabaseError, NotFoundError, ValidationError
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

_EQUIPEMENT_JOINS = """
    LEFT JOIN machine m ON ir.machine_id = m.id
    LEFT JOIN machine pm ON pm.id = m.equipement_mere
    LEFT JOIN equipement_class ec ON ec.id = m.equipement_class_id
    LEFT JOIN intervention i_h ON i_h.machine_id = m.id
    LEFT JOIN service s ON ir.service_id = s.id
"""

logger = logging.getLogger(__name__)


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
                    {_SERVICE_COLS}
                FROM intervention_request ir
                LEFT JOIN request_status_ref rs ON ir.statut = rs.code
                {_EQUIPEMENT_JOINS}
                {where_sql}
                GROUP BY ir.id, rs.label, rs.color, m.id, pm.id, pm.code, pm.name, ec.id, s.id
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
                    {_SERVICE_COLS}
                FROM intervention_request ir
                LEFT JOIN request_status_ref rs ON ir.statut = rs.code
                {_EQUIPEMENT_JOINS}
                WHERE ir.id = %s
                GROUP BY ir.id, rs.label, rs.color, m.id, pm.id, pm.code, pm.name, ec.id, s.id
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

            # ── Clôture : fermer l'intervention liée ──────────────────
            elif status_to == "cloturee":
                if intervention_id:
                    self._close_linked_intervention(
                        cur=cur, intervention_id=str(intervention_id))
                    logger.info(
                        "Demande %s clôturée : intervention %s fermée",
                        request_id, intervention_id,
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
                # Rattacher l'occurrence et les gamme_step_validation à l'intervention créée.
                # preventive_occurrence_id a été résolu AVANT _create_intervention_for_request
                # pour éviter toute pollution du curseur partagé.
                if preventive_occurrence_id:
                    cur.execute(
                        "UPDATE preventive_occurrence SET intervention_id = %s WHERE id = %s",
                        (str(intervention_id), preventive_occurrence_id),
                    )
                    cur.execute(
                        """
                        UPDATE gamme_step_validation
                        SET intervention_id = %s
                        WHERE occurrence_id = %s
                        AND intervention_id IS NULL
                        """,
                        (str(intervention_id), preventive_occurrence_id),
                    )
                    logger.info(
                        "Rattachement gamme : %s step(s) liés à l'intervention %s",
                        cur.rowcount, intervention_id,
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
                 reported_by, tech_initials, status_actual,
                 printed_fiche, reported_date, plan_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                status_pris_en_charge_id,
                False,
                reported_date,
                plan_id,
            ),
        )
        return intervention_id

    def _close_linked_intervention(self, cur: Any, intervention_id: str) -> None:
        """Passe une intervention au statut fermé (code = CLOSED_STATUS_CODE)."""
        cur.execute(
            "SELECT id FROM intervention_status_ref WHERE code = %s LIMIT 1",
            (CLOSED_STATUS_CODE,),
        )
        row = cur.fetchone()
        if not row:
            raise DatabaseError(
                "Impossible de résoudre le statut 'ferme' dans intervention_status_ref"
            )
        closed_status_id = row[0]

        cur.execute(
            "UPDATE intervention SET status_actual = %s WHERE id = %s",
            (closed_status_id, intervention_id),
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

            # 1. Clôturer la demande liée
            cur.execute(
                """
                SELECT id, statut FROM intervention_request
                WHERE intervention_id = %s AND statut = 'acceptee'
                LIMIT 1
                """,
                (intervention_id,),
            )
            row = cur.fetchone()
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

            # 2. Passer l'occurrence préventive liée à 'completed' (indépendant de l'étape 1)
            cur.execute(
                """
                UPDATE preventive_occurrence
                SET status = 'completed'
                WHERE intervention_id = %s
                  AND status NOT IN ('completed', 'skipped')
                """,
                (intervention_id,),
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

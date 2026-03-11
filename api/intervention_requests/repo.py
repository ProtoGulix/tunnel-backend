import logging
from typing import Any, Dict, List, Optional

from api.db import get_connection, release_connection
from api.errors.exceptions import DatabaseError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

# Transitions autorisées : statut_from → [statuts_to possibles]
ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "nouvelle":   ["en_attente", "acceptee", "rejetee"],
    "en_attente": ["acceptee", "rejetee"],
    "acceptee":   ["cloturee"],
    "rejetee":    [],
    "cloturee":   [],
}


class InterventionRequestRepository:

    def _get_connection(self):
        return get_connection()

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
            raise DatabaseError("Erreur récupération statuts: %s" % str(e)) from e
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
        machine_id: Optional[str] = None,
        search: Optional[str] = None,
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
                SELECT
                    ir.id, ir.code, ir.machine_id,
                    m.name AS machine_name,
                    ir.demandeur_nom, ir.demandeur_service, ir.description,
                    ir.statut,
                    rs.label AS statut_label, rs.color AS statut_color,
                    ir.created_at, ir.updated_at
                FROM intervention_request ir
                LEFT JOIN machine m ON ir.machine_id = m.id
                LEFT JOIN request_status_ref rs ON ir.statut = rs.code
                {where_sql}
                ORDER BY ir.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            raise DatabaseError("Erreur liste demandes: %s" % str(e)) from e
        finally:
            release_connection(conn)

    def count_list(
        self,
        statut: Optional[str] = None,
        machine_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            where = []
            params: List[Any] = []

            if statut:
                where.append("statut = %s")
                params.append(statut)
            if machine_id:
                where.append("machine_id = %s")
                params.append(machine_id)
            if search:
                where.append(
                    "(code ILIKE %s OR demandeur_nom ILIKE %s OR description ILIKE %s)"
                )
                params += [f"%{search}%", f"%{search}%", f"%{search}%"]

            where_sql = ("WHERE " + " AND ".join(where)) if where else ""
            cur.execute(f"SELECT COUNT(*) FROM intervention_request {where_sql}", params)
            return cur.fetchone()[0]
        except Exception as e:
            raise DatabaseError("Erreur comptage demandes: %s" % str(e)) from e
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
                """
                SELECT
                    ir.id, ir.code, ir.machine_id,
                    m.name AS machine_name,
                    ir.demandeur_nom, ir.demandeur_service, ir.description,
                    ir.statut,
                    rs.label AS statut_label, rs.color AS statut_color,
                    ir.created_at, ir.updated_at
                FROM intervention_request ir
                LEFT JOIN machine m ON ir.machine_id = m.id
                LEFT JOIN request_status_ref rs ON ir.statut = rs.code
                WHERE ir.id = %s
                """,
                (request_id,),
            )
            row = cur.fetchone()
            if not row:
                raise NotFoundError(f"Demande {request_id} non trouvée")
            cols = [d[0] for d in cur.description]
            result = dict(zip(cols, row))

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
            raise DatabaseError("Erreur récupération demande: %s" % str(e)) from e
        finally:
            release_connection(conn)

    # ──────────────────────────────────────────────────────────────
    # Création
    # ──────────────────────────────────────────────────────────────

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        demandeur_nom = (data.get("demandeur_nom") or "").strip()
        description = (data.get("description") or "").strip()
        if not demandeur_nom:
            raise ValidationError("demandeur_nom est obligatoire")
        if not description:
            raise ValidationError("description est obligatoire")
        if not data.get("machine_id"):
            raise ValidationError("machine_id est obligatoire")

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            # Le code et le statut initial sont gérés par les triggers DB
            cur.execute(
                """
                INSERT INTO intervention_request
                    (machine_id, demandeur_nom, demandeur_service, description, code, statut)
                VALUES (%s, %s, %s, %s, 'PLACEHOLDER', 'nouvelle')
                RETURNING id
                """,
                (
                    str(data["machine_id"]),
                    demandeur_nom,
                    data.get("demandeur_service"),
                    description,
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
        self, request_id: str, status_to: str, notes: Optional[str], changed_by: Optional[str]
    ) -> Dict[str, Any]:
        existing = self.get_by_id(request_id)
        current_statut = existing["statut"]

        # Validation transition
        allowed = ALLOWED_TRANSITIONS.get(current_statut, [])
        if status_to not in allowed:
            raise ValidationError(
                f"Transition '{current_statut}' → '{status_to}' non autorisée. "
                f"Transitions possibles : {allowed or 'aucune'}"
            )

        # Motif obligatoire pour rejet
        if status_to == "rejetee" and not (notes or "").strip():
            raise ValidationError("Un motif (notes) est obligatoire pour rejeter une demande")

        # Valider que status_to existe dans le référentiel
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT code FROM request_status_ref WHERE code = %s", (status_to,)
            )
            if not cur.fetchone():
                raise ValidationError(f"Statut '{status_to}' inconnu")

            # INSERT dans request_status_log → trigger fn_apply_request_status
            # met à jour intervention_request.statut automatiquement
            cur.execute(
                """
                INSERT INTO request_status_log (request_id, status_from, status_to, changed_by, notes)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (request_id, current_statut, status_to, changed_by, notes),
            )
            conn.commit()
            logger.info(
                "Demande %s : transition %s → %s", request_id, current_statut, status_to
            )
        except ValidationError:
            raise
        except Exception as e:
            conn.rollback()
            raise DatabaseError("Erreur transition statut: %s" % str(e)) from e
        finally:
            release_connection(conn)

        return self.get_by_id(request_id)

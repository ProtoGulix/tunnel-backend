"""Repository d'accès aux tables audit_log et audit_reason_code."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from psycopg2.extras import RealDictCursor

from api.db import get_connection, release_connection
from api.errors.exceptions import raise_db_error, ValidationError, ConflictError

logger = logging.getLogger(__name__)


def _shape_log_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Transforme une ligne plate SQL en dict conforme à AuditLogOut (reason et changed_by imbriqués)."""
    changed_by = None
    if row.get("user_id"):
        changed_by = {
            "id": row["user_id"],
            "first_name": row.get("user_first_name"),
            "last_name": row.get("user_last_name"),
            "initials": row.get("user_initials"),
        }

    reason = {
        "id": row["reason_id"],
        "code": row["reason_code"],
        "label": row["reason_label"],
        "category": row["reason_category"],
        "color": row.get("reason_color"),
        "description": row.get("reason_description"),
    }

    return {
        "id": row["id"],
        "entity_type": row["entity_type"],
        "entity_id": row["entity_id"],
        "decision_type": row["decision_type"],
        "old_value": row.get("old_value"),
        "new_value": row.get("new_value"),
        "reason": reason,
        "reason_text": row.get("reason_text"),
        "changed_by": changed_by,
        "is_system": row["is_system"],
        "logged_at": row["logged_at"],
    }


class AuditRepository:
    """Accès aux tables audit_log et audit_reason_code."""

    def _get_connection(self):
        return get_connection()

    # ── Raisons ──────────────────────────────────────────────────────────────

    def get_all_reasons(
        self,
        active_only: bool = True,
        category: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Liste les raisons disponibles avec filtres optionnels."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_clauses: List[str] = []
                params: List[Any] = []

                if active_only:
                    where_clauses.append("is_active = TRUE")
                if category:
                    where_clauses.append("category = %s")
                    params.append(category)
                if entity_type:
                    where_clauses.append("(%s = ANY(entity_types) OR entity_types IS NULL)")
                    params.append(entity_type)

                where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

                cur.execute(
                    f"""
                    SELECT id, code, label, category, color, description
                    FROM audit_reason_code
                    WHERE {where_sql}
                    ORDER BY category, label
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            raise_db_error(e, "liste des raisons d'audit")
        finally:
            if conn:
                release_connection(conn)

    def get_reason_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Retourne une raison par son code, ou None si inexistante/inactive."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, code, label, category, color, description, is_active
                    FROM audit_reason_code
                    WHERE code = %s
                    """,
                    (code,),
                )
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            raise_db_error(e, "récupération raison audit")
        finally:
            if conn:
                release_connection(conn)

    def get_all_reasons_admin(self) -> List[Dict[str, Any]]:
        """Liste complète des raisons (actives et inactives) pour la gestion en admin."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, code, label, category, entity_types, decision_types,
                           color, description, is_active, created_at, updated_at
                    FROM audit_reason_code
                    ORDER BY category, label
                    """
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            raise_db_error(e, "liste admin des raisons d'audit")
        finally:
            if conn:
                release_connection(conn)

    def create_reason(
        self,
        code: str,
        label: str,
        category: str,
        entity_types: Optional[List[str]] = None,
        decision_types: Optional[List[str]] = None,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Crée une raison d'audit. Le code doit être unique (contrainte DB)."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO audit_reason_code
                        (code, label, category, entity_types, decision_types, color, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, code, label, category, entity_types, decision_types,
                              color, description, is_active, created_at, updated_at
                    """,
                    (code, label, category, entity_types, decision_types, color, description),
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row)
        except Exception as e:
            if conn:
                conn.rollback()
            if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                raise ConflictError(f"Une raison avec le code '{code}' existe déjà") from e
            raise_db_error(e, "création raison d'audit")
        finally:
            if conn:
                release_connection(conn)

    def update_reason(
        self,
        reason_id: int,
        label: Optional[str] = None,
        category: Optional[str] = None,
        entity_types: Optional[List[str]] = None,
        decision_types: Optional[List[str]] = None,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Modifie partiellement une raison d'audit. Le code n'est pas modifiable."""
        sets: List[str] = ["updated_at = now()"]
        params: List[Any] = []

        if label is not None:
            sets.append("label = %s")
            params.append(label)
        if category is not None:
            sets.append("category = %s")
            params.append(category)
        if entity_types is not None:
            sets.append("entity_types = %s")
            params.append(entity_types)
        if decision_types is not None:
            sets.append("decision_types = %s")
            params.append(decision_types)
        if color is not None:
            sets.append("color = %s")
            params.append(color)
        if description is not None:
            sets.append("description = %s")
            params.append(description)

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    UPDATE audit_reason_code
                    SET {", ".join(sets)}
                    WHERE id = %s
                    RETURNING id, code, label, category, entity_types, decision_types,
                              color, description, is_active, created_at, updated_at
                    """,
                    (*params, reason_id),
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "modification raison d'audit")
        finally:
            if conn:
                release_connection(conn)

    def set_reason_active(self, reason_id: int, is_active: bool) -> Optional[Dict[str, Any]]:
        """Active/désactive une raison. Une raison inactive n'apparaît plus dans le picker."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE audit_reason_code
                    SET is_active = %s, updated_at = now()
                    WHERE id = %s
                    RETURNING id, code, label, category, entity_types, decision_types,
                              color, description, is_active, created_at, updated_at
                    """,
                    (is_active, reason_id),
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "activation/désactivation raison d'audit")
        finally:
            if conn:
                release_connection(conn)

    # ── Log via fonction PostgreSQL ───────────────────────────────────────────

    def call_fn_audit_log_decision(
        self,
        entity_type: str,
        entity_id: UUID,
        decision_type: str,
        old_value: Optional[Dict[str, Any]],
        new_value: Optional[Dict[str, Any]],
        reason_code: str,
        reason_text: Optional[str] = None,
        changed_by: Optional[UUID] = None,
        is_system: bool = False,
    ) -> Optional[UUID]:
        """
        Appelle fn_audit_log_decision() en base.
        La DB valide la raison, les contraintes métier, et insère le log.
        Retourne l'UUID du log créé, ou None si la fonction DB a retourné NULL.
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT public.fn_audit_log_decision(
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        entity_type,
                        entity_id,
                        decision_type,
                        json.dumps(old_value) if old_value is not None else None,
                        json.dumps(new_value) if new_value is not None else None,
                        reason_code,
                        reason_text,
                        changed_by,
                        is_system,
                    ),
                )
                row = cur.fetchone()
                conn.commit()
                return row[0] if row and row[0] else None
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "insertion audit log")
        finally:
            if conn:
                release_connection(conn)

    # ── Requêtes de lecture ───────────────────────────────────────────────────

    def get_logs(
        self,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        reason_code: Optional[str] = None,
        decision_type: Optional[str] = None,
        changed_by: Optional[UUID] = None,
        exclude_system: bool = False,
        limit: int = 50,
        offset: int = 0,
        include_facets: bool = False,
    ) -> Dict[str, Any]:
        """Requête paginée sur audit_log avec filtres optionnels et facettes optionnelles."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_clauses: List[str] = []
                params: List[Any] = []

                if from_dt:
                    where_clauses.append("al.logged_at >= %s")
                    params.append(from_dt)
                if to_dt:
                    where_clauses.append("al.logged_at <= %s")
                    params.append(to_dt)
                if entity_type:
                    where_clauses.append("al.entity_type = %s")
                    params.append(entity_type)
                if entity_id:
                    where_clauses.append("al.entity_id = %s")
                    params.append(entity_id)
                if reason_code:
                    where_clauses.append("arc.code = %s")
                    params.append(reason_code)
                if decision_type:
                    where_clauses.append("al.decision_type = %s")
                    params.append(decision_type)
                if changed_by:
                    where_clauses.append("al.changed_by = %s")
                    params.append(changed_by)
                if exclude_system:
                    where_clauses.append("al.is_system = FALSE")

                where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

                _SELECT = """
                    SELECT
                        al.id,
                        al.entity_type,
                        al.entity_id,
                        al.decision_type,
                        al.old_value,
                        al.new_value,
                        al.reason_text,
                        al.is_system,
                        al.logged_at,
                        arc.id          AS reason_id,
                        arc.code        AS reason_code,
                        arc.label       AS reason_label,
                        arc.category    AS reason_category,
                        arc.color       AS reason_color,
                        arc.description AS reason_description,
                        tu.id           AS user_id,
                        tu.first_name   AS user_first_name,
                        tu.last_name    AS user_last_name,
                        tu.initial      AS user_initials
                    FROM audit_log al
                    LEFT JOIN audit_reason_code arc ON al.reason_code_id = arc.id
                    LEFT JOIN tunnel_user tu ON tu.id = al.changed_by
                """

                # Total pour pagination
                cur.execute(
                    f"SELECT COUNT(*) FROM audit_log al LEFT JOIN audit_reason_code arc ON al.reason_code_id = arc.id WHERE {where_sql}",
                    params,
                )
                total = cur.fetchone()["count"]

                cur.execute(
                    f"{_SELECT} WHERE {where_sql} ORDER BY al.logged_at DESC LIMIT %s OFFSET %s",
                    [*params, min(limit, 1000), offset],
                )
                rows = cur.fetchall()
                items = [_shape_log_row(dict(row)) for row in rows]

                page_size = min(limit, 1000)
                total_pages = max(1, -(-total // page_size))  # ceil division

                result: Dict[str, Any] = {
                    "items": items,
                    "pagination": {
                        "total": total,
                        "offset": offset,
                        "limit": page_size,
                        "count": len(items),
                        "total_pages": total_pages,
                    },
                    "facets": None,
                }

                if include_facets:
                    cur.execute(
                        f"""
                        SELECT al.entity_type, COUNT(*) AS count
                        FROM audit_log al
                        LEFT JOIN audit_reason_code arc ON al.reason_code_id = arc.id
                        WHERE {where_sql}
                        GROUP BY al.entity_type ORDER BY count DESC
                        """,
                        params,
                    )
                    entity_facets = [{"value": r["entity_type"], "count": r["count"]} for r in cur.fetchall()]

                    cur.execute(
                        f"""
                        SELECT al.decision_type, COUNT(*) AS count
                        FROM audit_log al
                        LEFT JOIN audit_reason_code arc ON al.reason_code_id = arc.id
                        WHERE {where_sql}
                        GROUP BY al.decision_type ORDER BY count DESC
                        LIMIT 30
                        """,
                        params,
                    )
                    decision_facets = [{"value": r["decision_type"], "count": r["count"]} for r in cur.fetchall()]

                    cur.execute(
                        f"""
                        SELECT arc.code, arc.label, arc.color, COUNT(*) AS count
                        FROM audit_log al
                        LEFT JOIN audit_reason_code arc ON al.reason_code_id = arc.id
                        WHERE {where_sql}
                        GROUP BY arc.code, arc.label, arc.color ORDER BY count DESC
                        """,
                        params,
                    )
                    reason_facets = [
                        {"value": r["code"], "label": r["label"], "color": r["color"], "count": r["count"]}
                        for r in cur.fetchall()
                    ]

                    result["facets"] = {
                        "entity_type": entity_facets,
                        "decision_type": decision_facets,
                        "reason_code": reason_facets,
                    }

                return result
        except Exception as e:
            raise_db_error(e, "lecture audit logs")
        finally:
            if conn:
                release_connection(conn)

    def get_briefing(
        self,
        from_dt: datetime,
        to_dt: datetime,
        exclude_system: bool = False,
    ) -> Dict[str, Any]:
        """Génère un rapport de briefing sur une fenêtre temporelle."""
        rows = self.get_logs(
            from_dt=from_dt,
            to_dt=to_dt,
            exclude_system=exclude_system,
            limit=1000,
        )["items"]

        decisions = []
        by_entity: Dict[str, int] = {}
        by_decision: Dict[str, int] = {}

        for row in rows:
            old_v = row.get("old_value") or {}
            new_v = row.get("new_value") or {}
            from_val = next(iter(old_v.values()), None) if old_v else None
            to_val = next(iter(new_v.values()), None) if new_v else None

            reason = row["reason"]
            decisions.append({
                "timestamp": row["logged_at"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "decision_type": row["decision_type"],
                "from_value": from_val,
                "to_value": to_val,
                "reason_code": reason["code"],
                "reason_label": reason["label"],
                "reason_color": reason.get("color"),
                "reason_text": row.get("reason_text"),
                "changed_by": row.get("changed_by"),
                "is_system": row["is_system"],
            })

            et = row["entity_type"]
            dt = row["decision_type"]
            by_entity[et] = by_entity.get(et, 0) + 1
            by_decision[dt] = by_decision.get(dt, 0) + 1

        duration = (to_dt - from_dt).total_seconds() / 60

        return {
            "session_start": from_dt,
            "session_end": to_dt,
            "duration_minutes": round(duration, 2),
            "decisions": decisions,
            "summary": {
                "total_decisions": len(decisions),
                "by_entity_type": by_entity,
                "by_decision_type": by_decision,
            },
        }


class AuditRuleRepository:
    """Accès à la table audit_rule (règles routine/sensible par entité et champ)."""

    def _get_connection(self):
        return get_connection()

    def list_rules(self, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Liste les règles, filtrables par entity_type."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_sql = "TRUE"
                params: List[Any] = []
                if entity_type:
                    where_sql = "entity_type = %s"
                    params.append(entity_type)

                cur.execute(
                    f"""
                    SELECT id, entity_type, field, is_routine, default_reason_code
                    FROM audit_rule
                    WHERE {where_sql}
                    ORDER BY entity_type, field NULLS FIRST
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            raise_db_error(e, "liste des règles d'audit")
        finally:
            if conn:
                release_connection(conn)

    def get_known_fields(self, entity_type: str) -> List[str]:
        """
        Liste les champs déjà observés pour une entité : union des champs
        couverts par une règle (audit_rule.field) et des champs déjà modifiés
        au moins une fois (audit_log.decision_type = '{field}_changed').
        Sert à assister la saisie d'une nouvelle règle côté admin.
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT field FROM audit_rule
                    WHERE entity_type = %s AND field IS NOT NULL
                    UNION
                    SELECT substring(decision_type from '^(.+)_changed$') AS field
                    FROM audit_log
                    WHERE entity_type = %s AND decision_type LIKE '%%_changed'
                    ORDER BY field
                    """,
                    (entity_type, entity_type),
                )
                return [row[0] for row in cur.fetchall() if row[0]]
        except Exception as e:
            raise_db_error(e, "liste des champs connus d'audit")
        finally:
            if conn:
                release_connection(conn)

    def get_rules_for_fields(self, entity_type: str, fields: List[str]) -> List[Dict[str, Any]]:
        """
        Retourne les règles applicables pour un entity_type et un ensemble de champs.
        Inclut la règle par défaut (field IS NULL) si elle existe, utilisée en
        fallback quand un champ du payload n'a pas de règle dédiée.
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, entity_type, field, is_routine, default_reason_code
                    FROM audit_rule
                    WHERE entity_type = %s AND (field IS NULL OR field = ANY(%s))
                    """,
                    (entity_type, fields),
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            raise_db_error(e, "récupération règles d'audit par champ")
        finally:
            if conn:
                release_connection(conn)

    def create_rule(
        self,
        entity_type: str,
        field: Optional[str],
        is_routine: bool,
        default_reason_code: Optional[str],
    ) -> Dict[str, Any]:
        """Crée une règle d'audit. is_routine=True exige default_reason_code."""
        if is_routine and not default_reason_code:
            raise ValidationError("default_reason_code obligatoire si is_routine=True")

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO audit_rule (entity_type, field, is_routine, default_reason_code)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, entity_type, field, is_routine, default_reason_code
                    """,
                    (entity_type, field, is_routine, default_reason_code),
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row)
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "création règle d'audit")
        finally:
            if conn:
                release_connection(conn)

    def update_rule(
        self,
        rule_id: int,
        is_routine: Optional[bool] = None,
        default_reason_code: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Modifie partiellement une règle d'audit (is_routine et/ou default_reason_code)."""
        sets: List[str] = []
        params: List[Any] = []

        if is_routine is not None:
            sets.append("is_routine = %s")
            params.append(is_routine)
        if default_reason_code is not None:
            sets.append("default_reason_code = %s")
            params.append(default_reason_code)

        if not sets:
            raise ValidationError("Rien à mettre à jour")

        sets.append("updated_at = now()")
        params.append(rule_id)

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    UPDATE audit_rule
                    SET {', '.join(sets)}
                    WHERE id = %s
                    RETURNING id, entity_type, field, is_routine, default_reason_code
                    """,
                    params,
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None
        except Exception as e:
            if conn:
                conn.rollback()
            raise_db_error(e, "modification règle d'audit")
        finally:
            if conn:
                release_connection(conn)

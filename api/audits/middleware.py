"""
Middleware d'audit log.

Interceptionne PATCH/POST/DELETE sur les entités métier, vérifie la présence
d'un reason_code valide dans le payload, puis après exécution de la route
calcule le diff et appelle fn_audit_log_decision() en base.

Ordre dans la pile middleware Starlette :
  CORS → JWT → AuditMiddleware → route

Le JWT est donc déjà validé quand on arrive ici : request.state.user_id est disponible.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.audits.repo import AuditRepository

logger = logging.getLogger(__name__)

# Entités tracées : préfixe URL → entity_type
# intervention-tasks est exclu : l'audit est géré directement dans le repo
# (créations, PATCH, suppressions, transitions de statut via action)
_ENTITY_MAP: Dict[str, str] = {
    "interventions": "intervention",
    "intervention-requests": "request",
    "purchase-requests": "purchase_request",
    "intervention-actions": "action",
}

# Pattern : /interventions/{uuid} ou /interventions/{uuid}/sous-ressource
_PATH_RE = re.compile(
    r"^/([a-z][a-z0-9\-]+)/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)

# Champs ignorés dans le calcul du diff (méta-données techniques)
_DIFF_IGNORE = frozenset({"id", "created_at", "updated_at", "updated_by", "reason_code", "reason_text"})


def _extract_entity(path: str) -> Optional[Tuple[str, str]]:
    """Retourne (entity_type, entity_id_str) ou None."""
    m = _PATH_RE.match(path)
    if not m:
        return None
    resource, entity_id = m.groups()
    entity_type = _ENTITY_MAP.get(resource)
    return (entity_type, entity_id) if entity_type else None


def _compute_diff(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Tuple[Any, Any]]:
    """Retourne {champ: (ancienne_valeur, nouvelle_valeur)} pour les champs modifiés."""
    diff: Dict[str, Tuple[Any, Any]] = {}
    for key in set(old) | set(new):
        if key in _DIFF_IGNORE:
            continue
        if old.get(key) != new.get(key):
            diff[key] = (old.get(key), new.get(key))
    return diff


class AuditMiddleware(BaseHTTPMiddleware):
    """Trace les mutations métier en appelant fn_audit_log_decision() après chaque succès."""

    async def dispatch(self, request: Request, call_next):
        if request.method not in ("PATCH", "POST", "PUT", "DELETE"):
            return await call_next(request)

        entity_info = _extract_entity(request.url.path)
        if not entity_info:
            return await call_next(request)

        entity_type, entity_id_str = entity_info

        # ── Lecture et bufferisation du corps ────────────────────────────────
        # Starlette ne permet de lire request.body() qu'une fois ;
        # on le remet en place via un générateur pour que la route puisse le relire.
        raw_body = await request.body()

        payload: Dict[str, Any] = {}
        if raw_body:
            try:
                payload = json.loads(raw_body)
            except (json.JSONDecodeError, ValueError):
                pass

        # Reconstruit le corps lisible pour la route
        async def receive():
            return {"type": "http.request", "body": raw_body, "more_body": False}

        request = Request(request.scope, receive)

        reason_code: Optional[str] = payload.get("reason_code")
        reason_text: Optional[str] = payload.get("reason_text")

        # ── Validation reason_code AVANT la route ────────────────────────────
        if request.method in ("PATCH", "POST", "PUT"):
            if not reason_code:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "reason_code obligatoire pour cette mutation", "error_type": "ValidationError"},
                )
            repo = AuditRepository()
            reason = repo.get_reason_by_code(reason_code)
            if not reason or not reason.get("is_active"):
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Raison '{reason_code}' inconnue ou inactive", "error_type": "ValidationError"},
                )

        # ── Snapshot avant mutation (PATCH / DELETE uniquement) ──────────────
        old_state: Dict[str, Any] = {}
        if request.method in ("PATCH", "PUT", "DELETE") and entity_type and entity_id_str:
            old_state = await _fetch_entity_state(entity_type, entity_id_str)

        # ── Exécution de la route ────────────────────────────────────────────
        response = await call_next(request)

        # ── Log post-succès ──────────────────────────────────────────────────
        if 200 <= response.status_code < 300:
            new_state: Dict[str, Any] = {}
            if request.method != "DELETE":
                new_state = await _fetch_entity_state(entity_type, entity_id_str)

            diffs = _compute_diff(old_state, new_state)

            if not diffs and request.method in ("POST",):
                # Pour les créations, on n'a pas d'old_state ; on loggue le payload
                decision_type = "created"
                _write_audit_log(
                    entity_type=entity_type,
                    entity_id_str=entity_id_str,
                    decision_type=decision_type,
                    old_value=None,
                    new_value={k: v for k, v in payload.items() if k not in _DIFF_IGNORE},
                    reason_code=reason_code,
                    reason_text=reason_text,
                    request=request,
                )
            elif request.method == "DELETE":
                _write_audit_log(
                    entity_type=entity_type,
                    entity_id_str=entity_id_str,
                    decision_type="deleted",
                    old_value=old_state or None,
                    new_value=None,
                    reason_code=reason_code,
                    reason_text=reason_text,
                    request=request,
                )
            else:
                for field, (old_val, new_val) in diffs.items():
                    _write_audit_log(
                        entity_type=entity_type,
                        entity_id_str=entity_id_str,
                        decision_type=f"{field}_changed",
                        old_value={field: old_val},
                        new_value={field: new_val},
                        reason_code=reason_code,
                        reason_text=reason_text,
                        request=request,
                    )

        return response


def _write_audit_log(
    entity_type: str,
    entity_id_str: str,
    decision_type: str,
    old_value: Optional[Dict],
    new_value: Optional[Dict],
    reason_code: Optional[str],
    reason_text: Optional[str],
    request: Request,
) -> None:
    """Appelle fn_audit_log_decision() ; les erreurs n'interrompent pas la réponse."""
    if not reason_code:
        return
    try:
        entity_id = UUID(entity_id_str)
        changed_by: Optional[UUID] = None
        raw_user_id = getattr(request.state, "user_id", None)
        if raw_user_id:
            changed_by = UUID(str(raw_user_id))

        repo = AuditRepository()
        repo.call_fn_audit_log_decision(
            entity_type=entity_type,
            entity_id=entity_id,
            decision_type=decision_type,
            old_value=old_value,
            new_value=new_value,
            reason_code=reason_code,
            reason_text=reason_text,
            changed_by=changed_by,
            is_system=False,
        )
    except Exception as exc:
        # L'audit ne doit jamais faire échouer la réponse métier
        logger.error("AuditMiddleware — échec insertion log : %s", exc)


async def _fetch_entity_state(entity_type: str, entity_id_str: str) -> Dict[str, Any]:
    """
    Récupère l'état courant de l'entité directement en base.
    Retourne un dict vide si la table/entité n'est pas connue.
    """
    _TABLE_MAP: Dict[str, str] = {
        "intervention": "intervention",
        "request": "intervention_request",
        "purchase_request": "purchase_request",
        "task": "intervention_task",
        "action": "intervention_action",
    }
    table = _TABLE_MAP.get(entity_type)
    if not table:
        return {}

    from api.db import get_connection, release_connection
    from psycopg2.extras import RealDictCursor

    conn = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {table} WHERE id = %s", (entity_id_str,))  # noqa: S608
            row = cur.fetchone()
            return dict(row) if row else {}
    except Exception as exc:
        logger.warning("_fetch_entity_state(%s, %s) : %s", entity_type, entity_id_str, exc)
        return {}
    finally:
        if conn:
            release_connection(conn)

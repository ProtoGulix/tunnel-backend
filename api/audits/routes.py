from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from api.auth.permissions import require_authenticated
from api.audits.repo import AuditRepository
from api.audits.schemas import AuditLogCreate, AuditLogOut, AuditReasonOut, BriefingReport

router = APIRouter(prefix="/audit", tags=["Audit"])


def _repo() -> AuditRepository:
    return AuditRepository()


@router.get("/reasons", response_model=List[AuditReasonOut], dependencies=[Depends(require_authenticated)])
def list_reasons(
    category: Optional[str] = Query(None, description="Filtre par catégorie : system, manual, user"),
    entity_type: Optional[str] = Query(None, description="Filtre par type d'entité compatible"),
    active_only: bool = Query(True),
    repo: AuditRepository = Depends(_repo),
):
    """Liste les raisons d'audit disponibles."""
    return repo.get_all_reasons(
        active_only=active_only,
        category=category,
        entity_type=entity_type,
    )


@router.get("/briefing", response_model=BriefingReport, dependencies=[Depends(require_authenticated)])
def get_briefing(
    from_dt: datetime = Query(..., description="Début de la fenêtre (ISO 8601)"),
    to_dt: datetime = Query(..., description="Fin de la fenêtre (ISO 8601)"),
    exclude_system: bool = Query(False, description="Exclure les mutations système"),
    repo: AuditRepository = Depends(_repo),
):
    """Rapport de toutes les décisions sur une fenêtre temporelle."""
    return repo.get_briefing(from_dt=from_dt, to_dt=to_dt, exclude_system=exclude_system)


@router.get("/logs", dependencies=[Depends(require_authenticated)])
def get_logs(
    from_dt: Optional[datetime] = Query(None),
    to_dt: Optional[datetime] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    reason_code: Optional[str] = Query(None),
    decision_type: Optional[str] = Query(None),
    changed_by: Optional[UUID] = Query(None),
    exclude_system: bool = Query(False),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    include_facets: bool = Query(False, description="Inclure les facettes entity_type, decision_type, reason_code"),
    repo: AuditRepository = Depends(_repo),
):
    """Requête paginée sur les entrées d'audit log. Retourne { items, pagination, facets }."""
    return repo.get_logs(
        from_dt=from_dt,
        to_dt=to_dt,
        entity_type=entity_type,
        entity_id=entity_id,
        reason_code=reason_code,
        decision_type=decision_type,
        changed_by=changed_by,
        exclude_system=exclude_system,
        limit=limit,
        offset=offset,
        include_facets=include_facets,
    )


@router.post("/log", status_code=201, dependencies=[Depends(require_authenticated)])
def create_log(
    request: Request,
    payload: AuditLogCreate,
    repo: AuditRepository = Depends(_repo),
):
    """
    Crée manuellement une entrée d'audit (cas d'usage : mutations système non interceptées).
    La validation métier est déléguée à fn_audit_log_decision() en base.
    """
    user_id: Optional[UUID] = getattr(request.state, "user_id", None)

    log_id = repo.call_fn_audit_log_decision(
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        decision_type=payload.decision_type,
        old_value=payload.old_value,
        new_value=payload.new_value,
        reason_code=payload.reason_code,
        reason_text=payload.reason_text,
        changed_by=user_id,
        is_system=False,
    )
    return {"id": log_id}

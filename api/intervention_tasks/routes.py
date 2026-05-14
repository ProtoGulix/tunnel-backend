from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request, Response

from api.audits.schemas import AuditRules
from api.auth.permissions import require_authenticated
from api.errors.exceptions import ValidationError
from api.intervention_tasks.repo import InterventionTaskRepository
from api.intervention_tasks.schemas import (
    InterventionTaskDelete,
    InterventionTaskIn,
    InterventionTaskOut,
    InterventionTaskPatch,
    TaskProgressOut,
)
from api.utils.audit import get_audit_rules

router = APIRouter(
    prefix="/intervention-tasks",
    tags=["Intervention Tasks"],
    dependencies=[Depends(require_authenticated)],
)


@router.get("")
def list_tasks(
    intervention_id: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Valeurs CSV : todo,in_progress,done,skipped"),
    origin: Optional[str] = Query(None, description="Valeurs CSV : plan,resp,tech"),
    include_done: bool = Query(False),
) -> Dict[str, Any]:
    """Liste les tâches avec filtres optionnels."""
    repo = InterventionTaskRepository()
    statuses = [s.strip() for s in status.split(",")] if status else None
    origins = [o.strip() for o in origin.split(",")] if origin else None
    data = repo.get_list(
        intervention_id=intervention_id,
        assigned_to=assigned_to,
        statuses=statuses,
        origins=origins,
        include_done=include_done,
    )
    return {"data": data, "audit": get_audit_rules("task")}


@router.get("/progress", response_model=TaskProgressOut)
def get_progress(
    intervention_id: Optional[str] = Query(None),
    occurrence_id: Optional[str] = Query(None),
):
    """Calcule la progression des tâches pour une intervention ou une occurrence."""
    repo = InterventionTaskRepository()
    if intervention_id:
        return repo.get_progress(intervention_id)
    if occurrence_id:
        return repo.get_progress_by_occurrence(occurrence_id)
    raise ValidationError("intervention_id ou occurrence_id requis")


@router.get("/{task_id}")
def get_task(task_id: str) -> Dict[str, Any]:
    """Récupère une tâche par ID."""
    repo = InterventionTaskRepository()
    data = repo.get_by_id(task_id)
    return {"data": data, "audit": get_audit_rules("task")}


@router.post("", response_model=InterventionTaskOut, status_code=201)
def create_task(request: Request, data: InterventionTaskIn):
    """
    Crée une tâche manuelle (origin `resp` ou `tech` uniquement).

    **Audit obligatoire** : le champ `reason_code` est requis (voir `GET /audit/reasons`).
    `reason_text` est obligatoire si `reason_code=OTHER`.
    """
    user_id = str(getattr(request.state, "user_id", None) or "")
    repo = InterventionTaskRepository()
    return repo.create(data, created_by=user_id or None)


@router.patch("/{task_id}", response_model=InterventionTaskOut)
def patch_task(request: Request, task_id: str, data: InterventionTaskPatch):
    """
    Met à jour partiellement une tâche.

    Champs modifiables : `label`, `status` (→ `skipped` uniquement via PATCH direct),
    `skip_reason`, `assigned_to`, `due_date`, `sort_order`.

    Les transitions vers `in_progress` et `done` passent obligatoirement par une action
    (`POST /intervention-actions`).

    **Audit obligatoire** : le champ `reason_code` est requis (voir `GET /audit/reasons`).
    `reason_text` est obligatoire si `reason_code=OTHER`.
    """
    user_id = str(getattr(request.state, "user_id", None) or "")
    repo = InterventionTaskRepository()
    return repo.patch(task_id, data, closed_by=user_id or None)


@router.delete("/{task_id}", status_code=204)
def delete_task(request: Request, task_id: str, data: InterventionTaskDelete):
    """
    Supprime une tâche.

    Conditions : statut `todo` ET aucune action liée.
    La suppression est tracée dans l'audit log avec le `reason_code` fourni.
    """
    user_id = str(getattr(request.state, "user_id", None) or "")
    repo = InterventionTaskRepository()
    repo.delete(task_id, deleted_by=user_id or None, reason_code=data.reason_code)
    return Response(status_code=204)

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
    intervention_id: Optional[str] = Query(None, description="Filtrer par intervention"),
    assigned_to: Optional[str] = Query(None, description="UUID technicien assigné ou 'unassigned'"),
    status: Optional[str] = Query(None, description="Valeurs CSV : todo,in_progress,done,skipped"),
    origin: Optional[str] = Query(None, description="Valeurs CSV : plan,resp,tech"),
    include_done: bool = Query(False, description="Inclure les tâches done et skipped"),
    q: Optional[str] = Query(None, description="Recherche full-text sur label, titre et code intervention"),
    skip: int = Query(0, ge=0, description="Offset (nombre d'interventions à sauter)"),
    limit: int = Query(20, ge=1, le=200, description="Nombre d'interventions par page"),
    include_actions: bool = Query(False, description="Inclure les actions liées aux tâches"),
    include_options: bool = Query(False, description="Inclure listes de filtres (users, interventions)"),
    include_counters: bool = Query(False, description="Inclure compteurs globaux"),
) -> Dict[str, Any]:
    """Liste les tâches groupées par intervention.

    Retourne `{ items, pagination, audit }` — chaque item est une intervention
    contenant ses tâches. Compatible avec GET /tasks/workspace (même mécanique).
    """
    repo = InterventionTaskRepository()
    status_list = [s.strip() for s in status.split(",")] if status else None
    origin_list = [o.strip() for o in origin.split(",")] if origin else None

    # Filtre intervention_id injecté dans assignee_id n'est pas la bonne approche —
    # on passe intervention_id comme filtre SQL direct dans get_workspace via q
    # Pour compatibilité : si intervention_id fourni, on l'ajoute au filtre assignee
    result = repo.get_workspace(
        q=q,
        status=status_list,
        origin=origin_list,
        assignee_id=assigned_to,
        intervention_id=intervention_id,
        skip=skip,
        limit=limit,
        include_closed=include_done,
        include_actions=include_actions,
        include_options=include_options,
        include_counters=include_counters,
    )
    result["audit"] = get_audit_rules("task")
    return result


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

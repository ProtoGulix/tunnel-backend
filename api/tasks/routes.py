"""Endpoints pour le workspace unifié de tâches."""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from api.tasks.repo import TasksRepository
from api.tasks.schemas import TasksWorkspaceResponse
from api.auth.permissions import require_authenticated
from api.utils.audit import get_audit_rules

router = APIRouter(
    prefix="/tasks", tags=["tasks"], dependencies=[Depends(require_authenticated)])


@router.get("/workspace", response_model=TasksWorkspaceResponse)
def get_tasks_workspace(
    q: Optional[str] = Query(
        None, description="Recherche full-text sur label, intervention title, intervention code"),
    status: Optional[str] = Query(
        None, description="Filtres statut (CSV: todo,in_progress,done,skipped)"),
    origin: Optional[str] = Query(
        None, description="Filtres origine (CSV: plan,resp,tech)"),
    assignee_id: Optional[str] = Query(
        None, description="UUID d'utilisateur ou 'unassigned'"),
    skip: int = Query(0, ge=0, description="Offset (nombre d'interventions à sauter)"),
    limit: int = Query(20, ge=1, le=200, description="Nombre d'interventions par page"),
    include_closed: bool = Query(False, description="Inclure tâches done/skipped"),
    include_actions: bool = Query(False, description="Inclure actions liées aux tâches"),
    include_options: bool = Query(False, description="Inclure listes de filtres"),
    include_counters: bool = Query(False, description="Inclure compteurs globaux"),
):
    """Interventions avec leurs tâches agrégées. Pagination offset sur les interventions.

    Chaque item de la réponse est une intervention contenant toutes ses tâches
    correspondant aux filtres actifs.
    """
    status_list = [s.strip() for s in status.split(",")] if status else None
    origin_list = [o.strip() for o in origin.split(",")] if origin else None

    repo = TasksRepository()
    result = repo.get_workspace(
        q=q,
        status=status_list,
        origin=origin_list,
        assignee_id=assignee_id,
        skip=skip,
        limit=limit,
        include_closed=include_closed,
        include_actions=include_actions,
        include_options=include_options,
        include_counters=include_counters,
    )
    result["audit"] = get_audit_rules("task")
    return result

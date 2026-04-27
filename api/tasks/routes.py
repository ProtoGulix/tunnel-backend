"""Endpoints pour le workspace unifié de tâches."""
from fastapi import APIRouter, Query, Depends
from typing import Optional, List
from api.tasks.repo import TasksRepository
from api.tasks.schemas import TasksWorkspaceResponse, TaskDetail
from api.auth.permissions import require_authenticated

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
    grouping: Optional[str] = Query(
        None, description="Groupage optionnel (intervention,machine,status,technician)"),
    cursor: Optional[str] = Query(None, description="Curseur pagination"),
    limit: int = Query(
        50, ge=1, le=200, description="Nombre de tâches par page"),
    include_closed: bool = Query(
        False, description="Inclure tâches done/skipped"),
    include_actions: bool = Query(False, description="Inclure actions liées"),
    include_options: bool = Query(
        False, description="Inclure listes de filtres"),
    include_counters: bool = Query(
        False, description="Inclure compteurs globaux"),
):
    """Endpoint unifié pour page Tasks avec tous les filtres, pagination et options.

    Réponse incluant tâches enrichies, compteurs, listes de filtres et métadonnées.
    Conçu pour minimiser les appels frontend (1 appel = tous les détails préchargés).
    """
    status_list = [s.strip() for s in status.split(",")] if status else None
    origin_list = [o.strip() for o in origin.split(",")] if origin else None

    repo = TasksRepository()
    return repo.get_workspace(
        q=q,
        status=status_list,
        origin=origin_list,
        assignee_id=assignee_id,
        grouping=grouping,
        cursor=cursor,
        limit=limit,
        include_closed=include_closed,
        include_actions=include_actions,
        include_options=include_options,
        include_counters=include_counters,
    )

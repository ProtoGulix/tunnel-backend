from fastapi import APIRouter, Request, Query
from typing import List, Dict, Any
from api.interventions.repo import InterventionRepository
from api.intervention_actions.repo import InterventionActionRepository
from api.interventions.schemas import InterventionOut
from api.intervention_actions.schemas import InterventionActionOut

router = APIRouter(prefix="/interventions", tags=["interventions"])


def add_stats_to_intervention(intervention: Dict[str, Any], actions: List[Dict[str, Any]]) -> None:
    """Ajoute les stats calculées à une intervention"""
    intervention["actions"] = actions
    intervention["total_time"] = sum(a.get("time_spent") or 0 for a in actions)
    intervention["action_count"] = len(actions)
    complexities = [a.get("complexity_score")
                    for a in actions if a.get("complexity_score")]
    intervention["avg_complexity"] = round(
        sum(complexities) / len(complexities), 2) if complexities else None


@router.get("/")
async def list_interventions(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    equipement_id: str | None = Query(
        None, description="Filtre intervention.machine_id"),
    status: str | None = Query(
        None, description="CSV de codes statut (ex: open,in_progress,ferme)"),
    priority: str | None = Query(
        None, description="CSV de priorités (faible,normale,important,urgent)"),
    sort: str | None = Query(
        None, description="Ex: -priority,-reported_date ou -reported_date"),
    include: str | None = Query(None, description="Ex: stats")
):
    """Liste interventions avec filtres/sort et stats optionnelles (sans actions)"""
    intervention_repo = InterventionRepository()

    statuses = [s.strip() for s in status.split(',')] if status else None
    priorities = [p.strip() for p in priority.split(',')] if priority else None
    include_stats = (include is None) or (
        "stats" in [i.strip() for i in include.split(',')])

    return intervention_repo.get_all(
        limit=limit,
        offset=skip,
        equipement_id=equipement_id,
        statuses=statuses,
        priorities=priorities,
        sort=sort,
        include_stats=include_stats
    )


@router.get("/{intervention_id}", response_model=InterventionOut)
async def get_intervention(intervention_id: str, request: Request):
    """Récupère une intervention par ID avec ses actions et stats (calculées en SQL)"""
    intervention_repo = InterventionRepository()
    action_repo = InterventionActionRepository()

    intervention = intervention_repo.get_by_id(intervention_id)
    intervention['actions'] = action_repo.get_by_intervention(intervention_id)

    return intervention


@router.get("/{intervention_id}/actions", response_model=List[InterventionActionOut])
async def get_intervention_actions(intervention_id: str, request: Request):
    """Récupère les actions d'une intervention"""
    repo = InterventionActionRepository()
    return repo.get_by_intervention(intervention_id)

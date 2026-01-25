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
    complexities = [a.get("complexity_score") for a in actions if a.get("complexity_score")]
    intervention["avg_complexity"] = round(sum(complexities) / len(complexities), 2) if complexities else None


@router.get("/")
async def list_interventions(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Liste interventions avec pagination et stats (sans actions détaillées)"""
    intervention_repo = InterventionRepository()
    return intervention_repo.get_all(limit=limit, offset=skip)
    
    return interventions


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

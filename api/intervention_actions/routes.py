from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import date
from uuid import UUID
from api.intervention_actions.repo import InterventionActionRepository
from api.intervention_actions.schemas import InterventionActionOut, InterventionActionIn, InterventionActionPatch, InterventionActionsByDate, InterventionActionDetail

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/intervention-actions",
                   tags=["intervention-actions"], dependencies=[Depends(require_authenticated)])


@router.get("", response_model=List[InterventionActionsByDate])
def list_actions(
    start_date: Optional[date] = Query(None, description="Date de début incluse (YYYY-MM-DD). Défaut : aujourd'hui"),
    end_date: Optional[date] = Query(None, description="Date de fin incluse (YYYY-MM-DD). Défaut : aujourd'hui"),
    tech_id: Optional[UUID] = Query(None, description="Filtre sur l'UUID du technicien"),
):
    """Liste les actions groupées par date, du plus récent au plus ancien"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date
    repo = InterventionActionRepository()
    return repo.get_all(
        date_from=start_date,
        date_to=end_date,
        tech_id=str(tech_id) if tech_id else None,
    )


@router.get("/{action_id}", response_model=InterventionActionDetail)
def get_action(action_id: str):
    """Récupère une action par ID avec le contexte complet de l'intervention parente"""
    repo = InterventionActionRepository()
    return repo.get_by_id(action_id)


@router.post("", response_model=InterventionActionOut)
def add_action(action: InterventionActionIn):
    """Ajoute une action à une intervention"""
    repo = InterventionActionRepository()
    return repo.add(action.model_dump())


@router.patch("/{action_id}", response_model=InterventionActionOut)
def patch_action(action_id: str, patch: InterventionActionPatch):
    """Met à jour partiellement une action d'intervention"""
    repo = InterventionActionRepository()
    return repo.update(action_id, patch.model_dump(exclude_none=True))

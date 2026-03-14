from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import date
from uuid import UUID
from api.intervention_actions.repo import InterventionActionRepository
from api.intervention_actions.schemas import InterventionActionOut, InterventionActionIn, InterventionActionPatch

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/intervention-actions",
                   tags=["intervention-actions"], dependencies=[Depends(require_authenticated)])


@router.get("/", response_model=List[InterventionActionOut])
async def list_actions(
    date: Optional[date] = Query(None, description="Filtre sur created_at::date"),
    tech_id: Optional[UUID] = Query(None, description="Filtre sur l'UUID du technicien"),
):
    """Liste toutes les actions avec filtres optionnels"""
    repo = InterventionActionRepository()
    return repo.get_all(filter_date=date, tech_id=str(tech_id) if tech_id else None)


@router.get("/{action_id}", response_model=InterventionActionOut)
async def get_action(action_id: str):
    """Récupère une action par ID"""
    repo = InterventionActionRepository()
    return repo.get_by_id(action_id)


@router.post("/", response_model=InterventionActionOut)
async def add_action(action: InterventionActionIn):
    """Ajoute une action à une intervention"""
    repo = InterventionActionRepository()
    return repo.add(action.model_dump())


@router.patch("/{action_id}", response_model=InterventionActionOut)
async def patch_action(action_id: str, patch: InterventionActionPatch):
    """Met à jour partiellement une action d'intervention"""
    repo = InterventionActionRepository()
    return repo.update(action_id, patch.model_dump(exclude_none=True))

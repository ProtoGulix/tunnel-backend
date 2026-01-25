from fastapi import APIRouter, Request
from typing import List
from api.intervention_actions.repo import InterventionActionRepository
from api.intervention_actions.schemas import InterventionActionOut

router = APIRouter(prefix="/intervention_actions", tags=["intervention_actions"])


@router.get("/", response_model=List[InterventionActionOut])
async def list_actions(request: Request):
    """Liste toutes les actions"""
    repo = InterventionActionRepository()
    return repo.get_all()


@router.get("/{action_id}", response_model=InterventionActionOut)
async def get_action(action_id: str, request: Request):
    """Récupère une action par ID"""
    repo = InterventionActionRepository()
    return repo.get_by_id(action_id)

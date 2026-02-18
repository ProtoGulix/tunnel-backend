from fastapi import APIRouter, HTTPException
from typing import List
from api.intervention_actions.repo import InterventionActionRepository
from api.intervention_actions.schemas import InterventionActionOut, InterventionActionIn

router = APIRouter(prefix="/intervention-actions",
                   tags=["intervention-actions"])


@router.get("/", response_model=List[InterventionActionOut])
async def list_actions():
    """Liste toutes les actions"""
    repo = InterventionActionRepository()
    return repo.get_all()


@router.get("/{action_id}", response_model=InterventionActionOut)
async def get_action(action_id: str):
    """Récupère une action par ID"""
    repo = InterventionActionRepository()
    return repo.get_by_id(action_id)


@router.post("/", response_model=InterventionActionOut)
async def add_action(action: InterventionActionIn):
    """Ajoute une action à une intervention"""
    repo = InterventionActionRepository()
    try:
        return repo.add(action.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

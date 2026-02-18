from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from api.intervention_status.repo import InterventionStatusRepository
from api.errors.exceptions import DatabaseError

router = APIRouter(prefix="/intervention-status", tags=["intervention-status"])

repo = InterventionStatusRepository()


@router.get("", response_model=List[Dict[str, Any]])
async def list_intervention_status():
    """Liste tous les statuts d'intervention disponibles"""
    try:
        return repo.get_all()
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))

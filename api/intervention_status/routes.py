from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from api.intervention_status.repo import InterventionStatusRepository
from api.errors.exceptions import DatabaseError

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/intervention-status", tags=["intervention-status"], dependencies=[Depends(require_authenticated)])

repo = InterventionStatusRepository()


@router.get("", response_model=List[Dict[str, Any]])
async def list_intervention_status():
    """Liste tous les statuts d'intervention disponibles"""
    return repo.get_all()

from fastapi import APIRouter, Request, Query
from typing import List
from api.equipements.repo import EquipementRepository
from api.equipements.schemas import EquipementOut, EquipementListItem, EquipementDetail

router = APIRouter(prefix="/equipements", tags=["equipements"])


@router.get("/", response_model=List[EquipementListItem])
async def list_equipements(request: Request):
    """Liste tous les équipements avec statistiques interventions"""
    repo = EquipementRepository()
    return repo.get_all()


@router.get("/{equipement_id}", response_model=EquipementListItem)
async def get_equipement(equipement_id: str, request: Request):
    """Récupère un équipement par ID avec statistiques interventions"""
    repo = EquipementRepository()
    return repo.get_by_id(equipement_id)


@router.get("/{equipement_id}/detail", response_model=EquipementDetail)
async def get_equipement_detail(
    equipement_id: str,
    request: Request,
    period_days: int = Query(30, description="Période en jours pour interventions décisionnelles et temps passé")
):
    """Récupère un équipement avec interventions décisionnelles et statistiques période"""
    repo = EquipementRepository()
    return repo.get_by_id_with_details(equipement_id, period_days)


@router.get("/{equipement_id}/sous_equipements", response_model=List[EquipementListItem])
async def get_sous_equipements(equipement_id: str, request: Request):
    """Récupère les sous-équipements d'un équipement parent avec statistiques"""
    repo = EquipementRepository()
    return repo.get_by_equipement_mere(equipement_id)

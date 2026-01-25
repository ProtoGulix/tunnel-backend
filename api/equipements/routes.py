from fastapi import APIRouter, Request, Query
from typing import List
from api.equipements.repo import EquipementRepository
from api.equipements.schemas import (
    EquipementListItem, EquipementDetail, EquipementStatsDetailed, EquipementHealthOnly
)

router = APIRouter(prefix="/equipements", tags=["equipements"])


@router.get("", response_model=List[EquipementListItem])
@router.get("/", response_model=List[EquipementListItem])
async def list_equipements(request: Request):
    """Liste tous les équipements - vue légère avec health"""
    repo = EquipementRepository()
    return repo.get_all()


@router.get("/{equipement_id}", response_model=EquipementDetail)
async def get_equipement(equipement_id: str, request: Request):
    """Récupère un équipement par ID avec health et children_ids"""
    repo = EquipementRepository()
    return repo.get_by_id(equipement_id)


@router.get("/{equipement_id}/stats", response_model=EquipementStatsDetailed)
async def get_equipement_stats(
    equipement_id: str,
    request: Request,
    start_date: str | None = Query(
        None, description="Date de début (YYYY-MM-DD), optionnel"),
    end_date: str | None = Query(
        None, description="Date de fin (YYYY-MM-DD), défaut = maintenant")
):
    """Récupère les statistiques détaillées d'un équipement"""
    repo = EquipementRepository()
    return repo.get_stats_by_id(equipement_id, start_date=start_date, end_date=end_date)


@router.get("/{equipement_id}/health", response_model=EquipementHealthOnly)
async def get_equipement_health(equipement_id: str, request: Request):
    """Récupère uniquement le health d'un équipement (ultra-léger)"""
    repo = EquipementRepository()
    return repo.get_health_by_id(equipement_id)

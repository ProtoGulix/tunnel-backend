"""Routes pour les équipements"""
from fastapi import APIRouter, Query
from api.equipements.repo import EquipementRepository
from api.equipements.schemas import (
    EquipementListItem, EquipementDetail, EquipementStatsDetailed, EquipementHealthOnly
)

router = APIRouter(prefix="/equipements", tags=["equipements"])


@router.get("", response_model=list[EquipementListItem])
@router.get("/", response_model=list[EquipementListItem])
async def list_equipements():
    """Liste tous les équipements - vue légère avec health"""
    repo = EquipementRepository()
    return repo.get_all()


@router.get("/{equipement_id}", response_model=EquipementDetail)
async def get_equipement(equipement_id: str):
    """Récupère un équipement par ID avec health et children_ids"""
    repo = EquipementRepository()
    return repo.get_by_id(equipement_id)


@router.get("/{equipement_id}/stats", response_model=EquipementStatsDetailed)
async def get_equipement_stats(
    equipement_id: str,
    start_date: str | None = Query(
        None, description="Date de début (YYYY-MM-DD), optionnel"),
    end_date: str | None = Query(
        None, description="Date de fin (YYYY-MM-DD), défaut = maintenant")
):
    """Récupère les statistiques détaillées d'un équipement"""
    repo = EquipementRepository()
    return repo.get_stats_by_id(equipement_id, start_date=start_date, end_date=end_date)


@router.get("/{equipement_id}/health", response_model=EquipementHealthOnly)
async def get_equipement_health(equipement_id: str):
    """Récupère uniquement le health d'un équipement (ultra-léger)"""
    repo = EquipementRepository()
    return repo.get_health_by_id(equipement_id)

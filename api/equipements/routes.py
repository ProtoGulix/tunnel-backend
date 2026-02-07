"""Routes pour les équipements"""
from fastapi import APIRouter, Query, status
from api.equipements.repo import EquipementRepository
from api.equipements.schemas import (
    EquipementListItem,
    EquipementDetail,
    EquipementStatsDetailed,
    EquipementHealthOnly,
    EquipementCreate,
    EquipementUpdate
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


@router.post("", response_model=EquipementDetail, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=EquipementDetail, status_code=status.HTTP_201_CREATED)
async def create_equipement(data: EquipementCreate):
    """Crée un nouvel équipement"""
    repo = EquipementRepository()
    return repo.add(data.model_dump(exclude_unset=True))


@router.put("/{equipement_id}", response_model=EquipementDetail)
async def update_equipement(equipement_id: str, data: EquipementUpdate):
    """Met à jour un équipement existant"""
    repo = EquipementRepository()
    return repo.update(equipement_id, data.model_dump(exclude_unset=True))


@router.delete("/{equipement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipement(equipement_id: str):
    """Supprime un équipement"""
    repo = EquipementRepository()
    repo.delete(equipement_id)
    return None


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

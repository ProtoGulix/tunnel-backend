"""Routes pour les équipements"""
from fastapi import APIRouter, Query, status, Depends
from api.equipements.repo import EquipementRepository
from api.equipements.schemas import (
    EquipementListItem,
    EquipementDetail,
    EquipementChildrenPaginated,
    EquipementStatsDetailed,
    EquipementHealthOnly,
    EquipementCreate,
    EquipementUpdate
)

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/equipements", tags=["equipements"], dependencies=[Depends(require_authenticated)])


@router.get("", response_model=list[EquipementListItem])
@router.get("/", response_model=list[EquipementListItem])
async def list_equipements(
    search: str | None = Query(None, description="Recherche insensible à la casse sur code, nom ou affectation")
):
    """Liste tous les équipements - vue légère avec health"""
    repo = EquipementRepository()
    return repo.get_all(search=search)


@router.get("/{equipement_id}", response_model=EquipementDetail)
async def get_equipement(
    equipement_id: str,
    interventions_page: int = Query(1, ge=1, description="Page des interventions"),
    interventions_limit: int = Query(20, ge=1, le=100, description="Nombre d'interventions par page")
):
    """Récupère un équipement par ID avec tous les champs, children_count et interventions paginées"""
    repo = EquipementRepository()
    return repo.get_by_id(
        equipement_id,
        interventions_page=interventions_page,
        interventions_limit=interventions_limit
    )


@router.get("/{equipement_id}/children", response_model=EquipementChildrenPaginated)
async def get_equipement_children(
    equipement_id: str,
    page: int = Query(1, ge=1, description="Page"),
    limit: int = Query(20, ge=1, le=100, description="Nombre d'enfants par page"),
    search: str | None = Query(None, description="Filtre sur code ou nom")
):
    """Récupère les enfants paginés d'un équipement avec health"""
    repo = EquipementRepository()
    return repo.get_children(equipement_id, page=page, limit=limit, search=search)


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

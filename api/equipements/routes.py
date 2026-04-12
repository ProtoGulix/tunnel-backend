"""Routes pour les équipements"""
from fastapi import APIRouter, Query, status, Depends
from api.equipements.repo import EquipementRepository
from api.equipements.schemas import (
    EquipementListPaginated,
    EquipementDetail,
    EquipementStatsDetailed,
    EquipementHealthOnly,
    EquipementCreate,
    EquipementUpdate,
    EquipementPatch
)
from api.utils.pagination import create_pagination_meta

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/equipements",
                   tags=["equipements"], dependencies=[Depends(require_authenticated)])


@router.get("", response_model=EquipementListPaginated)
def list_equipements(
    search: str | None = Query(
        None, description="Recherche insensible à la casse sur code, nom ou affectation"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    exclude_class: str | None = Query(
        None, description="Codes de classes à exclure, séparés par virgule. Ex: POM,SCI"),
    select_class: str | None = Query(
        None, description="Codes de classes à inclure (filtre exclusif), séparés par virgule. Ex: POM,SCI"),
    select_mere: str | None = Query(
        None, description="UUID de l'équipement parent : retourne uniquement ses enfants directs"),
):
    """Liste les équipements avec pagination et facettes par classe"""
    repo = EquipementRepository()
    exclude_list = [c.strip() for c in exclude_class.split(",")
                    if c.strip()] if exclude_class else None
    select_list = [c.strip() for c in select_class.split(",")
                   if c.strip()] if select_class else None
    items = repo.get_all(search=search, skip=skip, limit=limit,
                         exclude_class=exclude_list, select_class=select_list, select_mere=select_mere)
    total = repo.count_all(
        search=search, exclude_class=exclude_list, select_class=select_list, select_mere=select_mere)
    facets = repo.get_facets(search=search)
    return {
        "items": items,
        "pagination": create_pagination_meta(total=total, offset=skip, limit=limit, count=len(items)),
        "facets": {
            "equipement_class": facets,
        },
    }


@router.get("/{equipement_id}", response_model=EquipementDetail)
def get_equipement(
    equipement_id: str,
    interventions_page: int = Query(
        1, ge=1, description="Page des interventions"),
    interventions_limit: int = Query(
        20, ge=1, le=100, description="Nombre d'interventions par page")
):
    """Récupère un équipement par ID avec tous les champs, children_count et interventions paginées"""
    repo = EquipementRepository()
    return repo.get_by_id(
        equipement_id,
        interventions_page=interventions_page,
        interventions_limit=interventions_limit
    )


@router.post("", response_model=EquipementDetail, status_code=status.HTTP_201_CREATED)
def create_equipement(data: EquipementCreate):
    """Crée un nouvel équipement"""
    repo = EquipementRepository()
    return repo.add(data.model_dump(exclude_unset=True))


@router.put("/{equipement_id}", response_model=EquipementDetail)
def update_equipement(equipement_id: str, data: EquipementUpdate):
    """Remplace complètement un équipement (tous les champs non envoyés passent à null)"""
    repo = EquipementRepository()
    return repo.update(equipement_id, data.model_dump())


@router.patch("/{equipement_id}", response_model=EquipementDetail)
def patch_equipement(equipement_id: str, data: EquipementPatch):
    """Met à jour partiellement un équipement (seuls les champs envoyés sont modifiés)"""
    repo = EquipementRepository()
    return repo.update(equipement_id, data.model_dump(exclude_unset=True))


@router.delete("/{equipement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipement(equipement_id: str):
    """Supprime un équipement"""
    repo = EquipementRepository()
    repo.delete(equipement_id)
    return None


@router.get("/{equipement_id}/stats", response_model=EquipementStatsDetailed)
def get_equipement_stats(
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
def get_equipement_health(equipement_id: str):
    """Récupère uniquement le health d'un équipement (ultra-léger)"""
    repo = EquipementRepository()
    return repo.get_health_by_id(equipement_id)

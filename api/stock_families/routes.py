"""Routes pour les familles de stock"""
from fastapi import APIRouter, Query, Depends
from typing import List, Optional

from api.stock_families.repo import StockFamilyRepository
from api.stock_families.schemas import StockFamilyListItem, StockFamilyDetail, StockFamilyPatch, StockFamilyIn
from api.errors.exceptions import DatabaseError, NotFoundError

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/stock-families",
                   tags=["stock-families"], dependencies=[Depends(require_authenticated)])


@router.get("/", response_model=List[StockFamilyListItem])
def list_stock_families():
    """
    Liste toutes les familles de stock

    Retourne la liste des codes de famille avec le nombre de sous-familles associées.
    Triées par code famille.
    """
    repo = StockFamilyRepository()
    return repo.get_all()


@router.get("/{family_code}", response_model=StockFamilyDetail)
def get_stock_family(
    family_code: str,
    search: Optional[str] = Query(
        None, description="Filtre sur code ou label des sous-familles")
):
    """
    Récupère une famille par son code avec ses sous-familles

    Args:
        family_code: Code de la famille
        search: Filtre optionnel sur code ou label des sous-familles (ILIKE)

    Returns:
        Détail de la famille incluant la liste de toutes ses sous-familles
        avec indication si elles ont un template associé
    """
    repo = StockFamilyRepository()
    return repo.get_by_code(family_code, search=search)


@router.post("/", response_model=StockFamilyDetail, status_code=201)
def create_stock_family(data: StockFamilyIn):
    """Crée une nouvelle famille de stock"""
    repo = StockFamilyRepository()
    return repo.create(data)


@router.patch("/{family_code}", response_model=StockFamilyDetail)
def patch_stock_family(family_code: str, data: StockFamilyPatch):
    """Renomme une famille de stock (met à jour family_code sur toutes les sous-familles)"""
    repo = StockFamilyRepository()
    return repo.update(family_code, data.code, data.label)

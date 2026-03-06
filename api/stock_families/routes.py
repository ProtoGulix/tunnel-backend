"""Routes pour les familles de stock"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from api.stock_families.repo import StockFamilyRepository
from api.stock_families.schemas import StockFamilyListItem, StockFamilyDetail, StockFamilyPatch
from api.errors.exceptions import DatabaseError, NotFoundError

router = APIRouter(prefix="/stock-families", tags=["stock-families"])


@router.get("/", response_model=List[StockFamilyListItem])
async def list_stock_families():
    """
    Liste toutes les familles de stock

    Retourne la liste des codes de famille avec le nombre de sous-familles associées.
    Triées par code famille.
    """
    repo = StockFamilyRepository()
    try:
        return repo.get_all()
    except (DatabaseError, Exception) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{family_code}", response_model=StockFamilyDetail)
async def get_stock_family(
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
    try:
        return repo.get_by_code(family_code, search=search)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{family_code}", response_model=StockFamilyDetail)
async def patch_stock_family(family_code: str, data: StockFamilyPatch):
    """Renomme une famille de stock (met à jour family_code sur toutes les sous-familles)"""
    repo = StockFamilyRepository()
    try:
        return repo.update(family_code, data.code, data.label)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

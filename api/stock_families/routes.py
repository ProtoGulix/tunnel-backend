"""Routes pour les familles de stock"""
from fastapi import APIRouter, HTTPException
from typing import List

from api.stock_families.repo import StockFamilyRepository
from api.stock_families.schemas import StockFamilyListItem, StockFamilyDetail
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
async def get_stock_family(family_code: str):
    """
    Récupère une famille par son code avec ses sous-familles

    Args:
        family_code: Code de la famille

    Returns:
        Détail de la famille incluant la liste de toutes ses sous-familles
        avec indication si elles ont un template associé
    """
    repo = StockFamilyRepository()
    try:
        return repo.get_by_code(family_code)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

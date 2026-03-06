from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.manufacturer_items.repo import ManufacturerItemRepository
from api.manufacturer_items.schemas import ManufacturerItemIn, ManufacturerItemOut, ManufacturerItemDetail
from api.errors.exceptions import NotFoundError
from api.utils.pagination import create_pagination_meta

router = APIRouter(prefix="/manufacturer-items", tags=["manufacturer-items"])


@router.get("/")
async def list_manufacturer_items(
    skip: int = Query(0, ge=0, description="Offset de pagination"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Nombre max d'éléments par page"),
    search: Optional[str] = Query(
        None, description="Recherche par nom fabricant ou référence")
):
    """Liste les références fabricants avec pagination et recherche"""
    repo = ManufacturerItemRepository()
    items = repo.get_all(limit=limit, offset=skip, search=search)
    total = repo.count_all(search=search)
    return {
        "items": items,
        "pagination": create_pagination_meta(total=total, offset=skip, limit=limit, count=len(items))
    }


@router.get("/{item_id}", response_model=ManufacturerItemDetail)
async def get_manufacturer_item(item_id: str):
    """Récupère une référence fabricant avec ses références fournisseurs liées"""
    repo = ManufacturerItemRepository()
    try:
        return repo.get_by_id_with_suppliers(item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/", response_model=ManufacturerItemOut, status_code=201)
async def create_manufacturer_item(data: ManufacturerItemIn):
    """Crée une nouvelle référence fabricant"""
    repo = ManufacturerItemRepository()
    try:
        return repo.add(data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/{item_id}", response_model=ManufacturerItemOut)
async def patch_manufacturer_item(item_id: str, data: ManufacturerItemIn):
    """Met à jour une référence fabricant"""
    repo = ManufacturerItemRepository()
    try:
        return repo.update(item_id, data.model_dump(exclude_none=True))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{item_id}", status_code=204)
async def delete_manufacturer_item(item_id: str):
    """Supprime une référence fabricant"""
    repo = ManufacturerItemRepository()
    try:
        repo.delete(item_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

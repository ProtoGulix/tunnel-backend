from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from api.stock_items.repo import StockItemRepository
from api.stock_items.schemas import StockItemOut, StockItemIn, StockItemListItem

router = APIRouter(prefix="/stock_items", tags=["stock_items"])


class QuantityUpdate(BaseModel):
    """Schéma pour la mise à jour de quantité"""
    quantity: int


@router.get("/", response_model=List[StockItemListItem])
async def list_stock_items(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max d'éléments"),
    family_code: Optional[str] = Query(None, description="Filtrer par code famille"),
    sub_family_code: Optional[str] = Query(None, description="Filtrer par code sous-famille"),
    search: Optional[str] = Query(None, description="Recherche par nom ou référence")
):
    """Liste tous les articles en stock avec filtres optionnels"""
    repo = StockItemRepository()
    return repo.get_all(
        limit=limit,
        offset=skip,
        family_code=family_code,
        sub_family_code=sub_family_code,
        search=search
    )


@router.get("/ref/{ref}", response_model=StockItemOut)
async def get_stock_item_by_ref(ref: str):
    """Récupère un article par sa référence"""
    repo = StockItemRepository()
    return repo.get_by_ref(ref)


@router.get("/{item_id}", response_model=StockItemOut)
async def get_stock_item(item_id: str):
    """Récupère un article par ID"""
    repo = StockItemRepository()
    return repo.get_by_id(item_id)


@router.post("/", response_model=StockItemOut)
async def create_stock_item(item: StockItemIn):
    """Crée un nouvel article en stock"""
    repo = StockItemRepository()
    try:
        return repo.add(item.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{item_id}", response_model=StockItemOut)
async def update_stock_item(item_id: str, item: StockItemIn):
    """Met à jour un article existant"""
    repo = StockItemRepository()
    try:
        return repo.update(item_id, item.model_dump(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/{item_id}/quantity", response_model=StockItemOut)
async def update_stock_quantity(item_id: str, data: QuantityUpdate):
    """Met à jour uniquement la quantité d'un article"""
    repo = StockItemRepository()
    try:
        return repo.update_quantity(item_id, data.quantity)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{item_id}")
async def delete_stock_item(item_id: str):
    """Supprime un article"""
    repo = StockItemRepository()
    try:
        repo.delete(item_id)
        return {"message": f"Article {item_id} supprimé"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

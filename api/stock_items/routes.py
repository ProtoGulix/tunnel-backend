from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from api.stock_items.repo import StockItemRepository
from api.stock_items.schemas import StockItemOut, StockItemIn, StockItemListItem
from api.stock_items.stock_item_service import StockItemService
from api.stock_items.template_schemas import StockItemWithCharacteristics
from api.errors.exceptions import ValidationError, NotFoundError, DatabaseError
from api.utils.pagination import PaginatedResponse, create_pagination_meta

router = APIRouter(prefix="/stock-items", tags=["stock-items"])


class QuantityUpdate(BaseModel):
    """Schéma pour la mise à jour de quantité"""
    quantity: int


@router.get("/", response_model=PaginatedResponse[StockItemListItem])
async def list_stock_items(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(50, ge=1, le=1000,
                       description="Nombre max d'éléments par page"),
    family_code: Optional[str] = Query(
        None, description="Filtrer par code famille"),
    sub_family_code: Optional[str] = Query(
        None, description="Filtrer par code sous-famille"),
    search: Optional[str] = Query(
        None, description="Recherche par nom ou référence")
):
    """Liste tous les articles en stock avec filtres optionnels et pagination"""
    repo = StockItemRepository()

    # Récupérer les items
    items = repo.get_all(
        limit=limit,
        offset=skip,
        family_code=family_code,
        sub_family_code=sub_family_code,
        search=search
    )

    # Récupérer le total
    total = repo.count_all(
        family_code=family_code,
        sub_family_code=sub_family_code,
        search=search
    )

    # Créer la réponse paginée
    pagination_meta = create_pagination_meta(
        total=total,
        offset=skip,
        limit=limit,
        count=len(items)
    )

    return PaginatedResponse(items=items, pagination=pagination_meta)


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


@router.get("/{item_id}/with-characteristics", response_model=StockItemWithCharacteristics)
async def get_stock_item_with_characteristics(item_id: str):
    """Récupère un article avec ses caractéristiques (si template)"""
    service = StockItemService()
    try:
        return service.get_item_with_characteristics(item_id)
    except (NotFoundError, DatabaseError) as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/", response_model=StockItemOut)
async def create_stock_item(item: StockItemIn):
    """Crée un nouvel article en stock (legacy ou template-based)"""
    service = StockItemService()
    try:
        return service.create_stock_item(item.model_dump())
    except (ValidationError, NotFoundError, DatabaseError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{item_id}", response_model=StockItemOut)
async def update_stock_item(item_id: str, item: StockItemIn):
    """Met à jour un article existant (respect immutabilité template)"""
    service = StockItemService()
    try:
        return service.update_stock_item(item_id, item.model_dump(exclude_unset=True))
    except (ValidationError, NotFoundError, DatabaseError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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

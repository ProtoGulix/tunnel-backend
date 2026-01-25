from fastapi import APIRouter, Request
from typing import List
from api.action_subcategories.repo import ActionSubcategoryRepository
from api.action_subcategories.schemas import ActionSubcategoryOut

router = APIRouter(prefix="/action_subcategories", tags=["action_subcategories"])


@router.get("/", response_model=List[ActionSubcategoryOut])
async def list_subcategories(request: Request):
    """Liste toutes les sous-catégories d'actions"""
    repo = ActionSubcategoryRepository()
    return repo.get_all()


@router.get("/{subcategory_id}", response_model=ActionSubcategoryOut)
async def get_subcategory(subcategory_id: int, request: Request):
    """Récupère une sous-catégorie par ID"""
    repo = ActionSubcategoryRepository()
    return repo.get_by_id(subcategory_id)

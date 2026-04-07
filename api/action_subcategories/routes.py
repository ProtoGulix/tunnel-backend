from fastapi import APIRouter, Request, Depends
from typing import List
from api.action_subcategories.repo import ActionSubcategoryRepository
from api.action_subcategories.schemas import ActionSubcategoryOut

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/action-subcategories", tags=["action-subcategories"], dependencies=[Depends(require_authenticated)])


@router.get("", response_model=List[ActionSubcategoryOut])
def list_subcategories(request: Request):
    """Liste toutes les sous-catégories d'actions"""
    repo = ActionSubcategoryRepository()
    return repo.get_all()


@router.get("/{subcategory_id}", response_model=ActionSubcategoryOut)
def get_subcategory(subcategory_id: int, request: Request):
    """Récupère une sous-catégorie par ID"""
    repo = ActionSubcategoryRepository()
    return repo.get_by_id(subcategory_id)

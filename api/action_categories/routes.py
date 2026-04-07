from fastapi import APIRouter, Request, Depends
from typing import List
from api.action_categories.repo import ActionCategoryRepository
from api.action_categories.schemas import ActionCategoryOut
from api.action_subcategories.repo import ActionSubcategoryRepository
from api.action_subcategories.schemas import ActionSubcategoryOut

from api.auth.permissions import require_authenticated

router = APIRouter(prefix="/action-categories", tags=["action-categories"], dependencies=[Depends(require_authenticated)])


@router.get("", response_model=List[ActionCategoryOut])
def list_categories(request: Request):
    """Liste toutes les catégories d'actions"""
    repo = ActionCategoryRepository()
    return repo.get_all()


@router.get("/{category_id}", response_model=ActionCategoryOut)
def get_category(category_id: int, request: Request):
    """Récupère une catégorie par ID"""
    repo = ActionCategoryRepository()
    return repo.get_by_id(category_id)


@router.get("/{category_id}/subcategories", response_model=List[ActionSubcategoryOut])
def get_category_subcategories(category_id: int, request: Request):
    """Récupère les sous-catégories d'une catégorie"""
    subcategory_repo = ActionSubcategoryRepository()
    return subcategory_repo.get_by_category(category_id)

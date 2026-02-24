from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from api.action_subcategories.schemas import ActionSubcategoryBase


class ActionCategoryBase(BaseModel):
    """Schéma de base pour une catégorie d'action"""
    id: int
    name: str
    code: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True


class ActionCategoryOut(ActionCategoryBase):
    """Schéma de sortie pour une catégorie avec sous-catégories imbriquées"""
    subcategories: List['ActionSubcategoryBase'] = []

    class Config:
        from_attributes = True


# Résolution des références forward après import
from api.action_subcategories.schemas import ActionSubcategoryBase  # noqa: E402
ActionCategoryOut.model_rebuild()

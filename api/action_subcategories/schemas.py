from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from api.action_categories.schemas import ActionCategoryBase


class ActionSubcategoryBase(BaseModel):
    """Schéma de base pour une sous-catégorie d'action"""
    id: int
    category_id: Optional[int] = None
    name: str
    code: Optional[str] = None

    class Config:
        from_attributes = True


class ActionSubcategoryOut(ActionSubcategoryBase):
    """Schéma de sortie pour une sous-catégorie avec catégorie imbriquée"""
    category: Optional['ActionCategoryBase'] = None

    class Config:
        from_attributes = True


# Résolution des références forward après import
from api.action_categories.schemas import ActionCategoryBase  # noqa: E402
ActionSubcategoryOut.model_rebuild()

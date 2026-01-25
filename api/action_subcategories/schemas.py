from pydantic import BaseModel
from typing import Optional


class ActionSubcategoryOut(BaseModel):
    """Schéma de sortie pour une sous-catégorie d'action"""
    id: int
    category_id: Optional[int] = None
    name: str
    code: Optional[str] = None

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import Optional


class ActionCategoryOut(BaseModel):
    """Schéma de sortie pour une catégorie d'action"""
    id: int
    name: str
    code: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True

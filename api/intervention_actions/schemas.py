from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class ActionCategoryDetail(BaseModel):
    """Détail de catégorie d'action"""
    id: int
    name: str
    code: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True


class ActionSubcategoryDetail(BaseModel):
    """Sous-catégorie avec catégorie parent imbriquée"""
    id: int
    name: str
    code: Optional[str] = None
    category: Optional[ActionCategoryDetail] = None

    class Config:
        from_attributes = True


class InterventionActionOut(BaseModel):
    """Schéma de sortie pour une action d'intervention"""
    id: UUID
    intervention_id: Optional[UUID] = None
    description: Optional[str] = None
    time_spent: Optional[float] = None
    subcategory: Optional[ActionSubcategoryDetail] = None
    tech: Optional[UUID] = None
    complexity_score: Optional[int] = None
    complexity_anotation: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

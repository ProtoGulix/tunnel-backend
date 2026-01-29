from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class InterventionActionIn(BaseModel):
    """Schéma d'entrée pour créer une action d'intervention"""
    intervention_id: UUID
    description: str
    time_spent: float
    action_subcategory: int
    tech: UUID
    complexity_score: int
    complexity_anotation: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)  # String format, validator convertira en datetime

    class Config:
        from_attributes = True


class ActionCategoryDetail(BaseModel):
    """Détail de catégorie d'action"""
    id: int
    name: str
    code: Optional[str] = Field(default=None)
    color: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True


class ActionSubcategoryDetail(BaseModel):
    """Sous-catégorie avec catégorie parent imbriquée"""
    id: int
    name: str
    code: Optional[str] = Field(default=None)
    category: Optional[ActionCategoryDetail] = Field(default=None)

    class Config:
        from_attributes = True


class InterventionActionOut(BaseModel):
    """Schéma de sortie pour une action d'intervention"""
    id: UUID
    intervention_id: Optional[UUID] = Field(default=None)
    description: Optional[str] = Field(default=None)
    time_spent: Optional[float] = Field(default=None)
    subcategory: Optional[ActionSubcategoryDetail] = Field(default=None)
    tech: Optional[UUID] = Field(default=None)
    complexity_score: Optional[int] = Field(default=None)
    complexity_anotation: Optional[dict] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True

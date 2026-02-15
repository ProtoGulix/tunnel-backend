from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from api.users.schemas import UserListItem


class InterventionActionIn(BaseModel):
    """Schéma d'entrée pour créer une action d'intervention"""
    intervention_id: UUID
    description: str
    time_spent: float
    action_subcategory: int
    tech: UUID
    complexity_score: int
    complexity_factor: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)

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
    tech: Optional[UserListItem] = Field(default=None)
    complexity_score: Optional[int] = Field(default=None)
    complexity_factor: Optional[str] = Field(default=None)
    purchase_requests: List[Any] = Field(
        default_factory=list,
        description="Demandes d'achat liées (PurchaseRequestOut) via table de jonction"
    )
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True

from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime, time, date
from uuid import UUID
from api.users.schemas import UserListItem
from api.purchase_requests.schemas import PurchaseRequestListItem


class GammeStepValidationRequest(BaseModel):
    """Requête pour valider/skipper un step de gamme lors de la création d'action"""
    step_validation_id: UUID = Field(
        description="ID du gamme_step_validation à valider/skipper"
    )
    status: str = Field(
        description="'validated' pour lier l'action, 'skipped' pour ignorer l'étape"
    )
    skip_reason: Optional[str] = Field(
        default=None,
        description="Motif du skip (OBLIGATOIRE si status='skipped')"
    )

    @model_validator(mode="after")
    def validate_skip_logic(self) -> "GammeStepValidationRequest":
        """Valide que skip_reason est cohérent avec le status"""
        if self.status not in ("validated", "skipped"):
            raise ValueError("status doit être 'validated' ou 'skipped'")

        if self.status == "skipped" and not (self.skip_reason or "").strip():
            raise ValueError("skip_reason est obligatoire quand status='skipped'")

        if self.status == "validated" and self.skip_reason:
            raise ValueError("skip_reason doit être null quand status='validated'")

        return self


class InterventionActionIn(BaseModel):
    """Schéma d'entrée pour créer une action d'intervention"""
    intervention_id: UUID
    description: str
    time_spent: Optional[float] = Field(default=None)
    action_subcategory: int
    tech: UUID
    complexity_score: int
    complexity_factor: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    action_start: Optional[time] = Field(default=None)
    action_end: Optional[time] = Field(default=None)
    # Embarquement optionnel de la validation de plusieurs gamme steps
    gamme_step_validations: Optional[List[GammeStepValidationRequest]] = Field(
        default=None,
        description="Liste optionnelle de steps à valider/skipper après création de l'action"
    )

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


class InterventionActionPatch(BaseModel):
    """Schéma de mise à jour partielle d'une action d'intervention"""
    description: Optional[str] = Field(default=None)
    time_spent: Optional[float] = Field(default=None)
    action_subcategory: Optional[int] = Field(default=None)
    tech: Optional[UUID] = Field(default=None)
    complexity_score: Optional[int] = Field(default=None)
    complexity_factor: Optional[str] = Field(default=None)
    action_start: Optional[time] = Field(default=None)
    action_end: Optional[time] = Field(default=None)
    created_at: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True


class InterventionRef(BaseModel):
    """Intervention légère embarquée dans une action"""
    id: UUID
    code: Optional[str] = None
    title: Optional[str] = None
    status_actual: Optional[str] = None
    equipement_id: Optional[UUID] = None
    equipement_code: Optional[str] = None
    equipement_name: Optional[str] = None

    class Config:
        from_attributes = True


class InterventionActionOut(BaseModel):
    """Schéma de sortie pour une action d'intervention"""
    id: UUID
    intervention_id: Optional[UUID] = Field(default=None)
    intervention: Optional[InterventionRef] = Field(default=None)
    description: Optional[str] = Field(default=None)
    time_spent: Optional[float] = Field(default=None)
    subcategory: Optional[ActionSubcategoryDetail] = Field(default=None)
    tech: Optional[UserListItem] = Field(default=None)
    complexity_score: Optional[int] = Field(default=None)
    complexity_factor: Optional[str] = Field(default=None)
    action_start: Optional[time] = None
    action_end: Optional[time] = None
    purchase_requests: List[PurchaseRequestListItem] = Field(default_factory=list)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class InterventionActionsByDate(BaseModel):
    """Actions groupées par jour — réponse de GET /intervention-actions"""
    date: date
    actions: List[InterventionActionOut]

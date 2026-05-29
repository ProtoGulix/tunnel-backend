from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditReasonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    label: str
    category: str
    color: Optional[str] = None
    description: Optional[str] = None


class AuditUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    initials: Optional[str] = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: str
    entity_id: UUID
    decision_type: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    reason: AuditReasonOut
    reason_text: Optional[str] = None
    changed_by: Optional[AuditUserOut] = None
    is_system: bool
    logged_at: datetime


class BriefingDecision(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    entity_type: str
    entity_id: UUID
    decision_type: str
    from_value: Any = None
    to_value: Any = None
    reason_code: str
    reason_label: str
    reason_color: Optional[str] = None
    reason_text: Optional[str] = None
    changed_by: Optional[UUID] = None
    is_system: bool


class BriefingSummary(BaseModel):
    total_decisions: int
    by_entity_type: Dict[str, int]
    by_decision_type: Dict[str, int]


class BriefingReport(BaseModel):
    session_start: datetime
    session_end: datetime
    duration_minutes: float
    decisions: List[BriefingDecision]
    summary: BriefingSummary


class AuditRuleReason(BaseModel):
    """Raison d'audit exposée dans les règles d'un endpoint."""
    model_config = ConfigDict(from_attributes=True)

    code: str
    label: str
    color: Optional[str] = None
    requires_text: bool = False


class AuditRules(BaseModel):
    """Règles d'audit portées par la réponse d'un endpoint GET.

    - required=True  : toute mutation doit inclure un reason_code
    - silent=True    : le front envoie default_reason_code sans afficher de sélecteur
    - silent=False   : le front affiche un picker parmi reasons
    """
    model_config = ConfigDict(from_attributes=True)

    required: bool
    silent: bool = False
    default_reason_code: Optional[str] = None
    silent_fields: Optional[List[str]] = None
    reasons: List[AuditRuleReason]


class AuditLogCreate(BaseModel):
    """Payload pour créer manuellement une entrée d'audit (via API directe)."""
    entity_type: str = Field(
        ..., description="Type d'entité : intervention, request, task, action, purchase_request")
    entity_id: UUID
    decision_type: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    reason_code: str
    reason_text: Optional[str] = None

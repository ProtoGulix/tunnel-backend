from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Any
from uuid import UUID
from datetime import datetime


# --- Utilisateurs ---

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    initial: str
    role_id: UUID


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    initial: Optional[str] = None


class AdminUserRolePatch(BaseModel):
    role_id: UUID


class AdminUserActivePatch(BaseModel):
    is_active: bool


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    initial: str
    role_id: UUID
    role_code: Optional[str] = None
    auth_provider: str
    is_active: bool
    provisioning: str
    created_at: datetime
    updated_at: datetime


class AdminUserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    initial: str
    role_code: Optional[str] = None
    is_active: bool
    auth_provider: str


class PasswordResetOut(BaseModel):
    temporary_password: str
    message: str


# --- Rôles et permissions ---

class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    label: str
    created_at: datetime


class EndpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    method: str
    path: str
    description: Optional[str] = None
    module: Optional[str] = None
    is_sensitive: bool


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role_id: UUID
    endpoint_id: UUID
    endpoint_code: Optional[str] = None
    endpoint_method: Optional[str] = None
    endpoint_path: Optional[str] = None
    allowed: bool


class PermissionPatch(BaseModel):
    allowed: bool


class EndpointPatch(BaseModel):
    description: Optional[str] = None
    module: Optional[str] = None
    is_sensitive: Optional[bool] = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    changed_by: UUID
    changed_by_email: Optional[str] = None
    role_id: UUID
    role_code: Optional[str] = None
    endpoint_id: UUID
    endpoint_code: Optional[str] = None
    old_allowed: Optional[bool] = None
    new_allowed: bool
    created_at: datetime


# --- Référentiel actions ---

class ActionCategoryPatch(BaseModel):
    label: Optional[str] = None
    color: Optional[str] = None


class ActionCategoryActivePatch(BaseModel):
    is_active: bool


class ActionSubcategoryCreate(BaseModel):
    code: str
    label: str
    category_id: int


class ActionSubcategoryPatch(BaseModel):
    label: Optional[str] = None


class ActionSubcategoryActivePatch(BaseModel):
    is_active: bool


class ComplexityFactorPatch(BaseModel):
    label: Optional[str] = None
    category: Optional[str] = None


class ComplexityFactorActivePatch(BaseModel):
    is_active: bool


# --- Référentiel interventions ---

class InterventionTypeCreate(BaseModel):
    code: str
    label: str


class InterventionTypePatch(BaseModel):
    label: Optional[str] = None


class InterventionTypeActivePatch(BaseModel):
    is_active: bool


class InterventionStatusPatch(BaseModel):
    label: Optional[str] = None
    color: Optional[str] = None


# --- Sécurité ---

class SecurityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    event_type: str
    user_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    detail: Optional[Any] = None
    created_at: datetime


class IpBlocklistCreate(BaseModel):
    ip_address: str
    reason: Optional[str] = None
    blocked_until: Optional[datetime] = None


class IpBlocklistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ip_address: str
    reason: Optional[str] = None
    blocked_until: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime


class EmailDomainRuleCreate(BaseModel):
    domain: str
    allowed: bool = True


class EmailDomainRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    domain: str
    allowed: bool
    created_at: datetime


# --- Mail ---

class MailSettingsOut(BaseModel):
    mail_enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from: str
    smtp_from_name: str
    smtp_starttls: bool
